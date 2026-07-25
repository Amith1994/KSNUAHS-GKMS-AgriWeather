$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop "Rainfall Status Auto-Updater.lnk"
$targetPath = "e:\1. AntiGravity\IMD forecast with map and pincode\Rainfall_Status_App\Update_Rainfall_Status.bat"
$workDir = "e:\1. AntiGravity\IMD forecast with map and pincode\Rainfall_Status_App"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $targetPath
$Shortcut.WorkingDirectory = $workDir
$Shortcut.WindowStyle = 1
$Shortcut.Description = "KSNDMC Rainfall Status Auto-Updater & Analytics App"
$Shortcut.IconLocation = "shell32.dll,238"
$Shortcut.Save()

Write-Host "Desktop shortcut created successfully at: $shortcutPath"
