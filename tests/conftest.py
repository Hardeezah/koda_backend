import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_retrieved_chunks():
    """Standard set of retrieved chunks for testing."""
    from app.domain.models.rag import RetrievedChunk
    return [
        RetrievedChunk(
            source="ncs_2026_prohibition_list",
            agency="Nigeria Customs Service",
            doc_date="2026-01",
            url="https://customs.gov.ng",
            chunk_index=0,
            content="Ginger imports require Form M declaration to the Central Bank of Nigeria.",
            similarity=0.82,
        ),
        RetrievedChunk(
            source="nafdac_import_guidelines",
            agency="NAFDAC",
            doc_date="2024-01",
            url="https://www.nafdac.gov.ng",
            chunk_index=1,
            content="NAFDAC registration is required for food products entering Nigeria.",
            similarity=0.71,
        ),
    ]


@pytest.fixture
def mock_cited_verdict():
    """Standard CitedComplianceVerdict for testing."""
    from app.domain.models.rag import CitedComplianceVerdict, Citation
    return CitedComplianceVerdict(
        product_name="Ginger",
        status="compliant",
        summary="Ginger may be imported with Form M.",
        what_to_do="Apply for Form M at your bank.",
        direction="import",
        retrieval_used=True,
        citations=[
            Citation(
                source="ncs_2026_prohibition_list",
                agency="Nigeria Customs Service",
                agency_short="NCS",
                excerpt="Ginger imports require Form M.",
                url="https://customs.gov.ng",
                doc_date="2026-01",
                relevance_score=0.82,
            )
        ],
    )


@pytest.fixture
def mock_llm_completion():
    """Factory fixture for creating mock Groq completions."""

    def _make(json_content: str):
        mock_message = MagicMock()
        mock_message.content = json_content
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        return mock_completion

    return _make
