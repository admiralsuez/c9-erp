@echo off
REM C9 ERP Setup Script for Windows (Batch version)
REM This is a simpler alternative to setup.ps1

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo              C9 ERP Project Setup
echo ============================================================
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    exit /b 1
)
echo OK: Python found

REM Check Node.js
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    exit /b 1
)
echo OK: Node.js found

REM Check Git
echo Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com/
    exit /b 1
)
echo OK: Git found

echo.
echo All prerequisites found!
echo.

REM ============================================
REM BACKEND SETUP
REM ============================================

echo ============================================================
echo Setting up Backend
echo ============================================================
echo.

if not exist "backend" (
    echo ERROR: Backend directory not found
    exit /b 1
)

REM Create .env if it doesn't exist
if not exist "backend\.env" (
    echo Creating backend\.env file...
    (
        echo # Database Configuration
        echo DATABASE_URL=postgresql://user:password@localhost:5432/c9_erp
        echo.
        echo # JWT Configuration
        echo SECRET_KEY=your-secret-key-change-this-in-production
        echo ALGORITHM=HS256
        echo.
        echo # File Upload
        echo UPLOAD_DIR=./uploads
        echo MAX_UPLOAD_SIZE=104857600
        echo.
        echo # Email Configuration
        echo SENDGRID_API_KEY=your-sendgrid-api-key
        echo.
        echo # Cloud Storage (DigitalOcean Spaces / AWS S3)
        echo AWS_ACCESS_KEY_ID=your-access-key
        echo AWS_SECRET_ACCESS_KEY=your-secret-key
        echo AWS_S3_BUCKET_NAME=your-bucket-name
        echo AWS_S3_REGION=us-east-1
        echo.
        echo # CORS
        echo CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
        echo.
        echo # Environment
        echo ENV=development
    ) > "backend\.env"
    echo Created backend\.env - please update with your configuration
)

REM Create virtual environment
if not exist "backend\venv" (
    echo Creating Python virtual environment...
    python -m venv backend\venv
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call backend\venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install requirements
echo Installing Python requirements...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python requirements
    exit /b 1
)
echo Backend requirements installed

echo.
echo Backend setup completed!
echo.

REM ============================================
REM FRONTEND SETUP
REM ============================================

echo ============================================================
echo Setting up Frontend
echo ============================================================
echo.

if not exist "frontend" (
    echo ERROR: Frontend directory not found
    exit /b 1
)

REM Create .env if it doesn't exist
if not exist "frontend\.env" (
    echo Creating frontend\.env file...
    (
        echo VITE_API_URL=http://64.227.191.1:8000
        echo VITE_APP_NAME=C9 ERP
    ) > "frontend\.env"
    echo Created frontend\.env
)

REM Install dependencies
echo Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies
    exit /b 1
)
echo Frontend dependencies installed
cd ..

echo.
echo Frontend setup completed!
echo.

REM ============================================
REM FINAL SUMMARY
REM ============================================

echo ============================================================
echo              Setup Complete!
echo ============================================================
echo.
echo Next Steps:
echo 1. Update .env files with your configuration
echo 2. Make sure PostgreSQL is running
echo 3. Start the backend:
echo    cd backend
echo    venv\Scripts\activate.bat
echo    uvicorn app.main:app --reload --port 8000
echo.
echo 4. In another terminal, start the frontend:
echo    cd frontend
echo    npm run dev
echo.
echo 5. Open http://localhost:5173 in your browser
echo.
echo ============================================================
echo.

pause
