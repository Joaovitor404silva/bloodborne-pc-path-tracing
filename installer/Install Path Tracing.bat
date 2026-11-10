@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
if errorlevel 1 (echo. & echo Install FAILED: see the message above.) else (echo. & echo Install OK.)
pause
