@echo off
setlocal
cd /d "%~dp0.."
if not exist ".env.local" (
  copy /Y ".env.local.example" ".env.local" >nul
)
start notepad ".env.local"
echo Otworzono plik .env.local. Uzupelnij dane skrzynki i zapisz zmiany.
pause
