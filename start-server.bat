@echo off
REM 3D Filament Inventory - Start Server
REM This batch file starts the Flask server on port 5000

echo Starting 3D Filament Inventory Server...
echo.

REM Set port to 5000 (3000 may be restricted on Windows)
set PORT=5000

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8 or higher from https://www.python.org
    echo.
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import flask; import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Dependencies OK
echo.

REM Start the server
echo ========================================
echo   3D Filament Inventory Server
echo ========================================
echo.

python app.py
