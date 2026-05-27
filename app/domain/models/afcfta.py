from pydantic import BaseModel

class AfCFTACheckRequest(BaseModel):
    product_name: str
    hs_code: str
    destination_country: str

class AfCFTACheckResponse(BaseModel):
    eligible: bool
    tariff_saving_percent: float
    roo_eligible: bool
    explanation: str
