from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.domain.models import ComplianceReport, ProductMetadata, TradeStatus, ComplianceRisk, TradeEntry
from app.api.v1.deps import get_product_repo, get_ledger_repo, get_profile_repo
from app.infrastructure.ai.intelligence import intelligence_service
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
    product_repo = Depends(get_product_repo),
    ledger_repo = Depends(get_ledger_repo),
    profile_repo = Depends(get_profile_repo)
):
    # 1. Fetch Metadata
    metadata = await product_repo.get_by_name(request.product_name)
    hs_code = metadata.hs_code if metadata else None
    
    # 2. Run Compliance Check
    try:
        compliance = await intelligence_service.analyze_compliance(
            product_name=request.product_name,
            hs_code=hs_code
        )
    except Exception as e:
        compliance = ComplianceReport(
            status=TradeStatus.DRAFT,
            risks=[ComplianceRisk(level="high", reason=f"AI check failed: {str(e)}")],
            summary="Compliance check failed."
        )

    # 3. Create Trade Entry
    # Mocking profile ID for now as we don't have auth context fully wired in this mock setup
    entry = TradeEntry(
        id=str(uuid.uuid4()),
        profile_id="mock_user_id",
        product_name=request.product_name,
        quantity=request.quantity,
        value_usd=request.value_usd,
        hs_code=compliance.suggested_hs_code or hs_code,
        status=compliance.status,
        compliance_report=compliance
    )
    await ledger_repo.create(entry)

    return OrchestrationResponse(
        entry_id=entry.id,
        product_metadata=metadata,
        compliance_report=compliance
    )
