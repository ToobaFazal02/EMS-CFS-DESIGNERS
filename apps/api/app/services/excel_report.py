"""Professional Excel (.xlsx) — clean black/white tables only (no charts)."""

from __future__ import annotations

from datetime import date, datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.services.duration import hours_to_hm
from app.services.timeutil import format_generated

FILL_HEADER = PatternFill("solid", fgColor="111111")
FILL_ALT = PatternFill("solid", fgColor="F5F5F5")
FILL_TITLE = PatternFill("solid", fgColor="111111")
FONT_PAID = Font(name="Calibri", bold=True, color="166534", size=11)
FONT_PENDING = Font(name="Calibri", bold=True, color="B91C1C", size=11)
FONT_SENT = Font(name="Calibri", bold=True, color="B45309", size=11)
FONT_HEADER = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
FONT_TITLE = Font(name="Calibri", bold=True, color="FFFFFF", size=16)
FONT_SUB = Font(name="Calibri", color="666666", size=10)
FONT_CELL = Font(name="Calibri", color="111111", size=11)
FONT_BOLD = Font(name="Calibri", bold=True, color="111111", size=11)
THIN = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _autosize(ws, min_width: int = 12, max_width: int = 40) -> None:
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        length = 0
        for cell in col:
            if cell.value is None:
                continue
            length = max(length, len(str(cell.value)))
        ws.column_dimensions[letter].width = min(max(length + 2, min_width), max_width)


def _title_block(ws, title: str, subtitle: str, cols: int = 8) -> None:
    end = get_column_letter(cols)
    ws.merge_cells(f"A1:{end}1")
    ws["A1"] = title
    ws["A1"].font = FONT_TITLE
    ws["A1"].fill = FILL_TITLE
    ws["A1"].alignment = CENTER
    ws.row_dimensions[1].height = 30

    ws.merge_cells(f"A2:{end}2")
    ws["A2"] = subtitle
    ws["A2"].font = FONT_SUB
    ws["A2"].alignment = CENTER
    ws.row_dimensions[2].height = 18


def build_attendance_xlsx(rows: list[dict], report_date: date) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Daily Attendance"

    date_label = report_date.strftime("%d-%b-%Y")
    _title_block(
        ws,
        "CFS Designers — Daily Attendance",
        f"{date_label}  ·  Generated {format_generated()}",
        cols=8,
    )

    headers = [
        "Code",
        "Employee",
        "Date",
        "Sessions",
        "Net Work",
        "Break Time",
        "First Sign In",
        "Last Sign Out",
    ]
    start_row = 4
    for i, h in enumerate(headers, 1):
        cell = ws.cell(start_row, i, h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = CENTER
        cell.border = THIN
    ws.row_dimensions[start_row].height = 22

    for r_i, row in enumerate(rows):
        excel_row = start_row + 1 + r_i
        net = float(row["net_hours"])
        brk = float(row["break_hours"])
        values = [
            row["code"],
            row["name"],
            date_label,
            row["sessions"],
            hours_to_hm(net),
            hours_to_hm(brk),
            row["sign_in"] or "—",
            row["sign_out"] or "—",
        ]
        for c_i, val in enumerate(values, 1):
            cell = ws.cell(excel_row, c_i, val)
            cell.font = FONT_CELL
            cell.border = THIN
            cell.alignment = CENTER
            if r_i % 2 == 1:
                cell.fill = FILL_ALT
        ws.cell(excel_row, 5).font = FONT_BOLD

    _autosize(ws)
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 14
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def build_monthly_xlsx(rows: list[dict], year: int, month: int) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Monthly Summary"

    month_label = datetime(year, month, 1).strftime("%B %Y")
    _title_block(
        ws,
        "CFS Designers — Monthly Attendance",
        f"{month_label}  ·  Generated {format_generated()}",
        cols=8,
    )

    headers = [
        "Code",
        "Employee",
        "Year",
        "Month",
        "Days Present",
        "Net Work",
        "Break Time",
        "Avg / Day",
    ]
    start_row = 4
    for i, h in enumerate(headers, 1):
        cell = ws.cell(start_row, i, h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = CENTER
        cell.border = THIN

    for r_i, row in enumerate(rows):
        excel_row = start_row + 1 + r_i
        days = int(row["days"])
        net = float(row["net_hours"])
        brk = float(row["break_hours"])
        avg = (net / days) if days else 0.0
        values = [
            row["code"],
            row["name"],
            year,
            datetime(year, month, 1).strftime("%b"),
            days,
            hours_to_hm(net),
            hours_to_hm(brk),
            hours_to_hm(avg),
        ]
        for c_i, val in enumerate(values, 1):
            cell = ws.cell(excel_row, c_i, val)
            cell.font = FONT_CELL
            cell.border = THIN
            cell.alignment = CENTER
            if r_i % 2 == 1:
                cell.fill = FILL_ALT
        ws.cell(excel_row, 6).font = FONT_BOLD

    _autosize(ws)
    ws.column_dimensions["B"].width = 22
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _payment_status_font(status: str) -> Font:
    s = (status or "").lower()
    if s == "paid":
        return FONT_PAID
    if s in ("pending", "overdue", "unpaid_info"):
        return FONT_PENDING
    if s in ("proforma", "sent", "info_sent"):
        return FONT_SENT
    return FONT_CELL


def build_payments_xlsx(rows: list[dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Payments Tracking"
    _title_block(
        ws,
        "CFS Designers Payments Tracking Sheet",
        f"CLIENT DETAILS  ·  Generated {format_generated()}",
        cols=11,
    )
    headers = [
        "S/No.",
        "CLIENT NAME",
        "LOCATION",
        "PROJECT",
        "INVOICE",
        "INVOICE VALUE",
        "INVOICE DATE",
        "FOLLOW UP DATE",
        "INVOICE DELAYED (DAYS)",
        "INVOICE STATUS",
        "Comments From Clients",
    ]
    for i, h in enumerate(headers, 1):
        cell = ws.cell(4, i, h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = CENTER
        cell.border = THIN
    for r_i, row in enumerate(rows, 1):
        excel_row = 4 + r_i
        inv_date = row.get("invoice_date")
        follow = row.get("follow_up_at")
        if isinstance(inv_date, datetime):
            inv_s = inv_date.strftime("%d-%b-%Y")
        else:
            inv_s = str(inv_date)[:10] if inv_date else ""
        if isinstance(follow, datetime):
            fol_s = follow.strftime("%d-%b-%Y")
        else:
            fol_s = str(follow)[:10] if follow else ""
        status_raw = str(row.get("status") or "")
        delayed = int(row.get("delayed_days") or 0)
        values = [
            r_i,
            row.get("client_name") or "",
            row.get("location") or "",
            row.get("project_name") or "",
            row.get("number") or "",
            f"{row.get('currency') or 'USD'} {float(row.get('amount') or 0):,.2f}",
            inv_s,
            fol_s,
            delayed,
            status_raw.replace("_", " ").upper(),
            row.get("client_comments") or "",
        ]
        status_font = _payment_status_font(status_raw)
        for c_i, val in enumerate(values, 1):
            cell = ws.cell(excel_row, c_i, val)
            cell.font = FONT_CELL
            cell.border = THIN
            cell.alignment = CENTER
            if r_i % 2 == 1:
                cell.fill = FILL_ALT
            if c_i == 9 and delayed > 0 and status_raw.lower() != "paid":
                cell.font = FONT_PENDING
            if c_i == 10:
                cell.font = status_font
    ws.freeze_panes = "A5"
    _autosize(ws, min_width=10, max_width=36)
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["D"].width = 26
    ws.column_dimensions["K"].width = 32
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
