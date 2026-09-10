"""Validate and serialize invoice line items (stored as JSON on Invoice)."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError, field_validator

MAX_LINE_ITEMS = 50
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
CELL_COLOR_KEYS = ("project", "scope", "area", "rate", "cost")


def _clean_hex(raw: object) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    if not s.startswith("#"):
        s = f"#{s}"
    if _HEX_RE.match(s):
        if len(s) == 4:
            s = f"#{s[1]*2}{s[2]*2}{s[3]*2}"
        return s.upper()
    return ""


def _clean_cell_colors(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key in CELL_COLOR_KEYS:
        hx = _clean_hex(raw.get(key))
        if hx:
            out[key] = hx
    return out


class InvoiceLineItem(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    scope: str = Field("", max_length=200)
    qty: float = Field(default=1.0, gt=0, le=99999)
    unit_price: float = Field(default=0.0, ge=0, le=1_000_000_000)
    area: str = Field("", max_length=80)
    rate: str = Field("", max_length=80)
    comments: str = Field("", max_length=500)
    unpaid: bool = False
    cell_colors: dict[str, str] = Field(default_factory=dict)

    @field_validator("cell_colors", mode="before")
    @classmethod
    def _validate_colors(cls, v: object) -> dict[str, str]:
        return _clean_cell_colors(v)

    @property
    def line_total(self) -> float:
        return round(self.qty * self.unit_price, 2)


def parse_line_items(raw: str | None) -> list[InvoiceLineItem]:
    if not raw or not str(raw).strip():
        return []
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    items: list[InvoiceLineItem] = []
    for row in data[:MAX_LINE_ITEMS]:
        if not isinstance(row, dict):
            continue
        try:
            items.append(InvoiceLineItem.model_validate(_row_dict(row)))
        except ValidationError:
            continue
    return items


def _row_dict(row) -> dict:
    if not isinstance(row, dict):
        dump = getattr(row, "model_dump", None)
        data = dump() if callable(dump) else {
            "description": getattr(row, "description", ""),
            "scope": getattr(row, "scope", ""),
            "qty": getattr(row, "qty", 1),
            "unit_price": getattr(row, "unit_price", 0),
            "area": getattr(row, "area", ""),
            "rate": getattr(row, "rate", ""),
            "comments": getattr(row, "comments", ""),
            "unpaid": getattr(row, "unpaid", False),
            "cell_colors": getattr(row, "cell_colors", {}) or {},
        }
    else:
        data = row
    desc = str(data.get("description") or data.get("project_name") or "").strip()
    area = str(data.get("area") or "").strip()
    rate = str(data.get("rate") or "").strip()
    qty_raw = data.get("qty")
    if qty_raw in (None, "") and area:
        try:
            qty_raw = float(area.replace(",", ""))
        except (TypeError, ValueError):
            qty_raw = 1
    price_raw = data.get("unit_price")
    if price_raw in (None, "") and rate:
        try:
            price_raw = float(str(rate).replace("$", "").replace(",", "").strip())
        except (TypeError, ValueError):
            price_raw = 0
    unpaid = data.get("unpaid")
    if isinstance(unpaid, str):
        unpaid = unpaid.strip().lower() in {"1", "true", "yes", "unpaid"}
    return {
        "description": desc,
        "scope": str(data.get("scope") or data.get("scope_of_work") or "").strip(),
        "qty": float(qty_raw or 1),
        "unit_price": float(price_raw or 0),
        "area": area,
        "rate": rate,
        "comments": str(data.get("comments") or "").strip(),
        "unpaid": bool(unpaid),
        "cell_colors": _clean_cell_colors(data.get("cell_colors")),
    }


def validate_line_items(rows: list) -> list[InvoiceLineItem]:
    if len(rows) > MAX_LINE_ITEMS:
        raise ValueError(f"Maximum {MAX_LINE_ITEMS} line items allowed")
    items: list[InvoiceLineItem] = []
    for row in rows:
        items.append(InvoiceLineItem.model_validate(_row_dict(row)))
    return items


def serialize_line_items(items: list[InvoiceLineItem]) -> str:
    return json.dumps([i.model_dump() for i in items[:MAX_LINE_ITEMS]])


def line_items_total(items: list[InvoiceLineItem]) -> float:
    return round(sum(i.line_total for i in items), 2)


def line_items_for_pdf(items: list[InvoiceLineItem], *, fallback_desc: str, fallback_amount: float) -> list[dict]:
    if items:
        return [
            {
                "description": i.description,
                "scope": i.scope,
                "qty": i.qty,
                "unit_price": i.unit_price,
                "area": i.area,
                "rate": i.rate,
                "amount": i.line_total,
                "comments": i.comments,
                "unpaid": i.unpaid,
                "cell_colors": dict(i.cell_colors or {}),
            }
            for i in items
        ]
    if fallback_amount > 0 or fallback_desc:
        amt = round(float(fallback_amount or 0), 2)
        return [
            {
                "description": (fallback_desc or "Services").strip() or "Services",
                "scope": "",
                "qty": 1.0,
                "unit_price": amt,
                "area": "",
                "rate": "",
                "amount": amt,
                "comments": "",
                "unpaid": False,
                "cell_colors": {},
            }
        ]
    return []
