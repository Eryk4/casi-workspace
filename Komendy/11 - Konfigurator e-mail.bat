@echo off
setlocal
cd /d "%~dp0.."
python configure_email_settings.py
pause
