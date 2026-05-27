# app/domain/models/__init__.py
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime


# ====================== Enums ======================
class TradeStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"


# ====================== Compliance Models ======================
class ComplianceRisk(BaseModel):
    level: str
    reason: str
    action_required: Optional[str] = None


class ComplianceReport(BaseModel):
    status: TradeStatus
    summary: str
    suggested_hs_code: Optional[str] = None
    risks: List[ComplianceRisk] = []
    confidence_score: float = 0.0


class AfCFTACheckRequest(BaseModel):
    product_name: str
    hs_code: str
    destination_country: str


class AfCFTACheckResponse(BaseModel):
    eligible: bool
    tariff_saving_percent: float
    roo_eligible: bool
    explanation: str
    suggested_hs_code: Optional[str] = None


# ====================== Profile Model ======================
class Profile(BaseModel):
    id: str
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    trade_type: Optional[str] = None
    primary_category: Optional[str] = None
    cac_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ====================== New Models ======================
class TradeEntry(BaseModel):
    id: Optional[str] = None
    profile_id: str
    product_name: str
    hs_code: Optional[str] = None
    status: TradeStatus
    quantity: Optional[float] = 0
    value_usd: Optional[float] = 0
    unit: Optional[str] = "kg"
    created_at: Optional[datetime] = None


class ProductMetadata(BaseModel):
    hs_code: str
    product_name: str
    category: Optional[str] = None
    description: Optional[str] = None
    risks: List[str] = []


__all__ = [
    "Profile",
    "TradeEntry",
    "ProductMetadata",
    "ComplianceReport",
    "TradeStatus",
    "ComplianceRisk",
    "AfCFTACheckRequest",
    "AfCFTACheckResponse",
]