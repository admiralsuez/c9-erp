from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, HTTPException as FastAPIHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.database import engine, Base
from app.core.config import settings
from app import models
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
import threading
from datetime import datetime, timezone
import os
import glob
import time

# --- Logging setup: rotated file logs (max 5) + console ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Rotate: keep only the 5 newest files, delete oldest (best-effort on Windows)
_log_files = sorted(glob.glob(os.path.join(LOG_DIR, "c9erp_*.log")))
while len(_log_files) >= 5:
    try:
        os.unlink(_log_files.pop(0))
    except PermissionError:
        # File in use by another process (uvicorn reload workers on Windows)
        _log_files.pop(0)
        continue

_log_path = os.path.join(LOG_DIR, f"c9erp_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log")

# Configure root logger so ALL modules (orders, inventory, etc.) write to same file
_root = logging.getLogger()
_root.setLevel(logging.DEBUG)

_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(name)-16s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

_fh = logging.FileHandler(_log_path, encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(_formatter)
_root.addHandler(_fh)

_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
_ch.setFormatter(_formatter)
_root.addHandler(_ch)

logger = logging.getLogger("main")
logger.info(f"Log file: {_log_path}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    # --- Alembic migrations (wrapped to avoid startup crash) ---
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations up to date")
    except Exception as e:
        logger.warning(f"Alembic migration failed (ignored for dev): {e}")

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

    def periodic_backup():
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

    t = threading.Thread(target=periodic_backup, daemon=True)
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

# CORS middleware - origins from env var (comma-separated string) or defaults.
# NOTE: in production the frontend calls the API via a same-origin /api path
# (reverse-proxied), so CORS is only relevant for local dev and explicit overrides.
_cors_origins = [
    o.strip()
    for o in settings.CORS_ORIGINS.split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sensitive paths — never log request bodies for these
_SENSITIVE_PATHS = ["/auth", "/vendor-portal", "/backup"]

# Request-logging middleware — logs every API hit (redacts sensitive bodies)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import asyncio
    from starlette.datastructures import Headers

    start = time.time()
    client = request.client.host if request.client else "unknown"
    auth = request.headers.get("authorization", "")
    has_token = "Bearer" in auth if auth else False

    skip = request.url.path in ("/favicon.ico", "/health")

    if not skip and request.method in ("POST", "PUT", "PATCH"):
        # Read the body ONCE and cache it so downstream handlers can still read it
        try:
            raw_body = await request.body()
        except Exception:
            raw_body = b""

        # Rebuild the ASGI receive stream so FastAPI can read the body again
        async def _receive():
            return {"type": "http.request", "body": raw_body, "more_body": False}

        request = Request(request.scope, _receive)

        is_sensitive = any(request.url.path.startswith(p) for p in _SENSITIVE_PATHS)
        if is_sensitive:
            body_snippet = " BODY=[redacted]"
        elif raw_body:
            decoded = raw_body.decode("utf-8", errors="replace")
            if len(decoded) > 3000:
                decoded = decoded[:3000] + "...[truncated]"
            body_snippet = f" BODY={decoded}"
        else:
            body_snippet = ""

        logger.info(
            f"IN  | {client} | {request.method} {request.url.path} | "
            f"auth={'yes' if has_token else 'no'}{body_snippet}"
        )
    elif not skip:
        logger.info(
            f"IN  | {client} | {request.method} {request.url.path} | "
            f"auth={'yes' if has_token else 'no'}"
        )

    response = await call_next(request)
    elapsed_ms = (time.time() - start) * 1000

    if not skip:
        status_code = response.status_code
        level = logging.WARNING if status_code >= 400 else logging.INFO
        logger.log(
            level,
            f"OUT | {client} | {request.method} {request.url.path} | "
            f"{status_code} | {elapsed_ms:.1f}ms"
        )

    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    client = request.client.host if request.client else "unknown"
    if isinstance(exc, FastAPIHTTPException):
        logger.warning(
            f"HTTP {exc.status_code} | {request.method} {request.url.path} "
            f"from {client} | {exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    logger.error(
        f"UNHANDLED | {request.method} {request.url.path} "
        f"from {client} | {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

# Mount static files
import os
_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(os.path.join(_static_dir, "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# Include routers
from app.routers import auth, users, settings as settings_router, vendors, inventory, warehouse, audit, orders, approval_rules, documents, vendor_portal, analytics, health, notifications, reports, backup
from app.api.routes import inventory_images, inventory_serials

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(settings_router.router)
app.include_router(vendors.router)
app.include_router(inventory.router)
app.include_router(inventory_images.router)
app.include_router(inventory_serials.router)
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_excludes=["*.log"])
