from app.infrastructure.repositories.supabase_repositories import (
    SupabaseProfileRepository,
    SupabaseLedgerRepository,
    SupabaseProductRepository
)

def get_profile_repo():
    return SupabaseProfileRepository()

def get_ledger_repo():
    return SupabaseLedgerRepository()

def get_product_repo():
    return SupabaseProductRepository()
