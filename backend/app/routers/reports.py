from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models import User
from app.services.analytics_service import get_analytics_service
from app.services.pdf_reports import PDFReportGenerator
from app.services.excel_reports import ExcelReportGenerator

router = APIRouter(prefix="/reports", tags=["Reports"])

PERIOD_MAP = {
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
    "quarterly": timedelta(days=90),
}


@router.post("/generate")
def generate_report(
    period: str = Query(..., pattern="^(weekly|monthly|quarterly)$"),
    format: str = Query("pdf", pattern="^(pdf|excel|json)$"),
    view: bool = Query(False, description="If true, serve inline for browser viewing instead of download"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Generate a comprehensive weekly/monthly/quarterly report."""
    delta = PERIOD_MAP.get(period)
    if not delta:
        raise HTTPException(status_code=400, detail="Invalid period")

    now = datetime.now(timezone.utc)
    period_start = now - delta
    analytics = get_analytics_service(db)
    analytics_data = analytics.get_dashboard_overview(date_from=period_start, date_to=now)

    if format == "json":
        from fastapi.responses import JSONResponse
        return JSONResponse(content=analytics_data)

    try:
        if format == "excel":
            gen = ExcelReportGenerator()
            content = gen.generate_analytics_report(analytics_data)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"{period}_report_{now.strftime('%Y%m%d')}.xlsx"
        else:
            gen = PDFReportGenerator()
            content = gen.generate_analytics_report(analytics_data, include_charts=False)
            media_type = "application/pdf"
            filename = f"{period}_report_{now.strftime('%Y%m%d')}.pdf"

        disposition = "inline" if view else "attachment"
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.post("/custom")
def generate_custom_report(
    date_from: str = Query(..., description="Start date (ISO format, e.g. 2026-01-01)"),
    date_to: str = Query(..., description="End date (ISO format, e.g. 2026-12-31)"),
    item_ids: Optional[List[int]] = Query(None, description="Filter by inventory item IDs"),
    vendor_ids: Optional[List[int]] = Query(None, description="Filter by vendor IDs"),
    format: str = Query("pdf", pattern="^(pdf|excel|json)$"),
    view: bool = Query(False, description="If true, serve inline for browser viewing instead of download"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Generate a custom report filtered by date range, items (SKU), and/or vendors."""
    try:
        start = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)")

    analytics = get_analytics_service(db)

    orders = analytics.get_filtered_orders(start, end, item_ids, vendor_ids)
    inventory = analytics.get_filtered_inventory(item_ids)

    report_data = {
        "orders": orders,
        "inventory": inventory,
        "total_orders": len(orders),
        "total_items": len(inventory),
        "period": {
            "label": "Custom",
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
        },
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "item_ids": item_ids,
            "vendor_ids": vendor_ids,
        },
    }

    if format == "json":
        from fastapi.responses import JSONResponse
        return JSONResponse(content=report_data)

    try:
        if format == "excel":
            gen = ExcelReportGenerator()
            # Use generate_custom_report if it exists, otherwise fall back to custom handling
            if hasattr(gen, 'generate_custom_report'):
                content = gen.generate_custom_report(report_data)
            else:
                # Manual handling for Excel custom report
                from openpyxl import Workbook
                wb = Workbook()
                wb.remove(wb.active)
                ws = wb.create_sheet("Orders", 0)
                gen._populate_orders_sheet(ws, orders, report_data.get("period"))
                ws_inv = wb.create_sheet("Inventory")
                gen._populate_inventory_sheet(ws_inv, inventory)
                from io import BytesIO
                excel_buffer = BytesIO()
                wb.save(excel_buffer)
                excel_buffer.seek(0)
                content = excel_buffer.getvalue()
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"custom_report_{end.strftime('%Y%m%d')}.xlsx"
        else:
            gen = PDFReportGenerator()
            content = gen.generate_custom_report(report_data)
            media_type = "application/pdf"
            filename = f"custom_report_{end.strftime('%Y%m%d')}.pdf"

        disposition = "inline" if view else "attachment"
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Custom report generation failed: {str(e)}")
