@echo off
title IMD Forecast Auto Updater & GitHub Sync
cd /d "%~dp0"
powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0run_update.ps1"
