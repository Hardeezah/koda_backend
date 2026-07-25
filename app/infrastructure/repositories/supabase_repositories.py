from typing import Optional, List
from app.domain.models import Profile, TradeEntry, ProductMetadata
from app.domain.repositories import ProfileRepository, LedgerRepository, ProductRepository
from app.infrastructure.supabase import get_supabase, get_supabase_admin

class SupabaseProfileRepository(ProfileRepository):
    def __init__(self):
        self.client = get_supabase_admin()

    async def get_by_id(self, profile_id: str) -> Optional[Profile]:
        response = self.client.table("profiles").select("*").eq("id", profile_id).execute()
        if not response.data:
            return None
        return Profile.model_validate(response.data[0])

    async def update(self, profile: Profile) -> Profile:
        data = profile.dict(exclude={"created_at"})
        response = self.client.table("profiles").upsert(data).execute()
        return Profile.model_validate(response.data[0])


class SupabaseLedgerRepository(LedgerRepository):
    def __init__(self):
        self.client = get_supabase_admin()

    async def get_by_profile(self, profile_id: str) -> List[TradeEntry]:
        response = self.client.table("ledger").select("*").eq("profile_id", profile_id).execute()
        return [TradeEntry.model_validate(item) for item in response.data]

    async def create(self, entry: TradeEntry) -> TradeEntry:
        data = entry.dict(exclude={"id", "created_at"})
        response = self.client.table("ledger").insert(data).execute()
        return TradeEntry.model_validate(response.data[0])

    async def update(self, entry: TradeEntry) -> TradeEntry:
        data = entry.dict(exclude={"created_at"})
        response = self.client.table("ledger").update(data).eq("id", entry.id).execute()
        return TradeEntry.model_validate(response.data[0])

    async def delete(self, entry_id: str) -> bool:
        self.client.table("ledger").delete().eq("id", entry_id).execute()
        return True


class SupabaseProductRepository(ProductRepository):
    def __init__(self):
        self.client = get_supabase()

    async def list_all(self) -> List[ProductMetadata]:
        response = self.client.table("products").select("*").execute()
        return [ProductMetadata.model_validate(item) for item in response.data]

    async def get_by_id(self, product_id: str) -> Optional[ProductMetadata]:
        response = self.client.table("products").select("*").eq("id", product_id).execute()
        if not response.data:
            return None
        return ProductMetadata.model_validate(response.data[0])

    async def get_by_name(self, name: str) -> Optional[ProductMetadata]:
        response = self.client.table("products").select("*").eq("name", name).execute()
        if not response.data:
            return None
        return ProductMetadata.model_validate(response.data[0])