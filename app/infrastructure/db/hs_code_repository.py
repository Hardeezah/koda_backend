import os
import logging
import asyncio
from typing import List, Optional
from app.infrastructure.supabase import get_supabase_admin
from app.domain.models.vision import HSCodeCandidate

logger = logging.getLogger(__name__)


class HSCodeRepository:
    def __init__(self):
        from fastembed import TextEmbedding
        self._embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    async def _embed_query(self, query: str) -> List[float]:
        def _do():
            results = list(self._embedder.embed([query]))
            return results[0].tolist()
        return await asyncio.get_event_loop().run_in_executor(None, _do)

    async def semantic_search(
        self, query: str, match_count: int = 5
    ) -> List[HSCodeCandidate]:
        try:
            query_vector = await self._embed_query(query)
            supabase = get_supabase_admin()

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: supabase.rpc(
                    "match_hs_codes",
                    {"query_embedding": query_vector, "match_count": match_count},
                ).execute(),
            )

            if not response.data:
                return []

            return [
                HSCodeCandidate(
                    code=row["code"],
                    description=row["description"],
                    similarity=row["similarity"],
                    chapter=row["chapter"],
                    heading=row["heading"],
                )
                for row in response.data
            ]
        except Exception as e:
            logger.error("HS code semantic search failed: %s", e)
            return []

    async def upsert(self, records: List[dict]) -> None:
        supabase = get_supabase_admin()
        for record in records:
            text = f"{record['code']} {record['description']}"
            record["embedding"] = await self._embed_query(text)
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: supabase.table("hs_codes").upsert(records, on_conflict="code").execute()
        )


hs_code_repository = HSCodeRepository()
