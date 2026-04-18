@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Konfiguracja PostgreSQL URL

echo Ten krok ustawi lub zaktualizuje URL bazy w pliku .env.local.
echo Uzyj DATABASE_PUBLIC_URL z Railway, bo uruchamiasz aplikacje lokalnie.
echo.

powershell -NoProfile -Command "$url = Read-Host 'Wklej DATABASE_PUBLIC_URL'; if ([string]::IsNullOrWhiteSpace($url)) { Write-Host 'Brak URL - anulowano.'; exit 1 }; $path = '.env.local'; if (Test-Path $path) { $lines = Get-Content -LiteralPath $path } else { $lines = @() }; $updated = @(); $replaced = $false; foreach ($line in $lines) { if ($line -match '^\s*INVOICE_DATABASE_URL\s*=') { if (-not $replaced) { $updated += ('INVOICE_DATABASE_URL=' + $url); $replaced = $true }; continue }; $updated += $line }; if (-not $replaced) { if ($updated.Count -gt 0 -and $updated[-1] -ne '') { $updated += '' }; $updated += ('INVOICE_DATABASE_URL=' + $url) }; Set-Content -LiteralPath $path -Value $updated -Encoding UTF8; Write-Host 'Zaktualizowano .env.local (bez nadpisywania innych ustawien).'"
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo Gotowe. Teraz mozesz uruchamiac aplikacje bez ustawiania zmiennej recznie.
pause
