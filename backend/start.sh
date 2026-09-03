#!/bin/sh
# Cloud9 ERP - Reliable startup script
# Validates env, waits for database, runs first-run admin setup, then starts the API server.
# Setup failures are blocking in production so bad deployments fail visibly.

set -e

# Initialize writable directories with proper permissions
echo "[*] Initializing directories..."
mkdir -p /app/logs /app/backups /app/static/uploads
chmod 755 /app/logs /app/backups /app/static/uploads

echo "[*] Validating production environment..."
python validate_env.py

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

# Run admin setup (blocking in production; first-run setup must succeed before serving traffic)
echo "[*] Running first-run setup (admin user, roles, permissions)..."
if python setup_firstrun.py; then
    echo "[✓] First-run setup completed successfully"
else
    echo "[✗] First-run setup failed."
    exit 1
fi

# Start the API server
echo "[*] Starting Uvicorn..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
