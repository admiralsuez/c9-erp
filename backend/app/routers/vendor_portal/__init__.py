"""Vendor portal routes."""

from fastapi import APIRouter

from app.routers.vendor_portal.auth import router as auth_router
from app.routers.vendor_portal.orders import router as orders_router
from app.routers.vendor_portal.dashboard import router as dashboard_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(orders_router)
router.include_router(dashboard_router)
