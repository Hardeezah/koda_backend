"""
Regulatory document ingestion runner.

Usage:
    cd backend
    python -m scripts.ingest_regulations

Drop PDFs or TXT files into assets/regulations/ named by source key:
    afcfta_rules_of_origin.pdf
    afcfta_nigeria_tariff_offer.pdf
    ncs_2026_prohibition_list.pdf
    cbn_trade_finance_circular.pdf
    nafdac_import_guidelines.pdf
    son_mancap_schedule.pdf

This script embeds and upserts all present files into the document_chunks
pgvector table in Supabase. Re-running is idempotent.
"""
import asyncio
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.infrastructure.rag.document_ingestion import ingest_all_from_assets, AGENCY_REGISTRY


async def main():
    print("Starting regulatory document ingestion...")
    print(f"Looking for files in: {pathlib.Path(__file__).resolve().parents[2] / 'assets' / 'regulations'}")
    print()

    results = await ingest_all_from_assets()

    total_chunks = 0
    for source_key, chunk_count in results.items():
        status = f"{chunk_count} chunks" if chunk_count > 0 else "FILE NOT FOUND — skipped"
        print(f"  {source_key}: {status}")
        total_chunks += chunk_count

    print()
    print(f"Ingestion complete. Total chunks upserted: {total_chunks}")

    missing = [meta["source"] for meta in AGENCY_REGISTRY if results.get(meta["source"], 0) == 0]
    if missing:
        print()
        print("Missing documents (place in assets/regulations/):")
        for source_key in missing:
            print(f"  - {source_key}.pdf  or  {source_key}.txt")


if __name__ == "__main__":
    asyncio.run(main())
