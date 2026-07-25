import logging
from fastapi import Depends, Header, HTTPException
from app.infrastructure.supabase import get_supabase_admin

logger = logging.getLogger(__name__)


async def get_current_user(authorization: str | None = Header(None)) -> str:
    """Extract and verify Supabase JWT from Authorization header.

    Returns the authenticated user's ID string.
    Used as a FastAPI dependency: user_id = Depends(get_current_user)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")

    try:
        supabase = get_supabase_admin()
        response = supabase.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return response.user.id
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Auth verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Authentication failed")


def get_profile_repo():
    from app.infrastructure.repositories.supabase_repositories import (
        SupabaseProfileRepository,
    )
    return SupabaseProfileRepository()


def get_ledger_repo():
    from app.infrastructure.repositories.supabase_repositories import (
        SupabaseLedgerRepository,
    )
    return SupabaseLedgerRepository()


def get_product_repo():
    from app.infrastructure.repositories.supabase_repositories import (
        SupabaseProductRepository,
    )
    return SupabaseProductRepository()
