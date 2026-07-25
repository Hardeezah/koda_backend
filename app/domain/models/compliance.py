from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class TradeStatus(str, Enum):
    DRAFT = "draft"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"
    SUBMITTED = "submitted"


class ComplianceRisk(BaseModel):
    level: str          # high, medium, low
    reason: str
    action_required: Optional[str] = None


class ComplianceReport(BaseModel):
    status: TradeStatus
    summary: str
    suggested_hs_code: Optional[str] = None
    risks: List[ComplianceRisk] = []
    confidence_score: float = 0.0


# AfCFTA Models (moved here for better organization)
class AfCFTACheckRequest(BaseModel):
    product_name: str
    hs_code: str
    destination_country: str
    user_id: Optional[str] = None


class AfCFTACheckResponse(BaseModel):
    eligible: bool
    tariff_saving_percent: float
    roo_eligible: bool
    explanation: str
    suggested_hs_code: Optional[str] = None