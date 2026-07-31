@echo off
title IMD Forecast Auto Updater & GitHub Sync
cd /d "%~dp0"
echo =======================================================
echo   GKMS IMD Forecast Auto-Updater & GitHub Sync
echo =======================================================
echo.
echo Searching for latest Weather XLS file, updating app, and syncing to GitHub...
python auto_update.py
echo.
echo Done! App updated, synced with GitHub, and launched in browser.
ping -n 5 127.0.0.1 >nul
