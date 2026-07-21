$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop "IMD forecast with map and pincode.lnk"
$targetPath = "e:\1. AntiGravity\IMD forecast with map and pincode\IMD forecast with map and pincode.bat"
$workDir = "e:\1. AntiGravity\IMD forecast with map and pincode"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $targetPath
$Shortcut.WorkingDirectory = $workDir
$Shortcut.Description = "IMD Weather Forecast Auto-Updater"
$Shortcut.IconLocation = "shell32.dll,14"
$Shortcut.Save()
Write-Host "Desktop shortcut created successfully at: $shortcutPath"
