"""User management routes."""

from fastapi import APIRouter

from app.routers.users.users_crud import router as crud_router
from app.routers.users.roles import router as roles_router
from app.routers.users.signatures import router as signatures_router

router = APIRouter()
router.include_router(crud_router)
router.include_router(roles_router)
router.include_router(signatures_router)
