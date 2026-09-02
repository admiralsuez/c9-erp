FROM python:3.11-slim

WORKDIR /app

# Install deployment/runtime utilities for readiness checks and healthchecks
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl netcat-openbsd postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make start script executable
RUN chmod +x start.sh

# Create non-root user and give it ownership of writable dirs
RUN useradd --create-home --uid 1001 --shell /bin/bash appuser \
    && rm -rf /app/logs /app/backups /app/static/uploads \
    && mkdir -p /app/logs /app/backups /app/static/uploads \
    && chown -R appuser:appuser /app \
    && chmod 777 /app/logs /app/backups /app/static/uploads /app
USER appuser

CMD ["sh", "start.sh"]
