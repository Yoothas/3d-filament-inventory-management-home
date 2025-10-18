@echo off
REM Wrapper script for post-print filament tracking
REM This file has no spaces in its path, avoiding slicer issues

"D:\python 3.10\python.exe" "D:\VSCode\Filament in python\3d-filament-inventory-management-home\tools\postprint_usage.py" %*
