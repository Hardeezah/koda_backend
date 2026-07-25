from app.infrastructure.supabase import get_supabase_admin
from typing import Optional, Dict, Any, List
import json


async def query_tariff_schedule(
    hs_code: str, destination_country: str
) -> Optional[Dict[str, Any]]:
    """Fetch AfCFTA tariff information for an HS code and destination."""
    try:
        supabase = get_supabase_admin()

        response = (
            supabase.from_("afcfta_tariff_schedule")
            .select("*")
            .eq("hs_code", hs_code)
            .eq("destination_country", destination_country)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]
        return None
    except Exception:
        return None


async def query_roo_requirements(hs_code_prefix: str) -> Optional[List[Dict[str, Any]]]:
    """Fetch Rules of Origin requirements for an HS code prefix (4-digit heading)."""
    try:
        supabase = get_supabase_admin()

        response = (
            supabase.from_("afcfta_roo_requirements")
            .select("*")
            .eq("hs_code_prefix", hs_code_prefix)
            .execute()
        )

        return response.data or None
    except Exception:
        return None


def format_afcfta_context(
    tariff: Optional[Dict[str, Any]],
    roo_rules: Optional[List[Dict[str, Any]]],
    destination_country: str,
) -> str:
    """Format structured AfCFTA DB rows as LLM context."""
    parts = [f"Destination country: {destination_country}"]

    if tariff:
        parts.append(
            "AfCFTA tariff schedule entry: "
            + json.dumps(
                {
                    "hs_code": tariff.get("hs_code"),
                    "product_description": tariff.get("product_description"),
                    "category": tariff.get("category"),
                    "current_rate_percent": tariff.get("current_rate_percent"),
                    "afcfta_rate_percent": tariff.get("afcfta_rate_percent"),
                    "phase_down_end_year": tariff.get("phase_down_end_year"),
                },
                default=str,
            )
        )

    if roo_rules:
        parts.append(
            "Rules of origin requirements: "
            + json.dumps(
                [
                    {
                        "hs_code_prefix": r.get("hs_code_prefix"),
                        "rule_type": r.get("rule_type"),
                        "rule_description": r.get("rule_description"),
                        "minimum_african_value_percent": r.get(
                            "minimum_african_value_percent"
                        ),
                        "requires_hs_change": r.get("requires_hs_change"),
                        "notes": r.get("notes"),
                    }
                    for r in roo_rules
                ],
                default=str,
            )
        )

    return "\n".join(parts)


def compute_tariff_saving(
    tariff: Optional[Dict[str, Any]], compliance: dict
) -> float:
    """Derive tariff saving from DB tariff row or LLM estimate."""
    if tariff:
        current = tariff.get("current_rate_percent")
        afcfta = tariff.get("afcfta_rate_percent")
        if current is not None and afcfta is not None:
            return max(0.0, float(current) - float(afcfta))

    saving = compliance.get("tariff_saving_percent")
    return float(saving) if saving is not None else 0.0
