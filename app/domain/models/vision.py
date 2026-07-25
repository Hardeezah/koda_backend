from pydantic import BaseModel
from typing import Optional, List


class ProductAttributes(BaseModel):
    product_name: str
    category: str
    description: str
    material: Optional[str] = None
    brand: Optional[str] = None
    weight_class: Optional[str] = None
    purpose: Optional[str] = None
    origin_cues: Optional[str] = None
    packaging: Optional[str] = None
    condition: Optional[str] = None


class HSCodeCandidate(BaseModel):
    code: str
    description: str
    similarity: float
    chapter: str
    heading: str


class HSCodeResult(BaseModel):
    assigned_code: str
    description: str
    confidence: float
    chapter: str
    heading: str
    candidates: List[HSCodeCandidate] = []
    reasoning: str


class VisualAnalysisResult(BaseModel):
    product_name: str
    attributes: ProductAttributes
    hs_code: HSCodeResult
    direction: str
