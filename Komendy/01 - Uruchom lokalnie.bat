@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Uruchom lokalnie
set "INVOICE_DATABASE_URL="
set "DATABASE_URL="
set "INVOICE_DB_ENGINE=sqlite"
set "INVOICE_SQLITE_PATH=%cd%\data\invoice_ops.sqlite3"
python run.py
pause
