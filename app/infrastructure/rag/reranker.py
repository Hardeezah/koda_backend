import logging
from typing import List
from app.domain.models.rag import RetrievedChunk

logger = logging.getLogger(__name__)

AGENCY_SHORT_MAP = {
    "AfCFTA Secretariat": "AfCFTA",
    "Nigeria Customs Service": "NCS",
    "Central Bank of Nigeria": "CBN",
    "NAFDAC": "NAFDAC",
    "Standards Organisation of Nigeria": "SON",
    "Nigerian Export Promotion Council": "NEPC",
    "National Agricultural Quarantine Service": "NAQS",
    "NESREA": "NESREA",
}


def rerank(chunks: List[RetrievedChunk], query_terms: List[str]) -> List[RetrievedChunk]:
    if not chunks:
        return []

    query_lower = [t.lower() for t in query_terms]

    def score(chunk: RetrievedChunk) -> float:
        content_lower = chunk.content.lower()
        keyword_hits = sum(1 for term in query_lower if term in content_lower)
        keyword_boost = keyword_hits * 0.05
        return chunk.similarity + keyword_boost

    ranked = sorted(chunks, key=score, reverse=True)
    return ranked


def format_context(chunks: List[RetrievedChunk], max_chars: int = 6000) -> str:
    if not chunks:
        return "No regulatory documents retrieved."

    parts = []
    total = 0
    truncated = False
    for chunk in chunks:
        agency_short = AGENCY_SHORT_MAP.get(chunk.agency, chunk.agency)
        header = f"[SOURCE: {chunk.source} | AGENCY: {agency_short} | DATE: {chunk.doc_date or 'N/A'}]"
        block = f"{header}\n{chunk.content}\n"
        if total + len(block) > max_chars:
            truncated = True
            break
        parts.append(block)
        total += len(block)

    result = "\n---\n".join(parts)
    if truncated:
        remaining = len(chunks) - len(parts)
        if remaining > 0:
            logger.warning(
                "Context truncated: %d chunks dropped (%d chars limit). "
                "Consider increasing max_chars or reducing chunk count.",
                remaining,
                max_chars,
            )
            result += f"\n---\n[NOTE: {remaining} additional regulatory document chunks were omitted due to context length limits.]"
    return result


def extract_citations(chunks: List[RetrievedChunk]) -> List[dict]:
    seen = set()
    citations = []
    for chunk in chunks:
        key = (chunk.source, chunk.chunk_index)
        if key in seen:
            continue
        seen.add(key)
        agency_short = AGENCY_SHORT_MAP.get(chunk.agency, chunk.agency)
        excerpt = chunk.content[:300].strip()
        if len(chunk.content) > 300:
            last_space = excerpt.rfind(" ")
            if last_space > 200:
                excerpt = excerpt[:last_space]
        citations.append(
            {
                "source": chunk.source,
                "agency": chunk.agency,
                "agency_short": agency_short,
                "excerpt": excerpt,
                "url": chunk.url,
                "doc_date": chunk.doc_date,
                "relevance_score": round(chunk.similarity, 4),
            }
        )
    return citations
