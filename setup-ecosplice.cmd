@echo off
cd /d "%~dp0"
python scripts\setup_local.py %*
if errorlevel 1 pause
