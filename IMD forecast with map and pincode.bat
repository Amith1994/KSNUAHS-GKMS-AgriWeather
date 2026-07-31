@echo off
title IMD Forecast Auto Updater & GitHub Sync
cd /d "%~dp0"
echo =======================================================
echo   GKMS IMD Forecast Auto-Updater & GitHub Sync
echo =======================================================
echo.
echo Searching for latest Weather XLS file and updating app...
python auto_update.py
echo.
echo Process complete. Closing window in 5 seconds...
ping -n 5 127.0.0.1 >nul
