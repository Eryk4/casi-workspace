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
python run.py --reset
pause
