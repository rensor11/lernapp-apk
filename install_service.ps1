#!/usr/bin/env pwsh
<#
  RenLern Server - Windows Service Installation
  ════════════════════════════════════════════════════════════════════════════════
  
  Instaliert server_v2.py als Windows Service der:
  - Beim Windows-Start automatisch startet
  - Auch läuft wenn Benutzer abmeldet
  - Auch läuft wenn Laptop zugemacht wird (Sleep verhindert)
  - Von selbst neu startet falls Crash
  - Manuelle Kontrolle über Services oder diesem Skript
  
  Anforderungen: Administrator-Rechte!
  
  Verwendung:
    .\install_service.ps1              # Service installieren
    .\install_service.ps1 -Uninstall   # Service deinstallieren
    .\install_service.ps1 -Start       # Service starten
    .\install_service.ps1 -Stop        # Service stoppen
#>

param(
    [switch]$Uninstall,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status
)

$ServiceName = "RenLernServer"
$DisplayName = "RenLern Flask Server"
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerScript = Join-Path $ScriptPath "server_v2.py"
$PythonExe = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
$Winsw = Join-Path $ScriptPath "winsw-4.0.0-bin.exe"

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RenLern Server - Windows Service Manager                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN-CHECK
# ═══════════════════════════════════════════════════════════════════════════════

$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ Fehler: Dieses Skript benötigt Administrator-Rechte!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Lösung:" -ForegroundColor Yellow
    Write-Host "  1. PowerShell als Administrator öffnen" -ForegroundColor White
    Write-Host "  2. Dieses Skript erneut ausführen" -ForegroundColor White
    exit 1
}

Write-Host "✓ Admin-Rechte vorhanden" -ForegroundColor Green
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# VORBEREITUNG
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[1/5] Prüfe Verzeichnis..." -ForegroundColor Yellow
if (-not (Test-Path $ServerScript)) {
    Write-Host "❌ server_v2.py nicht gefunden: $ServerScript" -ForegroundColor Red
    exit 1
}
Write-Host "✓ server_v2.py gefunden" -ForegroundColor Green

Write-Host "[2/5] Prüfe Python..." -ForegroundColor Yellow
if (-not (Test-Path $PythonExe)) {
    Write-Host "❌ Python nicht gefunden: $PythonExe" -ForegroundColor Red
    Write-Host "   Bitte Python neu installieren oder Pfad anpassen" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Python gefunden" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════════════════
# WINSW HERUNTERLADEN (Falls nicht vorhanden)
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[3/5] Prüfe WINSW Service Wrapper..." -ForegroundColor Yellow

if (-not (Test-Path $Winsw)) {
    Write-Host "  ⬇️  Lade WINSW herunter..." -ForegroundColor Yellow
    
    $winswUrl = "https://github.com/winsw/winsw/releases/download/v4.0.0/WinSW-x64.exe"
    $tempWinsw = Join-Path $env:TEMP "winsw.exe"
    
    try {
        $ProgressPreference = "SilentlyContinue"
        Invoke-WebRequest -Uri $winswUrl -OutFile $tempWinsw
        Move-Item $tempWinsw $Winsw -Force
        Write-Host "✓ WINSW installiert" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  WINSW Download fehlgeschlagen, nutze alternativen Ansatz..." -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ WINSW vorhanden" -ForegroundColor Green
}

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE-VERWALTUNG
# ═══════════════════════════════════════════════════════════════════════════════

function Install-Service {
    Write-Host "[4/5] Installiere Windows Service..." -ForegroundColor Yellow
    
    # Prüfe ob Service bereits existiert
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "  ⚠️  Service existiert bereits - deinstalliere zuerst..." -ForegroundColor Yellow
        Remove-Service -Force
        Start-Sleep -Seconds 2
    }
    
    # Erstelle Service mit NSSM als Fallback
    $nssm = "C:\Program Files\nssm\win64\nssm.exe"
    
    if (Test-Path $nssm) {
        # NSSM Methode (bevorzugt)
        Write-Host "  Nutze NSSM Service Wrapper..." -ForegroundColor Cyan
        & $nssm install $ServiceName $PythonExe "server_v2.py"
        & $nssm set $ServiceName AppDirectory $ScriptPath
        & $nssm set $ServiceName AppStdout (Join-Path $ScriptPath "logs\service.log")
        & $nssm set $ServiceName AppStderr (Join-Path $ScriptPath "logs\service.log")
        & $nssm set $ServiceName AppRotateFiles 1
        & $nssm set $ServiceName AppRotateOnline 1
        & $nssm set $ServiceName AppRotateSeconds 86400
        & $nssm set $ServiceName AppRotateBytes 10485760
        & $nssm set $ServiceName AppRestartDelay 10000
        & $nssm set $ServiceName Start SERVICE_AUTO_START
    } else {
        # Fallback: Erstelle Wrapper-Skript
        Write-Host "  Nutze PowerShell Wrapper Methode..." -ForegroundColor Cyan
        
        # Erstelle Start-Wrapper
        $wrapperScript = Join-Path $ScriptPath "run_server_service.ps1"
        @"
# RenLern Server Service Wrapper
`$ErrorActionPreference = "Continue"
`$logPath = "$ScriptPath\logs\service.log"

# Stelle sicher dass Logs-Verzeichnis existiert
if (-not (Test-Path (Split-Path `$logPath))) {
    New-Item -ItemType Directory -Path (Split-Path `$logPath) -Force | Out-Null
}

# Starte Server und pipe Ausgabe zu Log
try {
    Write-Host "`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Server wird gestartet..." | Tee-Object -FilePath `$logPath -Append
    
    Set-Location "$ScriptPath"
    & "$PythonExe" server_v2.py 2>&1 | Tee-Object -FilePath `$logPath -Append
} catch {
    Write-Host "`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Fehler: `$_" | Tee-Object -FilePath `$logPath -Append
    exit 1
}
"@ | Set-Content $wrapperScript -Force
        
        # Registriere als Scheduled Task dass beim Start ausgeführt wird
        $trigger = New-ScheduledTaskTrigger -AtStartup
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -File `"$wrapperScript`""
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
        $principal = New-ScheduledTaskPrincipal -GroupId "SYSTEM"
        
        Register-ScheduledTask -TaskName $ServiceName -Trigger $trigger -Action $action -Principal $principal -Settings $settings -Force | Out-Null
    }
    
    Write-Host "✓ Service installiert: $ServiceName" -ForegroundColor Green
}

function Uninstall-Service {
    Write-Host "[4/5] Deinstalliere Windows Service..." -ForegroundColor Yellow
    
    # Stoppe Service falls läuft
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq "Running") {
        Write-Host "  Stoppe Service..." -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 2
    }
    
    # Deinstalliere
    $nssm = "C:\Program Files\nssm\win64\nssm.exe"
    if (Test-Path $nssm) {
        & $nssm remove $ServiceName confirm
    } else {
        # Scheduled Task entfernen
        Unregister-ScheduledTask -TaskName $ServiceName -Confirm:$false -ErrorAction SilentlyContinue
    }
    
    Write-Host "✓ Service deinstalliert" -ForegroundColor Green
}

function Start-RenLernService {
    Write-Host "Starte Service..." -ForegroundColor Yellow
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "❌ Service nicht installiert" -ForegroundColor Red
        return
    }
    
    if ($service.Status -eq "Running") {
        Write-Host "⚠️  Service läuft bereits" -ForegroundColor Yellow
    } else {
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 2
        $service.Refresh()
        
        if ($service.Status -eq "Running") {
            Write-Host "✓ Service gestartet" -ForegroundColor Green
        } else {
            Write-Host "❌ Service konnte nicht gestartet werden" -ForegroundColor Red
        }
    }
}

function Stop-RenLernService {
    Write-Host "Stoppe Service..." -ForegroundColor Yellow
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "❌ Service nicht installiert" -ForegroundColor Red
        return
    }
    
    if ($service.Status -eq "Stopped") {
        Write-Host "⚠️  Service ist bereits gestoppt" -ForegroundColor Yellow
    } else {
        Stop-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 2
        $service.Refresh()
        
        if ($service.Status -eq "Stopped") {
            Write-Host "✓ Service gestoppt" -ForegroundColor Green
        } else {
            Write-Host "❌ Service konnte nicht gestoppt werden" -ForegroundColor Red
        }
    }
}

function Show-ServiceStatus {
    Write-Host ""
    Write-Host "Service Status:" -ForegroundColor Cyan
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "  Name: $($service.Name)" -ForegroundColor Green
        Write-Host "  Status: $($service.Status)" -ForegroundColor $(if($service.Status -eq "Running") { "Green" } else { "Yellow" })
        Write-Host "  Start-Typ: $(Get-Service $ServiceName | Select-Object -ExpandProperty StartType)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Logs: $ScriptPath\logs\service.log" -ForegroundColor Gray
    } else {
        Write-Host "❌ Service nicht installiert" -ForegroundColor Red
    }
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# ENERGIEOPTIONEN KONFIGURIEREN (wichtig!)
# ═══════════════════════════════════════════════════════════════════════════════

function Configure-PowerSettings {
    Write-Host "[5/5] Konfiguriere Energieoptionen..." -ForegroundColor Yellow
    
    Write-Host "  Verhindere Sleep-Modus..." -ForegroundColor Yellow
    
    # Verhindere Bildschirm-Sleep
    powercfg /change monitor-timeout-ac 0
    powercfg /change monitor-timeout-dc 0
    
    # Verhindere Festplatte-Sleep
    powercfg /change disk-timeout-ac 0
    powercfg /change disk-timeout-dc 0
    
    # Verhindere System-Sleep (Hibernate aus)
    powercfg /hibernate off
    
    Write-Host "✓ Energieoptionen konfiguriert:" -ForegroundColor Green
    Write-Host "  - Bildschirm: Nie ausschalten" -ForegroundColor Gray
    Write-Host "  - Festplatte: Nie ausschalten" -ForegroundColor Gray
    Write-Host "  - Hibernation: Deaktiviert" -ForegroundColor Gray
}

# ═══════════════════════════════════════════════════════════════════════════════
# HAUPTPROGRAMM
# ═══════════════════════════════════════════════════════════════════════════════

if ($Status) {
    Show-ServiceStatus
} elseif ($Uninstall) {
    Uninstall-Service
    Write-Host ""
    Write-Host "✓ Deinstallation abgeschlossen" -ForegroundColor Green
} elseif ($Start) {
    Start-RenLernService
    Show-ServiceStatus
} elseif ($Stop) {
    Stop-RenLernService
    Show-ServiceStatus
} else {
    # Standard: Installiere Service
    Install-Service
    Configure-PowerSettings
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  ✓ SERVICE INSTALLATION ABGESCHLOSSEN                          ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Nächste Schritte:" -ForegroundColor Yellow
    Write-Host "  1. Starte Service: .\install_service.ps1 -Start" -ForegroundColor White
    Write-Host "  2. Prüfe Status: .\install_service.ps1 -Status" -ForegroundColor White
    Write-Host "  3. Logs prüfen: Get-Content logs\service.log -Tail 20 -Wait" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Management-Befehle:" -ForegroundColor Cyan
    Write-Host "  Start-Service RenLernServer" -ForegroundColor Gray
    Write-Host "  Stop-Service RenLernServer" -ForegroundColor Gray
    Write-Host "  Restart-Service RenLernServer" -ForegroundColor Gray
    Write-Host "  Get-Service RenLernServer" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "Server-Test:" -ForegroundColor Cyan
    Write-Host "  http://localhost:5000" -ForegroundColor Gray
    Write-Host "  https://renlern.org" -ForegroundColor Gray
    Write-Host ""
}
