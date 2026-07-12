#!/usr/bin/env powershell
<#
.SYNOPSIS
Cloud9 ERP - Complete Local Development Server Startup
.DESCRIPTION
Starts the Cloud9 ERP system locally with SQLite database. 
All 7 phases: Authentication, Orders, Documents, Vendor Portal, Email, Analytics, and Advanced Features.
#>

param(
    [switch]$Test,
    [switch]$Reset,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Usage: .\start.ps1 [options]

Options:
  -Test   Run tests before starting the server
  -Reset  Delete database and reseed (fresh start)
  -Help   Show this help message

Examples:
  .\start.ps1                # Start the server
  .\start.ps1 -Test          # Start with tests
  .\start.ps1 -Reset         # Fresh database
"@
    exit 0
}

Write-Host ""
Write-Host "🎯 Cloud9 ERP - Complete System Startup 🎯" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan

if ($Reset) {
    Write-Host "🔄 Resetting database..." -ForegroundColor Yellow
    $dbFile = "erp_local.db"
    if (Test-Path $dbFile) {
        Remove-Item $dbFile -Force
        Write-Host "✓ Database deleted" -ForegroundColor Green
    }
}

# Start the server
$pythonScript = if ($Test) { 
    "python run_local_server.py --test" 
} else { 
    "python run_local_server.py" 
}

Write-Host ""
Write-Host "Starting Cloud9 ERP server..." -ForegroundColor Cyan
Write-Host ""

& cmd.exe /c $pythonScript
