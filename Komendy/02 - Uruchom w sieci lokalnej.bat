@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Uruchom w sieci lokalnej
python run.py --host 0.0.0.0 --port 8000
pause
