import os
import json
from groq import AsyncGroq
from app.domain.models.vision import ProductAttributes, HSCodeResult, HSCodeCandidate
from app.infrastructure.db.hs_code_repository import hs_code_repository
from typing import List


CATEGORY_CHAPTER_HINTS = {
    "food": ["02", "03", "04", "07", "08", "09", "10", "11", "15", "16", "17", "18", "19", "20", "21"],
    "agricultural": ["06", "07", "08", "09", "10", "12", "13", "14"],
    "textile": ["50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63"],
    "electronics": ["84", "85", "86", "90"],
    "machinery": ["84", "85", "86", "87", "88", "89"],
    "chemicals": ["28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38"],
    "pharmaceutical": ["29", "30"],
    "cosmetics": ["33", "34"],
    "building_materials": ["25", "26", "68", "69", "70", "72", "73", "74"],
    "consumer_goods": ["39", "40", "42", "44", "48", "61", "62", "64", "69", "70", "73", "83", "84", "85", "94", "95"],
    "vehicles": ["86", "87", "88", "89"],
}


class HSClassifier:
    def __init__(self):
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def _build_search_query(self, attrs: ProductAttributes) -> str:
        parts = [attrs.product_name]
        if attrs.category and attrs.category != "other":
            parts.append(attrs.category)
        if attrs.material:
            parts.append(attrs.material)
        if attrs.purpose:
            parts.append(attrs.purpose)
        if attrs.description:
            parts.append(attrs.description)
        return " ".join(parts)

    def _format_candidates(self, candidates: List[HSCodeCandidate]) -> str:
        if not candidates:
            return "No vector candidates found."
        lines = []
        for c in candidates:
            lines.append(
                f"- {c.code}: {c.description} (Chapter {c.chapter}, similarity: {c.similarity:.3f})"
            )
        return "\n".join(lines)

    async def classify(self, attrs: ProductAttributes) -> HSCodeResult:
        query = self._build_search_query(attrs)
        candidates = await hs_code_repository.semantic_search(query, match_count=5)

        chapter_hints = CATEGORY_CHAPTER_HINTS.get(attrs.category, [])

        prompt = f"""You are a Nigerian Customs HS Code classification expert.

Product attributes extracted from image:
- Name: {attrs.product_name}
- Category: {attrs.category}
- Description: {attrs.description}
- Material: {attrs.material or "unknown"}
- Brand: {attrs.brand or "unknown"}
- Purpose: {attrs.purpose or "unknown"}
- Packaging: {attrs.packaging or "unknown"}
- Weight Class: {attrs.weight_class or "unknown"}
- Origin Cues: {attrs.origin_cues or "none visible"}

Vector similarity search returned these HS Code candidates:
{self._format_candidates(candidates)}

Category-based chapter hints for "{attrs.category}": {", ".join(chapter_hints) if chapter_hints else "none"}

Select the single most accurate 6-digit or 4-digit HS Code for this product under the Nigerian Customs Tariff (based on WCO Harmonized System).
If vector candidates are strong (similarity > 0.85), prefer them. Otherwise use your expert knowledge.

Return ONLY this JSON:
{{
  "assigned_code": "exact HS code digits e.g. 090111",
  "description": "official HS description for this code",
  "confidence": 0.0 to 1.0,
  "chapter": "2-digit chapter number",
  "heading": "4-digit heading",
  "reasoning": "one sentence explaining why this code is correct for this specific product"
}}"""

        completion = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an HS Code classification expert. Return ONLY valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw = json.loads(completion.choices[0].message.content)

        return HSCodeResult(
            assigned_code=raw.get("assigned_code", ""),
            description=raw.get("description", ""),
            confidence=float(raw.get("confidence", 0.5)),
            chapter=raw.get("chapter", ""),
            heading=raw.get("heading", ""),
            candidates=candidates,
            reasoning=raw.get("reasoning", ""),
        )


hs_classifier = HSClassifier()
