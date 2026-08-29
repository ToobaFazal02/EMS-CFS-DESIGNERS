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
    _autosize(ws, min_width=10, max_width=36)
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["D"].width = 26
    ws.column_dimensions["K"].width = 32
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


FILL_GREEN = PatternFill("solid", fgColor="92D050")
FILL_YELLOW = PatternFill("solid", fgColor="FFFF00")
FILL_RED = PatternFill("solid", fgColor="FF0000")
FONT_COPPER = Font(name="Georgia", size=22, color="A85914")
FONT_BROWN = Font(name="Arial", size=8, color="615A22")
FONT_BROWN_B = Font(name="Arial", bold=True, size=9, color="615A22")
FONT_CLIENT = Font(name="Georgia", size=22, color="000000")
FONT_INVOICE_TO = Font(name="Georgia", size=11, color="A85914")
FONT_BANK = Font(name="Arial", bold=True, size=12, color="615A22", underline="single")
FONT_THANKS = Font(name="Arial", bold=True, size=11, color="615A22")
FONT_INV_CELL = Font(name="Arial", size=10, color="000000")
FONT_INV_CELL_B = Font(name="Arial", bold=True, size=10, color="000000")
FONT_INV_CELL_W = Font(name="Arial", size=10, color="FFFFFF")
THIN_BLACK = Border(
    left=Side(style="thin", color="000000"),
    right=Side(style="thin", color="000000"),
    top=Side(style="thin", color="000000"),
    bottom=Side(style="thin", color="000000"),
)


def _xlsx_area(row: dict) -> str:
    raw = str(row.get("area") or "").strip()
    if raw:
        return raw
    try:
        val = float(row.get("qty") or 0)
    except (TypeError, ValueError):
        return str(row.get("qty") or "")
    if val == int(val):
        n = int(val)
        return f"{n:,}" if n >= 1000 else str(n)
    return f"{val:g}"


def _xlsx_rate(row: dict) -> str:
    raw = str(row.get("rate") or "").strip()
    if raw:
        return raw
    try:
        val = float(row.get("unit_price") or 0)
    except (TypeError, ValueError):
        return str(row.get("unit_price") or "")
    if val == int(val):
        return str(int(val))
    return f"{val:g}"


def _xlsx_unpaid(row: dict) -> bool:
    val = row.get("unpaid")
    if isinstance(val, str):
        return val.strip().lower() in {"1", "true", "yes", "unpaid"}
    return bool(val)


def build_invoice_xlsx(
    *,
    number: str,
    amount: float,
    currency: str,
    invoice_date,
    bill_to_name: str,
    bill_to_location: str,
    bill_to_phone: str,
    line_items: list[dict],
    invoice_notes: str,
    settings: dict,
) -> bytes:
    """Editable invoice workbook matching the reference PDF table."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoice"
    s = settings or {}

    ws["A1"] = "INVOICE"
    ws["A1"].font = FONT_BROWN_B
    ws.merge_cells("A2:D2")
    ws["A2"] = s.get("issuer_name") or ""
    ws["A2"].font = FONT_COPPER
    ws["A3"] = s.get("issuer_address") or ""
    ws["A3"].font = FONT_BROWN
    ws["A4"] = s.get("issuer_phone") or ""
    ws["A4"].font = FONT_BROWN
    date_s = ""
    if invoice_date:
        try:
            date_s = invoice_date.strftime("%d-%m-%Y")
        except Exception:
            date_s = str(invoice_date)[:10]
    ws["A5"] = f"DATE : {date_s}"
    ws["A5"].font = FONT_BROWN_B

    ws["A7"] = "Invoice To"
    ws["A7"].font = FONT_INVOICE_TO
    ws.merge_cells("A8:D8")
    ws["A8"] = bill_to_name or ""
    ws["A8"].font = FONT_CLIENT
    ws["A9"] = bill_to_location or ""
    ws["A9"].font = FONT_BROWN
    ws["A10"] = bill_to_phone or ""
    ws["A10"].font = FONT_BROWN

    headers = ["S/NO", "Project Name", "Scope of Work", "AREA", "$ per sq.ft", "Budget ($)", "COMMENTS"]
    ws.merge_cells("A12:G12")
    ws["A12"] = (bill_to_name or "CLIENT").upper()
    ws["A12"].font = FONT_INV_CELL_B
    ws["A12"].fill = FILL_GREEN
    ws["A12"].alignment = CENTER
    for col in range(1, 8):
        ws.cell(12, col).fill = FILL_GREEN
        ws.cell(12, col).border = THIN_BLACK

    for i, h in enumerate(headers, 1):
        cell = ws.cell(13, i, h)
        cell.font = FONT_INV_CELL_B
        cell.alignment = CENTER
        cell.border = THIN_BLACK

    items = line_items or []
    start = 14
    if not items:
        items = [{"description": "", "scope": "", "qty": 1, "unit_price": 0, "comments": "", "unpaid": False}]
    for idx, row in enumerate(items):
        r = start + idx
        qty = float(row.get("qty") or 0)
        rate = float(row.get("unit_price") or 0)
        area_s = _xlsx_area(row)
        rate_s = _xlsx_rate(row)
        numeric = False
        try:
            float(str(area_s).replace(",", ""))
            float(str(rate_s).replace("$", "").replace(",", "").strip())
            numeric = True
        except (TypeError, ValueError):
            numeric = False
        values = [
            idx + 1,
            row.get("description") or "",
            row.get("scope") or "",
            area_s,
            rate_s,
            f"=IF(COUNT(D{r},E{r})=2,D{r}*E{r},{qty * rate})" if numeric else (qty * rate),
            row.get("comments") or "",
        ]
        if not numeric:
            values[5] = round(qty * rate, 2)
        for c, val in enumerate(values, 1):
            cell = ws.cell(r, c, val)
            cell.font = FONT_INV_CELL
            cell.border = THIN_BLACK
            cell.alignment = CENTER
            if c == 3 and "detailing" in str(row.get("scope") or "").lower():
                cell.fill = FILL_YELLOW
            if c == 6 and _xlsx_unpaid(row):
                cell.fill = FILL_RED
                cell.font = FONT_INV_CELL_W
        ws.cell(r, 2).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    last = start + len(items)
    ws.merge_cells(f"A{last}:E{last}")
    ws[f"A{last}"] = "TOTAL BUDGET"
    ws[f"A{last}"].font = FONT_INV_CELL_B
    ws[f"A{last}"].fill = FILL_YELLOW
    ws[f"A{last}"].alignment = CENTER
    for c in range(1, 6):
        ws.cell(last, c).fill = FILL_YELLOW
        ws.cell(last, c).border = THIN_BLACK
    ws[f"F{last}"] = f"=SUM(F{start}:F{last - 1})"
    ws[f"F{last}"].font = FONT_INV_CELL_B
    ws[f"F{last}"].fill = FILL_YELLOW
    ws[f"F{last}"].border = THIN_BLACK
    ws[f"G{last}"].border = THIN_BLACK
    ws[f"G{last}"].fill = FILL_YELLOW

    note_row = last + 2
    ws[f"A{note_row}"] = s.get("bank_title") or "USD Account Details:"
    ws[f"A{note_row}"].font = FONT_BANK
    note_row += 1
    ws.merge_cells(f"A{note_row}:G{note_row}")
    ws[f"A{note_row}"] = s.get("bank_intro") or ""
    ws[f"A{note_row}"].font = FONT_BROWN
    ws[f"A{note_row}"].alignment = Alignment(wrap_text=True)
    ws.row_dimensions[note_row].height = 32
    note_row += 2
    bank_lines = [
        ("Name", s.get("bank_account_name"), ""),
        ("Account number", s.get("bank_account_number"), ""),
        ("Account type", s.get("bank_account_type"), "Use when sending money from the US"),
        ("Routing number (for wire and ACH)", s.get("bank_routing"), "Use when sending money from the US"),
        ("Swift/BIC", s.get("bank_swift"), "Use when sending money from outside the US"),
        ("Bank name and address", s.get("bank_name_address"), ""),
    ]
    for label, val, hint in bank_lines:
        if not val:
            continue
        ws[f"A{note_row}"] = f"{label}: {val}"
        ws[f"A{note_row}"].font = Font(name="Arial", size=10, color="615A22")
        ws.merge_cells(f"A{note_row}:G{note_row}")
        note_row += 1
        if hint:
            ws[f"A{note_row}"] = hint
            ws[f"A{note_row}"].font = Font(name="Arial", size=10, color="615A22")
            ws.merge_cells(f"A{note_row}:G{note_row}")
            note_row += 1

    note_row += 1
    ws[f"A{note_row}"] = "If you have any questions concerning this invoice, use the following contact information:"
    ws[f"A{note_row}"].font = Font(name="Arial", size=11, color="615A22")
    ws.merge_cells(f"A{note_row}:G{note_row}")
    note_row += 1
    ws[f"A{note_row}"] = s.get("contact_name") or ""
    ws[f"A{note_row}"].font = Font(name="Arial", size=11, color="615A22")
    note_row += 1
    ws[f"A{note_row}"] = s.get("contact_email") or ""
    ws[f"A{note_row}"].font = Font(name="Arial", size=11, color="615A22")
    note_row += 1
    ws[f"A{note_row}"] = s.get("footer_thanks") or "THANK YOU FOR YOUR BUSINESS!"
    ws[f"A{note_row}"].font = FONT_THANKS

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 36
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 16
    ws.column_dimensions["E"].width = 16
    ws.column_dimensions["F"].width = 14
    ws.column_dimensions["G"].width = 18
    ws.row_dimensions[2].height = 28
    ws.row_dimensions[8].height = 28
    ws.row_dimensions[12].height = 22
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
