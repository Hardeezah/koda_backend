from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional, List, Any
from enum import Enum
from datetime import datetime
from app.domain.models.compliance import TradeStatus, ComplianceRisk, ComplianceReport, AfCFTACheckRequest, AfCFTACheckResponse
from app.domain.models.vision import ProductAttributes, HSCodeCandidate, HSCodeResult, VisualAnalysisResult
from app.domain.models.rag import RetrievedChunk, Citation, ComplianceItem, Risk, CitedComplianceVerdict

class Profile(BaseModel):
    id: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    trade_type: Optional[str] = None
    primary_category: Optional[str] = None
    sub_categories: Optional[List[str]] = None
    target_countries: Optional[List[str]] = None
    cac_number: Optional[str] = None
    tin: Optional[str] = None
    phone: Optional[str] = None
    onboarding_completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
    created_at: Optional[datetime] = None

class ProductMetadata(BaseModel):
    id: str
    name: str
    hs_code: str
    category: str
    common_unit: str = "kg"
    description: Optional[str] = None
    product_name: Optional[str] = None
    risks: List[str] = []

    @model_validator(mode="before")
    @classmethod
    def sync_names(cls, data: Any) -> Any:
        if isinstance(data, dict):
            name = data.get("name")
            prod_name = data.get("product_name")
            if name and not prod_name:
                data["product_name"] = name
            elif prod_name and not name:
                data["name"] = prod_name
        return data

__all__ = [
    "Profile",
    "TradeEntry",
    "ProductMetadata",
    "ComplianceReport",
    "TradeStatus",
    "ComplianceRisk",
    "AfCFTACheckRequest",
    "AfCFTACheckResponse",
    "ProductAttributes",
    "HSCodeCandidate",
    "HSCodeResult",
    "VisualAnalysisResult",
    "RetrievedChunk",
    "Citation",
    "ComplianceItem",
    "Risk",
    "CitedComplianceVerdict",
]