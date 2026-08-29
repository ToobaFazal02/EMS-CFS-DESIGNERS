"""Singleton invoice template settings (company + bank details)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InvoiceSettings

DEFAULT_INVOICE_SETTINGS: dict[str, str] = {
    "issuer_name": "Faisal Khan",
    "issuer_address": "Islamabad, Pakistan",
    "issuer_phone": "+92 348 4832513",
    "issuer_email": "cfsdesigners@gmail.com",
    "bank_title": "USD Account Details:",
    "bank_intro": (
        "If you're sending money from a bank in the US, you can use these details to make a domestic transfer. "
        "If you're sending from somewhere else, make an international Swift transfer."
    ),
    "bank_account_name": "Faisal Khan",
    "bank_account_number": "8313067383",
    "bank_account_type": "Checking",
    "bank_routing": "026073150",
    "bank_swift": "CMFGUS33",
    "bank_name_address": "Community Federal Savings Bank, 89-16 Jamaica Ave, Woodhaven, NY, 11421, United States",
    "contact_name": "Faisal Khan",
    "contact_email": "cfsdesigners@gmail.com",
    "footer_thanks": "THANK YOU FOR YOUR BUSINESS!",
    "header_color": "#92D050",
    "highlight_color": "#A85914",
}


async def get_or_create_invoice_settings(db: AsyncSession) -> InvoiceSettings:
    row = await db.get(InvoiceSettings, "default")
    if row:
        return row
    row = InvoiceSettings(id="default", **DEFAULT_INVOICE_SETTINGS)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


def settings_to_dict(row: InvoiceSettings) -> dict[str, str]:
    return {
        "issuer_name": getattr(row, "issuer_name", "") or "",
        "issuer_address": getattr(row, "issuer_address", "") or "",
        "issuer_phone": getattr(row, "issuer_phone", "") or "",
        "issuer_email": getattr(row, "issuer_email", "") or "",
        "bank_title": getattr(row, "bank_title", "") or "USD Account Details:",
        "bank_intro": getattr(row, "bank_intro", "") or "",
        "bank_account_name": getattr(row, "bank_account_name", "") or "",
        "bank_account_number": getattr(row, "bank_account_number", "") or "",
        "bank_account_type": getattr(row, "bank_account_type", "") or "",
        "bank_routing": getattr(row, "bank_routing", "") or "",
        "bank_swift": getattr(row, "bank_swift", "") or "",
        "bank_name_address": getattr(row, "bank_name_address", "") or "",
        "contact_name": getattr(row, "contact_name", "") or "",
        "contact_email": getattr(row, "contact_email", "") or "",
        "footer_thanks": getattr(row, "footer_thanks", "") or "THANK YOU FOR YOUR BUSINESS!",
        "header_color": (
            "#92D050"
            if str(getattr(row, "header_color", "") or "").strip().lower() in {"", "#548235"}
            else str(row.header_color)
        ),
        "highlight_color": getattr(row, "highlight_color", None) or "#A85914",
    }
