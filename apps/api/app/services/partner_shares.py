"""Partner profit split — Faisal Khan / Asad Khan 50/50.

Professional flow (CFS):
- Partner pool currency = USD (client invoices).
- Office expenses are entered in PKR, then converted to USD using that spend day's rate.
- net_usd = paid_invoices_usd − expenses_usd
- each partner = net_usd ÷ 2 (Faisal + Asad always sum to net)

Never expose to HR / employee / demo / manager — gate with require_partner.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Invoice, OfficeExpense
from app.services.fx_rates import pkr_to_usd, usd_pkr_rate_for
from app.services.timeutil import to_pk

PARTNER_A = "Faisal Khan"
PARTNER_B = "Asad Khan"


def _day_bounds(year: int, month: int | None) -> tuple[datetime, datetime]:
    if month is None:
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31, 23, 59, 59)
    else:
        last = monthrange(year, month)[1]
        start = datetime(year, month, 1)
        end = datetime(year, month, last, 23, 59, 59)
    return start, end


def _in_period(local: date | None, year: int, month: int | None) -> bool:
    if not local:
        return False
    if local.year != year:
        return False
    if month is not None and local.month != month:
        return False
    return True


def _split_half(net: float) -> tuple[float, float]:
    """50/50 with cent rounding so both parts always sum to net."""
    net = round(float(net or 0), 2)
    a = round(net / 2.0, 2)
    b = round(net - a, 2)
    return a, b


async def compute_partner_shares(
    db: AsyncSession,
    *,
    year: int,
    month: int | None = None,
) -> dict:
    """Paid USD invoices minus PKR expenses (→ USD at spend-day rate), then 50/50."""
    start, end = _day_bounds(year, month)

    invs = list(
        (
            await db.execute(
                select(Invoice)
                .options(selectinload(Invoice.client))
                .where(Invoice.is_demo == False)  # noqa: E712
            )
        ).scalars().all()
    )
    paid_usd = 0.0
    paid_count = 0
    paid_rows: list[dict] = []
    rates_used: list[float] = []

    for inv in invs:
        if (inv.status or "").strip().lower() != "paid":
            continue
        local = to_pk(inv.invoice_date).date() if inv.invoice_date else None
        if not _in_period(local, year, month):
            continue
        cur = (inv.currency or "USD").upper() or "USD"
        amt = round(float(inv.amount or 0), 2)
        in_pool = cur == "USD"
        if in_pool:
            paid_usd += amt
            paid_count += 1
        paid_rows.append(
            {
                "id": inv.id,
                "number": inv.number or "",
                "client_name": (inv.client.name if inv.client else "") or inv.bill_to_name or "—",
                "amount": amt,
                "amount_usd": amt if in_pool else None,
                "amount_pkr": None,
                "currency": cur,
                "invoice_date": local.isoformat() if local else None,
                "usd_pkr_rate": None,
                "rate_date": None,
                "in_pool": in_pool,
            }
        )

    exps = list(
        (
            await db.execute(
                select(OfficeExpense).where(
                    OfficeExpense.is_demo == False,  # noqa: E712
                    OfficeExpense.spent_on >= start,
                    OfficeExpense.spent_on <= end,
                )
            )
        ).scalars().all()
    )
    expenses_pkr = 0.0
    expenses_usd = 0.0
    expense_rows: list[dict] = []
    for r in exps:
        spent = r.spent_on.date() if isinstance(r.spent_on, datetime) else r.spent_on
        if hasattr(spent, "date"):
            spent = spent.date()  # type: ignore[assignment]
        day = spent if isinstance(spent, date) else None
        pkr = round(float(r.amount_pkr or 0), 2)
        usd, rate, rate_day = pkr_to_usd(pkr, day)
        expenses_pkr += pkr
        expenses_usd += usd
        rates_used.append(rate)
        expense_rows.append(
            {
                "id": r.id,
                "spent_on": day.isoformat() if day else str(spent)[:10],
                "category": r.category or "",
                "amount_pkr": pkr,
                "amount_usd": usd,
                "usd_pkr_rate": round(rate, 4),
                "rate_date": rate_day,
                "vendor_note": r.vendor_note or "",
            }
        )

    expenses_pkr = round(expenses_pkr, 2)
    expenses_usd = round(expenses_usd, 2)
    paid_usd = round(paid_usd, 2)
    net_usd = round(paid_usd - expenses_usd, 2)
    faisal, asad = _split_half(net_usd)

    if month is not None:
        last = monthrange(year, month)[1]
        summary_day = date(year, month, last)
        if summary_day > date.today():
            summary_day = date.today()
    else:
        summary_day = date.today() if year >= date.today().year else date(year, 12, 31)
    summary_rate, summary_rate_day, rate_note = usd_pkr_rate_for(summary_day)
    avg_rate = round(sum(rates_used) / len(rates_used), 4) if rates_used else summary_rate

    return {
        "year": year,
        "month": month,
        "currency": "USD",
        "display_currency": "USD",
        "usd_pkr_rate": round(avg_rate, 4),
        "rate_date": summary_rate_day,
        "rate_note": rate_note if not rates_used else "expense-day rates",
        "partner_a_name": PARTNER_A,
        "partner_b_name": PARTNER_B,
        "paid_invoices_usd": paid_usd,
        "paid_invoices_pkr": 0.0,
        "paid_invoice_count": paid_count,
        "expenses_pkr": expenses_pkr,
        "expenses_usd": expenses_usd,
        "expense_count": len(exps),
        "net_usd": net_usd,
        "net_pkr": 0.0,
        "faisal_share_usd": faisal,
        "faisal_share_pkr": 0.0,
        "asad_share_usd": asad,
        "asad_share_pkr": 0.0,
        "split_percent": 50,
        "paid_rows": paid_rows,
        "expense_rows": expense_rows,
    }


def month_label(year: int, month: int | None) -> str:
    if month is None:
        return str(year)
    return f"{year:04d}-{month:02d}"
