@echo off
title IMD Forecast Auto Updater and Weather Launcher
cd /d "%~dp0"
echo =======================================================
echo   GKMS IMD Forecast Auto-Updater and Weather Launcher
echo =======================================================
echo.
echo Searching for latest Weather XLS file and updating...
python auto_update.py
echo.
echo Done! App has been updated and launched in your browser.
ping -n 4 127.0.0.1 >nul
