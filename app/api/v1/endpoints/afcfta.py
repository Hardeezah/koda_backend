from fastapi import APIRouter, HTTPException
from app.domain.models import (
    AfCFTACheckRequest, 
    AfCFTACheckResponse,
    ComplianceReport,
    TradeStatus
)
from app.infrastructure.db.afcfta_queries import (
    query_tariff_schedule, 
    query_roo_requirements, 
    query_afcfta_guide
)
from app.infrastructure.supabase import get_supabase_admin
from app.infrastructure.redis_client import redis_service
from app.infrastructure.ai.intelligence import intelligence_service
import json

router = APIRouter(prefix="/afcfta", tags=["AfCFTA"])


@router.post("/check", response_model=AfCFTACheckResponse)
async def check_afcfta(request: AfCFTACheckRequest):
    try:
        # Fetch supporting data (you can remove await if these functions are sync)
        await query_tariff_schedule(request.hs_code, request.destination_country)
        await query_roo_requirements(request.hs_code[:4])
        await query_afcfta_guide(request.destination_country)

        # AI Analysis
        compliance: ComplianceReport = await intelligence_service.analyze_compliance(
            product_name=request.product_name,
            hs_code=request.hs_code
        )

        # Build response
        response = AfCFTACheckResponse(
            eligible=compliance.status == TradeStatus.COMPLIANT,
            tariff_saving_percent=15.0,
            roo_eligible=True,
            explanation=compliance.summary,
            suggested_hs_code=compliance.suggested_hs_code or request.hs_code,
        )

        # Save to database
        supabase = get_supabase_admin()
        record = {
            "user_id": None,  # TODO: Add authentication later
            "product_name": request.product_name,
            "hs_code": request.hs_code,
            "destination_country": request.destination_country,
            "eligible": response.eligible,
            "tariff_saving_percent": response.tariff_saving_percent,
            "roo_eligible": response.roo_eligible,
            "explanation": response.explanation,
        }

        supabase.from_("afcfta_checks").insert(record).execute()

        # Cache result
        cache_key = f"afcfta:{request.hs_code}:{request.destination_country}"
        await redis_service.redis.set(cache_key, json.dumps(record), ex=86400)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AfCFTA check failed: {str(e)}")