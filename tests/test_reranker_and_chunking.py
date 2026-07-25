import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.infrastructure.rag.reranker import (
    rerank,
    format_context,
    extract_citations,
    AGENCY_SHORT_MAP,
)
from app.domain.models.rag import RetrievedChunk
from app.infrastructure.rag.document_ingestion import _chunk_text, CHUNK_SIZE, CHUNK_OVERLAP


def _make_chunk(
    content="Test regulatory content about ginger imports.",
    source="ncs_2026_prohibition_list",
    agency="Nigeria Customs Service",
    similarity=0.75,
    chunk_index=0,
    doc_date="2026-01",
    url="https://customs.gov.ng",
) -> RetrievedChunk:
    return RetrievedChunk(
        source=source,
        agency=agency,
        doc_date=doc_date,
        url=url,
        chunk_index=chunk_index,
        content=content,
        similarity=similarity,
    )


class TestRerank:
    def test_empty_list(self):
        assert rerank([], ["ginger"]) == []

    def test_single_chunk(self):
        chunk = _make_chunk(similarity=0.6)
        result = rerank([chunk], ["ginger"])
        assert len(result) == 1
        assert result[0] is chunk

    def test_keyword_boost_moves_ranking(self):
        # "import regulations in nigeria compliance" = 4 keyword hits = 0.20 boost
        # "sugar export rules compliance" = 1 keyword hit (compliance) = 0.05 boost
        high_sim_no_keyword = _make_chunk(
            content="Sugar export rules compliance",
            similarity=0.80,
        )
        low_sim_with_keyword = _make_chunk(
            content="Import regulations in Nigeria compliance",
            similarity=0.65,
        )
        # 0.65 + 4*0.05 = 0.85 vs 0.80 + 1*0.05 = 0.85 — tie, stable sort preserves order
        # Let's use more keywords to be clear
        result = rerank(
            [high_sim_no_keyword, low_sim_with_keyword],
            ["import", "regulations", "nigeria", "compliance"],
        )
        # low_sim: 0.65 + 4*0.05 = 0.85, high_sim: 0.80 + 1*0.05 = 0.85
        # stable sort means first stays first. Let's increase low_sim keywords
        low_sim_with_many_keywords = _make_chunk(
            content="Import regulations in Nigeria compliance customs",
            similarity=0.65,
        )
        result = rerank(
            [high_sim_no_keyword, low_sim_with_many_keywords],
            ["import", "regulations", "nigeria", "compliance", "customs"],
        )
        # low_sim: 0.65 + 5*0.05 = 0.90, high_sim: 0.80 + 1*0.05 = 0.85
        assert result[0] is low_sim_with_many_keywords
        assert result[1] is high_sim_no_keyword

    def test_no_keyword_matches(self):
        c1 = _make_chunk(content="Sugar regulations", similarity=0.80)
        c2 = _make_chunk(content="Rice export rules", similarity=0.70)
        result = rerank([c1, c2], ["ginger"])
        assert result[0] is c1
        assert result[1] is c2

    def test_all_same_similarity(self):
        c1 = _make_chunk(content="Ginger imports", similarity=0.75, chunk_index=0)
        c2 = _make_chunk(content="Ginger imports", similarity=0.75, chunk_index=1)
        result = rerank([c1, c2], ["ginger"])
        assert len(result) == 2

    def test_case_insensitive(self):
        chunk = _make_chunk(content="GINGER is a regulated product", similarity=0.6)
        result = rerank([chunk], ["ginger"])
        assert len(result) == 1


class TestFormatContext:
    def test_empty_chunks(self):
        assert format_context([]) == "No regulatory documents retrieved."

    def test_single_chunk(self):
        chunk = _make_chunk(
            content="Ginger requires Form M for import.",
            agency="Nigeria Customs Service",
            source="ncs_2026_prohibition_list",
        )
        result = format_context([chunk])
        assert "[SOURCE: ncs_2026_prohibition_list" in result
        assert "Ginger requires Form M" in result
        assert AGENCY_SHORT_MAP["Nigeria Customs Service"] in result

    def test_multiple_chunks_separated(self):
        c1 = _make_chunk(content="Chunk one", chunk_index=0)
        c2 = _make_chunk(content="Chunk two", chunk_index=1)
        result = format_context([c1, c2])
        assert "---" in result
        assert "Chunk one" in result
        assert "Chunk two" in result

    def test_truncation_with_warning(self):
        big_content = "x" * 900
        chunks = [_make_chunk(content=big_content, chunk_index=i) for i in range(20)]
        result = format_context(chunks, max_chars=500)
        assert "[NOTE:" in result
        assert "omitted due to context length limits" in result

    def test_no_truncation_when_fits(self):
        chunks = [_make_chunk(content="Short content", chunk_index=i) for i in range(3)]
        result = format_context(chunks, max_chars=10000)
        assert "[NOTE:" not in result

    def test_agency_short_map_used(self):
        chunk = _make_chunk(agency="Central Bank of Nigeria")
        result = format_context([chunk])
        assert "CBN" in result

    def test_unknown_agency_passes_through(self):
        chunk = _make_chunk(agency="Some Unknown Agency")
        result = format_context([chunk])
        assert "Some Unknown Agency" in result

    def test_missing_date_shows_na(self):
        chunk = _make_chunk(doc_date=None)
        result = format_context([chunk])
        assert "DATE: N/A" in result


class TestExtractCitations:
    def test_empty_chunks(self):
        assert extract_citations([]) == []

    def test_single_chunk(self):
        chunk = _make_chunk(
            content="Ginger imports require Form M declaration.",
            source="ncs_2026_prohibition_list",
            agency="Nigeria Customs Service",
            similarity=0.85,
            chunk_index=0,
        )
        citations = extract_citations([chunk])
        assert len(citations) == 1
        c = citations[0]
        assert c["source"] == "ncs_2026_prohibition_list"
        assert c["agency_short"] == "NCS"
        assert c["relevance_score"] == 0.85
        assert "Ginger imports" in c["excerpt"]

    def test_deduplication(self):
        chunk = _make_chunk(chunk_index=0)
        citations = extract_citations([chunk, chunk])
        assert len(citations) == 1

    def test_different_chunks_same_source(self):
        c1 = _make_chunk(content="First chunk", chunk_index=0)
        c2 = _make_chunk(content="Second chunk", chunk_index=1)
        citations = extract_citations([c1, c2])
        assert len(citations) == 2

    def test_excerpt_truncation(self):
        long_content = "word " * 200
        chunk = _make_chunk(content=long_content)
        citations = extract_citations([chunk])
        assert len(citations[0]["excerpt"]) <= 300

    def test_missing_url_and_date(self):
        chunk = _make_chunk(url=None, doc_date=None)
        citations = extract_citations([chunk])
        assert citations[0]["url"] is None
        assert citations[0]["doc_date"] is None


class TestChunkText:
    def test_empty_string(self):
        assert _chunk_text("") == []
        assert _chunk_text("   ") == []

    def test_short_text_no_chunking(self):
        text = "Short text."
        chunks = _chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_exact_chunk_size(self):
        text = "x" * (CHUNK_SIZE - CHUNK_OVERLAP)
        chunks = _chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_overlap_preserved(self):
        text = "A" * (CHUNK_SIZE + 50)
        chunks = _chunk_text(text)
        assert len(chunks) >= 2
        step = CHUNK_SIZE - CHUNK_OVERLAP
        assert chunks[1] == text[step : step + CHUNK_SIZE]

    def test_multi_chunk_long_text(self):
        text = "word " * 500
        chunks = _chunk_text(text)
        assert len(chunks) > 2
        for chunk in chunks:
            assert len(chunk) <= CHUNK_SIZE

    def test_whitespace_only_chunks_filtered(self):
        text = "x" * CHUNK_SIZE + " " * 100 + "y" * CHUNK_SIZE
        chunks = _chunk_text(text)
        for chunk in chunks:
            assert chunk.strip()

    def test_whitespace_between_content(self):
        text = "A" * (CHUNK_SIZE - 10) + "\n\n\n\n" + "B" * (CHUNK_SIZE - 10)
        chunks = _chunk_text(text)
        assert len(chunks) >= 2
