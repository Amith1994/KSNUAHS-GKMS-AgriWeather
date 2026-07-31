# GKMS IMD Forecast Auto-Updater & GitHub Sync (PowerShell)
$Host.UI.RawUI.WindowTitle = "IMD Forecast Auto-Updater & GitHub Sync"
Clear-Host

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "   GKMS IMD Forecast Auto-Updater & GitHub Sync" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

# Set working directory to script folder
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = "e:\1. AntiGravity\IMD forecast with map and pincode" }
Set-Location -Path $scriptDir

Write-Host "[1/2] Searching for latest Weather Excel file and updating HTML files..." -ForegroundColor Green
python auto_update.py --skip-prompt

Write-Host ""
Write-Host "-------------------------------------------------------" -ForegroundColor Yellow
$response = Read-Host "Local HTML files updated! Do you want to update & push to GitHub account? (Y/N)"
Write-Host "-------------------------------------------------------" -ForegroundColor Yellow

if ($response -eq 'Y' -or $response -eq 'y' -or $response -eq 'yes' -or $response -eq 'YES') {
    Write-Host "[2/2] Staging and Committing changes..." -ForegroundColor Cyan
    git add .
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    git commit -m "Auto-update IMD weather forecast data ($timestamp)"
    
    Write-Host "Pushing updates to GitHub (origin main)..." -ForegroundColor Cyan
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[SUCCESS] Successfully updated and pushed all changes to your GitHub account!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[WARNING] Could not push to GitHub. Check your internet connection or git settings." -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "[INFO] GitHub push skipped by user. Local files updated successfully!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Process complete. Closing in 5 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 5
