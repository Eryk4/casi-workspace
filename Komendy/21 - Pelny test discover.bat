@echo off
setlocal
cd /d "%~dp0.."
set "INVOICE_DATABASE_URL="
set "DATABASE_URL="
set "INVOICE_DB_ENGINE=sqlite"
set "INVOICE_SQLITE_PATH=%cd%\data\test_runtime\commands\full_profile.sqlite3"
python run_quality_checks.py --profile full
pause
