@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Uruchom na PostgreSQL

echo [INFO] Start aplikacji...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do taskkill /PID %%a /F >nul 2>nul
set "INVOICE_DB_ENGINE=postgresql"
set PYTHONUNBUFFERED=1
python -u run.py --host 0.0.0.0 --port 8000
pause
