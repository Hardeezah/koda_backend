from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.infrastructure.documents.document_service import document_service
from app.api.v1.deps import get_profile_repo, get_ledger_repo, get_current_user

router = APIRouter()


@router.post("/generate/form-m")
async def generate_form_m(
    entry_id: str,
    user_id: str = Depends(get_current_user),
    profile_repo=Depends(get_profile_repo),
    ledger_repo=Depends(get_ledger_repo),
):
    entries = await ledger_repo.get_by_profile(user_id)
    entry = next((e for e in entries if e.id == entry_id), None)

    if not entry:
        raise HTTPException(status_code=404, detail="Trade entry not found")

    profile = await profile_repo.get_by_id(entry.profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    pdf_buffer = document_service.generate_form_m(entry, profile)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=form_m_{entry_id}.pdf"}
    )
