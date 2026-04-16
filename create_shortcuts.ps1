$DesktopPath = [Environment]::GetFolderPath('Desktop')
$RenLernFolder = Join-Path $DesktopPath 'RenLern'
$BatchFile = "c:\Users\Administrator\Desktop\Repo clone\lernapp-apk\RUN_LERNAPP.bat"

if (!(Test-Path $RenLernFolder)) {
    New-Item -ItemType Directory -Path $RenLernFolder | Out-Null
}

$shell = New-Object -ComObject WScript.Shell

@('01 Start:start',
  '02 Restart:restart',
  '03 Autostart:autostart_enable',
  '04 Shutdown:stop'
) | ForEach-Object {
    $parts = $_ -split ':'
    $name = $parts[0]
    $args = $parts[1]
    $lnkPath = Join-Path $RenLernFolder "$name.lnk"
    $lnk = $shell.CreateShortcut($lnkPath)
    $lnk.TargetPath = $BatchFile
    $lnk.Arguments = $args
    $lnk.WorkingDirectory = "c:\Users\Administrator\Desktop\Repo clone\lernapp-apk"
    $lnk.Description = "RenLern Service Manager - $name"
    $lnk.WindowStyle = 1
    $lnk.Save()
    Write-Host "Verknuepfung erstellt: $name"
}

Write-Host "Alle Verknuepfungen wurden erstellt!"

