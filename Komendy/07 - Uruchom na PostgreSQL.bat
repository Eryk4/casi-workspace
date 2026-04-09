@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Uruchom na PostgreSQL

if "%INVOICE_DATABASE_URL%"=="" if "%DATABASE_URL%"=="" (
  echo Brakuje konfiguracji bazy PostgreSQL.
  echo.
  echo Ustaw najpierw jedna z tych zmiennych srodowiskowych:
  echo - INVOICE_DATABASE_URL
  echo - DATABASE_URL
  echo.
  echo Przyklad dla PowerShell:
  echo $env:INVOICE_DATABASE_URL="postgresql://uzytkownik:haslo@host:5432/baza"
  echo.
  pause
  exit /b 1
)

set INVOICE_DB_ENGINE=postgresql
python run.py --host 0.0.0.0 --port 8000
pause
