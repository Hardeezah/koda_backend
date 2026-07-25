from fastapi import APIRouter, HTTPException, Depends
from app.infrastructure.ai.communication import communication_service, DraftEmail
from app.api.v1.deps import get_profile_repo, get_ledger_repo, get_current_user

router = APIRouter()


@router.post("/draft", response_model=DraftEmail)
async def draft_communication(
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

    return await communication_service.draft_broker_email(entry, profile)
