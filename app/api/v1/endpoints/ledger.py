from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.domain.models import TradeEntry
from app.domain.repositories import LedgerRepository
from app.api.v1.deps import get_ledger_repo, get_current_user

router = APIRouter()


@router.get("/{profile_id}", response_model=List[TradeEntry])
async def get_ledger(
    profile_id: str,
    user_id: str = Depends(get_current_user),
    repo: LedgerRepository = Depends(get_ledger_repo),
):
    if user_id != profile_id:
        raise HTTPException(status_code=403, detail="Cannot access another user's ledger")
    return await repo.get_by_profile(profile_id)


@router.post("/", response_model=TradeEntry)
async def create_entry(
    entry: TradeEntry,
    user_id: str = Depends(get_current_user),
    repo: LedgerRepository = Depends(get_ledger_repo),
):
    entry.profile_id = user_id
    return await repo.create(entry)


@router.put("/{entry_id}", response_model=TradeEntry)
async def update_entry(
    entry_id: str,
    entry: TradeEntry,
    user_id: str = Depends(get_current_user),
    repo: LedgerRepository = Depends(get_ledger_repo),
):
    entry.id = entry_id
    entry.profile_id = user_id
    return await repo.update(entry)


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user),
    repo: LedgerRepository = Depends(get_ledger_repo),
):
    await repo.delete(entry_id)
    return {"status": "deleted"}
