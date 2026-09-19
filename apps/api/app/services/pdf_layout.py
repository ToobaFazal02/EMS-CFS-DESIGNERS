"""
Professional A4 report layout helpers.

Conventions adapted from IEEE / business technical reports for timesheets:
- Consistent ≥18 mm margins
- Numbered section heads with keepWithNext (no orphan titles)
- Table captions ABOVE tables
- repeatRows=1 so header repeats when a table spans pages
- CondPageBreak / PageBreak so major sections start cleanly
- Running header + page numbers in footer
"""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BLACK = colors.HexColor("#000000")
DARK = colors.HexColor("#1A1A1A")
GRAY = colors.HexColor("#555555")
LIGHT = colors.HexColor("#F2F2F2")
LINE = colors.HexColor("#CCCCCC")
RULE = colors.HexColor("#222222")

# IEEE-like comfortable print margins on A4
MARGIN_L = 18 * mm
MARGIN_R = 18 * mm
MARGIN_T = 20 * mm
MARGIN_B = 18 * mm

# Minimum free space before starting a major section on the current page
SECTION_MIN_SPACE = 95 * mm


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "ProBrand",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=BLACK,
            alignment=TA_CENTER,
            spaceAfter=1,
            leading=12,
        ),
        "doc_title": ParagraphStyle(
            "ProDocTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=BLACK,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=3,
            leading=17,
        ),
        "subtitle": ParagraphStyle(
            "ProSub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=GRAY,
            alignment=TA_CENTER,
            spaceAfter=4,
            leading=11,
        ),
        "section": ParagraphStyle(
            "ProSection",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=BLACK,
            alignment=TA_LEFT,
            spaceBefore=2,
            spaceAfter=4,
            leading=13,
            keepWithNext=1,
            borderPadding=0,
        ),
        "caption": ParagraphStyle(
            "ProCaption",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=DARK,
            alignment=TA_LEFT,
            spaceBefore=2,
            spaceAfter=3,
            leading=10,
            keepWithNext=1,
        ),
        "body": ParagraphStyle(
            "ProBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            textColor=DARK,
            alignment=TA_LEFT,
            spaceAfter=4,
            leading=11,
        ),
        "small": ParagraphStyle(
            "ProSmall",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            textColor=GRAY,
            alignment=TA_LEFT,
            spaceAfter=3,
            leading=9.5,
        ),
        "label": ParagraphStyle(
            "ProLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            textColor=BLACK,
            alignment=TA_LEFT,
            leading=10,
        ),
        "value": ParagraphStyle(
            "ProValue",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            textColor=BLACK,
            alignment=TA_LEFT,
            leading=10,
        ),
        "cell": ParagraphStyle(
            "ProCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            textColor=BLACK,
            leading=9,
        ),
        "cell_b": ParagraphStyle(
            "ProCellB",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            textColor=colors.white,
            leading=9,
        ),
        "foot": ParagraphStyle(
            "ProFoot",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7,
            textColor=GRAY,
            alignment=TA_CENTER,
            spaceBefore=6,
        ),
    }


def make_doc(path: str, *, title: str, author: str = "CFS Designers EMS") -> SimpleDocTemplate:
    return SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
        title=title,
        author=author,
    )


def make_page_drawer(*, doc_id: str, left_meta: str, confidential: bool = True):
    """Canvas callback: running header + footer with page numbers."""

    def _draw(canvas, doc) -> None:
        canvas.saveState()
        w, h = A4
        # Header rule
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.7)
        y_head = h - 12 * mm
        canvas.line(MARGIN_L, y_head, w - MARGIN_R, y_head)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRAY)
        canvas.drawString(MARGIN_L, y_head + 2 * mm, "CFS Designers · EMS")
        canvas.drawRightString(w - MARGIN_R, y_head + 2 * mm, left_meta[:72])

        # Footer
        y_foot = 10 * mm
        canvas.line(MARGIN_L, y_foot + 4 * mm, w - MARGIN_R, y_foot + 4 * mm)
        conf = "Confidential — do not redistribute · " if confidential else ""
        canvas.drawString(MARGIN_L, y_foot, f"{conf}{doc_id}")
        canvas.drawRightString(w - MARGIN_R, y_foot, f"Page {doc.page}")
        canvas.restoreState()

    return _draw


def cover_block(styles: dict, *, org: str, title: str, subtitle: str) -> list:
    return [
        Paragraph(org, styles["brand"]),
        Paragraph(title, styles["doc_title"]),
        Paragraph(subtitle, styles["subtitle"]),
        HRFlowable(width="100%", thickness=1.4, color=BLACK, spaceBefore=2, spaceAfter=10),
    ]


def section_flow(
    styles: dict,
    title: str,
    *,
    new_page: bool = False,
    min_space: float = SECTION_MIN_SPACE,
) -> list:
    """
    Start a numbered/named section.
    Prefer CondPageBreak over hard PageBreak to avoid blank pages.
    """
    out: list = []
    if new_page:
        out.append(PageBreak())
    else:
        out.append(CondPageBreak(min_space))
    out.append(Paragraph(title, styles["section"]))
    out.append(HRFlowable(width="100%", thickness=0.6, color=BLACK, spaceAfter=6))
    return out


def section_lead(
    styles: dict,
    title: str,
    *lead_flowables,
    min_space: float = 55 * mm,
) -> list:
    """Section title + lead kept together (no orphan titles / empty pages)."""
    return [
        CondPageBreak(min_space),
        KeepTogether(
            [
                Paragraph(title, styles["section"]),
                HRFlowable(width="100%", thickness=0.6, color=BLACK, spaceAfter=6),
                *lead_flowables,
            ]
        ),
    ]


def table_caption(styles: dict, text: str) -> Paragraph:
    """IEEE-style: caption above the table."""
    return Paragraph(text, styles["caption"])


def styled_table(
    data: list,
    col_widths: list,
    *,
    repeat_header: bool = True,
    font_size: float = 8,
    center_cols: tuple[int, ...] | None = None,
) -> Table:
    """Data table with black header, zebra rows, optional repeating header."""
    t = Table(
        data,
        colWidths=col_widths,
        repeatRows=1 if repeat_header and data else 0,
    )
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("TEXTCOLOR", (0, 1), (-1, -1), BLACK),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("BOX", (0, 0), (-1, -1), 0.9, BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ]
    if center_cols:
        for c in center_cols:
            style_cmds.append(("ALIGN", (c, 1), (c, -1), "CENTER"))
    t.setStyle(TableStyle(style_cmds))
    return t


def kv_table(styles: dict, rows: list[tuple[str, str]], *, col0: float = 48 * mm, col1: float = 116 * mm) -> Table:
    data = [[Paragraph(k, styles["label"]), Paragraph(v, styles["value"])] for k, v in rows]
    t = Table(data, colWidths=[col0, col1])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.9, BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
            ]
        )
    )
    return t


def keep_section(styles: dict, title: str, *flowables, new_page: bool = False) -> list:
    """Keep section title with the first block (avoids orphan headings)."""
    head = section_flow(styles, title, new_page=new_page)
    # CondPageBreak/PageBreak stay outside KeepTogether
    prefix = head[:-2] if len(head) >= 2 else []
    title_bits = head[-2:]
    body = list(flowables)
    return [*prefix, KeepTogether([*title_bits, *body[:1]]), *body[1:]]


def end_matter(styles: dict, line: str) -> list:
    return [
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=0.6, color=BLACK, spaceAfter=4),
        Paragraph(line, styles["foot"]),
    ]
