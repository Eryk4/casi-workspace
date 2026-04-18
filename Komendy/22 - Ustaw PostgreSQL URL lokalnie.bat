@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Jednorazowa konfiguracja PostgreSQL

echo Ten krok zapisze URL bazy do pliku .env.local (jednorazowo).
echo Uzyj DATABASE_PUBLIC_URL z Railway, bo uruchamiasz aplikacje lokalnie.
echo.

powershell -NoProfile -Command "$url = Read-Host 'Wklej DATABASE_PUBLIC_URL'; if ([string]::IsNullOrWhiteSpace($url)) { Write-Host 'Brak URL - anulowano.'; exit 1 }; Set-Content -Path '.env.local' -Value ('INVOICE_DATABASE_URL=' + $url) -Encoding ASCII; Write-Host 'Zapisano .env.local'"
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo Gotowe. Teraz mozesz uruchamiac aplikacje bez ustawiania zmiennej recznie.
pause
