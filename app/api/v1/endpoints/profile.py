from fastapi import APIRouter, Depends, HTTPException
from app.domain.models import Profile
from app.domain.repositories import ProfileRepository
from app.api.v1.deps import get_profile_repo

router = APIRouter()

@router.get("/{profile_id}", response_model=Profile)
async def get_profile(
    profile_id: str,
    repo: ProfileRepository = Depends(get_profile_repo)
):
    profile = await repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/", response_model=Profile)
async def update_profile(
    profile: Profile,
    repo: ProfileRepository = Depends(get_profile_repo)
):
    return await repo.update(profile)
