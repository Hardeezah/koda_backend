import logging
from fastapi import APIRouter, Depends, HTTPException
from app.domain.models import Profile
from app.domain.repositories import ProfileRepository
from app.api.v1.deps import get_profile_repo, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{profile_id}", response_model=Profile)
async def get_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user),
    repo: ProfileRepository = Depends(get_profile_repo),
):
    if user_id != profile_id:
        raise HTTPException(status_code=403, detail="Cannot access another user's profile")
    profile = await repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/", response_model=Profile)
async def update_profile(
    profile: Profile,
    user_id: str = Depends(get_current_user),
    repo: ProfileRepository = Depends(get_profile_repo),
):
    if profile.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot update another user's profile")
    return await repo.update(profile)
