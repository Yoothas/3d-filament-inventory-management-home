@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Wrapper for Anycubic Slicer post-processing
REM Pass through common args. Example usage:
REM   postprint-usage.cmd -used_g 12.3 -material PLA -color Red -brand Hatchbox -job myfile.gcode

powershell -ExecutionPolicy Bypass -File "%~dp0postprint-usage.ps1" %*

endlocal
