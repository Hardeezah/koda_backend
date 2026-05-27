from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.domain.models import TradeEntry
from app.domain.repositories import LedgerRepository
from app.api.v1.deps import get_ledger_repo

router = APIRouter()

@router.get("/{profile_id}", response_model=List[TradeEntry])
async def get_ledger(
    profile_id: str,
    repo: LedgerRepository = Depends(get_ledger_repo)
):
    return await repo.get_by_profile(profile_id)

@router.post("/", response_model=TradeEntry)
async def create_entry(
    entry: TradeEntry,
    repo: LedgerRepository = Depends(get_ledger_repo)
):
    return await repo.create(entry)

@router.put("/{entry_id}", response_model=TradeEntry)
async def update_entry(
    entry_id: str,
    entry: TradeEntry,
    repo: LedgerRepository = Depends(get_ledger_repo)
):
    entry.id = entry_id
    return await repo.update(entry)

@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: str,
    repo: LedgerRepository = Depends(get_ledger_repo)
):
    await repo.delete(entry_id)
    return {"status": "deleted"}
