@echo off
echo.
echo ==========================================
echo  Filament Inventory - Slicer Setup
echo ==========================================
echo.
echo This will create the wrapper script at:
echo C:\3DPrint\slicer-postprint.bat
echo.
pause

REM Create directory
if not exist "C:\3DPrint" (
    echo Creating directory C:\3DPrint...
    mkdir "C:\3DPrint"
)

REM Create wrapper script
echo Creating wrapper script...
(
echo @echo off
echo "D:\python 3.10\python.exe" "D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py" %%*
) > "C:\3DPrint\slicer-postprint.bat"

if exist "C:\3DPrint\slicer-postprint.bat" (
    echo.
    echo ==========================================
    echo  SUCCESS!
    echo ==========================================
    echo.
    echo Wrapper created at: C:\3DPrint\slicer-postprint.bat
    echo.
    echo NEXT STEPS:
    echo.
    echo 1. Open Anycubic Slicer
    echo 2. Go to: Settings -^> Post-processing Scripts
    echo 3. Enter this command:
    echo.
    echo    C:\3DPrint\slicer-postprint.bat "{output_filepath}"
    echo.
    echo 4. Save and test with a print!
    echo.
) else (
    echo.
    echo ==========================================
    echo  ERROR!
    echo ==========================================
    echo.
    echo Failed to create wrapper script.
    echo Try running this as Administrator.
    echo.
)

pause
