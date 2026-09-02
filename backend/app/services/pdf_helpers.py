"""PDF generation helpers.

Shared utilities used by requisition / order / report PDF generators.
Centralizes the boilerplate of:

* fetching the live ``Settings`` row for branding (logo URL, header/footer text),
* coalescing None settings to safe defaults,
* normalizing a list of order-item dicts into the (name, qty, sku, description)
  shape the PDF expects.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Settings


def get_branding_dict(db: Session) -> Dict[str, Optional[str]]:
    """Return a dict of branding fields pulled from the current ``Settings`` row.

    Returns:
        Dictionary with keys ``company_name``, ``company_logo_url``,
        ``company_address``, ``company_contact``, ``pdf_header_text``,
        ``pdf_footer_text``. Any missing field is returned as ``None`` so
        PDF generators can fall back to their own defaults without
        NoneType errors.

    If no ``Settings`` row exists yet, every value is ``None``.
    """
    settings = db.query(Settings).first()
    if settings is None:
        return {
            "company_name": None,
            "company_logo_url": None,
            "company_address": None,
            "company_contact": None,
            "pdf_header_text": None,
            "pdf_footer_text": None,
        }
    return {
        "company_name": settings.company_name,
        "company_logo_url": settings.company_logo_url,
        "company_address": settings.company_address,
        "company_contact": settings.company_contact,
        "pdf_header_text": settings.pdf_header_text,
        "pdf_footer_text": settings.pdf_footer_text,
    }


def build_pdf_items(items: List[Any]) -> List[Dict[str, Any]]:
    """Normalize a list of order items to the dict shape PDF code expects.

    Accepts either ORM ``OrderItem`` instances or already-serialized dicts.
    Returns a list of ``{name, sku, quantity, description}`` dicts ready
    to drop into ``PDFGenerator.generate_requisition``.

    Falls back to empty strings / 0 when fields are missing so callers
    don't need defensive code.
    """
    out: List[Dict[str, Any]] = []
    for it in items or []:
        if isinstance(it, dict):
            out.append(
                {
                    "name": it.get("name", ""),
                    "sku": it.get("sku") or it.get("erp_code", "") or "",
                    "quantity": it.get("quantity")
                              or it.get("quantity_ordered")
                              or 0,
                    "description": it.get("description", ""),
                }
            )
        else:
            # ORM OrderItem
            item_rel = getattr(it, "item", None)
            out.append(
                {
                    "name": getattr(item_rel, "name", "")
                            if item_rel is not None
                            else getattr(it, "name", ""),
                    "sku": getattr(item_rel, "sku", "")
                            if item_rel is not None
                            else getattr(it, "sku", "")
                            or "",
                    "quantity": getattr(it, "quantity_ordered", 0),
                    "description": getattr(item_rel, "description", "")
                                   if item_rel is not None
                                   else "",
                }
            )
    return out


def get_header_footer(db: Session) -> Dict[str, str]:
    """Convenience wrapper for the common case of needing just header/footer text.

    Returns:
        ``{"header_text": str, "footer_text": str}`` with empty strings
        substituted for None values so callers can concatenate without
        checking.
    """
    branding = get_branding_dict(db)
    return {
        "header_text": branding.get("pdf_header_text") or "",
        "footer_text": branding.get("pdf_footer_text") or "",
    }
