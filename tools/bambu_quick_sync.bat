@echo off
REM Bambu AMS Sync Quick Helper
REM Makes it easy to sync Bambu AMS data to inventory

SET SCRIPT_DIR=%~dp0
SET ROOT_DIR=%SCRIPT_DIR%..
SET SYNC_SCRIPT=%ROOT_DIR%\tools\bambu_ams_sync.py
SET DATA_FILE=%ROOT_DIR%\data\my_ams_data.json

echo ========================================
echo    Bambu AMS Filament Sync Tool
echo ========================================
echo.

REM Check if data file exists
if not exist "%DATA_FILE%" (
    echo ERROR: AMS data file not found
    echo.
    echo Create it first with:
    echo   python tools\bambu_ams_sync.py --create-sample data\my_ams_data.json
    echo.
    echo Then edit the file with your actual AMS spool data
    echo.
    pause
    exit /b 1
)

REM Run sync
python "%SYNC_SCRIPT%" --manual "%DATA_FILE%"

echo.
echo Done! View updated inventory at http://localhost:8501
echo.
pause
