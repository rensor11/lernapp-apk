# RenLern Server - Desktop Shortcuts Creator
# Erstellt einen Ordner auf dem Desktop mit Links

$Desktop = [Environment]::GetFolderPath("Desktop")
$RenLernFolder = Join-Path $Desktop "RenLern Server"
$ServerDir = Split-Path -Parent $PSCommandPath

Write-Host ""
Write-Host "[*] Erstelle Desktop-Verknuepfungen fuer RenLern Server..." -ForegroundColor Cyan
Write-Host ""

# Erstelle Ordner
if (-not (Test-Path $RenLernFolder)) {
    New-Item -ItemType Directory -Path $RenLernFolder | Out-Null
    Write-Host "[+] Ordner erstellt: $RenLernFolder" -ForegroundColor Green
} else {
    Write-Host "[*] Ordner existiert bereits: $RenLernFolder" -ForegroundColor Yellow
}

# WScript Shell fuer Verknuepfungen
$Shell = New-Object -ComObject WScript.Shell

# Array mit Verknuepfungen: (Name, BatchDatei, Icon, Beschreibung)
$Shortcuts = @(
    @("01 - START Alle Services.lnk", "START_ALL_SERVICES.bat", "C:\Windows\System32\shell32.dll,16", "RenLern Server - START alle Services"),
    @("02 - STOP Alle Services.lnk", "STOP_ALL_SERVICES.bat", "C:\Windows\System32\shell32.dll,27", "RenLern Server - STOP alle Services"),
    @("03 - Autostart aktivieren.lnk", "AUTOSTART_RENLERN.bat", "C:\Windows\System32\shell32.dll,25", "RenLern Server - Autostart aktivieren")
)

# Erstelle Verknuepfungen
foreach ($Shortcut in $Shortcuts) {
    $ShortcutPath = Join-Path $RenLernFolder $Shortcut[0]
    $TargetPath = Join-Path $ServerDir $Shortcut[1]
    
    if (Test-Path $TargetPath) {
        $ShortcutObject = $Shell.CreateShortcut($ShortcutPath)
        $ShortcutObject.TargetPath = $TargetPath
        $ShortcutObject.WorkingDirectory = $ServerDir
        $ShortcutObject.WindowStyle = 1
        $ShortcutObject.IconLocation = $Shortcut[2]
        $ShortcutObject.Description = $Shortcut[3]
        $ShortcutObject.Save()
        Write-Host "  OK Erstellt: $($Shortcut[0])" -ForegroundColor Green
    } else {
        Write-Host "  FEHLER Datei nicht gefunden: $TargetPath" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "OK - Desktop-Verknuepfungen erfolgreich erstellt!" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ordner: $RenLernFolder" -ForegroundColor Yellow
Write-Host ""
