from app.infrastructure.documents.pdf_engine import render_document
import io


def ai_json_to_pdf(document_code: str, ai_content: dict, business_context: dict) -> io.BytesIO:
    merged = {**ai_content, **business_context}

    sections = ai_content.get("sections", [])
    for section in sections:
        title = section.get("title", "").lower().replace(" ", "_")
        content = section.get("content", "")
        if title and content and title not in merged:
            merged[title] = content

    return render_document(document_code, merged)
