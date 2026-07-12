from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.database import engine, Base
from app.core.config import settings
from app import models
import asyncio
import logging
import threading
from datetime import datetime, timezone
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations up to date")

    # Auto-backup: run an immediate backup, then schedule periodic backups
    from app.routers.backup import _backup_db, BACKUP_DIR, _IS_POSTGRES
    os.makedirs(BACKUP_DIR, exist_ok=True)
    _ext = ".sql" if _IS_POSTGRES else ".db"
    try:
        path = os.path.join(BACKUP_DIR, f"auto_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}{_ext}")
        actual_path = _backup_db(path)
        logger.info(f"Initial auto-backup created: {os.path.basename(actual_path)}")
    except Exception as e:
        logger.warning(f"Initial auto-backup failed: {e}")

    SHUTDOWN_EVENT = threading.Event()

    async def periodic_backup():
        while not SHUTDOWN_EVENT.is_set():
            try:
                SHUTDOWN_EVENT.wait(6 * 3600)
                if SHUTDOWN_EVENT.is_set():
                    break
                from app.routers.backup import _backup_db, BACKUP_DIR as bdir, _IS_POSTGRES
                _ext = ".sql" if _IS_POSTGRES else ".db"
                os.makedirs(bdir, exist_ok=True)
                path = os.path.join(bdir, f"auto_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}{_ext}")
                actual_path = _backup_db(path)
                auto_files = sorted([f for f in os.listdir(bdir) if f.startswith("auto_")])
                while len(auto_files) > 14:
                    to_delete = os.path.join(bdir, auto_files.pop(0))
                    os.unlink(to_delete)
                logger.info(f"Auto-backup created: {os.path.basename(actual_path)}")
            except Exception as e:
                logger.error(f"Auto-backup failed: {e}")

    t = threading.Thread(target=lambda: asyncio.run(periodic_backup()), daemon=True)
    t.start()
    logger.info("Auto-backup scheduler started (every 6 hours, max 14 files)")

    yield  # app runs here

    # --- shutdown ---
    logger.info("Shutting down...")
    SHUTDOWN_EVENT.set()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Cloud9 ERP System - Phase 1",
    lifespan=lifespan,
)

# CORS middleware - origins from env var (comma-separated) or defaults
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to always return JSON (with CORS) on 500
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

# Include routers
from app.routers import auth, users, settings as settings_router, vendors, inventory, warehouse, audit, orders, approval_rules, documents, vendor_portal, analytics, health, notifications, reports, backup

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(settings_router.router)
app.include_router(vendors.router)
app.include_router(inventory.router)
app.include_router(warehouse.router)
app.include_router(audit.router)
app.include_router(orders.router)
app.include_router(approval_rules.router)
app.include_router(documents.router)
app.include_router(vendor_portal.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(backup.router)

# Seed data endpoint - admin only
from app.core.auth import require_admin
from app.models import User

@app.post("/seed-data", tags=["Admin"])
def seed_database(current_user: User = Depends(require_admin)):
    """Populate database with seed data. Admin only."""
    try:
        from seed_data import main as seed_main
        seed_main()
        logger.info(f"Database seeded by {current_user.email}")
        return {"status": "success", "message": "Database seeded successfully"}
    except Exception as e:
        logger.error(f"Seed exception: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

logger.info(f"Starting {settings.APP_NAME}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
