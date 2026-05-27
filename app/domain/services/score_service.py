from app.infrastructure.supabase import get_supabase_admin

async def calculate_score(user_id: str) -> dict:
    """Calculate export readiness score."""
    supabase = get_supabase_admin()   # Make sure this returns the correct client

    score = 0

    # ====================== Profile Scoring ======================
    profile_resp = supabase.from_('profiles') \
        .select('business_name,business_type,trade_type,primary_category,cac_number') \
        .eq('id', user_id) \
        .single() \
        .execute()

    profile = profile_resp.data or {}

    if profile.get('business_name'):
        score += 10
    if profile.get('business_type'):
        score += 10
    if profile.get('trade_type'):
        score += 5
    if profile.get('primary_category'):
        score += 5
    if profile.get('cac_number'):
        score += 25

    # ====================== Ledger Scoring ======================
    ledger_resp = supabase.from_('ledger') \
        .select('status') \
        .eq('profile_id', user_id) \
        .execute()

    ledger = ledger_resp.data or []
    total_entries = len(ledger)
    compliant = sum(1 for e in ledger if e.get('status') == 'compliant')

    score += min(total_entries * 5, 25)
    score += min(compliant * 5, 20)

    # ====================== AfCFTA Scoring ======================
    afcfta_resp = supabase.from_('afcfta_checks') \
        .select('eligible,destination_country') \
        .eq('user_id', user_id) \
        .execute()

    afcfta = afcfta_resp.data or []

    if len(afcfta) >= 3:
        score += 10
    if any(ch.get('eligible') for ch in afcfta):
        score += 15

    afcfta_ready = any(ch.get('eligible') for ch in afcfta)
    corridors = list({ch.get('destination_country') 
                     for ch in afcfta 
                     if ch.get('destination_country')})

    final_score = min(score, 100)

    return {
        'score': final_score,
        'ready': final_score >= 70,
        'afcfta_ready': afcfta_ready,
        'afcfta_corridors': corridors,
        'total_ledger_entries': total_entries,
        'compliant_entries': compliant,
    }