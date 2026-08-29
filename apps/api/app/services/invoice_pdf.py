"""CFS invoice PDF — pixel-matched to the client reference (Letter, Georgia + Arial)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Reference PDF measured colors (PDFium spans + table image).
COPPER = colors.HexColor("#A85914")
BROWN = colors.HexColor("#615A22")
BLACK = colors.HexColor("#000000")
GREEN = colors.HexColor("#92D050")  # Excel lime used in the reference table
YELLOW = colors.HexColor("#FFFF00")
RED = colors.HexColor("#FF0000")
WHITE = colors.white
GREEN_LIGHT = colors.Color(0.57, 0.82, 0.31, alpha=0.2)

FONT_GEORGIA = "Times-Roman"
FONT_GEORGIA_B = "Times-Bold"
FONT_ARIAL = "Helvetica"
FONT_ARIAL_B = "Helvetica-Bold"
_FONTS_READY = False


def _hex_color(hex_str: str, fallback: str = "#92D050") -> colors.Color:
    try:
        return colors.HexColor(str(hex_str or fallback).strip())
    except (ValueError, AttributeError):
        return colors.HexColor(fallback)


def _e(text: str) -> str:
    return escape(str(text or "").strip())


def _register_fonts() -> None:
    global FONT_GEORGIA, FONT_GEORGIA_B, FONT_ARIAL, FONT_ARIAL_B, _FONTS_READY
    if _FONTS_READY:
        return
    roots = [
        Path(r"C:\Windows\Fonts"),
        Path("/usr/share/fonts/truetype/msttcorefonts"),
        Path("/usr/share/fonts/truetype/msttcorefonts".replace("msttcorefonts", "liberation")),
        Path("/usr/share/fonts/truetype/liberation"),
        Path("/usr/share/fonts/truetype/liberation2"),
        Path(__file__).resolve().parent / "fonts",
    ]
    georgia = georgiab = arial = arialbd = None
    for root in roots:
        if not root.is_dir():
            continue
        files = {p.name.lower(): p for p in root.glob("*.ttf")}
        georgia = georgia or files.get("georgia.ttf") or files.get("liberationserif-regular.ttf")
        georgiab = georgiab or files.get("georgiab.ttf") or files.get("liberationserif-bold.ttf")
        arial = arial or files.get("arial.ttf") or files.get("arialmt.ttf") or files.get("liberationsans-regular.ttf")
        arialbd = arialbd or files.get("arialbd.ttf") or files.get("arial-boldmt.ttf") or files.get("liberationsans-bold.ttf")
    try:
        if georgia and georgiab and arial and arialbd:
            pdfmetrics.registerFont(TTFont("CFSGeorgia", str(georgia)))
            pdfmetrics.registerFont(TTFont("CFSGeorgia-Bold", str(georgiab)))
            pdfmetrics.registerFont(TTFont("CFSArial", str(arial)))
            pdfmetrics.registerFont(TTFont("CFSArial-Bold", str(arialbd)))
            FONT_GEORGIA = "CFSGeorgia"
            FONT_GEORGIA_B = "CFSGeorgia-Bold"
            FONT_ARIAL = "CFSArial"
            FONT_ARIAL_B = "CFSArial-Bold"
    except Exception:
        pass
    _FONTS_READY = True


def _fmt_date(d: datetime | None) -> str:
    if not d:
        return "—"
    return d.strftime("%d-%m-%Y")


def _fmt_plain(value: float) -> str:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return str(value)
    if val == int(val):
        return str(int(val))
    return f"{val:g}"


def _fmt_area_num(qty: float) -> str:
    try:
        val = float(qty)
    except (TypeError, ValueError):
        return str(qty)
    if val == int(val):
        n = int(val)
        return f"{n:,}" if n >= 1000 else str(n)
    return f"{val:,.2f}"


def _fmt_budget(amount: float) -> str:
    try:
        val = float(amount)
    except (TypeError, ValueError):
        return str(amount)
    if val == int(val):
        return str(int(val))
    return f"{val:,.2f}"


def _display_area(row: dict) -> str:
    raw = str(row.get("area") or "").strip()
    if raw:
        return raw
    return _fmt_area_num(float(row.get("qty") or 0))


def _display_rate(row: dict) -> str:
    raw = str(row.get("rate") or "").strip()
    if raw:
        return raw
    return _fmt_plain(float(row.get("unit_price") or 0))


def _line_amount(row: dict) -> float:
    if row.get("amount") is not None and str(row.get("amount")).strip() != "":
        try:
            return round(float(row["amount"]), 2)
        except (TypeError, ValueError):
            pass
    try:
        return round(float(row.get("qty") or 0) * float(row.get("unit_price") or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _is_detailing(scope: str) -> bool:
    return "detailing" in (scope or "").strip().lower()


def _is_unpaid(row: dict) -> bool:
    val = row.get("unpaid")
    if isinstance(val, str):
        return val.strip().lower() in {"1", "true", "yes", "unpaid"}
    return bool(val)


def _banner_green(settings: dict) -> colors.Color:
    raw = str((settings or {}).get("header_color") or "#92D050").strip()
    if raw.lower() == "#548235":
        raw = "#92D050"
    return _hex_color(raw, "#92D050")


def build_invoice_pdf(
    out_path: Path,
    *,
    number: str,
    amount: float,
    currency: str,
    invoice_date: datetime | None,
    bill_to_name: str,
    bill_to_location: str,
    bill_to_phone: str,
    line_items: list[dict],
    invoice_notes: str,
    settings: dict,
) -> Path:
    _register_fonts()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Reference is US Letter 612×792, not A4.
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=50,
        rightMargin=53,
        topMargin=18,
        bottomMargin=22,
        title=number or "Invoice",
    )
    styles = getSampleStyleSheet()
    s = settings or {}
    header_color = _banner_green(s)

    inv_label = ParagraphStyle(
        "inv_label",
        parent=styles["Normal"],
        fontName=FONT_ARIAL_B,
        fontSize=8.8,
        textColor=BROWN,
        leading=12,
        spaceAfter=2,
    )
    issuer_name = ParagraphStyle(
        "issuer_name",
        parent=styles["Normal"],
        fontName=FONT_GEORGIA,
        fontSize=21.1,
        textColor=COPPER,
        leading=24,
        spaceAfter=6,
    )
    meta = ParagraphStyle(
        "meta",
        parent=styles["Normal"],
        fontName=FONT_ARIAL,
        fontSize=8,
        textColor=BROWN,
        leading=11,
    )
    date_style = ParagraphStyle(
        "inv_date",
        parent=styles["Normal"],
        fontName=FONT_ARIAL_B,
        fontSize=8.8,
        textColor=BROWN,
        leading=12,
        spaceBefore=1,
        spaceAfter=8,
    )
    invoice_to = ParagraphStyle(
        "invoice_to",
        parent=styles["Normal"],
        fontName=FONT_GEORGIA,
        fontSize=10.9,
        textColor=COPPER,
        leading=14,
        spaceAfter=2,
    )
    client_name = ParagraphStyle(
        "client_name",
        parent=styles["Normal"],
        fontName=FONT_GEORGIA,
        fontSize=21.1,
        textColor=BLACK,
        leading=24,
        spaceAfter=2,
    )
    client_banner = ParagraphStyle(
        "client_banner",
        parent=styles["Normal"],
        fontName=FONT_ARIAL_B,
        fontSize=11,
        textColor=BLACK,
        alignment=TA_CENTER,
        leading=14,
    )
    th = ParagraphStyle(
        "th",
        parent=styles["Normal"],
        fontName=FONT_ARIAL_B,
        fontSize=8,
        textColor=BLACK,
        alignment=TA_CENTER,
        leading=10,
    )
    td = ParagraphStyle(
        "td",
        parent=styles["Normal"],
        fontName=FONT_ARIAL,
        fontSize=8,
        textColor=BLACK,
        leading=10,
        alignment=TA_CENTER,
    )
    td_l = ParagraphStyle("td_l", parent=td, alignment=TA_LEFT)
    td_w = ParagraphStyle("td_w", parent=td, textColor=WHITE)
    tot = ParagraphStyle(
        "tot",
        parent=styles["Normal"],
        fontName=FONT_ARIAL_B,
        fontSize=9,
        textColor=BLACK,
        alignment=TA_CENTER,
        leading=12,
    )
    bank_h = ParagraphStyle(
        "bank_h",
        parent=styles["Normal"],
        fontName=FONT_ARIAL_B,
        fontSize=12,
        textColor=BROWN,
        leading=16,
        spaceAfter=6,
    )
    bank_p = ParagraphStyle(
        "bank_p",
        parent=styles["Normal"],
        fontName=FONT_ARIAL,
        fontSize=9.8,
        textColor=BROWN,
        leading=12.5,
        spaceAfter=6,
    )
    bank_line = ParagraphStyle(
        "bank_line",
        parent=styles["Normal"],
        fontName=FONT_ARIAL,
        fontSize=9.8,
        textColor=BROWN,
        leading=12,
    )
    contact = ParagraphStyle(
        "contact",
        parent=styles["Normal"],
        fontName=FONT_ARIAL,
        fontSize=11,
        textColor=BROWN,
        leading=14,
        spaceAfter=2,
    )
    thanks = ParagraphStyle(
        "thanks",
        parent=styles["Normal"],
        fontName=FONT_ARIAL_B,
        fontSize=11,
        textColor=BROWN,
        leading=14,
        spaceBefore=4,
    )

    issuer = _e(s.get("issuer_name", ""))
    issuer_addr = _e(s.get("issuer_address", ""))
    issuer_phone = _e(s.get("issuer_phone", ""))
    bank_title = _e(s.get("bank_title", "USD Account Details:"))
    bank_intro = _e(s.get("bank_intro", ""))
    contact_name = _e(s.get("contact_name", ""))
    contact_email = _e(s.get("contact_email", ""))
    footer_thanks = _e(s.get("footer_thanks", "THANK YOU FOR YOUR BUSINESS!"))

    story: list = []
    story.append(Paragraph("INVOICE", inv_label))
    story.append(Paragraph(issuer or "—", issuer_name))
    if issuer_addr:
        story.append(Paragraph(issuer_addr, meta))
    if issuer_phone:
        story.append(Paragraph(issuer_phone, meta))
    story.append(Paragraph(f"DATE : {_fmt_date(invoice_date)}", date_style))

    story.append(Paragraph("Invoice To", invoice_to))
    story.append(Paragraph(_e(bill_to_name) or "—", client_name))
    if bill_to_location:
        story.append(Paragraph(_e(bill_to_location), meta))
    if bill_to_phone:
        story.append(Paragraph(_e(bill_to_phone), meta))
    story.append(Spacer(1, 8))

    # Column widths from the embedded table image (778px → 509pt).
    col_w = [38, 124, 74, 62, 66, 72, 73]
    client_label = (_e(bill_to_name) or "CLIENT").upper()

    rows_data: list[list] = [
        [Paragraph(client_label, client_banner), "", "", "", "", "", ""],
        [
            Paragraph("S/NO", th),
            Paragraph("Project Name", th),
            Paragraph("Scope of Work", th),
            Paragraph("AREA", th),
            Paragraph("$ per sq.ft", th),
            Paragraph("Budget ($)", th),
            Paragraph("COMMENTS", th),
        ],
    ]
    subtotal = 0.0
    items = line_items or []
    unpaid_rows: list[int] = []
    yellow_rows: list[int] = []
    for i, row in enumerate(items, 1):
        desc = _e(row.get("description", ""))
        scope = str(row.get("scope", "") or "")
        comments = _e(row.get("comments", ""))
        line_amt = _line_amount(row)
        subtotal += line_amt
        ridx = len(rows_data)
        unpaid = _is_unpaid(row)
        if _is_detailing(scope):
            yellow_rows.append(ridx)
        if unpaid:
            unpaid_rows.append(ridx)
        rows_data.append(
            [
                Paragraph(str(i), td),
                Paragraph(desc, td_l),
                Paragraph(_e(scope), td),
                Paragraph(_e(_display_area(row)), td),
                Paragraph(_e(_display_rate(row)), td),
                Paragraph(_fmt_budget(line_amt), td_w if unpaid else td),
                Paragraph(comments, td),
            ]
        )
    if not items:
        rows_data.append(
            [
                Paragraph("1", td),
                Paragraph("—", td_l),
                Paragraph("", td),
                Paragraph("", td),
                Paragraph("", td),
                Paragraph("0", td),
                Paragraph("", td),
            ]
        )

    total_amt = round(float(amount or subtotal), 2)
    last = len(rows_data)
    rows_data.append(
        [
            Paragraph("TOTAL BUDGET", tot),
            "",
            "",
            "",
            "",
            Paragraph(_fmt_budget(total_amt), tot),
            Paragraph("", td),
        ]
    )

    items_tbl = Table(rows_data, colWidths=col_w, repeatRows=2)
    tbl_style = [
        ("SPAN", (0, 0), (-1, 0)),
        ("SPAN", (0, last), (4, last)),
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("BACKGROUND", (0, last), (-1, last), YELLOW),
        ("GRID", (0, 1), (-1, -1), 0.5, BLACK),
        ("BOX", (0, 0), (-1, -1), 0.5, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (0, 0), 6),
        ("BOTTOMPADDING", (0, 0), (0, 0), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
    ]
    for ridx in yellow_rows:
        tbl_style.append(("BACKGROUND", (2, ridx), (2, ridx), YELLOW))
    for ridx in unpaid_rows:
        tbl_style.append(("BACKGROUND", (5, ridx), (5, ridx), RED))
        tbl_style.append(("TEXTCOLOR", (5, ridx), (5, ridx), WHITE))
    items_tbl.setStyle(TableStyle(tbl_style))
    story.append(items_tbl)

    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<u>{bank_title}</u>", bank_h))
    if bank_intro:
        story.append(Paragraph(bank_intro, bank_p))

    bank_fields = [
        ("Name", s.get("bank_account_name", ""), ""),
        ("Account number", s.get("bank_account_number", ""), ""),
        ("Account type", s.get("bank_account_type", ""), "Use when sending money from the US"),
        ("Routing number (for wire and ACH)", s.get("bank_routing", ""), "Use when sending money from the US"),
        ("Swift/BIC", s.get("bank_swift", ""), "Use when sending money from outside the US"),
        ("Bank name and address", s.get("bank_name_address", ""), ""),
    ]
    for label, value, hint in bank_fields:
        val = _e(value)
        if not val:
            continue
        story.append(Paragraph(f"{_e(label)}: {val}", bank_line))
        if hint:
            story.append(Paragraph(_e(hint), bank_line))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "If you have any questions concerning this invoice, use the following contact information:",
            contact,
        )
    )
    if contact_name:
        story.append(Paragraph(contact_name, contact))
    if contact_email:
        story.append(Paragraph(contact_email, contact))
    story.append(Paragraph(footer_thanks, thanks))

    doc.build(story)
    return out_path
