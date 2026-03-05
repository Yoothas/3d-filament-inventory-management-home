# Bambu AMS Quick Sync Helper Script
# This makes it easy to sync your Bambu AMS data to inventory

param(
    [switch]$DryRun,
    [switch]$CreateNew,
    [string]$DataFile = "data\my_ams_data.json"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$SyncScript = Join-Path $RootDir "tools\bambu_ams_sync.py"
$DataPath = Join-Path $RootDir $DataFile

# Function to display header
function Show-Header {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "    Bambu AMS Filament Sync Tool" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Function to check if Flask is running
function Test-FlaskRunning {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:5000/api/filaments" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Create new data file
if ($CreateNew) {
    Show-Header
    Write-Host "Creating new AMS data file..." -ForegroundColor Yellow
    python $SyncScript --create-sample $DataPath
    
    if (Test-Path $DataPath) {
        Write-Host ""
        Write-Host "✓ File created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Open your Bambu printer AMS display"
        Write-Host "  2. Note down the remaining weight for each spool"
        Write-Host "  3. Edit the file: $DataPath"
        Write-Host "  4. Run this script again to sync"
        Write-Host ""
        
        # Ask if they want to open the file now
        $open = Read-Host "Open the file now? (y/n)"
        if ($open -eq "y" -or $open -eq "Y") {
            notepad $DataPath
        }
    }
    exit
}

# Main sync operation
Show-Header

# Check if data file exists
if (-not (Test-Path $DataPath)) {
    Write-Host "ERROR: AMS data file not found: $DataFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "Create it first with:" -ForegroundColor Yellow
    Write-Host "  .\tools\bambu_quick_sync.ps1 -CreateNew" -ForegroundColor White
    Write-Host ""
    Write-Host "Or specify a different file:" -ForegroundColor Yellow
    Write-Host "  .\tools\bambu_quick_sync.ps1 -DataFile ""path\to\your_file.json""" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Check if Flask is running
Write-Host "Checking Flask API..." -ForegroundColor Yellow
if (-not (Test-FlaskRunning)) {
    Write-Host "ERROR: Flask API is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Start Flask first with:" -ForegroundColor Yellow
    Write-Host "  python app.py" -ForegroundColor White
    Write-Host ""
    exit 1
}
Write-Host "✓ Flask API is running" -ForegroundColor Green
Write-Host ""

# Run sync
if ($DryRun) {
    Write-Host "Running DRY-RUN (no changes will be made)..." -ForegroundColor Yellow
    Write-Host ""
    python $SyncScript --manual $DataPath --dry-run
    Write-Host ""
    Write-Host "To apply these changes, run without -DryRun:" -ForegroundColor Cyan
    Write-Host "  .\tools\bambu_quick_sync.ps1" -ForegroundColor White
    Write-Host ""
}
else {
    Write-Host "Syncing AMS data to inventory..." -ForegroundColor Yellow
    Write-Host ""
    python $SyncScript --manual $DataPath
    Write-Host ""
    Write-Host "Done! Sync complete" -ForegroundColor Green
    Write-Host ""
    Write-Host "View updated inventory in Dashboard at http://localhost:8501" -ForegroundColor Cyan
    Write-Host ""
}
