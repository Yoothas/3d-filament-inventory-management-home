@echo off
REM Slicer-friendly wrapper (no spaces in path)
REM This script calls the main postprint script from a location without spaces
REM Place this file somewhere with no spaces in the path, like C:\3DPrint\

REM Set the actual script location (with spaces)
set SCRIPT_PATH=D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py

REM Enable logging
set FILAMENT_POSTPRINT_LOG=1
set FILAMENT_SERVER_PORT=5000

echo ========================================
echo 3D Filament Auto-Deduct
echo ========================================
echo.
echo Script: %SCRIPT_PATH%
echo G-code: %1
echo.

REM Check if Python exists
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

REM Run the script
python "%SCRIPT_PATH%" %*

set RESULT=%ERRORLEVEL%

if %RESULT%==0 (
    echo.
    echo SUCCESS: Filament updated!
) else (
    echo.
    echo FAILED: Error code %RESULT%
    echo Check log: %USERPROFILE%\.filament-inventory\postprint.log
)

exit /b %RESULT%
