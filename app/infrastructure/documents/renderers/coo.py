import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

HEADER_COLOR = colors.HexColor("#8B0000")
LIGHT_RED = colors.HexColor("#FFF0F0")
BORDER_COLOR = colors.HexColor("#CCCCCC")
GOLD_COLOR = colors.HexColor("#DAA520")


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


def render_coo(content: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    today = date.today().strftime("%d %B %Y")
    cert_number = f"NG/COO/{date.today().strftime('%Y')}/{date.today().strftime('%m%d%H%M')}"
    elements = []

    header_data = [[
        Paragraph(
            "<b>CERTIFICATE OF ORIGIN</b><br/>African Continental Free Trade Area (AfCFTA)<br/>Nigerian Export Promotion Council (NEPC)",
            ParagraphStyle("h", fontSize=12, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER),
        ),
        Paragraph(
            f"<b>Certificate No:</b><br/>{cert_number}<br/><b>Date Issued:</b> {today}",
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

    afcfta_banner = Table(
        [["This certificate is issued under the African Continental Free Trade Agreement (AfCFTA) Protocol on Trade in Goods and the AfCFTA Rules of Origin Annex."]],
        colWidths=[7 * inch]
    )
    afcfta_banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD_COLOR),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(afcfta_banner)
    elements.append(Spacer(1, 0.15 * inch))

    section_style = ParagraphStyle("sec", fontSize=10, textColor=HEADER_COLOR, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=8)
    footer_style = ParagraphStyle("ft", fontSize=7, textColor=colors.gray, alignment=TA_CENTER)

    elements.append(Paragraph("EXPORTER / PRODUCER", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Exporter / Producer Name:", content.get("business_name", "[EXPORTER NAME]")),
        ("CAC Registration No.:", content.get("cac_number", "[CAC NUMBER]")),
        ("Address:", content.get("business_address", "[EXPORTER ADDRESS]")),
        ("Country of Export:", "Nigeria"),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("CONSIGNEE (IMPORTER)", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Consignee Name:", content.get("consignee_name", "[CONSIGNEE NAME]")),
        ("Consignee Address:", content.get("consignee_address", "[CONSIGNEE ADDRESS]")),
        ("Country of Destination:", content.get("destination_country", "[DESTINATION COUNTRY]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("GOODS DESCRIPTION", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    goods_data = [
        ["Description of Goods", "HS Code", "Quantity", "Value (USD)", "Net Weight"],
        [
            content.get("product_name", "[PRODUCT]"),
            content.get("hs_code", "[HS CODE]"),
            content.get("quantity", "[QTY]"),
            f"${content.get('value_usd', '[VALUE]')}",
            content.get("net_weight", "[NET WEIGHT kg]"),
        ],
    ]
    goods_t = Table(goods_data, colWidths=[2.2 * inch, 1.0 * inch, 1.0 * inch, 1.2 * inch, 1.6 * inch])
    goods_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_RED),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(goods_t)

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("RULES OF ORIGIN DECLARATION", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    roo_type = content.get("roo_type", "substantial transformation")
    elements.append(_field_row("Rules of Origin Criterion:", f"{roo_type.title()} (AfCFTA Annex 2)"))
    elements.append(_field_row("Production / Transformation:", content.get("production_description", "[DESCRIBE HOW GOODS MEET RULES OF ORIGIN]")))

    elements.append(Spacer(1, 0.2 * inch))
    cert_data = [
        ["CERTIFICATION — ISSUING AUTHORITY (NEPC)", "EXPORTER DECLARATION"],
        [
            "The undersigned authority hereby certifies that the goods described above originate in Nigeria and meet the AfCFTA Rules of Origin requirements.\n\nIssuing Authority: Nigerian Export Promotion Council (NEPC)\nAddress: NEPC Headquarters, Olusegun Obasanjo Way, Wuse II, Abuja\n\nAuthorised Officer: __________________________\n\nOfficial Stamp:",
            "I, the undersigned, declare that the above details and statements are correct; that all goods were produced in Nigeria and comply with the origin requirements specified for AfCFTA export.\n\nSignature: __________________________\nName: [SIGNATORY]\nDesignation: [TITLE]\nDate: _______________",
        ],
    ]
    cert_t = Table(cert_data, colWidths=[3.5 * inch, 3.5 * inch])
    cert_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_RED),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 30),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(cert_t)
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(f"Certificate No: {cert_number} | Generated by KodaTrade AI Trade Co-Pilot | NEPC certified issuers only", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
