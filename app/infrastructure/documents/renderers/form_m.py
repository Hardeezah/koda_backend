import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


HEADER_COLOR = colors.HexColor("#003366")
LIGHT_BLUE = colors.HexColor("#E8F0FE")
BORDER_COLOR = colors.HexColor("#CCCCCC")


def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("DocTitle", fontSize=14, textColor=colors.white, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=4))
    styles.add(ParagraphStyle("DocSubtitle", fontSize=9, textColor=colors.white, alignment=TA_CENTER, fontName="Helvetica"))
    styles.add(ParagraphStyle("SectionHeader", fontSize=10, textColor=HEADER_COLOR, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=8))
    styles.add(ParagraphStyle("FieldLabel", fontSize=8, textColor=colors.gray, fontName="Helvetica"))
    styles.add(ParagraphStyle("FieldValue", fontSize=9, textColor=colors.black, fontName="Helvetica", spaceAfter=2))
    styles.add(ParagraphStyle("FooterText", fontSize=7, textColor=colors.gray, alignment=TA_CENTER))
    styles.add(ParagraphStyle("CoverBody", fontSize=9, fontName="Helvetica", leading=14, spaceAfter=6))
    return styles


def _header_table(title: str, subtitle: str, ref_number: str, doc_date: str) -> Table:
    header_data = [
        [
            Paragraph(f"<b>FEDERAL REPUBLIC OF NIGERIA</b><br/>{title}", ParagraphStyle("h", fontSize=13, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Paragraph(f"<b>Ref:</b> {ref_number}<br/><b>Date:</b> {doc_date}", ParagraphStyle("h2", fontSize=9, textColor=colors.white, fontName="Helvetica", alignment=TA_RIGHT)),
        ]
    ]
    t = Table(header_data, colWidths=[4.5 * inch, 2.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HEADER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 12),
    ]))
    return t


def _field_row(label: str, value: str) -> Table:
    data = [[
        Paragraph(label, ParagraphStyle("lbl", fontSize=8, textColor=colors.gray, fontName="Helvetica")),
        Paragraph(str(value), ParagraphStyle("val", fontSize=9, fontName="Helvetica")),
    ]]
    t = Table(data, colWidths=[2 * inch, 5 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (1, 0), (1, 0), 0.5, BORDER_COLOR),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def render_form_m(content: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = _base_styles()
    today = date.today().strftime("%d %B %Y")
    ref = f"KT/FORM-M/{date.today().strftime('%Y%m%d')}"
    elements = []

    elements.append(_header_table("FORM M — APPLICATION FOR VALID FUND", "Central Bank of Nigeria — Trade Finance", ref, today))
    elements.append(Spacer(1, 0.15 * inch))

    elements.append(Paragraph("APPLICANT INFORMATION", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    business_name = content.get("business_name", "[BUSINESS NAME]")
    cac_number = content.get("cac_number", "[CAC NUMBER]")
    product_name = content.get("product_name", "[PRODUCT]")
    hs_code = content.get("hs_code", "[HS CODE]")
    quantity = content.get("quantity", "[QUANTITY]")
    value_usd = content.get("value_usd", "[VALUE USD]")
    direction = content.get("direction", "import")

    for label, value in [
        ("Importer / Exporter Name:", business_name),
        ("CAC Registration No.:", cac_number),
        ("TIN:", content.get("tin", "[TIN]")),
        ("Bank:", content.get("bank", "[AUTHORISED DEALER BANK]")),
        ("Bank Branch:", content.get("bank_branch", "[BRANCH]")),
        ("Account Number:", content.get("account_number", "[ACCOUNT NUMBER]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("GOODS DETAILS", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Description of Goods:", product_name),
        ("HS Code:", hs_code),
        ("Quantity / Unit:", quantity),
        ("Country of Supply:", content.get("country_of_supply", "[COUNTRY OF SUPPLY]")),
        ("Port of Entry:", content.get("port_of_entry", "[PORT OF ENTRY]")),
        ("Country of Origin:", content.get("country_of_origin", "[COUNTRY OF ORIGIN]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("FINANCIAL DETAILS", styles["SectionHeader"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("FOB Value (USD):", f"${value_usd}"),
        ("Currency:", "USD"),
        ("Payment Terms:", content.get("payment_terms", "[PAYMENT TERMS e.g. 100% L/C]")),
        ("Incoterms:", content.get("incoterms", "[CIF / FOB / EXW]")),
        ("Import Duty Rate:", f"{content.get('import_duty_percent', '[DUTY %]')}%"),
        ("VAT:", "7.5%"),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.25 * inch))

    declaration = [
        ["DECLARATION", ""],
        ["I/We hereby declare that the information furnished above is true and correct to the best of my/our knowledge and belief, and that the goods described herein are for legitimate commercial purposes in compliance with the laws of the Federal Republic of Nigeria.", ""],
        ["Authorised Signatory:", "__________________________"],
        ["Name:", "[SIGNATORY NAME]"],
        ["Designation:", "[DESIGNATION]"],
        ["Date:", "[DATE]"],
        ["Bank Stamp:", ""],
    ]
    decl_table = Table(declaration, colWidths=[3.5 * inch, 3.5 * inch])
    decl_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("SPAN", (0, 1), (-1, 1)),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(decl_table)

    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Generated by KodaTrade AI Trade Co-Pilot | For official submission, verify with your Authorised Dealer Bank", styles["FooterText"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer
