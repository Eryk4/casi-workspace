@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Reset danych demo
echo UWAGA: ten krok usunie obecna baze danych i odtworzy dane demonstracyjne.
echo.
set /p confirm=Czy na pewno chcesz kontynuowac? (tak/nie): 
if /I not "%confirm%"=="tak" (
  echo Anulowano reset.
  pause
  exit /b 0
)
set "INVOICE_DATABASE_URL="
set "DATABASE_URL="
set "INVOICE_DB_ENGINE=sqlite"
set "INVOICE_SQLITE_PATH=%cd%\data\invoice_ops.sqlite3"
python run.py --reset
pause
