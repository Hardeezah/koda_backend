from pydantic import BaseModel
from typing import Optional, List


class RetrievedChunk(BaseModel):
    source: str
    agency: str
    doc_date: Optional[str] = None
    url: Optional[str] = None
    chunk_index: int = 0
    content: str
    similarity: float


class Citation(BaseModel):
    source: str
    agency: str
    agency_short: str
    excerpt: str
    url: Optional[str] = None
    doc_date: Optional[str] = None
    relevance_score: float


class ComplianceItem(BaseModel):
    code: str
    name: str
    agency: str
    agency_short: str
    description: str
    how_to_obtain: str
    processing_time: str
    cost_estimate: str
    is_critical: bool
    agency_url: Optional[str] = None


class Risk(BaseModel):
    level: str
    reason: str
    action_required: str


class CitedComplianceVerdict(BaseModel):
    product_name: str
    status: str
    suggested_hs_code: Optional[str] = None
    summary: str
    what_to_do: str
    risks: List[Risk] = []
    compliance_items: List[ComplianceItem] = []
    citations: List[Citation] = []
    direction: str
    afcfta_eligible: Optional[bool] = None
    tariff_saving_percent: Optional[float] = None
    roo_eligible: Optional[bool] = None
    roo_type: Optional[str] = None
    prohibited: Optional[bool] = None
    prohibition_reason: Optional[str] = None
    import_duty_percent: Optional[float] = None
    vat_percent: Optional[float] = None
    retrieval_used: bool = False
