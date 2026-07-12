from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.core.auth import get_current_user, require_admin
from app.models import User
from app.services.email_service import get_email_service
import sqlite3
import os
import shutil
import subprocess
import tempfile
import logging
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["Backup & Restore"])

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backups")

# Detect dialect
_db_url = str(engine.url)
_IS_POSTGRES = _db_url.startswith("postgresql")

if _IS_POSTGRES:
    DB_PATH = None
    # Extract connection info from engine URL for pg_dump
    _PG_HOST = engine.url.host or "localhost"
    _PG_PORT = str(engine.url.port or 5432)
    _PG_DB = engine.url.database or ""
    _PG_USER = engine.url.username or "postgres"
else:
    DB_PATH = os.path.abspath(engine.url.database) if engine.url.database else os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "erp_local.db"
    )
    DB_PATH = os.path.abspath(DB_PATH)
    _PG_HOST = _PG_PORT = _PG_DB = _PG_USER = None


def _pg_env() -> dict:
    """Return environment dict with PGPASSWORD if set."""
    env = os.environ.copy()
    if engine.url.password:
        env["PGPASSWORD"] = engine.url.password
    return env


def _backup_db(destination: str) -> str:
    """Backup the database — pg_dump for Postgres, sqlite3 backup for SQLite."""
    if _IS_POSTGRES:
        dump_path = destination.rsplit(".", 1)[0] + ".sql"
        cmd = [
            "pg_dump",
            "--host", _PG_HOST,
            "--port", _PG_PORT,
            "--username", _PG_USER,
            "--dbname", _PG_DB,
            "--format", "custom",
            "--file", dump_path,
        ]
        result = subprocess.run(cmd, env=_pg_env(), capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr.strip()}")
        return dump_path
    else:
        src = sqlite3.connect(DB_PATH)
        dst = sqlite3.connect(destination)
        src.backup(dst)
        src.close()
        dst.close()
        return destination


def _validate_backup(filepath: str) -> bool:
    """Validate backup file — pg_dump custom format or SQLite."""
    if _IS_POSTGRES:
        try:
            cmd = ["pg_restore", "--list", filepath]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception:
            return False
    else:
        try:
            if os.path.getsize(filepath) < 100:
                return False
            with open(filepath, "rb") as f:
                header = f.read(16)
            if header[:16] != b"SQLite format 3\x00":
                return False
            conn = sqlite3.connect(filepath)
            conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            conn.close()
            return True
        except Exception:
            return False


@router.get("/download")
def download_backup(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Download a full database backup."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"erp_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, filename)

    actual_path = _backup_db(backup_path)
    actual_filename = os.path.basename(actual_path)

    return FileResponse(
        path=actual_path,
        media_type="application/octet-stream",
        filename=actual_filename,
    )


@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Restore database from a backup file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    if _IS_POSTGRES and not file.filename.endswith(".sql"):
        raise HTTPException(status_code=400, detail="Postgres restore requires a .sql dump file")
    if not _IS_POSTGRES and not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="SQLite restore requires a .db file")

    suffix = ".sql" if _IS_POSTGRES else ".db"
    os.makedirs(BACKUP_DIR, exist_ok=True)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        content = await file.read()
        tmp.write(content)
        tmp.close()

        if not _validate_backup(tmp.name):
            os.unlink(tmp.name)
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid backup")

        # Safety backup first
        safety_suffix = ".sql" if _IS_POSTGRES else ".db"
        safety_name = f"pre_restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}{safety_suffix}"
        safety_path = os.path.join(BACKUP_DIR, safety_name)
        _backup_db(safety_path)

        engine.dispose()

        if _IS_POSTGRES:
            cmd = [
                "psql",
                "--host", _PG_HOST,
                "--port", _PG_PORT,
                "--username", _PG_USER,
                "--dbname", _PG_DB,
                "--file", tmp.name,
            ]
            result = subprocess.run(cmd, env=_pg_env(), capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(f"psql restore failed: {result.stderr.strip()}")
            os.unlink(tmp.name)
            return {
                "status": "restored",
                "message": "PostgreSQL database restored from SQL dump.",
                "safety_backup": safety_name,
            }
        else:
            shutil.move(tmp.name, DB_PATH)
            return {
                "status": "restored",
                "message": "SQLite database restored.",
                "safety_backup": safety_name,
            }
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.get("/list")
def list_backups(
    current_user: User = Depends(require_admin),
):
    """List available backup files."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    _ext = ".sql" if _IS_POSTGRES else ".db"
    files = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.endswith(_ext):
            full_path = os.path.join(BACKUP_DIR, f)
            size_kb = round(os.path.getsize(full_path) / 1024, 1)
            mtime = datetime.fromtimestamp(os.path.getmtime(full_path), tz=timezone.utc)
            files.append({
                "filename": f,
                "size_kb": size_kb,
                "created_at": mtime.isoformat(),
                "download_url": f"/backup/download-file/{f}",
            })

    return {"backups": files, "count": len(files)}


@router.get("/download-file/{filename:path}")
def download_specific_backup(
    filename: str,
    current_user: User = Depends(require_admin),
):
    """Download a specific backup file by name."""
    filepath = os.path.normpath(os.path.join(BACKUP_DIR, filename))
    if not filepath.startswith(os.path.normpath(BACKUP_DIR)):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Backup file not found")
    return FileResponse(
        path=filepath,
        media_type="application/octet-stream",
        filename=filename,
    )


@router.post("/email")
def email_backup(
    recipients: str = Query(..., description="Comma-separated email addresses to send the backup to"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a backup and email it as an attachment to specified recipients."""
    _ext = ".sql" if _IS_POSTGRES else ".db"
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"erp_backup_{timestamp}{_ext}"
    backup_path = os.path.join(BACKUP_DIR, filename)

    backup_path = _backup_db(backup_path)

    email_list = [e.strip() for e in recipients.split(",") if e.strip()]
    if not email_list:
        raise HTTPException(status_code=400, detail="At least one recipient email is required")

    with open(backup_path, "rb") as f:
        backup_content = f.read()

    size_kb = round(len(backup_content) / 1024, 1)
    email_service = get_email_service()

    results = []
    for email in email_list:
        attachments = [{
            "filename": filename,
            "content": backup_content,
            "mimetype": "application/octet-stream",
        }]
        html_body = f"""<h2>Cloud9 ERP - Database Backup</h2>
<p><strong>Generated:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
<p><strong>Requested by:</strong> {current_user.email}</p>
<p><strong>File:</strong> {filename}</p>
<p><strong>Size:</strong> {size_kb} KB</p>
<p>Attached: {filename}</p>
<p style="margin-top:20px;color:#888;">This is an automated backup from your Cloud9 ERP system.</p>
"""
        success = email_service.send(to_email=email, subject=f"Cloud9 ERP Backup - {timestamp}", body_html=html_body, attachments=attachments)
        results.append({"email": email, "sent": success})
        logger.info(f"Backup emailed to {email}: {'sent' if success else 'failed'}")

    all_sent = all(r["sent"] for r in results)

    return {
        "status": "success" if all_sent else "partial_failure",
        "backup_file": filename,
        "size_kb": size_kb,
        "results": results,
    }


@router.post("/trigger")
def trigger_backup(
    current_user: User = Depends(require_admin),
):
    """Manually trigger an auto-backup now (same as periodic)."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    _ext = ".sql" if _IS_POSTGRES else ".db"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"erp_backup_{timestamp}{_ext}"
    backup_path = os.path.join(BACKUP_DIR, filename)

    backup_path = _backup_db(backup_path)

    size_kb = round(os.path.getsize(backup_path) / 1024, 1)
    logger.info(f"Manual backup triggered by {current_user.email}: {filename} ({size_kb} KB)")

    return {
        "status": "created",
        "backup_file": filename,
        "size_kb": size_kb,
        "download_url": f"/backup/download-file/{filename}",
    }