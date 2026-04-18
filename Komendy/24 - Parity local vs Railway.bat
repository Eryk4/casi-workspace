@echo off
setlocal
cd /d "%~dp0.."

echo Upewnij sie, ze lokalny serwer dziala na http://127.0.0.1:8000
set /p REMOTE_BASE=Podaj adres Railway (np. https://twoj-app.up.railway.app): 
if "%REMOTE_BASE%"=="" (
  echo Brak adresu Railway - anulowano.
  pause
  exit /b 1
)

python compare_environment_parity.py --remote-base "%REMOTE_BASE%" --require-same-release --require-same-assets
if errorlevel 1 (
  echo.
  echo [UWAGA] Wykryto krytyczne roznice parity. Sprawdz raport JSON powyzej.
  pause
  exit /b 1
)

echo.
echo [OK] Release i kluczowe assety sa zgodne lokalnie i na Railway.
pause
