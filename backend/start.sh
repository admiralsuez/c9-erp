#!/bin/sh
# Cloud9 ERP - Reliable startup script
# Waits for database, attempts admin setup, then starts the API server.
# Does NOT block on setup failure — logs a warning but continues to start uvicorn.

set -e

# Extract host from DATABASE_URL
# Supports postgresql://user:pass@host:port/db and postgresql+asyncpg://...
if [ -z "$DATABASE_URL" ]; then
    echo "[ERROR] DATABASE_URL environment variable is not set."
    exit 1
fi

DB_HOST=$(echo "$DATABASE_URL" | sed -E 's/^postgresql(\+[a-z]+)?:\/\/([^:]+:[^@]+@)?([^:/]+).*/\3/')
DB_PORT=${DB_PORT:-5432}

echo "[*] Database host: $DB_HOST (port $DB_PORT)"
echo "[*] Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
        echo "[✓] PostgreSQL is ready!"
        break
    fi
    echo "[*] Attempt $attempt/$max_attempts: PostgreSQL not ready yet..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "[✗] PostgreSQL did not become ready in time."
    exit 1
fi

# Run admin setup (non-blocking; logs failure but continues)
echo "[*] Running first-run setup (admin user, roles, permissions)..."
if python setup_firstrun.py; then
    echo "[✓] First-run setup completed successfully"
else
    echo "[⚠] First-run setup failed or skipped (admin may already exist). Continuing to start API..."
fi

# Start the API server
echo "[*] Starting Uvicorn..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
