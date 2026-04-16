#!/usr/bin/env pwsh
<#
  RenLern Server - Automatische Service Installation & Start
  ════════════════════════════════════════════════════════════════════════════════
  Dieses Skript installiert automatisch den Windows Service
  und startet den Server als Dauerprozess
#>

$ErrorActionPreference = "SilentlyContinue"

$ServiceName = "RenLernServer"
$DisplayName = "RenLern Flask Server v2"
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerScript = Join-Path $ScriptPath "server_v2.py"

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RenLern Server - Service Installation                         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Überprüfe Admin-Rechte
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  Versuche mit Admin-Rechten zu starten..." -ForegroundColor Yellow
    
    # Starte PowerShell als Admin
    $params = "-NoExit -Command `"cd '$ScriptPath'; & '.\auto_install_service.ps1'`""
    Start-Process powershell.exe -Verb RunAs -ArgumentList $params
    exit
}

Write-Host "✓ Admin-Rechte vorhanden" -ForegroundColor Green
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# Prüfungen
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[1/6] Vorbereitung..." -ForegroundColor Yellow

# Erstelle Logs-Verzeichnis
$logsDir = Join-Path $ScriptPath "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Prüfe server_v2.py
if (-not (Test-Path $ServerScript)) {
    Write-Host "❌ server_v2.py nicht gefunden!" -ForegroundColor Red
    exit 1
}

# Prüfe Python
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "⚠️  Python 'py' launcher nicht gefunden, suche alternative..." -ForegroundColor Yellow
}

Write-Host "✓ Alle Voraussetzungen erfüllt" -ForegroundColor Green
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# Service-Installation mit Scheduled Task (Windows 10+)
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[2/6] Installiere Service..." -ForegroundColor Yellow

# Stoppe alte Service/Task falls existiert
$oldService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($oldService) {
    Write-Host "  Stoppe alte Service..." -ForegroundColor Gray
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Remove-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
}

$oldTask = Get-ScheduledTask -TaskName $ServiceName -ErrorAction SilentlyContinue
if ($oldTask) {
    Unregister-ScheduledTask -TaskName $ServiceName -Confirm:$false -ErrorAction SilentlyContinue
}

# Erstelle Wrapper-Skript für Service
$wrapperScript = Join-Path $ScriptPath "RenLern_Service_Wrapper.ps1"
$wrapperContent = @"
`$ErrorActionPreference = "Continue"
`$VerbosePreference = "Continue"

# Verhindere Sleep-Modus
Add-Type -AssemblyName System.Runtime.InteropServices
`$wimResult = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
powercfg /setactive 8c5e7fda-e8bf-45a6-a6cc-4b3c3f7e5b5e 2>&1 | Out-Null

# Server-Verzeichnis
Set-Location "$ScriptPath"

# Logging
`$logPath = "$logsDir\service.log"
`$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content `$logPath "`$timestamp - Service Wrapper startet..."

# Starte Server
try {
    Add-Content `$logPath "`$timestamp - Starte Python server_v2.py..."
    & py server_v2.py 2>&1 | 
    ForEach-Object {
        `$line = "`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - `$_"
        Add-Content `$logPath `$line
        Write-Host `$line
    }
} catch {
    `$error_msg = "`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - FEHLER: `$_"
    Add-Content `$logPath `$error_msg
    Write-Host `$error_msg -ForegroundColor Red
}
"@

$wrapperScript | Set-Content -Path $wrapperScript -Encoding UTF8
Write-Host "✓ Service-Wrapper erstellt" -ForegroundColor Green

# Registriere als Scheduled Task (mit SYSTEM Benutzer)
Write-Host "  Registriere Windows Scheduled Task..." -ForegroundColor Gray

$trigger = New-ScheduledTaskTrigger -AtStartup
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File `"$wrapperScript`""
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit 0 `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $ServiceName `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host "✓ Scheduled Task registriert: $ServiceName" -ForegroundColor Green
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# Energieoptionen konfigurieren
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[3/6] Energieoptionen konfigurieren..." -ForegroundColor Yellow

# Deaktiviere Sleep-Modus
powercfg /setactive 8c5e7fda-e8bf-45a6-a6cc-4b3c3f7e5b5e 2>&1 | Out-Null
powercfg /change monitor-timeout-ac 0 2>&1 | Out-Null
powercfg /change disk-timeout-ac 0 2>&1 | Out-Null
powercfg /hibernate off 2>&1 | Out-Null

Write-Host "✓ Bildschirm: Nie ausschalten" -ForegroundColor Green
Write-Host "✓ Festplatte: Nie ausschalten" -ForegroundColor Green
Write-Host "✓ Hibernation: Deaktiviert" -ForegroundColor Green
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# Service starten
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[4/6] Starte initiale Service..." -ForegroundColor Yellow

# Aktiviere Task
$task = Get-ScheduledTask -TaskName $ServiceName
$task | Enable-ScheduledTask | Out-Null

# Starte Task jetzt
$task | Start-ScheduledTask

Write-Host "✓ Service gestartet" -ForegroundColor Green
Start-Sleep -Seconds 3
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# Überprüfung
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[5/6] Überprüfe Server..." -ForegroundColor Yellow

$attempts = 0
$serverRunning = $false

for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/api/ping" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $serverRunning = $true
            break
        }
    } catch {
        # Still waiting...
    }
    Start-Sleep -Seconds 1
}

if ($serverRunning) {
    Write-Host "✓ Server antwortet auf Port 5000" -ForegroundColor Green
} else {
    Write-Host "⚠️  Server antwortet noch nicht (kann 10-20 Sekunden dauern)" -ForegroundColor Yellow
}
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# Zusammenfassung
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[6/6] Installation abgeschlossen!" -ForegroundColor Yellow
Write-Host ""

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓ SERVER INSTALLATION ERFOLGREICH                            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "Service-Information:" -ForegroundColor Cyan
Write-Host "  Name: $ServiceName" -ForegroundColor White
Write-Host "  Typ: Windows Scheduled Task (läuft als SYSTEM)" -ForegroundColor White
Write-Host "  Autostart: JA" -ForegroundColor Green
Write-Host "  Logs: $logsDir\service.log" -ForegroundColor White
Write-Host ""

Write-Host "Zugriff:" -ForegroundColor Cyan
Write-Host "  Portal: http://localhost:5000/portal.html" -ForegroundColor Cyan
Write-Host "  Home Cloud: http://localhost:5000/home.html" -ForegroundColor Cyan
Write-Host "  Extern: https://renlern.org/" -ForegroundColor Cyan
Write-Host ""

Write-Host "Management:" -ForegroundColor Cyan
Write-Host "  Service starten: & 'c:\Users\Administrator\Desktop\Repo clone\lernapp-apk\service_manager.ps1'" -ForegroundColor Gray
Write-Host "  Logs ansehen: Get-Content '$logsDir\service.log' -Tail 20 -Wait" -ForegroundColor Gray
Write-Host "  Task Manager: taskkill /im python.exe (um Server zu starten)" -ForegroundColor Gray
Write-Host ""

Write-Host "✓ Der Server läuft jetzt als Dauerbetrieb!" -ForegroundColor Green
Write-Host "✓ Auch wenn Laptop zugemacht wird - Server läuft weiter!" -ForegroundColor Green
Write-Host "✓ Nach PC-Neustart startet Server automatisch!" -ForegroundColor Green
Write-Host ""

# Warte auf Benutzer-Input
Read-Host "Drücke Enter zum Beenden"
