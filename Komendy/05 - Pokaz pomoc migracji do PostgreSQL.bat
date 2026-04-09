@echo off
setlocal
cd /d "%~dp0.."
title Panel Faktur - Pomoc migracji
python migrate_sqlite_to_configured_db.py --help
pause
