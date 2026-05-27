import os
import json
import pathlib
import requests
from typing import List, Dict, Any

from app.infrastructure.ai.intelligence import add_metadata, intelligence_service
from app.infrastructure.redis_client import redis_service

# Directory where PDFs are stored (committed assets)
ASSETS_DIR = pathlib.Path(__file__).resolve().parents[2] / "assets" / "afcfta"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

PDF_SOURCES = {
    "afcfta_rules_of_origin": "https://www.afcfta.int/sites/default/files/2023-02/Rules_of_Origin_Annex.pdf",
    "nigeria_afcfta_tariff": "https://www.afcfta.int/sites/default/files/2023-03/Nigeria_AfCFTA_Tariff_Offer.pdf",
    "afcfta_guided_trade_factsheet": "https://www.afcfta.int/sites/default/files/2023-04/Guided_Trade_Initiative_Factsheet.pdf",
}

CHUNK_SIZE = 1000  # characters – matches existing pipeline settings
OVERLAP = 200


def download_pdfs() -> Dict[str, pathlib.Path]:
    """Download PDFs if not already present and return mapping of source -> local path."""
    paths = {}
    for source, url in PDF_SOURCES.items():
        dest = ASSETS_DIR / f"{source}.pdf"
        if not dest.exists():
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        paths[source] = dest
    return paths


def simple_chunk(text: str) -> List[str]:
    """Very naive fixed‑size chunker with overlap, mirroring existing pipeline."""
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i : i + CHUNK_SIZE]
        chunks.append(chunk)
        i += CHUNK_SIZE - OVERLAP
    return chunks


def extract_text_from_pdf(pdf_path: pathlib.Path) -> str:
    """Extract raw text from a PDF using PyMuPDF (already a dependency)."""
    import fitz  # PyMuPDF
    doc = fitz.open(str(pdf_path))
    text = "\n".join(page.get_text() for page in doc)
    return text


async def ingest():
    # 1. Ensure PDFs are available
    pdf_paths = download_pdfs()

    for source, path in pdf_paths.items():
        raw_text = extract_text_from_pdf(path)
        chunks = simple_chunk(raw_text)
        for idx, chunk in enumerate(chunks):
            # Build metadata – for Rules of Origin we attempt to pull HS code range via regex
            extra = {}
            if source == "afcfta_rules_of_origin":
                import re
                matches = re.findall(r"(\d{4})-(\d{4})", chunk)
                if matches:
                    # take first match as example
                    start, end = matches[0]
                    extra["hs_code_range"] = f"{start}-{end}"
            meta_chunk = {"content": chunk, "metadata": {"source": source}}
            meta_chunk = add_metadata(meta_chunk, source, extra if extra else None)
            # Store vector – reuse existing redis embedding helper
            await redis_service.upsert_vector(meta_chunk)
    print("AfCFTA documents ingested successfully.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest())
