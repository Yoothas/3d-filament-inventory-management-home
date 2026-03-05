@echo off
REM Wrapper script for Anycubic Slicer post-processing
REM This helps diagnose issues with auto-deduction
REM
REM Usage: Add this to your slicer's post-processing command:
REM   "path\to\tools\postprint-wrapper.bat"
REM
REM The slicer will automatically pass the G-code file path as the first argument

echo ========================================
echo 3D Filament Auto-Deduct Script
echo ========================================
echo.

REM Enable logging
set FILAMENT_POSTPRINT_LOG=1

REM Set the correct port
set FILAMENT_SERVER_PORT=5000

REM Get the script directory
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%postprint_usage.py

echo Script directory: %SCRIPT_DIR%
echo Python script: %PYTHON_SCRIPT%
echo G-code file: %1
echo Server port: %FILAMENT_SERVER_PORT%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please ensure Python is installed and in your PATH
    pause
    exit /b 1
)

REM Check if the Python script exists
if not exist "%PYTHON_SCRIPT%" (
    echo ERROR: Python script not found at: %PYTHON_SCRIPT%
    pause
    exit /b 1
)

REM Check if G-code file was provided
if "%~1"=="" (
    echo ERROR: No G-code file provided
    echo This script should be called by your slicer with the G-code path
    pause
    exit /b 1
)

REM Check if G-code file exists
if not exist "%~1" (
    echo ERROR: G-code file not found: %~1
    pause
    exit /b 1
)

echo Running auto-deduct script...
echo.

REM Run the Python script with the G-code file
python "%PYTHON_SCRIPT%" "%~1"

set ERROR_LEVEL=%ERRORLEVEL%

echo.
echo ========================================
if %ERROR_LEVEL%==0 (
    echo SUCCESS: Filament usage updated!
) else (
    echo FAILED: Error code %ERROR_LEVEL%
    echo Check the output above for details
)
echo ========================================
echo.

REM Show log location
echo Log file: %USERPROFILE%\.filament-inventory\postprint.log
echo.

REM Don't pause automatically - let slicer continue
REM Uncomment the line below if you want to see output when testing manually
REM pause

exit /b %ERROR_LEVEL%
