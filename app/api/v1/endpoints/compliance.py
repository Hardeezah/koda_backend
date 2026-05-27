from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.domain.models import ComplianceReport
from app.infrastructure.ai.intelligence import intelligence_service

router = APIRouter(tags=["Compliance"])


class ImageAnalysisRequest(BaseModel):
    base64_image: str
    direction: str = "import"  # 'import' or 'export'


class TextComplianceRequest(BaseModel):
    product_name: str
    hs_code: str | None = None
    direction: str = "import"

class DocumentGenerationRequest(BaseModel):
    document_code: str        # e.g. "FORM_M", "COO", "NXP"
    document_name: str
    product_name: str
    hs_code: str | None = None
    direction: str = "import"
    destination_country: str | None = None
    business_name: str | None = None
    business_address: str | None = None
    cac_number: str | None = None


@router.post("/check")
async def check_compliance(request: TextComplianceRequest):
    try:
        return await intelligence_service.analyze_compliance(
            product_name=request.product_name,
            hs_code=request.hs_code,
            direction=request.direction,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze_image")
async def analyze_image_endpoint(request: ImageAnalysisRequest):
    try:
        if not request.base64_image:
            raise HTTPException(status_code=400, detail="base64_image is required")
        result = await intelligence_service.analyze_image(
            base64_image=request.base64_image,
            direction=request.direction,
        )
        return result
    except Exception as e:
        print(f"[ERROR] analyze_image_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {str(e)}")


@router.post("/generate_document")
async def generate_document(request: DocumentGenerationRequest):
    try:
        print(f"[DOC] Generating: {request.document_code} for {request.product_name}")
        result = await intelligence_service.generate_document(
            document_code=request.document_code,
            document_name=request.document_name,
            product_name=request.product_name,
            hs_code=request.hs_code,
            direction=request.direction,
            destination_country=request.destination_country,
            business_name=request.business_name,
            business_address=request.business_address,
            cac_number=request.cac_number,
        )
        print(f"[DOC] Result keys: {list(result.keys())}")
        return result
    except Exception as e:
        print(f"[ERROR] generate_document: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))