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

CMD ["sh", "start.sh"]
