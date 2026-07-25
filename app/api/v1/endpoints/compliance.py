import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from app.infrastructure.ai.intelligence import intelligence_service
from app.api.v1.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Compliance"])


class ImageAnalysisRequest(BaseModel):
    base64_image: str
    direction: str = "import"

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v not in ("import", "export"):
            raise ValueError("direction must be 'import' or 'export'")
        return v


class TextComplianceRequest(BaseModel):
    product_name: str
    hs_code: str | None = None
    direction: str = "import"

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v not in ("import", "export"):
            raise ValueError("direction must be 'import' or 'export'")
        return v


class DocumentGenerationRequest(BaseModel):
    document_code: str
    document_name: str
    product_name: str
    hs_code: str | None = None
    direction: str = "import"
    destination_country: str | None = None
    business_name: str | None = None
    business_address: str | None = None
    cac_number: str | None = None

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v not in ("import", "export"):
            raise ValueError("direction must be 'import' or 'export'")
        return v


@router.post("/check")
async def check_compliance(
    request: TextComplianceRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        return await intelligence_service.analyze_compliance(
            product_name=request.product_name,
            hs_code=request.hs_code,
            direction=request.direction,
        )
    except Exception as e:
        logger.exception("Compliance check failed for %s", request.product_name)
        raise HTTPException(status_code=500, detail="Compliance check failed")


@router.post("/analyze_image")
async def analyze_image_endpoint(
    request: ImageAnalysisRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        if not request.base64_image:
            raise HTTPException(status_code=400, detail="base64_image is required")
        result = await intelligence_service.analyze_image(
            base64_image=request.base64_image,
            direction=request.direction,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image analysis failed")
        raise HTTPException(status_code=500, detail="Vision analysis failed")


@router.post("/generate_document")
async def generate_document(
    request: DocumentGenerationRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        logger.info("Generating document: %s for %s", request.document_code, request.product_name)
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
        return result
    except Exception as e:
        logger.exception("Document generation failed")
        raise HTTPException(status_code=500, detail="Document generation failed")
