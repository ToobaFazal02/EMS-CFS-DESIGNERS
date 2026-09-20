"""Daily PDF — Click Timesheet–style; performance graph = clicks per 30 min."""

from __future__ import annotations

from datetime import datetime, timedelta
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
    width = 164 * mm  # must fit A4 content width (≤174mm with 18mm margins)
    height = 78 * mm
    d = Drawing(width, height)

    d.add(
        String(
            width / 2,
            height - 8,
            "Graph Performance (per 30 min intervals)",
            textAnchor="middle",
            fontSize=10,
            fillColor=BLACK,
        )
    )

    plot_x = 16 * mm
    plot_y = 28 * mm
    plot_w = 140 * mm
    plot_h = 40 * mm

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
        d.add(String(plot_x - 2.5, yy - 2, str(t), textAnchor="end", fontSize=6, fillColor=GRAY))

    yg = Group()
    yg.add(String(0, 0, "Click Count", fontSize=7.5, fillColor=BLACK, textAnchor="middle"))
    a = radians(90)
    yg.transform = (cos(a), sin(a), -sin(a), cos(a), 6 * mm, plot_y + plot_h / 2)
    d.add(yg)

    n = max(len(values), 1)
    gap = 0.8
    bar_w = max(1.8, (plot_w - gap * (n + 1)) / n)

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

    # Sparse HH:MM labels only (avoid overflow / unreadable overlap)
    label_step = 1
    if n > 24:
        label_step = 4
    elif n > 16:
        label_step = 2
    for i, lab in enumerate(labels):
        if i % label_step != 0 and i != n - 1:
            continue
        short = str(lab).split()[-1] if " " in str(lab) else str(lab)
        x = plot_x + gap + i * (bar_w + gap) + bar_w / 2
        d.add(_rotated_label(x + 1, plot_y - 3, short, font_size=5.5))

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
    Professional daily timesheet PDF (IEEE/business report layout).

    click_log: list of (minute_label, window_title, quantity).
    """
    from app.services import pdf_layout as layout
    from app.services.window_categories import classify_window

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    styles = layout.make_styles()
    doc_id = f"EMS-DR-{employee_code or 'STAFF'}-{date_str.replace('-', '')}"
    left_meta = f"{employee_name} · {date_str}"

    # Overview times from sessions
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
            else "None (≤ " + hours_to_hm(overtime_hours_per_day) + " / day)",
        ),
    ]
    if overview_note:
        overview_rows.append(("Note", overview_note))

    story: list = []
    story.extend(
        layout.cover_block(
            styles,
            org="CFS DESIGNERS",
            title="Daily Timesheet",
            subtitle=f"Document ID: {doc_id} · Classification: Confidential · Timezone: Asia/Karachi (PKT)",
        )
    )

    # 1) Performance overview — keep title + table together
    story.extend(
        layout.section_lead(
            styles,
            "1. Performance overview",
            layout.table_caption(styles, "Table I. Day summary metrics"),
            layout.kv_table(styles, overview_rows),
            min_space=70 * mm,
        )
    )

    # 2) Activity graph — only break if not enough room (no forced blank page)
    story.extend(
        layout.section_lead(
            styles,
            "2. Activity graph (clicks / 30 min)",
            Paragraph(
                "Half-hour click counts during the tracked day (office window extended if activity falls outside).",
                styles["small"],
            ),
            min_space=100 * mm,
        )
    )
    story.append(_activity_chart(activity_series or [], report_date=date_str))

    # 3) Sessions
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

    st = layout.styled_table(
        sess_rows,
        [10 * mm, 32 * mm, 32 * mm, 28 * mm, 28 * mm, 34 * mm],
        repeat_header=True,
        center_cols=(0, 1, 2, 3, 4, 5),
    )
    story.extend(
        layout.section_lead(
            styles,
            "3. Sessions",
            layout.table_caption(styles, "Table II. Sign-in / sign-out sessions"),
            st if len(sess_rows) <= 14 else Spacer(1, 1),
            min_space=55 * mm,
        )
    )
    if len(sess_rows) > 14:
        story.append(st)

    # 4) Categories + top windows
    cats = summarize_categories(top_windows)
    cat_rows = [["Category", "Activity qty"]]
    for lab in ("Work", "Browser", "Other"):
        cat_rows.append([lab, str(cats.get(lab, 0))])
    ct = layout.styled_table(cat_rows, [90 * mm, 50 * mm], center_cols=(1,))

    win_rows: list = [["Window title", "Cat", "Qty"]]
    for title_text, clicks in (top_windows or [])[:20]:
        win_rows.append(
            [
                Paragraph((title_text or "(blank)")[:80].replace("&", "&amp;"), styles["cell"]),
                classify_window(title_text or ""),
                str(clicks),
            ]
        )
    if len(win_rows) == 1:
        win_rows.append(["—", "—", "0"])
    wt = layout.styled_table(win_rows, [118 * mm, 22 * mm, 20 * mm], center_cols=(1, 2))

    story.extend(
        layout.section_lead(
            styles,
            "4. Applications & windows",
            layout.table_caption(styles, "Table III. Activity by category"),
            ct,
            min_space=50 * mm,
        )
    )
    story.append(Spacer(1, 8))
    story.append(layout.table_caption(styles, "Table IV. Top windows / apps"))
    story.append(wt)

    # 5) Click time sheet — title + first rows kept together (no blank title page)
    log = click_log or []
    if log:
        log_header = [
            Paragraph("<b>Minute</b>", styles["cell_b"]),
            Paragraph("<b>Window Title</b>", styles["cell_b"]),
            Paragraph("<b>Qty</b>", styles["cell_b"]),
        ]
        data_rows = []
        for minute, title_text, qty in log[:500]:
            data_rows.append(
                [
                    Paragraph(str(minute).replace("&", "&amp;"), styles["cell"]),
                    Paragraph((title_text or "(blank)")[:85].replace("&", "&amp;"), styles["cell"]),
                    Paragraph(str(qty), styles["cell"]),
                ]
            )
        tbl_style = TableStyle(
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
        cols = [32 * mm, 118 * mm, 18 * mm]
        first_n = min(18, len(data_rows))
        first_tbl = Table([log_header] + data_rows[:first_n], colWidths=cols, repeatRows=0)
        first_tbl.setStyle(tbl_style)
        from reportlab.platypus import CondPageBreak

        story.append(CondPageBreak(48 * mm))
        story.append(
            KeepTogether(
                [
                    Paragraph("5. Click time sheet", styles["section"]),
                    HRFlowable(width="100%", thickness=0.6, color=BLACK, spaceAfter=6),
                    Paragraph(
                        "Minute-level activity log (window title and quantity). Header repeats on each page.",
                        styles["small"],
                    ),
                    layout.table_caption(styles, "Table V. Click time sheet detail"),
                    first_tbl,
                ]
            )
        )
        if len(data_rows) > first_n:
            rest = Table([log_header] + data_rows[first_n:], colWidths=cols, repeatRows=1)
            rest.setStyle(tbl_style)
            story.append(rest)

    story.extend(
        layout.end_matter(
            styles,
            f"{doc_id} · Generated {format_generated()} · CFS Designers EMS · Confidential",
        )
    )

    doc = layout.make_doc(
        str(path),
        title=f"Daily Timesheet — {employee_name} — {date_str}",
    )
    on_page = layout.make_page_drawer(doc_id=doc_id, left_meta=left_meta)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return path


def build_monthly_pdf(
    path: Path,
    year: int,
    month: int,
    rows: list[dict],
    overtime_hours_per_day: float = 8.0,
) -> Path:
    """Team monthly summary PDF — professional layout, repeating headers."""
    from app.services import pdf_layout as layout

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    month_label = datetime(year, month, 1).strftime("%B %Y")
    styles = layout.make_styles()
    doc_id = f"EMS-TM-{year}{month:02d}"

    story: list = []
    story.extend(
        layout.cover_block(
            styles,
            org="CFS DESIGNERS",
            title="Monthly Attendance — Team Summary",
            subtitle=f"{month_label} · Document ID: {doc_id} · Confidential",
        )
    )
    story.append(
        Paragraph(
            f"Overtime = Net Work − (Days Present × {hours_to_hm(overtime_hours_per_day)} standard day).",
            styles["small"],
        )
    )
    story.extend(layout.section_flow(styles, "1. Employee roll-up", min_space=50 * mm))
    story.append(layout.table_caption(styles, f"Table I. Team attendance — {month_label}"))

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

    t = layout.styled_table(
        table_rows,
        [16 * mm, 48 * mm, 14 * mm, 24 * mm, 22 * mm, 24 * mm, 20 * mm],
        repeat_header=True,
        center_cols=(0, 2, 3, 4, 5, 6),
    )
    story.append(t)
    story.extend(
        layout.end_matter(
            styles,
            f"{doc_id} · Generated {format_generated()} · CFS Designers · Confidential",
        )
    )

    doc = layout.make_doc(str(path), title=f"Monthly Attendance — {month_label}")
    on_page = layout.make_page_drawer(doc_id=doc_id, left_meta=month_label)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
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
    break_hours: float = 0.0,
    total_clicks: int = 0,
    total_keys: int = 0,
    progress_rows: list[dict] | None = None,
    role_label: str = "Staff",
) -> Path:
    """
    Professional personal monthly attendance PDF.

    Layout follows IEEE/business technical-report conventions:
    cover → numbered sections on clean page starts → captions above tables →
    repeating table headers → acknowledgement.
    """
    from app.services import pdf_layout as layout

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    month_label = datetime(year, month, 1).strftime("%B %Y")
    period_start = datetime(year, month, 1).strftime("%d %b %Y")
    if month == 12:
        last_d = datetime(year, 12, 31)
    else:
        last_d = datetime(year, month + 1, 1) - timedelta(days=1)
    period_end = last_d.strftime("%d %b %Y")

    present_days = [r for r in day_rows if float(r.get("net_hours") or 0) > 0.01]
    days_n = len(present_days)
    net = sum(float(r.get("net_hours") or 0) for r in present_days)
    avg = (net / days_n) if days_n else 0.0
    ot = max(0.0, net - (days_n * float(overtime_hours_per_day)))
    scheduled = 0
    for r in day_rows:
        try:
            d_obj = datetime.strptime(str(r.get("date") or ""), "%Y-%m-%d")
            if d_obj.weekday() < 5:
                scheduled += 1
        except ValueError:
            pass
    off_days = max(0, scheduled - days_n)
    attend_pct = round((days_n / scheduled) * 100, 1) if scheduled else 0.0
    doc_id = f"EMS-MR-{employee_code or 'STAFF'}-{year}{month:02d}"

    styles = layout.make_styles()
    story: list = []
    story.extend(
        layout.cover_block(
            styles,
            org="CFS DESIGNERS",
            title="Monthly Attendance & Performance Report",
            subtitle=(
                f"Document ID: {doc_id} · Confidential — Employee copy · "
                f"Timezone: Asia/Karachi (PKT)"
            ),
        )
    )

    # Page 1: control + identity + summary + legend (kept compact)
    story.extend(layout.section_flow(styles, "1. Document control", min_space=40 * mm))
    story.append(layout.table_caption(styles, "Table I. Document control"))
    story.append(
        layout.kv_table(
            styles,
            [
                ("Reporting period", f"{period_start} — {period_end} ({month_label})"),
                ("Generated", format_generated()),
                ("Document type", "Personal monthly timesheet / attendance roll-up"),
                ("Audience", "Named employee (self-service)"),
                ("Standard day", f"{hours_to_hm(overtime_hours_per_day)} net work"),
            ],
        )
    )

    story.extend(layout.section_flow(styles, "2. Employee identification", min_space=35 * mm))
    story.append(layout.table_caption(styles, "Table II. Employee identification"))
    ident = [
        [
            Paragraph("<b>Employee name</b>", styles["cell"]),
            Paragraph(employee_name or "—", styles["cell"]),
            Paragraph("<b>Employee code</b>", styles["cell"]),
            Paragraph(employee_code or "—", styles["cell"]),
        ],
        [
            Paragraph("<b>Role</b>", styles["cell"]),
            Paragraph(role_label or "Staff", styles["cell"]),
            Paragraph("<b>Report scope</b>", styles["cell"]),
            Paragraph("Own attendance & activity only", styles["cell"]),
        ],
    ]
    it = Table(ident, colWidths=[32 * mm, 50 * mm, 32 * mm, 50 * mm])
    it.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("BACKGROUND", (2, 0), (2, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.8, BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(it)

    story.extend(layout.section_flow(styles, "3. Period summary", min_space=50 * mm))
    story.append(
        Paragraph(
            "Snapshot of the reporting month. Hours are net working time (breaks excluded).",
            styles["small"],
        )
    )
    story.append(layout.table_caption(styles, "Table III. Period summary metrics"))
    summary = [
        ["Metric", "Value", "Metric", "Value"],
        ["Days present (P)", str(days_n), "Scheduled weekdays*", str(scheduled)],
        ["Days with no hours**", str(off_days), "Attendance %", f"{attend_pct}%" if scheduled else "—"],
        ["Net work (total)", hours_to_hm(net), "Break time (total)", hours_to_hm(break_hours)],
        ["Average net / present day", hours_to_hm(avg), "Overtime (est.)", hours_to_hm(ot) if ot > 0 else "—"],
        ["Clicks (month)", f"{int(total_clicks):,}", "Keys (month)", f"{int(total_keys):,}"],
    ]
    st = layout.styled_table(
        summary,
        [46 * mm, 36 * mm, 46 * mm, 36 * mm],
        repeat_header=True,
        center_cols=(1, 3),
    )
    # Bold first column of each pair for data rows — styled_table already bold header
    story.append(st)
    story.append(
        Paragraph(
            "* Scheduled weekdays = Mon–Fri in the calendar month. "
            "** Includes weekends and weekdays with 0.0 h tracked.",
            styles["small"],
        )
    )

    story.extend(layout.section_flow(styles, "4. Status legend", min_space=40 * mm))
    story.append(layout.table_caption(styles, "Table IV. Status legend"))
    legend = [
        ["Code", "Meaning"],
        ["P", "Present — net work hours recorded for this calendar day"],
        ["—", "No tracked hours (off day, weekend, or not signed in)"],
        ["OT", "Overtime estimate = Net work − (Days present × standard day)"],
    ]
    story.append(KeepTogether([layout.styled_table(legend, [18 * mm, 146 * mm])]))

    # 5) Daily attendance log — long table; ensure room for title + rows
    story.extend(
        layout.section_lead(
            styles,
            "5. Daily attendance log",
            Paragraph(
                "One row per calendar day. Open any day in the app (My Day) for sessions, "
                "screenshots, and the detailed daily PDF.",
                styles["small"],
            ),
            layout.table_caption(styles, "Table V. Daily attendance log"),
            min_space=90 * mm,
        )
    )
    daily = [["Date", "Weekday", "Status", "Net work", "Remark"]]
    for r in day_rows:
        d_s = str(r.get("date") or "")
        try:
            d_obj = datetime.strptime(d_s, "%Y-%m-%d")
            wd = d_obj.strftime("%a")
            nice = d_obj.strftime("%d %b %Y")
            is_weekend = d_obj.weekday() >= 5
        except ValueError:
            wd, nice, is_weekend = "—", d_s, False
        h = float(r.get("net_hours") or 0)
        present = h > 0.01
        if present:
            status, remark = "P", "Hours tracked"
        elif is_weekend:
            status, remark = "—", "Weekend"
        else:
            status, remark = "—", "No hours / not signed in"
        daily.append(
            [
                nice,
                wd,
                status,
                hours_to_hm(h) if present else "—",
                remark,
            ]
        )
    dt = layout.styled_table(
        daily,
        [34 * mm, 20 * mm, 18 * mm, 26 * mm, 66 * mm],
        repeat_header=True,
        center_cols=(1, 2, 3),
    )
    story.append(dt)

    # 6) Monthly totals
    story.extend(
        layout.section_lead(
            styles,
            "6. Monthly totals",
            layout.table_caption(styles, "Table VI. Monthly totals"),
            layout.styled_table(
                [
                    ["Present days", "Net work", "Break", "Avg / day", "OT (est.)", "Clicks", "Keys"],
                    [
                        str(days_n),
                        hours_to_hm(net),
                        hours_to_hm(break_hours),
                        hours_to_hm(avg),
                        hours_to_hm(ot) if ot > 0 else "—",
                        f"{int(total_clicks):,}",
                        f"{int(total_keys):,}",
                    ],
                ],
                [24 * mm, 26 * mm, 22 * mm, 26 * mm, 24 * mm, 22 * mm, 20 * mm],
                center_cols=(0, 1, 2, 3, 4, 5, 6),
            ),
            min_space=45 * mm,
        )
    )

    # 7) Project progress
    prog = list(progress_rows or [])
    if prog:
        prow = [["Date", "Project", "Code", "%", "Note"]]
        for p in prog[:40]:
            prow.append(
                [
                    Paragraph(str(p.get("work_date") or "—"), styles["cell"]),
                    Paragraph(str(p.get("project_name") or "—")[:60], styles["cell"]),
                    Paragraph(str(p.get("project_code") or "—"), styles["cell"]),
                    f'{float(p.get("percent") or 0):.0f}%',
                    Paragraph(str(p.get("note") or "—")[:80], styles["cell"]),
                ]
            )
        story.extend(
            layout.section_lead(
                styles,
                "7. Project progress logged this month",
                Paragraph(
                    "End-of-day % updates saved on assigned jobs during this period.",
                    styles["small"],
                ),
                layout.table_caption(styles, "Table VII. Project progress"),
                min_space=55 * mm,
            )
        )
        story.append(
            layout.styled_table(
                prow,
                [24 * mm, 56 * mm, 22 * mm, 16 * mm, 46 * mm],
                repeat_header=True,
                center_cols=(3,),
            )
        )
    else:
        story.extend(
            layout.section_lead(
                styles,
                "7. Project progress logged this month",
                Paragraph(
                    "No end-of-day project % rows were logged in this month. "
                    "Use My dashboard → Log today’s project progress to record completion.",
                    styles["body"],
                ),
                min_space=40 * mm,
            )
        )

    # 8) How to read
    story.extend(
        layout.section_lead(
            styles,
            "8. How to read this report",
            Paragraph(
                "• <b>Daily report (My Day):</b> sessions, idle, clicks/keys, screenshots, and day PDF.<br/>"
                "• <b>This monthly report:</b> roll-up of attendance and activity for the full calendar month.<br/>"
                "• Hours come from Sign In / Break / Sign Out and activity on the Employee Agent.",
                styles["body"],
            ),
            min_space=40 * mm,
        )
    )

    # 9) Acknowledgement
    ack = [
        ["Employee acknowledgement", "Office / manager review"],
        ["Name: ________________________", "Name: ________________________"],
        ["Date: ________________________", "Date: ________________________"],
        ["Signature: ___________________", "Signature: ___________________"],
    ]
    at = Table(ack, colWidths=[82 * mm, 82 * mm])
    at.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.8, BLACK),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend(
        layout.section_lead(
            styles,
            "9. Acknowledgement",
            Paragraph(
                "This copy is generated for the named employee from live EMS records. "
                "It does not replace payroll statements. Questions about hours or progress: contact your manager.",
                styles["body"],
            ),
            layout.table_caption(styles, "Table VIII. Acknowledgement"),
            at,
            min_space=70 * mm,
        )
    )
    story.extend(
        layout.end_matter(
            styles,
            f"{doc_id} · Generated {format_generated()} · CFS Designers EMS · Confidential — do not redistribute",
        )
    )

    doc = layout.make_doc(
        str(path),
        title=f"Monthly Attendance Report — {employee_name} — {month_label}",
    )
    on_page = layout.make_page_drawer(
        doc_id=doc_id,
        left_meta=f"{employee_name} · {month_label}",
    )
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return path

