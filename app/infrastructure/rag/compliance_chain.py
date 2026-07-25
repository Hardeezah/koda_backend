import os
import json
import logging
from groq import AsyncGroq
from typing import Optional
from app.infrastructure.rag.retriever import regulatory_retriever
from app.infrastructure.rag.reranker import rerank, format_context, extract_citations
from app.domain.models.rag import CitedComplianceVerdict, Citation, ComplianceItem, Risk

logger = logging.getLogger(__name__)

EXPORT_SCHEMA = """{
  "product_name": "proper commercial name",
  "status": "compliant" or "non_compliant" or "under_review",
  "suggested_hs_code": "6-digit Nigerian Customs HS tariff code",
  "afcfta_eligible": true or false,
  "tariff_saving_percent": number,
  "roo_eligible": true or false,
  "roo_type": "wholly obtained" or "substantial transformation" or "value added threshold",
  "summary": "2-3 sentence plain English verdict grounded in the retrieved documents above",
  "what_to_do": "step by step plain English export instructions citing the relevant regulatory requirements",
  "risks": [{"level": "high/medium/low", "reason": "specific risk with source reference", "action_required": "concrete action"}],
  "compliance_items": [
    {
      "code": "e.g. COO",
      "name": "full document name",
      "agency": "full agency name",
      "agency_short": "short name",
      "description": "what this is and why required for this product",
      "how_to_obtain": "step by step",
      "processing_time": "realistic timeline",
      "cost_estimate": "realistic Naira or USD cost",
      "is_critical": true or false,
      "agency_url": "official URL or null"
    }
  ]
}"""

IMPORT_SCHEMA = """{
  "product_name": "proper commercial name",
  "status": "compliant" or "non_compliant" or "under_review",
  "suggested_hs_code": "6-digit Nigerian Customs HS tariff code",
  "prohibited": true or false,
  "prohibition_reason": "specific reason if prohibited, null otherwise",
  "import_duty_percent": number,
  "vat_percent": 7.5,
  "summary": "2-3 sentence plain English verdict grounded in the retrieved documents above",
  "what_to_do": "step by step plain English import instructions citing the relevant regulatory requirements",
  "risks": [{"level": "high/medium/low", "reason": "specific risk with source reference", "action_required": "concrete action"}],
  "compliance_items": [
    {
      "code": "e.g. FORM_M",
      "name": "full document name",
      "agency": "full agency name",
      "agency_short": "short name",
      "description": "what this is and why required for this product",
      "how_to_obtain": "step by step",
      "processing_time": "realistic timeline",
      "cost_estimate": "realistic Naira cost",
      "is_critical": true or false,
      "agency_url": "official URL or null"
    }
  ]
}"""


class ComplianceChain:
    def __init__(self):
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.temperature = float(os.environ.get("COMPLIANCE_TEMPERATURE", "0.2"))

    def _build_system_prompt(self, direction: str) -> str:
        direction_label = "EXPORT from Nigeria to an African country" if direction == "export" else "IMPORT into Nigeria"
        return (
            f"You are a senior Nigerian trade compliance expert specializing in Nigerian {direction_label} regulations. "
            "You have been provided with retrieved excerpts from official regulatory documents below. "
            "Your compliance verdict MUST be grounded in these documents. "
            "If the documents directly address the product, cite the specific provision. "
            "If no documents were retrieved, state this limitation and reduce your confidence. "
            "Never invent specific legal citations or document names that are not in the retrieved context. "
            "Return ONLY valid JSON. No markdown, no explanation outside the JSON."
        )

    def _build_user_prompt(
        self,
        product_name: str,
        hs_code: Optional[str],
        direction: str,
        context: str,
        supplementary_context: Optional[str] = None,
    ) -> str:
        schema = EXPORT_SCHEMA if direction == "export" else IMPORT_SCHEMA
        direction_label = "EXPORT from Nigeria to an African country" if direction == "export" else "IMPORT into Nigeria"

        extra_block = ""
        if supplementary_context:
            extra_block = f"\n\nSTRUCTURED TRADE DATA:\n{supplementary_context}\n"

        return f"""RETRIEVED REGULATORY DOCUMENTS:
{context}
{extra_block}
---

TASK: Analyze the following trade query for Nigerian {direction_label} compliance.

Product: {product_name}
HS Code: {hs_code or "Unknown — suggest the correct one"}
Direction: {direction_label}

Using the retrieved documents above as your primary evidence, produce a compliance verdict.
Reference the specific source documents in your summary and what_to_do fields where applicable.

Return ONLY this JSON structure:
{schema}"""

    def _parse_verdict(self, raw: dict, product_name: str, hs_code: Optional[str], direction: str, retrieval_used: bool, citations: list) -> CitedComplianceVerdict:
        risks = []
        for r in raw.get("risks", []):
            if isinstance(r, dict):
                risks.append(Risk(
                    level=str(r.get("level", "medium")),
                    reason=str(r.get("reason", "")),
                    action_required=str(r.get("action_required", "")),
                ))

        compliance_items = []
        for item in raw.get("compliance_items", []):
            if isinstance(item, dict):
                compliance_items.append(ComplianceItem(
                    code=str(item.get("code", "")),
                    name=str(item.get("name", "")),
                    agency=str(item.get("agency", "")),
                    agency_short=str(item.get("agency_short", "")),
                    description=str(item.get("description", "")),
                    how_to_obtain=str(item.get("how_to_obtain", "")),
                    processing_time=str(item.get("processing_time", "")),
                    cost_estimate=str(item.get("cost_estimate", "")),
                    is_critical=bool(item.get("is_critical", False)),
                    agency_url=item.get("agency_url"),
                ))

        def _safe_float(val, default=None):
            if val is None:
                return default
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        def _safe_bool(val, default=None):
            if val is None:
                return default
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ("true", "yes", "1")
            return default

        status = raw.get("status", "under_review")
        if status not in ("compliant", "non_compliant", "under_review"):
            status = "under_review"

        return CitedComplianceVerdict(
            product_name=raw.get("product_name") or product_name,
            status=status,
            suggested_hs_code=raw.get("suggested_hs_code") or hs_code,
            summary=raw.get("summary", ""),
            what_to_do=raw.get("what_to_do", ""),
            risks=risks,
            compliance_items=compliance_items,
            citations=citations,
            direction=direction,
            afcfta_eligible=_safe_bool(raw.get("afcfta_eligible")),
            tariff_saving_percent=_safe_float(raw.get("tariff_saving_percent")),
            roo_eligible=_safe_bool(raw.get("roo_eligible")),
            roo_type=raw.get("roo_type"),
            prohibited=_safe_bool(raw.get("prohibited")),
            prohibition_reason=raw.get("prohibition_reason"),
            import_duty_percent=_safe_float(raw.get("import_duty_percent")),
            vat_percent=_safe_float(raw.get("vat_percent"), default=7.5),
            retrieval_used=retrieval_used,
        )

    async def run(
        self,
        product_name: str,
        hs_code: Optional[str] = None,
        direction: str = "import",
        supplementary_context: Optional[str] = None,
    ) -> CitedComplianceVerdict:
        chunks = await regulatory_retriever.retrieve_for_compliance(product_name, direction)

        query_terms = product_name.lower().split() + [direction, "nigeria", "compliance"]
        ranked_chunks = rerank(chunks, query_terms)
        context = format_context(ranked_chunks)
        raw_citations = extract_citations(ranked_chunks)
        retrieval_used = len(ranked_chunks) > 0

        system_prompt = self._build_system_prompt(direction)
        if not retrieval_used:
            system_prompt += (
                " No regulatory documents were retrieved from the vector store. "
                "State this limitation in the summary, reduce confidence, and avoid inventing "
                "specific legal citations."
            )

        user_prompt = self._build_user_prompt(
            product_name, hs_code, direction, context, supplementary_context
        )

        try:
            completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=self.temperature,
            )
        except Exception as e:
            logger.error("Groq LLM call failed: %s", e)
            raise

        raw_content = completion.choices[0].message.content
        try:
            raw = json.loads(raw_content)
        except json.JSONDecodeError as e:
            logger.error("LLM returned invalid JSON: %s | raw=%s", e, raw_content[:200])
            raise ValueError(f"LLM returned invalid JSON: {e}") from e

        citations = [Citation(**c) for c in raw_citations]

        return self._parse_verdict(raw, product_name, hs_code, direction, retrieval_used, citations)


compliance_chain = ComplianceChain()
