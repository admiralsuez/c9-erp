# C9 ERP Setup Script for Windows
# This script sets up the entire project (backend + frontend)

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$SkipDatabase
)

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host "`n" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host $Text -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
}

function Write-Step {
    param([string]$Text)
    Write-Host "`n▶ $Text" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Text)
    Write-Host "⚠ $Text" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Text)
    Write-Host "✗ $Text" -ForegroundColor Red
}

# Get the project root directory
$projectRoot = Get-Location

Write-Header "C9 ERP Project Setup"
Write-Host "Project Root: $projectRoot" -ForegroundColor White

# Check prerequisites
Write-Step "Checking prerequisites..."

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Error "Python is not installed or not in PATH"
    Write-Host "Please install Python 3.10+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Success "Node.js found: $nodeVersion, npm: $npmVersion"
} catch {
    Write-Error "Node.js/npm is not installed or not in PATH"
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check Git
try {
    $gitVersion = git --version
    Write-Success "Git found: $gitVersion"
} catch {
    Write-Error "Git is not installed or not in PATH"
    Write-Host "Please install Git from https://git-scm.com/" -ForegroundColor Red
    exit 1
}

Write-Success "All prerequisites installed!"

# ============================================
# BACKEND SETUP
# ============================================

if (-not $SkipBackend) {
    Write-Header "Setting up Backend"
    
    $backendDir = Join-Path $projectRoot "backend"
    
    if (-not (Test-Path $backendDir)) {
        Write-Error "Backend directory not found at $backendDir"
        exit 1
    }
    
    # Check for .env file
    $envFile = Join-Path $backendDir ".env"
    if (-not (Test-Path $envFile)) {
        Write-Warning ".env file not found in backend directory"
        Write-Host "Creating sample .env file..." -ForegroundColor Yellow
        
        $envContent = @"
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/c9_erp

# JWT Configuration
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256

# File Upload
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=104857600

# Email Configuration
SENDGRID_API_KEY=your-sendgrid-api-key

# Cloud Storage (DigitalOcean Spaces / AWS S3)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_S3_REGION=us-east-1

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Environment
ENV=development
"@
        Set-Content -Path $envFile -Value $envContent
        Write-Success "Sample .env file created at $envFile"
        Write-Warning "Please update the .env file with your actual configuration"
    } else {
        Write-Success ".env file found"
    }
    
    # Create Python virtual environment
    Write-Step "Creating Python virtual environment..."
    $venvDir = Join-Path $backendDir "venv"
    
    if (Test-Path $venvDir) {
        Write-Warning "Virtual environment already exists at $venvDir"
    } else {
        python -m venv $venvDir
        Write-Success "Virtual environment created"
    }
    
    # Activate virtual environment
    Write-Step "Activating virtual environment..."
    $activateScript = Join-Path $venvDir "Scripts" "Activate.ps1"
    & $activateScript
    Write-Success "Virtual environment activated"
    
    # Upgrade pip
    Write-Step "Upgrading pip..."
    python -m pip install --upgrade pip --quiet
    Write-Success "pip upgraded"
    
    # Install requirements
    Write-Step "Installing Python requirements..."
    $requirementsFile = Join-Path $backendDir "requirements.txt"
    
    if (-not (Test-Path $requirementsFile)) {
        Write-Error "requirements.txt not found at $requirementsFile"
        exit 1
    }
    
    pip install -r $requirementsFile
    Write-Success "Python requirements installed"
    
    # Database setup
    if (-not $SkipDatabase) {
        Write-Step "Preparing database..."
        Write-Warning "Make sure PostgreSQL is running and DATABASE_URL in .env is correct"
        
        # Run Alembic migrations
        Write-Step "Running database migrations..."
        alembic upgrade head
        Write-Success "Database migrations completed"
    }
    
    Write-Success "Backend setup completed!"
    Write-Host "To start the backend server, run:" -ForegroundColor White
    Write-Host "  cd backend" -ForegroundColor Cyan
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "  uvicorn app.main:app --reload --port 8000" -ForegroundColor Cyan
}

# ============================================
# FRONTEND SETUP
# ============================================

if (-not $SkipFrontend) {
    Write-Header "Setting up Frontend"
    
    $frontendDir = Join-Path $projectRoot "frontend"
    
    if (-not (Test-Path $frontendDir)) {
        Write-Error "Frontend directory not found at $frontendDir"
        exit 1
    }
    
    # Check for .env file
    $envFile = Join-Path $frontendDir ".env"
    if (-not (Test-Path $envFile)) {
        Write-Warning ".env file not found in frontend directory"
        Write-Host "Creating sample .env file..." -ForegroundColor Yellow
        
        $envContent = @"
VITE_API_URL=http://64.227.191.1:5173
VITE_APP_NAME=C9 ERP
"@
        Set-Content -Path $envFile -Value $envContent
        Write-Success "Sample .env file created at $envFile"
    } else {
        Write-Success ".env file found"
    }
    
    # Install dependencies
    Write-Step "Installing frontend dependencies..."
    Push-Location $frontendDir
    npm install
    Write-Success "Frontend dependencies installed"
    Pop-Location
    
    Write-Success "Frontend setup completed!"
    Write-Host "To start the frontend development server, run:" -ForegroundColor White
    Write-Host "  cd frontend" -ForegroundColor Cyan
    Write-Host "  npm run dev" -ForegroundColor Cyan
}

# ============================================
# FINAL SUMMARY
# ============================================

Write-Header "Setup Complete! 🎉"

Write-Host "`nNext Steps:" -ForegroundColor White
Write-Host "1. Update .env files with your configuration" -ForegroundColor Cyan
Write-Host "2. Make sure PostgreSQL is running" -ForegroundColor Cyan
Write-Host "3. Start the backend: cd backend && .\venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload" -ForegroundColor Cyan
Write-Host "4. In another terminal, start the frontend: cd frontend && npm run dev" -ForegroundColor Cyan
Write-Host "5. Open http://localhost:5173 in your browser" -ForegroundColor Cyan

Write-Host "`nUseful Commands:" -ForegroundColor White
Write-Host "  Backend database reset: alembic downgrade base && alembic upgrade head" -ForegroundColor Cyan
Write-Host "  Frontend lint: npm run lint" -ForegroundColor Cyan
Write-Host "  Frontend build: npm run build" -ForegroundColor Cyan

Write-Host "`n" -ForegroundColor Green
