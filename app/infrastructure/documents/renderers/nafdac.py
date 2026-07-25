import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

HEADER_COLOR = colors.HexColor("#4A148C")
LIGHT_PURPLE = colors.HexColor("#F3E5F5")
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


def render_nafdac(content: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    today = date.today().strftime("%d %B %Y")
    ref = f"KT/NAFDAC/{date.today().strftime('%Y%m%d')}"
    elements = []

    header_data = [[
        Paragraph(
            "<b>NATIONAL AGENCY FOR FOOD AND DRUG ADMINISTRATION AND CONTROL</b><br/>APPLICATION FOR PRODUCT REGISTRATION / IMPORT PERMIT",
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

    elements.append(Paragraph("NOTE: NAFDAC registration is mandatory for food, drugs, cosmetics, medical devices, chemicals, and detergents imported into Nigeria under NAFDAC Act Cap N1 LFN 2004.", note_style))

    elements.append(Paragraph("APPLICANT / IMPORTER DETAILS", section_style))
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
    elements.append(Paragraph("PRODUCT INFORMATION", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Product Name:", content.get("product_name", "[PRODUCT NAME]")),
        ("HS Code:", content.get("hs_code", "[HS CODE]")),
        ("Product Category:", content.get("product_category", "[food / drug / cosmetic / medical device / chemical]")),
        ("Brand Name:", content.get("brand_name", "[BRAND NAME]")),
        ("Generic / Common Name:", content.get("generic_name", "[GENERIC NAME]")),
        ("Manufacturer Name:", content.get("manufacturer_name", "[MANUFACTURER NAME]")),
        ("Manufacturer Address:", content.get("manufacturer_address", "[MANUFACTURER COUNTRY AND ADDRESS]")),
        ("Composition / Ingredients:", content.get("composition", "[LIST ACTIVE INGREDIENTS / COMPOSITION]")),
        ("Pack Size / Volume:", content.get("pack_size", "[PACK SIZE e.g. 500ml, 250g]")),
        ("Storage Conditions:", content.get("storage", "[e.g. Store below 25°C, keep in dry place]")),
        ("Shelf Life:", content.get("shelf_life", "[e.g. 24 months from manufacture]")),
        ("Country of Manufacture:", content.get("country_of_origin", "[COUNTRY OF MANUFACTURE]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("REGULATORY STATUS IN COUNTRY OF MANUFACTURE", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    for label, value in [
        ("Regulatory Approval Status:", content.get("foreign_regulatory_status", "[Approved / Pending / Not applicable]")),
        ("Foreign Regulatory Authority:", content.get("foreign_regulatory_authority", "[Name of foreign regulatory body]")),
        ("Foreign Registration Number:", content.get("foreign_reg_number", "[FOREIGN REG NUMBER or N/A]")),
    ]:
        elements.append(_field_row(label, value))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("REQUIRED SUPPORTING DOCUMENTS CHECKLIST", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=HEADER_COLOR, spaceAfter=6))

    checklist = [
        ["", "Document", "Status"],
        ["[ ]", "Certificate of Analysis (from accredited lab)", "Mandatory"],
        ["[ ]", "Certificate of Manufacture / Free Sale Certificate", "Mandatory"],
        ["[ ]", "Product Label (all sides)", "Mandatory"],
        ["[ ]", "Product Specification Sheet", "Mandatory"],
        ["[ ]", "Commercial Invoice", "Mandatory"],
        ["[ ]", "CAC Certificate of Incorporation", "Mandatory"],
        ["[ ]", "NAFDAC Application Form (Form A or Form B)", "Mandatory"],
        ["[ ]", "Manufacturing Process Description", "For drugs/medical devices"],
        ["[ ]", "Pharmacopoeial Monograph (for drugs)", "For drugs only"],
        ["[ ]", "Clinical Trial Data or Literature References", "For new drugs"],
    ]
    checklist_t = Table(checklist, colWidths=[0.3 * inch, 5.2 * inch, 1.5 * inch])
    checklist_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_PURPLE),
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
        "Submit to: NAFDAC Headquarters, 77/79 Adetokunbo Ademola Crescent, Wuse 2, Abuja | Website: www.nafdac.gov.ng",
        footer_style
    ))
    elements.append(Paragraph("Generated by KodaTrade AI Trade Co-Pilot | This is a draft — verify requirements with NAFDAC before submission", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
