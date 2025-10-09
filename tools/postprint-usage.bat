@echo off
REM Wrapper to call the PowerShell post-print script
REM Usage examples:
REM   postprint-usage.bat "C:\path\to\gcode.gcode"
REM   postprint-usage.bat -used_g 12.34 -material PLA -color Red -brand HATCHBOX -job jobname

setlocal enableextensions
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0postprint-usage.ps1" %*
endlocal
