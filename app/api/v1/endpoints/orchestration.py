from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.domain.models import ComplianceReport, ProductMetadata, TradeStatus, ComplianceRisk, TradeEntry
from app.api.v1.deps import get_product_repo, get_ledger_repo, get_current_user
from app.infrastructure.ai.intelligence import intelligence_service
from app.infrastructure.ai.compliance_utils import compliance_dict_to_report
import uuid

router = APIRouter()


class OrchestrationRequest(BaseModel):
    product_name: str
    quantity: float
    value_usd: float


class OrchestrationResponse(BaseModel):
    entry_id: str
    product_metadata: Optional[ProductMetadata]
    compliance_report: Optional[ComplianceReport]


@router.post("/process", response_model=OrchestrationResponse)
async def process_capture(
    request: OrchestrationRequest,
    user_id: str = Depends(get_current_user),
    product_repo=Depends(get_product_repo),
    ledger_repo=Depends(get_ledger_repo),
):
    metadata = await product_repo.get_by_name(request.product_name)
    hs_code = metadata.hs_code if metadata else None

    compliance_data = None
    try:
        compliance_data = await intelligence_service.analyze_compliance(
            product_name=request.product_name,
            hs_code=hs_code,
        )
        compliance = compliance_dict_to_report(compliance_data)
    except Exception:
        compliance = ComplianceReport(
            status=TradeStatus.DRAFT,
            risks=[ComplianceRisk(level="high", reason="AI check failed")],
            summary="Compliance check failed."
        )

    hs_from_data = None
    if isinstance(compliance_data, dict):
        hs_from_data = compliance_data.get("suggested_hs_code")
    elif hasattr(compliance_data, "suggested_hs_code"):
        hs_from_data = compliance_data.suggested_hs_code

    resolved_hs = hs_from_data or compliance.suggested_hs_code or hs_code

    entry = TradeEntry(
        id=str(uuid.uuid4()),
        profile_id=user_id,
        product_name=request.product_name,
        quantity=request.quantity,
        value_usd=request.value_usd,
        hs_code=resolved_hs,
        status=compliance.status,
        compliance_report=compliance,
    )
    await ledger_repo.create(entry)

    return OrchestrationResponse(
        entry_id=entry.id,
        product_metadata=metadata,
        compliance_report=compliance,
    )
