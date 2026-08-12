"""Serial number management routes.

Split from the former app/api/routes/inventory_serials.py monolith into
purpose-focused modules. The combined router keeps the same prefix and
tags, so `inventory_serials.router` (imported by main.py) is unchanged.
"""

from fastapi import APIRouter

from app.api.routes.inventory_serials.create import router as create_router
from app.api.routes.inventory_serials.query import router as query_router
from app.api.routes.inventory_serials.update import router as update_router
from app.api.routes.inventory_serials.delete import router as delete_router

router = APIRouter()
router.include_router(create_router)
router.include_router(query_router)
router.include_router(update_router)
router.include_router(delete_router)
