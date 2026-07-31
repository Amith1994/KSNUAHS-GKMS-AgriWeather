$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop "IMD forecast with map and pincode.lnk"
$targetPath = "powershell.exe"
$psScript = "e:\1. AntiGravity\IMD forecast with map and pincode\run_update.ps1"
$workDir = "e:\1. AntiGravity\IMD forecast with map and pincode"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $targetPath
$Shortcut.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$psScript`""
$Shortcut.WorkingDirectory = $workDir
$Shortcut.Description = "IMD Weather Forecast Auto-Updater & GitHub Sync"
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()
Write-Host "Desktop PowerShell shortcut created successfully at: $shortcutPath"
