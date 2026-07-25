import os
import json
import logging
from datetime import datetime, timezone
from groq import AsyncGroq
from typing import Optional

logger = logging.getLogger(__name__)


class IntelligenceService:
    def __init__(self):
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.vision_model = os.environ.get("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        self.temperature = float(os.environ.get("COMPLIANCE_TEMPERATURE", "0.2"))

    def _build_prompt(self, product_name: str, hs_code: str, direction: str, retrieved_context: Optional[str] = None) -> str:
        context_block = ""
        if retrieved_context:
            context_block = f"\nRELEVANT REGULATORY DOCUMENTS:\n{retrieved_context}\n\nGround your answer in the above documents where applicable.\n"

        if direction == "export":
            return f"""{context_block}
You are a Nigerian export trade compliance expert specializing in AfCFTA and Nigerian export regulations.

Product: {product_name}
HS Code: {hs_code or "Unknown"}
Direction: EXPORT from Nigeria to an African country

Analyze this product for Nigerian export compliance and AfCFTA eligibility.

Return a JSON object with exactly these fields:
{{
  "product_name": "proper commercial name of this product",
  "status": "compliant" or "non_compliant" or "under_review",
  "suggested_hs_code": "Nigerian Customs HS tariff code",
  "afcfta_eligible": true or false,
  "tariff_saving_percent": estimated percentage tariff saving under AfCFTA (number),
  "roo_eligible": true or false,
  "roo_type": "wholly obtained" or "substantial transformation" or "value added threshold",
  "summary": "2-3 sentence plain English explanation of this product's export status and AfCFTA opportunity",
  "what_to_do": "Step by step plain English instructions for this trader on how to export this product legally and claim AfCFTA rates",
  "risks": [
    {{"level": "high/medium/low", "reason": "specific risk description", "action_required": "what the trader must do"}}
  ],
  "compliance_items": [
    {{
      "code": "unique short code like COO or NXP",
      "name": "full document or permit name",
      "agency": "full agency name",
      "agency_short": "short agency name",
      "description": "plain English explanation of what this is and why it is needed for this specific product",
      "how_to_obtain": "step by step on how to get this specific document",
      "processing_time": "realistic time estimate",
      "cost_estimate": "realistic cost in Naira or USD if known",
      "is_critical": true or false,
      "agency_url": "official website URL if known"
    }}
  ]
}}

The compliance_items must include all relevant documents from this list that apply to this specific product:
- AfCFTA Certificate of Origin (NEPC/MAN/NACCIMA) - always required for AfCFTA
- Form NXP (CBN) - always required
- NEPC Export Certificate - always required
- NAFDAC Export Permit - only for food, drugs, cosmetics
- SON Export Conformity Certificate - only for manufactured goods
- Phytosanitary Certificate - only for agricultural produce, plants, food
- Combined Export Declaration (Nigeria Customs)
- AfCFTA Rules of Origin Evidence Pack

Only include items that genuinely apply to this product. Explain each one in the context of this specific product.
"""
        else:
            return f"""{context_block}
You are a Nigerian import trade compliance expert specializing in Nigerian Customs regulations, the 2026 Import Prohibition List, and trade documentation.

Product: {product_name}
HS Code: {hs_code or "Unknown"}
Direction: IMPORT into Nigeria

Analyze this product for Nigerian import compliance.

Return a JSON object with exactly these fields:
{{
  "product_name": "proper commercial name of this product",
  "status": "compliant" or "non_compliant" or "under_review",
  "suggested_hs_code": "Nigerian Customs HS tariff code",
  "prohibited": true or false,
  "prohibition_reason": "specific reason if prohibited, null if not",
  "import_duty_percent": estimated import duty percentage (number),
  "vat_percent": 7.5,
  "summary": "2-3 sentence plain English explanation of this product's import status in Nigeria",
  "what_to_do": "Step by step plain English instructions for this trader on how to import this product legally into Nigeria",
  "risks": [
    {{"level": "high/medium/low", "reason": "specific risk description", "action_required": "what the trader must do"}}
  ],
  "compliance_items": [
    {{
      "code": "unique short code like FORM_M or PAAR",
      "name": "full document or permit name",
      "agency": "full agency name",
      "agency_short": "short agency name",
      "description": "plain English explanation of what this is and why it is needed for this specific product",
      "how_to_obtain": "step by step on how to get this specific document for this product",
      "processing_time": "realistic time estimate",
      "cost_estimate": "realistic cost in Naira if known",
      "is_critical": true or false,
      "agency_url": "official website URL if known"
    }}
  ]
}}

The compliance_items must include all relevant documents from this list that apply to this specific product:
- Form M (CBN) - always required for imports above $1000
- PAAR / Destination Inspection (Nigeria Customs) - always required
- CCVO benchmark value (Nigeria Customs) - include the benchmark value for this HS code if known
- NAFDAC Import Registration - only for food, drugs, cosmetics, medical devices, chemicals
- SON MANCAP Certification - only for electrical goods, building materials, tyres, consumer goods
- NAQS Import Permit - only for plants, animals, agricultural products
- NESREA Permit - only for chemicals, hazardous materials, electronics
- Combined Customs Declaration (Nigeria Customs) - always required

Only include items that genuinely apply to this product. Be specific about this product, not generic.
"""

    async def analyze_compliance(
        self,
        product_name: str,
        hs_code: str = None,
        direction: str = "import",
        retrieved_context: Optional[str] = None,
        supplementary_context: Optional[str] = None,
    ) -> dict:
        from app.infrastructure.rag.compliance_chain import compliance_chain

        extra = supplementary_context or ""
        if retrieved_context:
            extra = f"{retrieved_context}\n{extra}".strip() if extra else retrieved_context

        try:
            verdict = await compliance_chain.run(
                product_name=product_name,
                hs_code=hs_code,
                direction=direction,
                supplementary_context=extra or None,
            )
            return verdict.model_dump()
        except Exception as e:
            logger.warning("RAG compliance chain failed for %s, falling back to LLM: %s", product_name, e)
            return await self._analyze_compliance_llm_only(
                product_name, hs_code, direction, retrieved_context, supplementary_context
            )

    async def _analyze_compliance_llm_only(
        self,
        product_name: str,
        hs_code: str = None,
        direction: str = "import",
        retrieved_context: Optional[str] = None,
        supplementary_context: Optional[str] = None,
    ) -> dict:
        context_parts = []
        if retrieved_context:
            context_parts.append(retrieved_context)
        if supplementary_context:
            context_parts.append(supplementary_context)
        combined_context = "\n".join(context_parts) if context_parts else None

        prompt = self._build_prompt(product_name, hs_code, direction, combined_context)
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Nigerian trade compliance expert. Always return valid JSON only. No markdown, no explanation outside the JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=self.temperature,
            )
            result = json.loads(chat_completion.choices[0].message.content)
            result["direction"] = direction
            result["retrieval_used"] = False
            result["citations"] = []
            return result
        except Exception as e:
            logger.error("LLM-only compliance analysis failed: %s", e)
            raise

    async def analyze_image(self, base64_image: str, direction: str = "import") -> dict:
        from app.infrastructure.ai.vision_pipeline import vision_pipeline
        from app.infrastructure.ai.hs_classifier import hs_classifier
        from app.domain.models.vision import VisualAnalysisResult

        try:
            logger.info("Processing image - length: %d", len(base64_image))

            attributes = await vision_pipeline.identify_product(base64_image)
            logger.info("Identified: %s (category: %s)", attributes.product_name, attributes.category)

            hs_result = await hs_classifier.classify(attributes)
            logger.info("HS Code: %s (confidence: %s)", hs_result.assigned_code, hs_result.confidence)

            compliance = await self.analyze_compliance(
                product_name=attributes.product_name,
                hs_code=hs_result.assigned_code,
                direction=direction,
            )

            visual_result = VisualAnalysisResult(
                product_name=attributes.product_name,
                attributes=attributes,
                hs_code=hs_result,
                direction=direction,
            )

            compliance["product_name"] = attributes.product_name
            compliance["direction"] = direction
            compliance["visual_analysis"] = visual_result.model_dump()

            return compliance

        except Exception as e:
            logger.exception("Vision analysis failed")
            raise Exception(f"Vision analysis failed: {str(e)}") from e

    async def generate_document(
        self,
        document_code: str,
        document_name: str,
        product_name: str,
        hs_code: str = None,
        direction: str = "import",
        destination_country: str = None,
        business_name: str = None,
        business_address: str = None,
        cac_number: str = None,
    ) -> dict:
        from app.infrastructure.rag.retriever import regulatory_retriever
        from app.infrastructure.rag.reranker import rerank, format_context

        reg_context = ""
        try:
            chunks = await regulatory_retriever.retrieve_for_compliance(
                f"{document_code} {document_name} {product_name}",
                direction,
            )
            ranked = rerank(
                chunks,
                [document_code, product_name, direction, "nigeria"],
            )
            reg_context = format_context(ranked, max_chars=4000)
        except Exception as e:
            logger.warning("Document RAG retrieval failed: %s", e)

        context_block = ""
        if reg_context and reg_context != "No regulatory documents retrieved.":
            context_block = f"""
    RELEVANT REGULATORY DOCUMENTS:
    {reg_context}

    Ground the document content in the above regulations where applicable.
    """

        prompt = f"""You are a Nigerian trade compliance officer generating official document drafts.
    {context_block}
    Generate a complete draft of: {document_name} ({document_code})

    Details:
    - Product: {product_name}
    - HS Code: {hs_code or "To be confirmed"}
    - Direction: {direction}
    - Business Name: {business_name or "[BUSINESS NAME]"}
    - CAC Number: {cac_number or "[CAC NUMBER]"}
    - Destination: {destination_country or "N/A"}

    You MUST return ONLY a JSON object. No text before or after. No markdown. No explanation.
    The JSON must have EXACTLY these keys:

    {{
    "document_title": "official title of this document",
    "agency": "full agency name",
    "agency_address": "official Nigerian agency address",
    "purpose": "one sentence explaining what this document does for this trader",
    "sections": [
        {{
        "title": "section name",
        "content": "complete filled content for this section"
        }}
    ],
    "cover_letter": "complete formal cover letter from trader to agency, ready to print",
    "submission_steps": [
        "step 1 description",
        "step 2 description"
    ],
    "supporting_documents_checklist": [
        {{
        "item": "document name",
        "description": "what it is and where to get it",
        "mandatory": true
        }}
    ],
    "important_notes": "critical warnings specific to this product",
    "estimated_processing": "realistic timeline",
    "estimated_cost": "realistic cost in Naira"
    }}

    For sections, include all relevant fields for {document_name} filled with the product details above.
    Use [PLACEHOLDER] only for information the trader must supply themselves like bank details, signature, or exact values.
    The cover_letter must be fully written, professional, addressed to {document_name} department.
    """

        try:
            logger.info("Generating document: %s for %s", document_code, product_name)
            completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Nigerian trade document specialist. Return ONLY valid JSON. No markdown, no code blocks, no explanation. Start your response with {{ and end with }}."
                    },
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            raw = completion.choices[0].message.content
            logger.info("Document response length: %d", len(raw))

            result = json.loads(raw)

            if "document_title" not in result or "sections" not in result:
                logger.info("Model returned wrong shape, converting to structured format")
                result = self._convert_flat_to_structured(
                    result, document_code, document_name, product_name
                )

            return result

        except json.JSONDecodeError as e:
            logger.error("JSON decode failed for document generation: %s", e)
            raise ValueError("AI returned invalid JSON") from e
        except Exception as e:
            logger.exception("generate_document failed: %s", e)
            raise

    def _convert_flat_to_structured(
        self,
        raw: dict,
        document_code: str,
        document_name: str,
        product_name: str,
    ) -> dict:
        import re

        content = raw.get("content", "")
        chunks = re.split(r'\n(?=\d+\.\s|\n)', content.strip())
        sections = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            lines = chunk.split('\n')
            first_line = lines[0].strip()
            if re.match(r'^\d+\.', first_line) or first_line.endswith(':'):
                title = re.sub(r'^\d+\.\s*', '', first_line).rstrip(':')
                body = '\n'.join(lines[1:]).strip()
            else:
                title = f"Section {len(sections) + 1}"
                body = chunk
            if body or title:
                sections.append({"title": title, "content": body or chunk})

        agency_map = {
            "FORM_M": ("Central Bank of Nigeria (CBN)", "CBN Headquarters, Central Business District, Abuja"),
            "PAAR": ("Nigeria Customs Service", "NCS Headquarters, Wuse Zone 3, Abuja"),
            "NAFDAC": ("National Agency for Food and Drug Administration and Control", "NAFDAC Headquarters, Wuse Zone 7, Abuja"),
            "SON_MANCAP": ("Standards Organisation of Nigeria", "SON Headquarters, Lome Street, Wuse Zone 7, Abuja"),
            "NAQS": ("National Agricultural Quarantine Service", "NAQS Headquarters, Area 11, Garki, Abuja"),
            "COO": ("Nigerian Export Promotion Council", "NEPC Headquarters, Olusegun Obasanjo Way, Abuja"),
            "NXP": ("Central Bank of Nigeria (CBN)", "CBN Headquarters, Central Business District, Abuja"),
            "NEPC": ("Nigerian Export Promotion Council", "NEPC Headquarters, Olusegun Obasanjo Way, Abuja"),
        }

        agency, agency_address = agency_map.get(
            document_code,
            ("Relevant Government Agency", "Nigeria")
        )

        return {
            "document_title": raw.get("document_name", document_name),
            "agency": agency,
            "agency_address": agency_address,
            "purpose": f"This {document_name} is required for the {raw.get('direction', 'import')} of {product_name} into/from Nigeria.",
            "sections": sections,
            "cover_letter": self._generate_cover_letter(document_name, agency, product_name),
            "submission_steps": [
                "Complete all [PLACEHOLDER] fields in this document with your business details.",
                f"Gather all supporting documents listed in the checklist.",
                f"Visit your bank's trade finance desk to submit Form M (for CBN documents) or go directly to {agency}.",
                "Retain a stamped copy of your submission for your records.",
                "Follow up after the processing period if you have not received a response.",
            ],
            "supporting_documents_checklist": [
                {"item": "Valid means of identification", "description": "National ID, International Passport, or Driver's License", "mandatory": True},
                {"item": "CAC Certificate of Incorporation", "description": "Proof that your business is registered in Nigeria", "mandatory": True},
                {"item": "Proforma Invoice or Commercial Invoice", "description": "Invoice from your supplier showing product details and value", "mandatory": True},
                {"item": "Packing List", "description": "Detailed list of goods in the shipment", "mandatory": True},
            ],
            "important_notes": f"This is a KodaTrade-generated draft for {product_name}. Review all details carefully before submission. Fields marked [PLACEHOLDER] must be completed by you.",
            "estimated_processing": raw.get("estimated_processing", "5-15 business days"),
            "estimated_cost": raw.get("estimated_cost", "Varies by bank/agency"),
        }

    def _generate_cover_letter(self, document_name: str, agency: str, product_name: str) -> str:
        today = datetime.now(timezone.utc).strftime("%d %B %Y")
        return f"""[YOUR BUSINESS NAME]
[YOUR BUSINESS ADDRESS]
[CITY, STATE]
[PHONE NUMBER]
[EMAIL ADDRESS]

{today}

The Director/Manager
{agency}
[AGENCY ADDRESS]

Dear Sir/Madam,

RE: APPLICATION FOR {document_name.upper()} — {product_name.upper()}

I write on behalf of [YOUR BUSINESS NAME] (CAC Reg. No: [CAC NUMBER]) to formally submit our application for the above-referenced document in relation to the importation/exportation of {product_name} (HS Code: [HS CODE]).

Our company is duly registered under the laws of the Federal Republic of Nigeria and has been engaged in lawful trade activities. We hereby declare that all information provided in the attached documents is true, accurate, and complete to the best of our knowledge.

We kindly request the prompt processing of this application and remain available to provide any additional information or documentation that may be required.

Please find attached all required supporting documents for your review and processing.

Yours faithfully,

_____________________________
[AUTHORISED SIGNATORY NAME]
[DESIGNATION]
[YOUR BUSINESS NAME]
[DATE]"""


intelligence_service = IntelligenceService()
