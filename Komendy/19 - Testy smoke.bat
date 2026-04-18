@echo off
setlocal
cd /d "%~dp0.."
python run_quality_checks.py --profile smoke
pause
