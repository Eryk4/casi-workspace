@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Testy
set "INVOICE_DATABASE_URL="
set "DATABASE_URL="
set "INVOICE_DB_ENGINE=sqlite"
set "INVOICE_SQLITE_PATH=%cd%\data\test_runtime\commands\full_discover.sqlite3"
python -m unittest discover -s tests -v
pause
