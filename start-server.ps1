# 3D Filament Inventory - Start Server
# This script starts the Flask server on port 5000

Write-Host "Starting 3D Filament Inventory Server..." -ForegroundColor Cyan
Write-Host ""

# Set port to 5000 (3000 may be restricted on Windows)
$env:PORT = 5000

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to the script directory
Set-Location $scriptDir

# Find Python executable
$pythonExe = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonExe) {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher from https://www.python.org" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if dependencies are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
& python -c "import flask; import requests" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    & python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "Dependencies OK" -ForegroundColor Green
Write-Host ""

# Start the server
Write-Host "========================================" -ForegroundColor Green
Write-Host "  3D Filament Inventory Server" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

& python app.py
