@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Testy HTTP szybkie
set "INVOICE_DATABASE_URL="
set "DATABASE_URL="
set "INVOICE_DB_ENGINE=sqlite"
set "INVOICE_SQLITE_PATH=%cd%\data\test_runtime\commands\http_quick.sqlite3"
python -u -m unittest tests.test_http_server_system tests.test_http_server_integrations tests.test_http_server_invoices tests.test_http_server_access tests.test_http_server_telegram -v
pause
