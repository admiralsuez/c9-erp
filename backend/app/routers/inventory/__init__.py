from fastapi import APIRouter

from app.routers.inventory.inventory_items import router as items_router
from app.routers.inventory.inventory_stock import router as stock_router

router = APIRouter()
router.include_router(items_router)
router.include_router(stock_router)
