import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

HEADER_COLOR = colors.HexColor("#1A237E")
LIGHT_INDIGO = colors.HexColor("#E8EAF6")
BORDER_COLOR = colors.HexColor("#CCCCCC")


def _field_row(label: str, value: str) -> Table:
    data = [[
        Paragraph(label, ParagraphStyle("lbl", fontSize=8, textColor=colors.gray, fontName="Helvetica")),
        Paragraph(str(value), ParagraphStyle("val", fontSize=9, fontName="Helvetica")),
    ]]
    t = Table(data, colWidths=[2.5 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (1, 0), (1, 0), 0.5, BORDER_COLOR),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def render_son_mancap(content: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    today = date.today().strftime("%d %B %Y")
    ref = f"KT/SON-MANCAP/{date.today().strftime('%Y%m%d')}"
    elements = []

    header_data = [[
        Paragraph(
            "<b>STANDARDS ORGANISATION OF NIGERIA (SON)</b><br/>MANDATORY CONFORMITY ASSESSMENT PROGRAMME (MANCAP)<br/>APPLICATION FOR PRODUCT CERTIFICATION",
            ParagraphStyle("h", fontSize=11, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER),
        ),
        Paragraph(
            f"<b>Ref:</b> {ref}<br/><b>Date:</b> {today}",
            ParagraphStyle("h2", fontSize=9, textColor=colors.white, fontName="Helvetica", alignment=TA_RIGHT),
        ),
    ]]
    header_t = Table(header_data, colWidths=[4.5 * inch, 2.5 * inch])
    header_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HEADER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 12),
    ]))
    elements.append(header_t)
    elements.append(Spacer(1, 0.15 * inch))

    section_style = ParagraphStyle("sec", fontSize=10, textColor=HEADER_COLOR, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=8)
    footer_style = ParagraphStyle("ft", fontSize=7, textColor=colors.gray, alignment=TA_CENTER)
    note_style = ParagraphStyle("note", fontSize=8, textColor=colors.HexColor("#880000"), fontName="Helvetica-Oblique", spaceAfter=6)

    elements.append(Paragraph(
        "NOTE: MANCAP certification is mandatory for all manufactured goods including electrical products, building materials, tyres, food contact materials, and consumer goods under SON Act 2015.",
        note_style
    ))

    elements.append(Paragraph("APPLICANT INFORMATION", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Company Name:", content.get("business_name", "[COMPANY NAME]")),
        ("CAC Registration No.:", content.get("cac_number", "[CAC NUMBER]")),
        ("TIN:", content.get("tin", "[TIN]")),
        ("Company Address:", content.get("business_address", "[COMPANY ADDRESS]")),
        ("Contact Person:", content.get("contact_person", "[CONTACT PERSON]")),
        ("Phone Number:", content.get("phone", "[PHONE NUMBER]")),
        ("Email Address:", content.get("email", "[EMAIL ADDRESS]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("PRODUCT DETAILS", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Product Name / Model:", content.get("product_name", "[PRODUCT NAME]")),
        ("HS Code:", content.get("hs_code", "[HS CODE]")),
        ("Product Category:", content.get("product_category", "[electrical / building material / tyre / consumer good / other]")),
        ("Brand Name:", content.get("brand_name", "[BRAND NAME]")),
        ("Manufacturer Name:", content.get("manufacturer_name", "[MANUFACTURER]")),
        ("Country of Manufacture:", content.get("country_of_origin", "[COUNTRY OF MANUFACTURE]")),
        ("Model / Batch Number:", content.get("model_number", "[MODEL / BATCH NUMBER]")),
        ("Intended Use:", content.get("purpose", "[DESCRIBE PRIMARY USE]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("APPLICABLE NIGERIAN STANDARDS", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Applicable NIS Standard(s):", content.get("applicable_standard", "[e.g. NIS 444:2021 for LED lamps / NIS 196:2016 for extension cords]")),
        ("International Equivalent Standard:", content.get("international_standard", "[e.g. IEC 60598, ISO 9001]")),
        ("Third-Party Test Report No.:", content.get("test_report_number", "[TEST REPORT NUMBER FROM ACCREDITED LAB]")),
        ("Testing Laboratory:", content.get("testing_lab", "[NAME OF SON-ACCREDITED TESTING LABORATORY]")),
        ("Test Date:", content.get("test_date", "[DATE OF TESTING]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("REQUIRED SUPPORTING DOCUMENTS CHECKLIST", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    checklist = [
        ["", "Document", "Status"],
        ["[ ]", "Third-Party Product Test Report (from SON-accredited lab)", "Mandatory"],
        ["[ ]", "Product Sample (minimum 3 units for physical inspection)", "Mandatory"],
        ["[ ]", "Technical Specification / Data Sheet", "Mandatory"],
        ["[ ]", "Certificate of Conformance from manufacturer", "Mandatory"],
        ["[ ]", "Quality Management System Certificate (ISO 9001 or equivalent)", "Mandatory"],
        ["[ ]", "Commercial Invoice for the batch", "Mandatory"],
        ["[ ]", "Product Labeling showing country of manufacture, model, batch no.", "Mandatory"],
        ["[ ]", "CAC Certificate of Incorporation", "Mandatory"],
        ["[ ]", "Power of Attorney (if agent applying on behalf of manufacturer)", "If applicable"],
    ]
    checklist_t = Table(checklist, colWidths=[0.3 * inch, 5.2 * inch, 1.5 * inch])
    checklist_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_INDIGO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(checklist_t)

    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(
        "Submit to: SON Headquarters, 52 Lome Street, Wuse Zone 7, Abuja | Website: www.son.gov.ng | Hotline: 0800-766-7667",
        footer_style
    ))
    elements.append(Paragraph("Generated by KodaTrade AI Trade Co-Pilot | This is a draft — verify current standards with SON before submission", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
