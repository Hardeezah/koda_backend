import os
import pathlib
import logging
from typing import List, Dict, Optional
from app.infrastructure.supabase import get_supabase_admin

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_BATCH_SIZE = 50

AGENCY_REGISTRY: List[Dict] = [
    {
        "source": "afcfta_rules_of_origin",
        "agency": "AfCFTA Secretariat",
        "doc_date": "2024-01",
        "url": "https://au-afcfta.org",
    },
    {
        "source": "afcfta_nigeria_tariff_offer",
        "agency": "AfCFTA Secretariat",
        "doc_date": "2025-04",
        "url": "https://fmiti.gov.ng",
    },
    {
        "source": "ncs_2026_prohibition_list",
        "agency": "Nigeria Customs Service",
        "doc_date": "2026-04",
        "url": "https://customs.gov.ng",
    },
    {
        "source": "cbn_trade_finance_circular",
        "agency": "Central Bank of Nigeria",
        "doc_date": "2026-06",
        "url": "https://www.cbn.gov.ng",
    },
    {
        "source": "nafdac_import_guidelines",
        "agency": "NAFDAC",
        "doc_date": "2025-01",
        "url": "https://www.nafdac.gov.ng",
    },
    {
        "source": "son_mancap_schedule",
        "agency": "Standards Organisation of Nigeria",
        "doc_date": "2025-01",
        "url": "https://www.son.gov.ng",
    },
]

ASSETS_DIR = pathlib.Path(__file__).resolve().parents[3] / "assets" / "regulations"


def _chunk_text(text: str) -> List[str]:
    chunks: List[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + CHUNK_SIZE])
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c.strip()]


def _extract_text_from_pdf(pdf_path: pathlib.Path) -> str:
    import fitz
    doc = fitz.open(str(pdf_path))
    return "\n".join(page.get_text() for page in doc)


def _extract_text_from_txt(txt_path: pathlib.Path) -> str:
    return txt_path.read_text(encoding="utf-8")


def _embed_in_batches(_embedder, texts: List[str], batch_size: int = EMBEDDING_BATCH_SIZE) -> List[List[float]]:
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        results = list(_embedder.embed(batch))
        vectors = [v.tolist() for v in results]
        all_vectors.extend(vectors)
        logger.info("Embedded batch %d/%d (%d chunks)", i // batch_size + 1, (len(texts) + batch_size - 1) // batch_size, len(batch))
    return all_vectors


def _shared_embeddings():
    if not hasattr(_shared_embeddings, "_instance"):
        from fastembed import TextEmbedding
        _shared_embeddings._instance = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _shared_embeddings._instance


async def ingest_source(source_key: str, content: str, meta: Dict) -> int:
    embeddings = _shared_embeddings()
    supabase = get_supabase_admin()

    chunks = _chunk_text(content)
    if not chunks:
        logger.info("No chunks produced for source=%s", source_key)
        return 0

    vectors = _embed_in_batches(embeddings, chunks)
    records = []
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        records.append(
            {
                "source": source_key,
                "agency": meta["agency"],
                "doc_date": meta.get("doc_date"),
                "url": meta.get("url"),
                "chunk_index": idx,
                "content": chunk,
                "embedding": vector,
            }
        )

    import asyncio
    await asyncio.get_event_loop().run_in_executor(
        None, lambda: supabase.table("document_chunks").delete().eq("source", source_key).execute()
    )
    if records:
        for i in range(0, len(records), 100):
            batch = records[i : i + 100]
            await asyncio.get_event_loop().run_in_executor(
                None, lambda b=batch: supabase.table("document_chunks").insert(b).execute()
            )
        logger.info("Ingested %d chunks for source=%s", len(records), source_key)

    return len(records)


async def ingest_all_from_assets() -> Dict[str, int]:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    results: Dict[str, int] = {}

    for meta in AGENCY_REGISTRY:
        source_key = meta["source"]
        pdf_path = ASSETS_DIR / f"{source_key}.pdf"
        txt_path = ASSETS_DIR / f"{source_key}.txt"

        if pdf_path.exists():
            content = _extract_text_from_pdf(pdf_path)
            results[source_key] = await ingest_source(source_key, content, meta)
        elif txt_path.exists():
            content = _extract_text_from_txt(txt_path)
            results[source_key] = await ingest_source(source_key, content, meta)
        else:
            results[source_key] = 0
            logger.warning("No document found for %s (looked for %s, %s)", source_key, pdf_path, txt_path)

    return results


async def ingest_raw(source_key: str, content: str, agency: str, doc_date: Optional[str] = None, url: Optional[str] = None) -> int:
    meta = {"agency": agency, "doc_date": doc_date, "url": url}
    return await ingest_source(source_key, content, meta)
