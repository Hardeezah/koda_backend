from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TradeStatus(str, Enum):
    DRAFT = "draft"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    SUBMITTED = "submitted"

class ComplianceRisk(BaseModel):
    level: str
    reason: str
    action_required: Optional[str] = None

class ComplianceReport(BaseModel):
    status: TradeStatus
    risks: List[ComplianceRisk]
    suggested_hs_code: Optional[str] = None
    summary: str
    product_name: Optional[str] = None

class Profile(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    cac_number: Optional[str] = None
    tin: Optional[str] = None
    created_at: datetime = datetime.now()

class TradeEntry(BaseModel):
    id: Optional[str] = None
    profile_id: str
    product_name: str
    quantity: float
    unit: str = "kg"
    value_usd: float
    hs_code: Optional[str] = None
    status: TradeStatus = TradeStatus.DRAFT
    compliance_report: Optional[ComplianceReport] = None
    created_at: datetime = datetime.now()

class ProductMetadata(BaseModel):
    id: str
    name: str
    hs_code: str
    category: str
    common_unit: str = "kg"
    description: Optional[str] = None
