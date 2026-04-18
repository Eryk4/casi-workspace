@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Testy HTTP
set "INVOICE_DATABASE_URL="
set "DATABASE_URL="
set "INVOICE_DB_ENGINE=sqlite"
set "INVOICE_SQLITE_PATH=%cd%\data\test_runtime\commands\http.sqlite3"
python -u -m unittest discover -s tests -p "test_http_server_*.py" -v
pause
