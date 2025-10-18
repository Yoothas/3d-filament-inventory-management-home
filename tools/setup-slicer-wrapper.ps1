# Setup script for Anycubic Slicer Post-Processing
# Run this as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Filament Inventory - Slicer Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  Warning: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "   Some operations might fail. Consider running as Admin." -ForegroundColor Yellow
    Write-Host ""
}

# Paths
$wrapperDir = "C:\3DPrint"
$wrapperPath = "$wrapperDir\slicer-postprint.bat"
$pythonPath = "D:\python 3.10\python.exe"
$scriptPath = "D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py"

Write-Host "📁 Creating wrapper directory..." -ForegroundColor Yellow

try {
    New-Item -Path $wrapperDir -ItemType Directory -Force -ErrorAction Stop | Out-Null
    Write-Host "✅ Directory created: $wrapperDir" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create directory: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📝 Creating wrapper script..." -ForegroundColor Yellow

# Create wrapper script content
$wrapperContent = @"
@echo off
REM Anycubic Slicer Post-Processing Wrapper
REM This wrapper avoids path-with-spaces issues

"$pythonPath" "$scriptPath" %*
"@

try {
    $wrapperContent | Out-File -FilePath $wrapperPath -Encoding ASCII -Force -ErrorAction Stop
    Write-Host "✅ Wrapper created: $wrapperPath" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create wrapper: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔍 Verifying setup..." -ForegroundColor Yellow

# Check Python exists
if (Test-Path $pythonPath) {
    Write-Host "✅ Python found: $pythonPath" -ForegroundColor Green
} else {
    Write-Host "⚠️  Python not found at: $pythonPath" -ForegroundColor Yellow
    Write-Host "   Update the wrapper if Python is elsewhere" -ForegroundColor Yellow
}

# Check script exists
if (Test-Path $scriptPath) {
    Write-Host "✅ Post-print script found" -ForegroundColor Green
} else {
    Write-Host "❌ Post-print script not found!" -ForegroundColor Red
    Write-Host "   Expected: $scriptPath" -ForegroundColor Red
}

# Check wrapper created
if (Test-Path $wrapperPath) {
    Write-Host "✅ Wrapper script created successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Wrapper script creation failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ✅ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Open Anycubic Slicer" -ForegroundColor White
Write-Host "2. Go to: Settings → Post-processing Scripts" -ForegroundColor White
Write-Host "3. Enter this command:" -ForegroundColor White
Write-Host ""
Write-Host "   $wrapperPath ""{output_filepath}""" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Save settings" -ForegroundColor White
Write-Host "5. Make sure Flask server is running:" -ForegroundColor White
Write-Host "   python app.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Documentation: FIXING_SLICER_PATH.md" -ForegroundColor Yellow
Write-Host ""

# Offer to copy to clipboard if possible
try {
    $clipboardCommand = "$wrapperPath ""{output_filepath}"""
    Set-Clipboard -Value $clipboardCommand
    Write-Host "📋 Command copied to clipboard!" -ForegroundColor Green
    Write-Host "   Just paste (Ctrl+V) in Anycubic Slicer!" -ForegroundColor Green
    Write-Host ""
} catch {
    # Clipboard not available, skip
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
