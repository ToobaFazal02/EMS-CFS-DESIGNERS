"""Office expenses — cash out only. Office roles (admin/manager/HR). Never client invoices."""

from __future__ import annotations

import re
import uuid
from calendar import monthrange
from datetime import date, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_office_or_demo
from app.config import get_settings
from app.db import get_db
from app.models import Employee, ExpenseCategory, OfficeExpense
from app.schemas import EXPENSE_CATEGORIES, ExpenseIn, ExpenseMonthBucket, ExpenseMonthOut, ExpenseOut
from app.services.data_scope import wants_demo_rows
from app.services.timeutil import today_pk
from app.services.validation import parse_day_or_400, reject_future_day, reject_future_month

router = APIRouter(prefix="/api/v1", tags=["expenses"])
settings = get_settings()

_CAT_SET = set(EXPENSE_CATEGORIES)
_RECEIPT_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}
_MAX_RECEIPT = 5 * 1024 * 1024


def _day_start(d: date) -> datetime:
    return datetime(d.year, d.month, d.day)


def _expense_out(row: OfficeExpense) -> ExpenseOut:
    d = row.spent_on.date() if isinstance(row.spent_on, datetime) else row.spent_on
    has_file = bool((row.receipt_path or "").strip())
    return ExpenseOut(
        id=row.id,
        spent_on=d.isoformat() if hasattr(d, "isoformat") else str(d)[:10],
        category=row.category,
        amount_pkr=round(float(row.amount_pkr or 0), 2),
        vendor_note=row.vendor_note or "",
        receipt_name=row.receipt_name or "",
        receipt_url=f"/api/v1/expenses/{row.id}/receipt" if has_file else None,
        created_by_id=row.created_by_id,
        created_at=row.created_at,
    )


def _validate_category(raw: str) -> str:
    c = (raw or "").strip().lower()
    if c not in _CAT_SET:
        raise HTTPException(status_code=400, detail=f"Invalid category. Use one of: {', '.join(EXPENSE_CATEGORIES)}")
    return c


def _safe_receipt_stem(name: str) -> str:
    base = Path(name or "receipt").name
    stem = Path(base).stem
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")[:80]
    return stem or "receipt"


async def _store_receipt(expense_id: str, upload: UploadFile) -> tuple[str, str]:
    """Save receipt under data/receipts/{id}/… Return (display_name, relative_path)."""
    ctype = (upload.content_type or "").split(";")[0].strip().lower()
    if ctype not in _RECEIPT_TYPES:
        raise HTTPException(status_code=400, detail="Receipt must be JPEG, PNG, WebP, or PDF")
    raw = await upload.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty receipt file")
    if len(raw) > _MAX_RECEIPT:
        raise HTTPException(status_code=400, detail="Receipt too large (max 5 MB)")

    ext = _RECEIPT_TYPES[ctype]
    # Prefer extension from filename when it matches allowlist
    orig = Path(upload.filename or "").name
    if orig.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".pdf")):
        ext = "." + orig.rsplit(".", 1)[-1].lower()
        if ext == ".jpeg":
            ext = ".jpg"
    display = f"{_safe_receipt_stem(orig)}{ext}"
    rel_dir = Path("receipts") / expense_id
    abs_dir = settings.data_path / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    # Unique file name to avoid collisions on replace
    stored = f"{uuid.uuid4().hex[:12]}_{display}"
    dest = abs_dir / stored
    dest.write_bytes(raw)
    rel = str(rel_dir / stored).replace("\\", "/")
    return display[:220], rel


async def _year_rollup(db: AsyncSession, year: int, *, demo: bool) -> tuple[float, int, list[ExpenseMonthBucket]]:
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31, 23, 59, 59)
    rows = list(
        (
            await db.execute(
                select(OfficeExpense).where(
                    OfficeExpense.spent_on >= start,
                    OfficeExpense.spent_on <= end,
                    OfficeExpense.is_demo == demo,
                )
            )
        )
        .scalars()
        .all()
    )
    by_m: dict[int, list[float]] = {i: [] for i in range(1, 13)}
    for r in rows:
        m = r.spent_on.month if isinstance(r.spent_on, datetime) else 0
        if 1 <= m <= 12:
            by_m[m].append(float(r.amount_pkr or 0))
    months = [
        ExpenseMonthBucket(month=m, total_pkr=round(sum(vals), 2), count=len(vals))
        for m, vals in by_m.items()
        if vals
    ]
    year_total = round(sum(float(r.amount_pkr or 0) for r in rows), 2)
    return year_total, len(rows), months


@router.get("/expenses", response_model=ExpenseMonthOut)
async def list_expenses(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    category: str | None = Query(None),
) -> ExpenseMonthOut:
    reject_future_month(year, month)
    start = datetime(year, month, 1)
    last = monthrange(year, month)[1]
    end = datetime(year, month, last, 23, 59, 59)
    demo = wants_demo_rows(user)
    q = (
        select(OfficeExpense)
        .where(
            OfficeExpense.spent_on >= start,
            OfficeExpense.spent_on <= end,
            OfficeExpense.is_demo == demo,
        )
        .order_by(OfficeExpense.spent_on.asc(), OfficeExpense.created_at.asc())
    )
    if category:
        cat = _validate_category(category)
        q = q.where(OfficeExpense.category == cat)
    rows = list((await db.execute(q)).scalars().all())
    by_cat: dict[str, float] = {c: 0.0 for c in EXPENSE_CATEGORIES}
    total = 0.0
    items: list[ExpenseOut] = []
    for r in rows:
        amt = float(r.amount_pkr or 0)
        total += amt
        key = r.category if r.category in by_cat else ExpenseCategory.other.value
        by_cat[key] = round(by_cat.get(key, 0.0) + amt, 2)
        items.append(_expense_out(r))
    year_total, year_count, months = await _year_rollup(db, year, demo=demo)
    return ExpenseMonthOut(
        year=year,
        month=month,
        total_pkr=round(total, 2),
        count=len(items),
        year_total_pkr=year_total,
        year_count=year_count,
        months=months,
        by_category=by_cat,
        items=items,
    )


@router.post("/expenses", response_model=ExpenseOut)
async def create_expense(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
    spent_on: str = Form(...),
    category: str = Form(...),
    amount_pkr: float = Form(...),
    vendor_note: str = Form(""),
    receipt: UploadFile | None = File(None),
) -> ExpenseOut:
    day = parse_day_or_400(spent_on)
    reject_future_day(day)
    if day > today_pk():
        raise HTTPException(status_code=400, detail="Future dates are not allowed")
    if amount_pkr <= 0 or amount_pkr > 50_000_000:
        raise HTTPException(status_code=400, detail="Enter a valid amount (PKR)")
    cat = _validate_category(category)
    note = (vendor_note or "").strip()[:300]
    row = OfficeExpense(
        spent_on=_day_start(day),
        category=cat,
        amount_pkr=round(float(amount_pkr), 2),
        vendor_note=note,
        receipt_name="",
        receipt_path="",
        created_by_id=user.id,
        is_demo=wants_demo_rows(user),
    )
    db.add(row)
    await db.flush()
    if receipt is not None and (receipt.filename or "").strip():
        display, rel = await _store_receipt(row.id, receipt)
        row.receipt_name = display
        row.receipt_path = rel
    await db.commit()
    await db.refresh(row)
    return _expense_out(row)


@router.post("/expenses/json", response_model=ExpenseOut)
async def create_expense_json(
    body: ExpenseIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> ExpenseOut:
    """JSON create without file (API / scripts). Prefer multipart POST /expenses for receipts."""
    day = parse_day_or_400(body.spent_on)
    reject_future_day(day)
    if day > today_pk():
        raise HTTPException(status_code=400, detail="Future dates are not allowed")
    cat = _validate_category(body.category)
    note = (body.vendor_note or "").strip()[:300]
    receipt = (body.receipt_name or "").strip()[:220]
    if ".." in receipt or "/" in receipt or "\\" in receipt:
        raise HTTPException(status_code=400, detail="Receipt name must be a plain file name")
    row = OfficeExpense(
        spent_on=_day_start(day),
        category=cat,
        amount_pkr=round(float(body.amount_pkr), 2),
        vendor_note=note,
        receipt_name=receipt,
        receipt_path="",
        created_by_id=user.id,
        is_demo=wants_demo_rows(user),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _expense_out(row)


@router.get("/expenses/{expense_id}/receipt")
async def download_receipt(
    expense_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
):
    row = await db.get(OfficeExpense, expense_id)
    if not row or bool(row.is_demo) != wants_demo_rows(user):
        raise HTTPException(status_code=404, detail="Expense not found")
    rel = (row.receipt_path or "").strip()
    if not rel:
        raise HTTPException(status_code=404, detail="No receipt on file")
    path = (settings.data_path / rel).resolve()
    root = settings.data_path.resolve()
    if not str(path).startswith(str(root)) or not path.is_file():
        raise HTTPException(status_code=404, detail="Receipt file missing")
    media = "application/pdf" if path.suffix.lower() == ".pdf" else "application/octet-stream"
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        media = "image/jpeg"
    elif path.suffix.lower() == ".png":
        media = "image/png"
    elif path.suffix.lower() == ".webp":
        media = "image/webp"
    return FileResponse(
        path,
        media_type=media,
        filename=row.receipt_name or path.name,
        headers={"Cache-Control": "private, no-store"},
    )


@router.patch("/expenses/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: str,
    body: ExpenseIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> ExpenseOut:
    row = await db.get(OfficeExpense, expense_id)
    if not row or bool(row.is_demo) != wants_demo_rows(user):
        raise HTTPException(status_code=404, detail="Expense not found")
    day = parse_day_or_400(body.spent_on)
    reject_future_day(day)
    cat = _validate_category(body.category)
    receipt = (body.receipt_name or "").strip()[:220]
    if ".." in receipt or "/" in receipt or "\\" in receipt:
        raise HTTPException(status_code=400, detail="Receipt name must be a plain file name")
    row.spent_on = _day_start(day)
    row.category = cat
    row.amount_pkr = round(float(body.amount_pkr), 2)
    row.vendor_note = (body.vendor_note or "").strip()[:300]
    if receipt and not row.receipt_path:
        row.receipt_name = receipt
    row.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(row)
    return _expense_out(row)


@router.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[Employee, Depends(require_office_or_demo)],
) -> dict:
    row = await db.get(OfficeExpense, expense_id)
    if not row or bool(row.is_demo) != wants_demo_rows(user):
        raise HTTPException(status_code=404, detail="Expense not found")
    rel = (row.receipt_path or "").strip()
    await db.delete(row)
    await db.commit()
    if rel:
        path = settings.data_path / rel
        try:
            if path.is_file():
                path.unlink()
            parent = path.parent
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            pass
    return {"ok": True}
