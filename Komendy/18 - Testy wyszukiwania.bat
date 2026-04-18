@echo off
setlocal
cd /d "%~dp0.."
set "INVOICE_DATABASE_URL="
set "DATABASE_URL="
set "INVOICE_DB_ENGINE=sqlite"
set "INVOICE_SQLITE_PATH=%cd%\data\test_runtime\commands\search.sqlite3"
python -u -m unittest tests.test_search_access tests.test_search_descriptive -v
pause
