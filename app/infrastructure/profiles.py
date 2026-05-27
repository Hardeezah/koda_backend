from app.infrastructure.supabase import get_supabase_admin

async def set_user_mode(user_id: str, mode: str) -> None:
    """Persist the import/export mode for a user.
    mode must be either "import" or "export".
    """
    supabase = get_supabase_admin()
    await supabase.from_('profiles').update({"active_mode": mode}).eq('id', user_id).execute()

async def get_user_mode(user_id: str) -> str:
    """Retrieve the import/export mode for a user, defaulting to "import".
    """
    supabase = get_supabase_admin()
    resp = await supabase.from_('profiles').select('active_mode').eq('id', user_id).single().execute()
    return resp.data.get('active_mode', 'import') if resp.data else 'import'
