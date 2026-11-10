@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Uninstall %*
if errorlevel 1 (echo. & echo Uninstall FAILED: see the message above.) else (echo. & echo Uninstall OK.)
pause
