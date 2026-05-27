from app.infrastructure.supabase import get_supabase_admin
from typing import Optional, Dict, Any

async def query_tariff_schedule(hs_code: str, destination_country: str) -> Optional[Dict[str, Any]]:
    """Fetch tariff information for AfCFTA"""
    try:
        supabase = get_supabase_admin()
        
        response = supabase.from_('tariff_schedule') \
            .select('*') \
            .eq('hs_code', hs_code) \
            .eq('destination_country', destination_country) \
            .single() \
            .execute()
        
        return response.data
    except Exception:
        return None


async def query_roo_requirements(hs_chapter: str) -> Optional[Dict[str, Any]]:
    """Fetch Rules of Origin requirements"""
    try:
        supabase = get_supabase_admin()
        
        response = supabase.from_('roo_requirements') \
            .select('*') \
            .eq('hs_chapter', hs_chapter) \
            .execute()
        
        return response.data
    except Exception:
        return None


async def query_afcfta_guide(destination_country: str) -> Optional[str]:
    """Fetch AfCFTA guide/explanation for a country"""
    try:
        supabase = get_supabase_admin()
        
        response = supabase.from_('afcfta_guides') \
            .select('content') \
            .eq('country', destination_country) \
            .single() \
            .execute()
        
        return response.data.get('content') if response.data else None
    except Exception:
        return None