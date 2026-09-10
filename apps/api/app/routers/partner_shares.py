"""Partner shares — Faisal Khan / Asad Khan 50/50. Admin/partner only."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_partner
from app.db import get_db
from app.models import Employee
from app.schemas import PartnerShareExpenseRow, PartnerSharePaidRow, PartnerSharesOut
from app.services.partner_shares import compute_partner_shares
from app.services.timeutil import today_pk
from app.services.validation import reject_future_month

router = APIRouter(prefix="/api/v1", tags=["partner-shares"])


@router.get("/partner-shares", response_model=PartnerSharesOut)
async def partner_shares(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_partner)],
    year: int | None = Query(None, ge=2020, le=2100),
    month: int | None = Query(None, ge=1, le=12),
) -> PartnerSharesOut:
    """Paid invoices − office expenses ÷ 2 using each row's daily USD/PKR rate."""
    today = today_pk()
    y = int(year or today.year)
    if year is None and month is None:
        m: int | None = today.month
    else:
        m = month
    if m is not None:
        reject_future_month(y, m)
    raw = await compute_partner_shares(db, year=y, month=m)
    paid_rows = [PartnerSharePaidRow(**r) for r in raw.pop("paid_rows", [])]
    expense_rows = [PartnerShareExpenseRow(**r) for r in raw.pop("expense_rows", [])]
    return PartnerSharesOut(**raw, paid_rows=paid_rows, expense_rows=expense_rows)
