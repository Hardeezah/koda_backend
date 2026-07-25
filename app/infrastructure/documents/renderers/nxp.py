import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

HEADER_COLOR = colors.HexColor("#006400")
LIGHT_GREEN = colors.HexColor("#E8F5E9")
BORDER_COLOR = colors.HexColor("#CCCCCC")


def _field_row(label: str, value: str) -> Table:
    data = [[
        Paragraph(label, ParagraphStyle("lbl", fontSize=8, textColor=colors.gray, fontName="Helvetica")),
        Paragraph(str(value), ParagraphStyle("val", fontSize=9, fontName="Helvetica")),
    ]]
    t = Table(data, colWidths=[2.2 * inch, 4.8 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (1, 0), (1, 0), 0.5, BORDER_COLOR),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def render_nxp(content: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    today = date.today().strftime("%d %B %Y")
    ref = f"KT/NXP/{date.today().strftime('%Y%m%d')}"
    elements = []

    header_data = [[
        Paragraph(
            "<b>FEDERAL REPUBLIC OF NIGERIA</b><br/>FORM NXP — NON-OIL EXPORT PROCEED FORM<br/>Central Bank of Nigeria",
            ParagraphStyle("h", fontSize=12, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER),
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

    elements.append(Paragraph("EXPORTER DETAILS", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Exporter Business Name:", content.get("business_name", "[BUSINESS NAME]")),
        ("CAC Registration No.:", content.get("cac_number", "[CAC NUMBER]")),
        ("TIN:", content.get("tin", "[TIN]")),
        ("NEPC Registration No.:", content.get("nepc_number", "[NEPC REG NUMBER]")),
        ("Exporter Address:", content.get("business_address", "[BUSINESS ADDRESS]")),
        ("Authorised Dealer Bank:", content.get("bank", "[AUTHORISED DEALER BANK]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("EXPORT GOODS DETAILS", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Description of Goods:", content.get("product_name", "[PRODUCT]")),
        ("HS Code:", content.get("hs_code", "[HS CODE]")),
        ("Quantity / Unit:", content.get("quantity", "[QUANTITY]")),
        ("Destination Country:", content.get("destination_country", "[DESTINATION COUNTRY]")),
        ("Port of Export:", content.get("port_of_export", "[PORT OF EXPORT e.g. Apapa, Lagos]")),
        ("Mode of Transport:", content.get("mode_of_transport", "[SEA / AIR / ROAD]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("PROCEEDS DETAILS", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Export Value (USD):", f"${content.get('value_usd', '[FOB VALUE]')}"),
        ("Currency of Invoice:", "USD"),
        ("Payment Terms:", content.get("payment_terms", "[LETTER OF CREDIT / ADVANCE PAYMENT / OPEN ACCOUNT]")),
        ("Repatriation Period:", "90 days from shipment date (CBN requirement)"),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.2 * inch))
    decl_data = [
        ["EXPORTER DECLARATION"],
        ["I/We hereby certify that the above information is correct and that the export proceeds will be repatriated to Nigeria within the time prescribed by the Central Bank of Nigeria Foreign Exchange Manual."],
        ["Authorised Signatory: __________________________    Date: _______________"],
        ["Bank Endorsement Stamp:"],
    ]
    decl_t = Table(decl_data, colWidths=[7 * inch])
    decl_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GREEN),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(decl_t)
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph("Generated by KodaTrade AI Trade Co-Pilot | Submit to your Authorised Dealer Bank with supporting export documents", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
