@echo off
setlocal
cd /d "%~dp0.."
python sync_release_id.py
pause
