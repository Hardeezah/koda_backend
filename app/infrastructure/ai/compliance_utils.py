import logging
from datetime import datetime, timezone
from app.domain.models import ComplianceReport, ComplianceRisk, TradeStatus

logger = logging.getLogger(__name__)


def compliance_dict_to_report(data: dict) -> ComplianceReport:
    """Convert a RAG/LLM compliance dict into a ComplianceReport domain model."""
    status_raw = data.get("status", "under_review")
    try:
        status = TradeStatus(status_raw)
    except ValueError:
        status = TradeStatus.UNDER_REVIEW

    risks = [
        ComplianceRisk(
            level=r.get("level", "medium"),
            reason=r.get("reason", ""),
            action_required=r.get("action_required"),
        )
        for r in data.get("risks", [])
    ]

    confidence = float(data.get("confidence_score", 0.0))
    if confidence == 0.0:
        if data.get("retrieval_used") is True:
            confidence = 0.75
        elif data.get("retrieval_used") is False:
            confidence = 0.40

    return ComplianceReport(
        status=status,
        summary=data.get("summary", ""),
        suggested_hs_code=data.get("suggested_hs_code"),
        risks=risks,
        confidence_score=confidence,
    )
