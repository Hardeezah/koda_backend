from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.infrastructure.supabase import get_supabase_admin
from app.domain.models import Profile
from app.api.v1.deps import get_profile_repo

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

@router.post("/register")
async def register_user(
    request: RegisterRequest,
    profile_repo = Depends(get_profile_repo)
):
    admin = get_supabase_admin()
    
    # 1. Create User in Auth with email_confirm=True
    try:
        response = admin.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "user_metadata": {"full_name": request.full_name},
            "email_confirm": True
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not response.user:
        raise HTTPException(status_code=400, detail="User creation failed")

    # 2. Initialize Profile
    profile = Profile(
        id=response.user.id,
        email=request.email,
        full_name=request.full_name
    )
    await profile_repo.update(profile)

    return {"message": "User registered and verified successfully", "user_id": response.user.id}
