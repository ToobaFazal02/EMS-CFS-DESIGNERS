"""Daily PDF — Click Timesheet–style; performance graph = clicks per 30 min."""

from __future__ import annotations

from datetime import datetime
from math import cos, radians, sin
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Group, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.duration import hours_to_hm, minutes_to_hm
from app.services.timeutil import format_generated, format_pk_datetime, format_pk_time
from app.services.window_categories import summarize_categories

BLACK = colors.HexColor("#000000")
DARK = colors.HexColor("#1A1A1A")
GRAY = colors.HexColor("#555555")
LIGHT = colors.HexColor("#F5F5F5")
LINE = colors.HexColor("#CCCCCC")
BAR_BLUE = colors.HexColor("#2E86DE")  # same idea as old Timesheet click graph

# Standard PKT office window (9 AM – 5 PM)
WORK_START_HOUR = 9
WORK_END_HOUR = 17


def _floor_half_hour(hh: int, mm: int) -> tuple[int, int]:
    return hh, 0 if mm < 30 else 30


def expand_half_hour_series(
    series: list[tuple[str, float]] | None,
    report_date: str | None = None,
    work_start: int = WORK_START_HOUR,
    work_end: int = WORK_END_HOUR,
) -> list[tuple[str, float]]:
    """
    Build 30-min Click Count slots for the graph.

    - Axis always covers PKT 09:00–17:00 (9–5).
    - If this report has clicks outside that window, extend only to cover them
      (no hardcoded empty 06:00–21:00 stretch).
    - Labels use YYYY-MM-DD HH:MM when report_date is provided (Timesheet-style).
    """
    filled: dict[str, float] = {}
    for label, val in series or []:
        key = str(label).strip()
        try:
            part = key.split()[-1] if " " in key else key
            hh, mm = map(int, part.split(":")[:2])
            hh, mm = _floor_half_hour(hh, mm)
            key = f"{hh:02d}:{mm:02d}"
        except ValueError:
            continue
        filled[key] = filled.get(key, 0.0) + float(val)

    start_h, start_m = work_start, 0
    end_h, end_m = work_end, 0

    keys_with = sorted(k for k, v in filled.items() if v > 0)
    if keys_with:
        try:
            fh, fm = map(int, keys_with[0].split(":"))
            lh, lm = map(int, keys_with[-1].split(":"))
            if (fh, fm) < (start_h, start_m):
                start_h, start_m = fh, fm
            if (lh, lm) > (end_h, end_m):
                end_h, end_m = lh, lm
        except ValueError:
            pass

    out: list[tuple[str, float]] = []
    h, m = start_h, start_m
    while (h, m) <= (end_h, end_m):
        slot = f"{h:02d}:{m:02d}"
        disp = f"{report_date} {slot}" if report_date else slot
        out.append((disp, filled.get(slot, 0.0)))
        if m == 0:
            m = 30
        else:
            m = 0
            h += 1
    return out


def _rotated_label(x: float, y: float, text: str, font_size: float = 5.5) -> Group:
    """90° CCW time label under the axis (Timesheet-style)."""
    g = Group()
    g.add(String(0, 0, text, fontSize=font_size, fillColor=GRAY, textAnchor="start"))
    a = radians(90)
    g.transform = (cos(a), sin(a), -sin(a), cos(a), x, y)
    return g


def _activity_chart(
    bucket_clicks: list[tuple[str, float]],
    report_date: str | None = None,
) -> Drawing:
    """Graph Performance (per 30 min) — Click Count bars like old Timesheet PDF."""
    series = expand_half_hour_series(bucket_clicks, report_date=report_date)
    labels = [h for h, _ in series]
    values = [max(0.0, float(v)) for _, v in series]
    width = 180 * mm
    height = 105 * mm
    d = Drawing(width, height)

    d.add(
        String(
            width / 2,
            height - 10,
            "Graph Performance (per 30 min intervals)",
            textAnchor="middle",
            fontSize=11,
            fillColor=BLACK,
        )
    )

    plot_x = 18 * mm
    plot_y = 38 * mm
    plot_w = 155 * mm
    plot_h = 52 * mm

    d.add(Rect(plot_x, plot_y, plot_w, plot_h, strokeColor=BLACK, fillColor=colors.white, strokeWidth=0.8))

    vmax = max(values) if values else 0.0
    if vmax <= 0:
        y_max = 100.0
    else:
        rough = vmax * 1.15
        step = 200 if rough > 800 else (100 if rough > 400 else (50 if rough > 150 else 20))
        y_max = max(step, ((int(rough) // step) + 1) * step)

    tick_step = max(1, int(y_max) // 5)
    for t in range(0, int(y_max) + 1, tick_step):
        yy = plot_y + (t / y_max) * plot_h
        d.add(Line(plot_x, yy, plot_x + plot_w, yy, strokeColor=LINE, strokeWidth=0.4))
        d.add(String(plot_x - 3, yy - 2, str(t), textAnchor="end", fontSize=6, fillColor=GRAY))

    yg = Group()
    yg.add(String(0, 0, "Click Count", fontSize=8, fillColor=BLACK, textAnchor="middle"))
    a = radians(90)
    yg.transform = (cos(a), sin(a), -sin(a), cos(a), 7 * mm, plot_y + plot_h / 2)
    d.add(yg)

    n = max(len(values), 1)
    gap = 1.2
    bar_w = max(2.5, (plot_w - gap * (n + 1)) / n)

    if vmax <= 0:
        d.add(
            String(
                plot_x + plot_w / 2,
                plot_y + plot_h / 2,
                "No clicks recorded for this day",
                textAnchor="middle",
                fontSize=8,
                fillColor=GRAY,
            )
        )
    else:
        for i, v in enumerate(values):
            bh = (v / y_max) * (plot_h - 1)
            x = plot_x + gap + i * (bar_w + gap)
            d.add(
                Rect(
                    x,
                    plot_y + 0.5,
                    bar_w,
                    max(bh, 0.5 if v > 0 else 0),
                    strokeColor=BAR_BLUE,
                    fillColor=BAR_BLUE,
                    strokeWidth=0.2,
                )
            )

    d.add(Line(plot_x, plot_y, plot_x + plot_w, plot_y, strokeColor=BLACK, strokeWidth=0.9))

    font_sz = 4.5 if report_date else 5.5
    for i, lab in enumerate(labels):
        x = plot_x + gap + i * (bar_w + gap) + bar_w / 2
        d.add(_rotated_label(x + 2, plot_y - 4, lab, font_size=font_sz))

    return d


def _header_table(style_label, style_value, rows: list[tuple[str, str]]) -> Table:
    data = [[Paragraph(k, style_label), Paragraph(v, style_value)] for k, v in rows]
    t = Table(data, colWidths=[45 * mm, 120 * mm])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 1, BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
            ]
        )
    )
    return t


def build_daily_pdf(
    path: Path,
    employee_name: str,
    employee_code: str,
    date_str: str,
    sessions: list[dict],
    total_clicks: int,
    total_keys: int,
    idle_minutes: float,
    net_hours: float,
    break_hours: float,
    top_windows: list[tuple[str, int]],
    activity_series: list[tuple[str, float]] | None = None,
    click_log: list[tuple[str, str, int]] | None = None,
    overtime_hours_per_day: float = 8.0,
    first_activity_at=None,
    last_activity_at=None,
    overview_note: str | None = None,
) -> Path:
    """
    click_log: list of (minute_label, window_title, quantity) — Click Time Sheet rows.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # Always overwrite so managers never get a stale themed PDF
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Daily Timesheet — {employee_name} — {date_str}",
        author="CFS Designers",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleBW",
        parent=styles["Heading1"],
        textColor=BLACK,
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=2,
        fontName="Helvetica-Bold",
        leading=20,
    )
    sub = ParagraphStyle(
        "SubBW",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=DARK,
        fontSize=10,
        spaceAfter=6,
        fontName="Helvetica",
    )
    h2 = ParagraphStyle(
        "H2BW",
        parent=styles["Heading2"],
        textColor=BLACK,
        fontSize=11,
        spaceBefore=10,
        spaceAfter=5,
        fontName="Helvetica-Bold",
        borderPadding=0,
    )
    label = ParagraphStyle(
        "Lab",
        parent=styles["Normal"],
        textColor=BLACK,
        fontSize=9,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )
    value = ParagraphStyle(
        "Val",
        parent=styles["Normal"],
        textColor=BLACK,
        fontSize=9,
        fontName="Helvetica",
        alignment=TA_LEFT,
    )
    foot = ParagraphStyle(
        "Foot",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=GRAY,
        fontSize=7,
        spaceBefore=8,
    )
    cell = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        textColor=BLACK,
        fontSize=7.5,
        leading=9,
    )

    # Overview times from sessions (like old Click Timesheet cover)
    first_in = None
    last_out = None
    open_session = False
    for s in sessions:
        if s.get("sign_in") and (first_in is None or s["sign_in"] < first_in):
            first_in = s["sign_in"]
        if s.get("sign_out") and (last_out is None or s["sign_out"] > last_out):
            last_out = s["sign_out"]
        if s.get("sign_in") and not s.get("sign_out"):
            open_session = True
    # Daily Start/End follow proof-of-work (overnight Sign In must not show as yesterday's time)
    display_start = first_activity_at or first_in
    end_anchor = last_out
    if last_activity_at is not None:
        if end_anchor is None or open_session:
            end_anchor = last_activity_at
        else:
            end_anchor = min(end_anchor, last_activity_at)
    elif display_start is None and first_in is not None:
        display_start = first_in
    start_s = format_pk_datetime(display_start) if display_start else "—"
    if end_anchor:
        end_s = format_pk_datetime(end_anchor)
    elif display_start and open_session:
        end_s = "In progress"
    else:
        end_s = "—"

    overview_rows = [
        ("Employee", f"{employee_name}  (Code {employee_code})"),
        ("Date", date_str),
        ("Start Time", start_s),
        ("End Time", end_s),
        ("Hours Worked", hours_to_hm(net_hours)),
        ("Break Time", hours_to_hm(break_hours)),
        ("Idle Time", minutes_to_hm(idle_minutes)),
        ("Total Clicks", f"{total_clicks:,}"),
        ("Key Presses", f"{total_keys:,}"),
        ("Sessions", str(len(sessions))),
        (
            "Overtime",
            hours_to_hm(max(0.0, float(net_hours) - float(overtime_hours_per_day)))
            if float(net_hours) > float(overtime_hours_per_day)
            else "None (≤ "
            + hours_to_hm(overtime_hours_per_day)
            + " / day)",
        ),
    ]
    if overview_note:
        overview_rows.append(("Note", overview_note))

    story: list = [
        Paragraph("CFS Designers", title),
        Paragraph("Daily Timesheet", sub),
        HRFlowable(width="100%", thickness=1.5, color=BLACK, spaceAfter=8),
        Paragraph("Performance Overview", h2),
        _header_table(
            label,
            value,
            overview_rows,
        ),
        Paragraph("Graph Performance", h2),
        _activity_chart(activity_series or [], report_date=date_str),
        Paragraph("Sessions", h2),
    ]

    sess_rows = [["#", "Sign In", "Sign Out", "Break", "Net Work", "Status"]]
    for i, s in enumerate(sessions, 1):
        si = format_pk_time(s.get("sign_in")) if s.get("sign_in") else "—"
        if s.get("sign_out"):
            so = format_pk_time(s.get("sign_out"))
            status = "Ended"
        elif s.get("status") == "inactive":
            so = "—"
            status = "Inactive"
        elif s.get("sign_in"):
            so = "—"
            status = "In progress" if s.get("status") != "on_break" else "On break"
        else:
            so = "—"
            status = "Incomplete"
        sess_rows.append(
            [
                str(i),
                si,
                so,
                minutes_to_hm(s.get("break_minutes")),
                hours_to_hm(s.get("net_hours")),
                status,
            ]
        )
    if len(sess_rows) == 1:
        sess_rows.append(["—", "—", "—", "—", "—", "No sessions"])

    st = Table(sess_rows, colWidths=[10 * mm, 32 * mm, 32 * mm, 28 * mm, 28 * mm, 30 * mm])
    st.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLACK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 1), (-1, -1), BLACK),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("BOX", (0, 0), (-1, -1), 1, BLACK),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    story.append(st)

    cats = summarize_categories(top_windows)
    story.append(Paragraph("App Categories (Work vs Browser vs Other)", h2))
    cat_rows = [["Category", "Activity qty"]]
    for label in ("Work", "Browser", "Other"):
        cat_rows.append([label, str(cats.get(label, 0))])
    ct = Table(cat_rows, colWidths=[80 * mm, 40 * mm])
    ct.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLACK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("BOX", (0, 0), (-1, -1), 1, BLACK),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    story.append(ct)

    story.append(Paragraph("Top Windows / Apps", h2))
    win_rows: list = [[Paragraph("<b>Window title</b>", cell), Paragraph("<b>Cat</b>", cell), Paragraph("<b>Qty</b>", cell)]]
    from app.services.window_categories import classify_window

    for title_text, clicks in (top_windows or [])[:20]:
        win_rows.append(
            [
                Paragraph((title_text or "(blank)")[:80].replace("&", "&amp;"), cell),
                Paragraph(classify_window(title_text or ""), cell),
                Paragraph(str(clicks), cell),
            ]
        )
    if len(win_rows) == 1:
        win_rows.append([Paragraph("—", cell), Paragraph("—", cell), Paragraph("0", cell)])
    wt = Table(win_rows, colWidths=[120 * mm, 25 * mm, 20 * mm])
    wt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLACK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 0), (2, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, LINE),
                ("BOX", (0, 0), (-1, -1), 1, BLACK),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    story.append(wt)

    # Click Time Sheet detail (old software style)
    log = click_log or []
    if log:
        story.append(Paragraph("Click Time Sheet", h2))
        log_header = [
            Paragraph("<b>Minute</b>", cell),
            Paragraph("<b>Window Title</b>", cell),
            Paragraph("<b>Qty</b>", cell),
        ]
        chunk: list = [log_header]
        for minute, title_text, qty in log[:400]:
            chunk.append(
                [
                    Paragraph(minute.replace("&", "&amp;"), cell),
                    Paragraph((title_text or "(blank)")[:85].replace("&", "&amp;"), cell),
                    Paragraph(str(qty), cell),
                ]
            )
            if len(chunk) >= 36:
                lt = Table(chunk, colWidths=[32 * mm, 120 * mm, 18 * mm])
                lt.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), BLACK),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("ALIGN", (2, 0), (2, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("GRID", (0, 0), (-1, -1), 0.25, LINE),
                            ("BOX", (0, 0), (-1, -1), 0.8, BLACK),
                            ("TOPPADDING", (0, 0), (-1, -1), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                        ]
                    )
                )
                story.append(KeepTogether([lt]))
                story.append(Spacer(1, 4))
                chunk = [log_header]
        if len(chunk) > 1:
            lt = Table(chunk, colWidths=[32 * mm, 120 * mm, 18 * mm])
            lt.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (2, 0), (2, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.25, LINE),
                        ("BOX", (0, 0), (-1, -1), 0.8, BLACK),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ]
                )
            )
            story.append(lt)

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.6, color=BLACK, spaceAfter=4))
    story.append(
        Paragraph(
            f"Generated {format_generated()} · CFS Designers · Confidential",
            foot,
        )
    )
    doc.build(story)
    return path


def build_monthly_pdf(
    path: Path,
    year: int,
    month: int,
    rows: list[dict],
    overtime_hours_per_day: float = 8.0,
) -> Path:
    """Team monthly summary PDF — black/white, no instructional filler."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    month_label = datetime(year, month, 1).strftime("%B %Y")
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Monthly Attendance — {month_label}",
        author="CFS Designers",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "MT",
        parent=styles["Heading1"],
        textColor=BLACK,
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=2,
        fontName="Helvetica-Bold",
    )
    sub = ParagraphStyle(
        "MS",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=DARK,
        fontSize=10,
        spaceAfter=8,
    )
    foot = ParagraphStyle(
        "MF",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=GRAY,
        fontSize=7,
        spaceBefore=8,
    )

    story = [
        Paragraph("CFS Designers", title),
        Paragraph(f"Monthly Attendance — {month_label}", sub),
        Paragraph(
            f"Overtime = Net Work − (Days Present × {hours_to_hm(overtime_hours_per_day)} standard)",
            ParagraphStyle("Hint", parent=sub, fontSize=8, textColor=GRAY),
        ),
        HRFlowable(width="100%", thickness=1.5, color=BLACK, spaceAfter=10),
    ]

    table_rows = [["Code", "Employee", "Days", "Net Work", "Break", "Avg/Day", "OT"]]
    for r in rows:
        days = int(r.get("days") or 0)
        net = float(r.get("net_hours") or 0)
        brk = float(r.get("break_hours") or 0)
        avg = (net / days) if days else 0.0
        ot = max(0.0, net - (days * float(overtime_hours_per_day)))
        table_rows.append(
            [
                str(r.get("code") or ""),
                str(r.get("name") or ""),
                str(days),
                hours_to_hm(net),
                hours_to_hm(brk),
                hours_to_hm(avg),
                hours_to_hm(ot) if ot > 0 else "—",
            ]
        )
    if len(table_rows) == 1:
        table_rows.append(["—", "—", "0", hours_to_hm(0), hours_to_hm(0), hours_to_hm(0), "—"])

    t = Table(table_rows, colWidths=[16 * mm, 48 * mm, 16 * mm, 26 * mm, 22 * mm, 24 * mm, 22 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLACK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 1), (-1, -1), BLACK),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (1, 1), (1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("BOX", (0, 0), (-1, -1), 1, BLACK),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.6, color=BLACK, spaceAfter=4))
    story.append(Paragraph(f"Generated {format_generated()} · CFS Designers · Confidential", foot))
    doc.build(story)
    return path


def build_personal_monthly_pdf(
    path: Path,
    *,
    year: int,
    month: int,
    employee_code: str,
    employee_name: str,
    day_rows: list[dict],
    overtime_hours_per_day: float = 8.0,
) -> Path:
    """
    Employee self-service monthly report: summary + every calendar day.
    day_rows: {date, net_hours, present} (PKT).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    month_label = datetime(year, month, 1).strftime("%B %Y")
    present_days = [r for r in day_rows if float(r.get("net_hours") or 0) > 0.01]
    days_n = len(present_days)
    net = sum(float(r.get("net_hours") or 0) for r in present_days)
    avg = (net / days_n) if days_n else 0.0
    ot = max(0.0, net - (days_n * float(overtime_hours_per_day)))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"My Monthly Report — {month_label}",
        author="CFS Designers",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "PMT",
        parent=styles["Heading1"],
        textColor=BLACK,
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=2,
        fontName="Helvetica-Bold",
    )
    sub = ParagraphStyle(
        "PMS",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=DARK,
        fontSize=10,
        spaceAfter=6,
    )
    foot = ParagraphStyle(
        "PMF",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=GRAY,
        fontSize=7,
        spaceBefore=8,
    )
    body = ParagraphStyle(
        "PMB",
        parent=styles["Normal"],
        textColor=DARK,
        fontSize=9,
        spaceAfter=8,
    )

    who = f"{employee_name} (#{employee_code})" if employee_code else employee_name
    story = [
        Paragraph("CFS Designers", title),
        Paragraph(f"My Monthly Attendance & Performance — {month_label}", sub),
        Paragraph(who, ParagraphStyle("Who", parent=sub, fontName="Helvetica-Bold", spaceAfter=4)),
        Paragraph(
            "This report is yours only. Daily PDF (My Day) has screenshots & session detail. "
            "Team-wide Reports stay with Admin/Managers.",
            body,
        ),
        HRFlowable(width="100%", thickness=1.5, color=BLACK, spaceAfter=10),
    ]

    summary = [
        ["Days present", "Net work", "Avg / day", "Overtime"],
        [
            str(days_n),
            hours_to_hm(net),
            hours_to_hm(avg),
            hours_to_hm(ot) if ot > 0 else "—",
        ],
    ]
    st = Table(summary, colWidths=[40 * mm, 40 * mm, 40 * mm, 40 * mm])
    st.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLACK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("BOX", (0, 0), (-1, -1), 1, BLACK),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 1), (-1, 1), LIGHT),
            ]
        )
    )
    story.append(st)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Day-by-day (Asia/Karachi)", ParagraphStyle("DH", parent=body, fontName="Helvetica-Bold")))

    daily = [["Date", "Weekday", "Net work", "Status"]]
    for r in day_rows:
        d_s = str(r.get("date") or "")
        try:
            d_obj = datetime.strptime(d_s, "%Y-%m-%d")
            wd = d_obj.strftime("%a")
            nice = d_obj.strftime("%d %b %Y")
        except ValueError:
            wd, nice = "—", d_s
        h = float(r.get("net_hours") or 0)
        present = h > 0.01
        daily.append(
            [
                nice,
                wd,
                hours_to_hm(h) if present else "—",
                "Present" if present else "Off / no hours",
            ]
        )

    dt = Table(daily, colWidths=[42 * mm, 28 * mm, 36 * mm, 48 * mm])
    dt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLACK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("BOX", (0, 0), (-1, -1), 1, BLACK),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    story.append(dt)
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.6, color=BLACK, spaceAfter=4))
    story.append(Paragraph(f"Generated {format_generated()} · CFS Designers · Confidential — employee copy", foot))
    doc.build(story)
    return path
