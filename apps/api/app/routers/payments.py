from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import require_manager
from app.db import get_db
from app.models import Client, Employee, Invoice, Project
from app.schemas import InvoiceIn, InvoiceOut
from app.services.excel_report import build_payments_xlsx
from app.services.payments import INVOICE_STATUSES, delayed_days, normalize_currency

router = APIRouter(prefix="/api/v1", tags=["payments"])


def _invoice_sort_key(inv: Invoice) -> tuple:
    """Naive-safe sort key (avoids TypeError if any date is timezone-aware)."""
    name = (inv.client.name if inv.client else "").lower()
    d = inv.invoice_date
    if d is None:
        stamp = ""
    else:
        try:
            stamp = d.isoformat()
        except Exception:
            stamp = str(d)
    return (name, stamp, inv.number or "")


def _sort_invoices(rows: list[Invoice]) -> list[Invoice]:
    return sorted(rows, key=_invoice_sort_key)


def _out(inv: Invoice) -> InvoiceOut:
    client = inv.client
    proj = inv.project
    return InvoiceOut(
        id=inv.id,
        client_id=inv.client_id,
        client_name=client.name if client else "",
        location=client.location if client else "",
        project_id=inv.project_id,
        project_name=proj.name if proj else "",
        number=inv.number,
        amount=float(inv.amount or 0),
        currency=inv.currency or "USD",
        invoice_date=inv.invoice_date,
        follow_up_at=inv.follow_up_at,
        status=inv.status,
        client_comments=inv.client_comments or "",
        kind=inv.kind or "deposit",
        delayed_days=delayed_days(inv),
    )


async def _load(db: AsyncSession, invoice_id: str) -> Invoice | None:
    return (
        await db.execute(
            select(Invoice)
            .options(selectinload(Invoice.client), selectinload(Invoice.project))
            .where(Invoice.id == invoice_id)
        )
    ).scalar_one_or_none()


@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> list[InvoiceOut]:
    rows = _sort_invoices(
        (
            await db.execute(
                select(Invoice)
                .options(selectinload(Invoice.client), selectinload(Invoice.project))
            )
        )
        .scalars()
        .all()
    )
    return [_out(i) for i in rows]


@router.post("/invoices", response_model=InvoiceOut)
async def create_invoice(
    body: InvoiceIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> InvoiceOut:
    number = (body.number or "").strip()
    if not number:
        raise HTTPException(status_code=400, detail="Invoice number is required")
    if body.status not in INVOICE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid invoice status")
    try:
        currency = normalize_currency(body.currency)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid currency code (use ISO 4217, e.g. USD, AUD, PKR)")
    client = await db.get(Client, body.client_id)
    if not client:
        raise HTTPException(status_code=400, detail="Client not found")
    if body.project_id:
        proj = await db.get(Project, body.project_id)
        if not proj:
            raise HTTPException(status_code=400, detail="Project not found")
        if proj.client_id and proj.client_id != body.client_id:
            raise HTTPException(status_code=400, detail="Project does not belong to this client")
    inv = Invoice(
        client_id=body.client_id,
        project_id=body.project_id,
        number=number,
        amount=float(body.amount or 0),
        currency=currency,
        invoice_date=body.invoice_date,
        follow_up_at=body.follow_up_at,
        status=body.status,
        client_comments=body.client_comments or "",
        kind=body.kind or "deposit",
    )
    db.add(inv)
    await db.commit()
    loaded = await _load(db, inv.id)
    assert loaded
    return _out(loaded)


@router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
async def update_invoice(
    invoice_id: str,
    body: InvoiceIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> InvoiceOut:
    inv = await db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if body.status not in INVOICE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid invoice status")
    number = (body.number or "").strip()
    if not number:
        raise HTTPException(status_code=400, detail="Invoice number is required")
    client = await db.get(Client, body.client_id)
    if not client:
        raise HTTPException(status_code=400, detail="Client not found")
    if body.project_id:
        proj = await db.get(Project, body.project_id)
        if not proj:
            raise HTTPException(status_code=400, detail="Project not found")
        if proj.client_id and proj.client_id != body.client_id:
            raise HTTPException(status_code=400, detail="Project does not belong to this client")
    inv.client_id = body.client_id
    inv.project_id = body.project_id
    inv.number = number
    inv.amount = float(body.amount or 0)
    try:
        inv.currency = normalize_currency(body.currency)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid currency code (use ISO 4217, e.g. USD, AUD, PKR)")
    inv.invoice_date = body.invoice_date
    inv.follow_up_at = body.follow_up_at
    inv.status = body.status
    inv.client_comments = body.client_comments or ""
    inv.kind = body.kind or "deposit"
    await db.commit()
    loaded = await _load(db, invoice_id)
    assert loaded
    return _out(loaded)


@router.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> dict:
    inv = await db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    number = inv.number
    await db.delete(inv)
    await db.commit()
    return {"ok": True, "id": invoice_id, "number": number}


@router.get("/reports/payments.xlsx")
async def payments_xlsx(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> Response:
    rows = _sort_invoices(
        (
            await db.execute(
                select(Invoice)
                .options(selectinload(Invoice.client), selectinload(Invoice.project))
            )
        )
        .scalars()
        .all()
    )
    data = build_payments_xlsx([_out(i).model_dump() for i in rows])
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="CFS_Payments_Tracking.xlsx"',
            "Cache-Control": "no-store",
        },
    )
