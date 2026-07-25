import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from app.domain.models import AfCFTACheckRequest, AfCFTACheckResponse
from app.infrastructure.db.afcfta_queries import (
    query_tariff_schedule,
    query_roo_requirements,
    format_afcfta_context,
    compute_tariff_saving,
)
from app.infrastructure.supabase import get_supabase_admin
from app.infrastructure.redis_client import redis_service
from app.infrastructure.ai.intelligence import intelligence_service
from app.api.v1.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/afcfta", tags=["AfCFTA"])


@router.post("/check", response_model=AfCFTACheckResponse)
async def check_afcfta(
    request: AfCFTACheckRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        hs_prefix = request.hs_code[:4] if len(request.hs_code) >= 4 else request.hs_code

        cache_key = f"afcfta:{request.hs_code}:{request.destination_country}"
        if redis_service.redis:
            try:
                cached = redis_service.redis.get(cache_key)
                if cached:
                    logger.info("AfCFTA cache hit for %s", cache_key)
                    return AfCFTACheckResponse(**json.loads(cached))
            except Exception as e:
                logger.warning("Redis read failed: %s", e)

        tariff = await query_tariff_schedule(request.hs_code, request.destination_country)
        roo_rules = await query_roo_requirements(hs_prefix)
        supplementary = format_afcfta_context(tariff, roo_rules, request.destination_country)

        compliance = await intelligence_service.analyze_compliance(
            product_name=request.product_name,
            hs_code=request.hs_code,
            direction="export",
            supplementary_context=supplementary,
        )

        eligible = bool(
            compliance.get("afcfta_eligible")
            or compliance.get("status") == "compliant"
        )
        roo_eligible = bool(compliance.get("roo_eligible", False))
        tariff_saving = compute_tariff_saving(tariff, compliance)

        response = AfCFTACheckResponse(
            eligible=eligible,
            tariff_saving_percent=tariff_saving,
            roo_eligible=roo_eligible,
            explanation=compliance.get("summary", ""),
            suggested_hs_code=compliance.get("suggested_hs_code") or request.hs_code,
        )

        supabase = get_supabase_admin()
        record = {
            "user_id": user_id,
            "hs_code": request.hs_code,
            "product_description": request.product_name,
            "destination_country": request.destination_country,
            "roo_eligible": response.roo_eligible,
            "tariff_saving_percent": response.tariff_saving_percent,
            "ai_explanation": response.explanation,
        }
        supabase.from_("afcfta_checks").insert(record).execute()

        if redis_service.redis:
            try:
                redis_service.redis.set(cache_key, response.model_dump_json(), ex=86400)
            except Exception as e:
                logger.warning("Redis write failed: %s", e)

        return response

    except Exception as e:
        logger.exception("AfCFTA check failed")
        raise HTTPException(status_code=500, detail="AfCFTA check failed")
