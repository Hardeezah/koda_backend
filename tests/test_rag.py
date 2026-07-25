import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.domain.models.rag import RetrievedChunk, CitedComplianceVerdict, Citation, Risk
from app.infrastructure.ai.compliance_utils import compliance_dict_to_report
from app.domain.models import TradeStatus


def test_compliance_dict_to_report():
    data = {
        "status": "compliant",
        "summary": "Product is allowed.",
        "suggested_hs_code": "090111",
        "risks": [{"level": "low", "reason": "None", "action_required": "Proceed"}],
    }
    report = compliance_dict_to_report(data)
    assert report.status == TradeStatus.COMPLIANT
    assert report.suggested_hs_code == "090111"
    assert len(report.risks) == 1


def test_compliance_dict_to_report_invalid_status():
    data = {"status": "invalid_status", "summary": "test", "risks": []}
    report = compliance_dict_to_report(data)
    assert report.status == TradeStatus.UNDER_REVIEW


def test_compliance_dict_to_report_retrieval_used():
    data = {"status": "compliant", "summary": "test", "risks": [], "retrieval_used": True}
    report = compliance_dict_to_report(data)
    assert report.confidence_score == 0.75


def test_compliance_dict_to_report_no_retrieval():
    data = {"status": "compliant", "summary": "test", "risks": [], "retrieval_used": False}
    report = compliance_dict_to_report(data)
    assert report.confidence_score == 0.40


def test_compliance_dict_to_report_empty_risks():
    data = {"status": "compliant", "summary": "test", "risks": []}
    report = compliance_dict_to_report(data)
    assert report.risks == []


def test_compliance_dict_to_report_explicit_confidence():
    data = {"status": "compliant", "summary": "test", "risks": [], "confidence_score": 0.95}
    report = compliance_dict_to_report(data)
    assert report.confidence_score == 0.95


@pytest.mark.asyncio
async def test_compliance_chain_uses_retrieval():
    mock_chunks = [
        RetrievedChunk(
            source="ncs_2026_prohibition_list",
            agency="Nigeria Customs Service",
            chunk_index=0,
            content="Ginger imports require Form M.",
            similarity=0.82,
        )
    ]
    mock_verdict_json = """{
        "product_name": "Ginger",
        "status": "compliant",
        "suggested_hs_code": "091011",
        "summary": "Ginger may be imported with Form M.",
        "what_to_do": "Apply for Form M at your bank.",
        "risks": [],
        "compliance_items": []
    }"""

    mock_message = MagicMock()
    mock_message.content = mock_verdict_json
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch(
        "app.infrastructure.rag.compliance_chain.regulatory_retriever.retrieve_for_compliance",
        new=AsyncMock(return_value=mock_chunks),
    ):
        from app.infrastructure.rag.compliance_chain import ComplianceChain
        chain = ComplianceChain.__new__(ComplianceChain)
        chain.client = MagicMock()
        chain.client.chat.completions.create = AsyncMock(return_value=mock_completion)
        chain.model = "llama-3.3-70b-versatile"
        chain.temperature = 0.2

        verdict = await chain.run("Ginger", direction="import")

    assert isinstance(verdict, CitedComplianceVerdict)
    assert verdict.retrieval_used is True
    assert verdict.product_name == "Ginger"
    assert len(verdict.citations) == 1


@pytest.mark.asyncio
async def test_analyze_compliance_routes_through_chain():
    mock_verdict = CitedComplianceVerdict(
        product_name="Ginger",
        status="compliant",
        summary="OK",
        what_to_do="Apply",
        direction="import",
        retrieval_used=True,
        citations=[Citation(
            source="ncs",
            agency="NCS",
            agency_short="NCS",
            excerpt="test",
            relevance_score=0.9,
        )],
    )

    with patch(
        "app.infrastructure.rag.compliance_chain.compliance_chain.run",
        new=AsyncMock(return_value=mock_verdict),
    ):
        from app.infrastructure.ai.intelligence import IntelligenceService
        service = IntelligenceService()
        result = await service.analyze_compliance("Ginger", direction="import")

    assert result["retrieval_used"] is True
    assert result["product_name"] == "Ginger"
    assert len(result["citations"]) == 1
