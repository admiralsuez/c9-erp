#!/bin/bash

echo "======================================"
echo "Fixing C9 ERP Remote Deployment"
echo "======================================"
echo ""

cd ~/apps/c9-erp || exit 1

echo "[1/5] Pulling latest code from GitHub..."
git pull origin main

echo ""
echo "[2/5] Stopping all containers..."
docker compose down --remove-orphans

echo ""
echo "[3/5] Removing unused Docker resources..."
docker system prune -f --volumes

echo ""
echo "[4/5] Killing any processes on port 8000 and 5173..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
lsof -ti:5432 | xargs kill -9 2>/dev/null || true

sleep 2

echo ""
echo "[5/5] Building and starting services..."
docker compose up -d --build

echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "Services:"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  Database:  localhost:5432"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
