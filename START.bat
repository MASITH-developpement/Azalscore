@echo off
REM ============================================================
REM AZALSCORE - Double-cliquez pour demarrer
REM ============================================================
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "start-azalscore.ps1"
pause
