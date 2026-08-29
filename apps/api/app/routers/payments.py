from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import require_manager
from app.config import get_settings
from app.db import get_db
from app.models import Client, Employee, Invoice, Project
from app.schemas import InvoiceIn, InvoiceOut, InvoiceSettingsIn, InvoiceSettingsOut
from app.services.excel_report import build_invoice_xlsx, build_payments_xlsx
from app.services.invoice_items import (
    line_items_for_pdf,
    line_items_total,
    parse_line_items,
    serialize_line_items,
    validate_line_items,
)
from app.services.invoice_pdf import build_invoice_pdf
from app.services.invoice_settings import get_or_create_invoice_settings, settings_to_dict
from app.services.payments import INVOICE_STATUSES, delayed_days, normalize_currency

router = APIRouter(prefix="/api/v1", tags=["payments"])
settings = get_settings()


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


def _line_items_out(inv: Invoice) -> list[dict]:
    return [i.model_dump() for i in parse_line_items(inv.line_items)]


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
        bill_to_name=inv.bill_to_name or "",
        bill_to_location=inv.bill_to_location or "",
        bill_to_phone=inv.bill_to_phone or "",
        line_items=_line_items_out(inv),
        invoice_notes=inv.invoice_notes or "",
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


def _resolve_bill_to(body: InvoiceIn, client: Client) -> tuple[str, str, str]:
    name = (body.bill_to_name or client.name or "").strip()[:120]
    location = (body.bill_to_location or client.location or "").strip()[:200]
    phone = (body.bill_to_phone or getattr(client, "phone", "") or "").strip()[:40]
    return name, location, phone


def _resolve_amount(body: InvoiceIn) -> tuple[float, list]:
    try:
        items = validate_line_items(body.line_items or [])
    except (ValueError, ValidationError, TypeError, AttributeError) as exc:
        raise HTTPException(status_code=400, detail=f"Line items validation failed: {exc}") from exc
    
    if not items:
        amount = float(body.amount or 0)
        if amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invoice must have either line items with descriptions or a positive amount"
            )
        return amount, items
    
    # Validate each line item individually
    for idx, item in enumerate(items, 1):
        if not item.description.strip():
            raise HTTPException(status_code=400, detail=f"Line {idx}: Description cannot be empty")
        if item.qty <= 0:
            raise HTTPException(status_code=400, detail=f"Line {idx}: Quantity must be greater than 0")
        if item.unit_price < 0:
            raise HTTPException(status_code=400, detail=f"Line {idx}: Unit price cannot be negative")
    
    total = line_items_total(items)
    if total < 0:
        raise HTTPException(status_code=400, detail="Invoice total cannot be negative")
    
    return total, items


def _apply_invoice_fields(inv: Invoice, body: InvoiceIn, client: Client) -> None:
    amount, items = _resolve_amount(body)
    bill_name, bill_loc, bill_phone = _resolve_bill_to(body, client)
    inv.amount = amount
    inv.bill_to_name = bill_name
    inv.bill_to_location = bill_loc
    inv.bill_to_phone = bill_phone
    inv.line_items = serialize_line_items(items)
    inv.invoice_notes = (body.invoice_notes or "").strip()[:4000]
    inv.client_comments = (body.client_comments or "").strip()[:4000]


async def _validate_invoice_refs(db: AsyncSession, body: InvoiceIn) -> Client:
    client = await db.get(Client, body.client_id)
    if not client:
        raise HTTPException(status_code=400, detail="Client not found")
    if body.project_id:
        proj = await db.get(Project, body.project_id)
        if not proj:
            raise HTTPException(status_code=400, detail="Project not found")
        if proj.client_id and proj.client_id != body.client_id:
            raise HTTPException(status_code=400, detail="Project does not belong to this client")
    return client


@router.get("/invoice-settings", response_model=InvoiceSettingsOut)
async def get_invoice_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> InvoiceSettingsOut:
    row = await get_or_create_invoice_settings(db)
    return InvoiceSettingsOut(
        issuer_name=row.issuer_name or "",
        issuer_address=row.issuer_address or "",
        issuer_phone=row.issuer_phone or "",
        issuer_email=row.issuer_email or "",
        bank_title=row.bank_title or "USD Account Details:",
        bank_intro=row.bank_intro or "",
        bank_account_name=row.bank_account_name or "",
        bank_account_number=row.bank_account_number or "",
        bank_account_type=row.bank_account_type or "",
        bank_routing=row.bank_routing or "",
        bank_swift=row.bank_swift or "",
        bank_name_address=row.bank_name_address or "",
        contact_name=row.contact_name or "",
        contact_email=row.contact_email or "",
        footer_thanks=row.footer_thanks or "THANK YOU FOR YOUR BUSINESS!",
        header_color=row.header_color or "#548235",
        highlight_color=row.highlight_color or "#c9a227",
        updated_at=row.updated_at,
    )


@router.patch("/invoice-settings", response_model=InvoiceSettingsOut)
async def update_invoice_settings(
    body: InvoiceSettingsIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> InvoiceSettingsOut:
    row = await get_or_create_invoice_settings(db)
    for field in InvoiceSettingsIn.model_fields:
        setattr(row, field, getattr(body, field) or "")
    await db.commit()
    await db.refresh(row)
    return InvoiceSettingsOut(
        issuer_name=row.issuer_name or "",
        issuer_address=row.issuer_address or "",
        issuer_phone=row.issuer_phone or "",
        issuer_email=row.issuer_email or "",
        bank_title=row.bank_title or "USD Account Details:",
        bank_intro=row.bank_intro or "",
        bank_account_name=row.bank_account_name or "",
        bank_account_number=row.bank_account_number or "",
        bank_account_type=row.bank_account_type or "",
        bank_routing=row.bank_routing or "",
        bank_swift=row.bank_swift or "",
        bank_name_address=row.bank_name_address or "",
        contact_name=row.contact_name or "",
        contact_email=row.contact_email or "",
        footer_thanks=row.footer_thanks or "THANK YOU FOR YOUR BUSINESS!",
        header_color=row.header_color or "#548235",
        highlight_color=row.highlight_color or "#c9a227",
        updated_at=row.updated_at,
    )


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
    if len(number) > 80:
        raise HTTPException(status_code=400, detail="Invoice number too long (max 80 characters)")
    
    if body.status not in INVOICE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(INVOICE_STATUSES)}"
        )
    
    try:
        currency = normalize_currency(body.currency)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid currency: {exc}") from exc
    
    client = await _validate_invoice_refs(db, body)
    
    try:
        inv = Invoice(
            client_id=body.client_id,
            project_id=body.project_id,
            number=number,
            currency=currency,
            invoice_date=body.invoice_date,
            follow_up_at=body.follow_up_at,
            status=body.status,
            kind=body.kind or "deposit",
        )
        _apply_invoice_fields(inv, body, client)
        db.add(inv)
        await db.commit()
        loaded = await _load(db, inv.id)
        assert loaded
        return _out(loaded)
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(exc)}") from exc


@router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
async def update_invoice(
    invoice_id: str,
    body: InvoiceIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> InvoiceOut:
    inv = await db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
    
    number = (body.number or "").strip()
    if not number:
        raise HTTPException(status_code=400, detail="Invoice number is required")
    if len(number) > 80:
        raise HTTPException(status_code=400, detail="Invoice number too long (max 80 characters)")
    
    if body.status not in INVOICE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(INVOICE_STATUSES)}"
        )
    
    try:
        currency = normalize_currency(body.currency)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid currency: {exc}") from exc
    
    client = await _validate_invoice_refs(db, body)
    
    try:
        inv.client_id = body.client_id
        inv.project_id = body.project_id
        inv.number = number
        inv.currency = currency
        inv.invoice_date = body.invoice_date
        inv.follow_up_at = body.follow_up_at
        inv.status = body.status
        inv.kind = body.kind or "deposit"
        _apply_invoice_fields(inv, body, client)
        await db.commit()
        loaded = await _load(db, invoice_id)
        assert loaded
        return _out(loaded)
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update invoice: {str(exc)}") from exc


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


@router.get("/invoices/{invoice_id}/pdf")
async def invoice_pdf(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
    inline: bool = False,
) -> FileResponse:
    try:
        inv = await _load(db, invoice_id)
        if not inv:
            raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
        
        tpl = await get_or_create_invoice_settings(db)
        items = parse_line_items(inv.line_items)
        proj_name = inv.project.name if inv.project else ""
        kind = inv.kind or "deposit"
        fallback_desc = f"{kind.replace('_', ' ').title()}"
        if proj_name:
            fallback_desc = f"{fallback_desc} — {proj_name}"
        
        pdf_items = line_items_for_pdf(
            items,
            fallback_desc=fallback_desc,
            fallback_amount=float(inv.amount or 0),
        )
        
        safe_num = "".join(c if c.isalnum() or c in "-_" else "_" for c in (inv.number or "invoice"))
        out_path = settings.data_path / "reports" / f"invoice_{safe_num}.pdf"
        
        build_invoice_pdf(
            out_path,
            number=inv.number,
            amount=float(inv.amount or 0),
            currency=inv.currency or "USD",
            invoice_date=inv.invoice_date,
            bill_to_name=inv.bill_to_name or (inv.client.name if inv.client else ""),
            bill_to_location=inv.bill_to_location or (inv.client.location if inv.client else ""),
            bill_to_phone=inv.bill_to_phone or (getattr(inv.client, "phone", "") if inv.client else ""),
            line_items=pdf_items,
            invoice_notes=inv.invoice_notes or "",
            settings=settings_to_dict(tpl),
        )
        
        disposition = "inline" if inline else "attachment"
        filename = f"CFS_Invoice_{safe_num}.pdf"
        return FileResponse(
            out_path,
            media_type="application/pdf",
            filename=filename,
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": f'{disposition}; filename="{filename}"',
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(exc)}") from exc


@router.get("/invoices/{invoice_id}/xlsx")
async def invoice_xlsx(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Employee, Depends(require_manager)],
) -> Response:
    inv = await _load(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    tpl = await get_or_create_invoice_settings(db)
    items = parse_line_items(inv.line_items)
    proj_name = inv.project.name if inv.project else ""
    kind = inv.kind or "deposit"
    fallback_desc = f"{kind.replace('_', ' ').title()}"
    if proj_name:
        fallback_desc = f"{fallback_desc} — {proj_name}"
    pdf_items = line_items_for_pdf(
        items,
        fallback_desc=fallback_desc,
        fallback_amount=float(inv.amount or 0),
    )
    data = build_invoice_xlsx(
        number=inv.number or "",
        amount=float(inv.amount or 0),
        currency=inv.currency or "USD",
        invoice_date=inv.invoice_date,
        bill_to_name=inv.bill_to_name or (inv.client.name if inv.client else ""),
        bill_to_location=inv.bill_to_location or (inv.client.location if inv.client else ""),
        bill_to_phone=inv.bill_to_phone or (getattr(inv.client, "phone", "") if inv.client else ""),
        line_items=pdf_items,
        invoice_notes=inv.invoice_notes or "",
        settings=settings_to_dict(tpl),
    )
    safe_num = "".join(c if c.isalnum() or c in "-_" else "_" for c in (inv.number or "invoice"))
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="CFS_Invoice_{safe_num}.xlsx"',
            "Cache-Control": "no-store",
        },
    )


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
