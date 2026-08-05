@echo off
REM Start C9 ERP Local Development Environment

echo.
echo ====================================
echo C9 ERP Local Development Setup
echo ====================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or not installed.
    echo Please start Docker Desktop and try again.
    exit /b 1
)

echo [1/3] Stopping any existing containers...
docker compose down -v --remove-orphans

echo.
echo [2/3] Building and starting services (this may take a few minutes)...
docker compose up -d --build

echo.
echo [3/3] Waiting for services to be ready...
timeout /t 10 /nobreak

echo.
echo ====================================
echo Services Started
echo ====================================
echo.
echo Frontend:  http://localhost:5173
echo Backend:   http://localhost:8000
echo Database:  localhost:5432
echo.
echo Default Login Credentials:
echo   Email:    admin@thecloud9corp.com
echo   Password: admin@123
echo.
echo To view logs, run:
echo   docker compose logs -f
echo.
echo To stop services, run:
echo   docker compose down
echo.
