import io
from typing import Optional
from app.infrastructure.documents.renderers.form_m import render_form_m
from app.infrastructure.documents.renderers.nxp import render_nxp
from app.infrastructure.documents.renderers.coo import render_coo
from app.infrastructure.documents.renderers.nafdac import render_nafdac
from app.infrastructure.documents.renderers.son_mancap import render_son_mancap

SUPPORTED_DOCUMENTS = {
    "FORM_M": {
        "name": "Form M — Application for Valid Fund",
        "agency": "Central Bank of Nigeria",
        "agency_short": "CBN",
        "direction": "import",
        "description": "Required for all imports into Nigeria above $1,000 USD. Must be opened through an Authorised Dealer Bank.",
        "agency_url": "https://www.cbn.gov.ng",
    },
    "NXP": {
        "name": "Form NXP — Non-Oil Export Proceed Form",
        "agency": "Central Bank of Nigeria",
        "agency_short": "CBN",
        "direction": "export",
        "description": "Required for all non-oil exports from Nigeria. Ensures repatriation of export proceeds within 90 days.",
        "agency_url": "https://www.cbn.gov.ng",
    },
    "COO": {
        "name": "Certificate of Origin (AfCFTA)",
        "agency": "Nigerian Export Promotion Council",
        "agency_short": "NEPC",
        "direction": "export",
        "description": "Certifies Nigerian origin of goods for preferential AfCFTA tariff rates. Issued by NEPC or approved bodies.",
        "agency_url": "https://www.nepc.gov.ng",
    },
    "NAFDAC": {
        "name": "NAFDAC Product Registration / Import Permit",
        "agency": "National Agency for Food and Drug Administration and Control",
        "agency_short": "NAFDAC",
        "direction": "import",
        "description": "Mandatory for food, drugs, cosmetics, medical devices, chemicals. Required before clearing goods at port.",
        "agency_url": "https://www.nafdac.gov.ng",
    },
    "SON_MANCAP": {
        "name": "SON MANCAP — Mandatory Conformity Assessment",
        "agency": "Standards Organisation of Nigeria",
        "agency_short": "SON",
        "direction": "import",
        "description": "Mandatory for electrical goods, building materials, tyres, and consumer goods. Required before importation.",
        "agency_url": "https://www.son.gov.ng",
    },
}

_RENDERER_MAP = {
    "FORM_M": render_form_m,
    "NXP": render_nxp,
    "COO": render_coo,
    "NAFDAC": render_nafdac,
    "SON_MANCAP": render_son_mancap,
}


def render_document(document_code: str, content: dict) -> io.BytesIO:
    renderer = _RENDERER_MAP.get(document_code.upper())
    if not renderer:
        raise ValueError(
            f"Unsupported document code: {document_code}. "
            f"Supported: {list(_RENDERER_MAP.keys())}"
        )
    return renderer(content)


def list_supported_documents() -> list:
    return [
        {
            "code": code,
            **meta,
        }
        for code, meta in SUPPORTED_DOCUMENTS.items()
    ]
