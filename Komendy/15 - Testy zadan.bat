@echo off
setlocal
cd /d "%~dp0.."
set "INVOICE_DATABASE_URL="
set "DATABASE_URL="
set "INVOICE_DB_ENGINE=sqlite"
set "INVOICE_SQLITE_PATH=%cd%\data\test_runtime\commands\tasks.sqlite3"
python -u -m unittest tests.test_task_service tests.test_task_commands tests.test_task_http -v
pause
