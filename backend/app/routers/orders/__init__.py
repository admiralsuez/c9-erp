from fastapi import APIRouter

from app.routers.orders.orders_crud import router as crud_router
from app.routers.orders.orders_documents import router as documents_router
from app.routers.orders.orders_workflow import router as workflow_router

router = APIRouter()
router.include_router(crud_router)
router.include_router(workflow_router)
router.include_router(documents_router)
