@echo off
setlocal
cd /d "%~dp0.."
python check_email_connection.py
echo.
pause
