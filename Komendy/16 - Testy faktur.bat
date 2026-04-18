@echo off
setlocal
cd /d "%~dp0.."
set "INVOICE_DATABASE_URL="
set "DATABASE_URL="
set "INVOICE_DB_ENGINE=sqlite"
set "INVOICE_SQLITE_PATH=%cd%\data\test_runtime\commands\invoices.sqlite3"
python -u -m unittest tests.test_invoice_duplicates tests.test_invoice_review_and_ksef tests.test_invoice_collaboration -v
pause
