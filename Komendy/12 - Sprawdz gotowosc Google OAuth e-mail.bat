@echo off
setlocal
cd /d "%~dp0.."
python check_email_google_oauth_readiness.py
pause
