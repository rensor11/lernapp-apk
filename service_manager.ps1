#!/usr/bin/env pwsh
<#
  RenLern Server - Service Management & Monitoring
  ════════════════════════════════════════════════════════════════════════════════
  
  Verwaltung und Überwachung des RenLern Flask Servers als Windows Service
  
  Menü-Optionen:
    1. Service Status anzeigen
    2. Service starten
    3. Service stoppen
    4. Service neu starten
    5. Logs anzeigen (live)
    6. Server gesundheit prüfen
    7. Energieoptionen prüfen
    8. Service neu installieren
#>

param(
    [string]$Action = "menu"
)

$ServiceName = "RenLernServer"
$LogPath = "$PSScriptRoot\logs\service.log"

# ═══════════════════════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════════

function Show-Menu {
    Clear-Host
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  RenLern Server - Service Management                            ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        $statusColor = if($service.Status -eq "Running") { "Green" } else { "Red" }
        Write-Host "  📊 Service: $($service.Name)" -ForegroundColor Gray
        Write-Host "  🔄 Status: $($service.Status)" -ForegroundColor $statusColor
        Write-Host "  ⚙️  Autostart: $($service.StartType)" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ Service nicht installiert" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "  [1] 📊 Service Status" -ForegroundColor Cyan
    Write-Host "  [2] ▶️  Service starten" -ForegroundColor Cyan
    Write-Host "  [3] ⏹️  Service stoppen" -ForegroundColor Cyan
    Write-Host "  [4] 🔄 Service neu starten" -ForegroundColor Cyan
    Write-Host "  [5] 📋 Logs anzeigen (live)" -ForegroundColor Cyan
    Write-Host "  [6] 💚 Gesundheit prüfen" -ForegroundColor Cyan
    Write-Host "  [7] ⚡ Energieoptionen prüfen" -ForegroundColor Cyan
    Write-Host "  [8] 🛠️  Service neu installieren" -ForegroundColor Cyan
    Write-Host "  [0] ✕ Beenden" -ForegroundColor Gray
    Write-Host ""
}

function Show-Status {
    Write-Host ""
    Write-Host "📊 SERVICE STATUS" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "❌ Service nicht installiert" -ForegroundColor Red
        Read-Host "Drücke Enter zum Zurückgehen"
        return
    }
    
    Write-Host ""
    Write-Host "Service Information:" -ForegroundColor Green
    Write-Host "  Name: $($service.Name)" -ForegroundColor White
    Write-Host "  Display Name: $($service.DisplayName)" -ForegroundColor White
    
    $statusColor = if($service.Status -eq "Running") { "Green" } else { "Yellow" }
    Write-Host "  Status: $($service.Status)" -ForegroundColor $statusColor
    Write-Host "  Start-Typ: $($service.StartType)" -ForegroundColor White
    
    if ($service.Status -eq "Running") {
        try {
            $proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*Python*" -or $_.Name -like "*python*" } | Select-Object -First 1
            if ($proc) {
                Write-Host "  Process ID: $($proc.Id)" -ForegroundColor Cyan
                Write-Host "  Memory: $([math]::Round($proc.WorkingSet / 1MB))MB" -ForegroundColor Cyan
                Write-Host "  CPU (handles): $($proc.HandleCount)" -ForegroundColor Cyan
            }
        } catch {}
    }
    
    Write-Host ""
    Write-Host "Logs:" -ForegroundColor Green
    Write-Host "  Pfad: $LogPath" -ForegroundColor White
    
    if (Test-Path $LogPath) {
        $logSize = (Get-Item $LogPath).Length
        Write-Host "  Größe: $([math]::Round($logSize/1KB))KB" -ForegroundColor White
        Write-Host ""
        Write-Host "  Letzte Einträge:" -ForegroundColor Cyan
        Get-Content $LogPath -Tail 5 | Write-Host -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️  Keine Logs vorhanden" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Read-Host "Drücke Enter zum Fortfahren"
}

function Start-Service-Safe {
    Write-Host ""
    Write-Host "▶️  Service wird gestartet..." -ForegroundColor Yellow
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "❌ Service nicht installiert" -ForegroundColor Red
        Read-Host "Drücke Enter"
        return
    }
    
    if ($service.Status -eq "Running") {
        Write-Host "⚠️  Service läuft bereits" -ForegroundColor Yellow
    } else {
        try {
            Start-Service -Name $ServiceName
            Start-Sleep -Seconds 2
            $service.Refresh()
            
            if ($service.Status -eq "Running") {
                Write-Host "✓ Service erfolgreich gestartet" -ForegroundColor Green
                Write-Host "  http://localhost:5000 sollte jetzt antworten" -ForegroundColor Cyan
            } else {
                Write-Host "❌ Service konnte nicht gestartet werden" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Fehler: $_" -ForegroundColor Red
        }
    }
    
    Read-Host "Drücke Enter zum Fortfahren"
}

function Stop-Service-Safe {
    Write-Host ""
    Write-Host "⏹️  Service wird gestoppt..." -ForegroundColor Yellow
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "❌ Service nicht installiert" -ForegroundColor Red
        Read-Host "Drücke Enter"
        return
    }
    
    if ($service.Status -eq "Stopped") {
        Write-Host "⚠️  Service ist bereits gestoppt" -ForegroundColor Yellow
    } else {
        try {
            Stop-Service -Name $ServiceName -Force
            Start-Sleep -Seconds 2
            $service.Refresh()
            
            if ($service.Status -eq "Stopped") {
                Write-Host "✓ Service erfolgreich gestoppt" -ForegroundColor Green
            } else {
                Write-Host "❌ Service konnte nicht gestoppt werden" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Fehler: $_" -ForegroundColor Red
        }
    }
    
    Read-Host "Drücke Enter zum Fortfahren"
}

function Restart-Service-Safe {
    Write-Host ""
    Write-Host "🔄 Service wird neu gestartet..." -ForegroundColor Yellow
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "❌ Service nicht installiert" -ForegroundColor Red
        Read-Host "Drücke Enter"
        return
    }
    
    try {
        Restart-Service -Name $ServiceName
        Start-Sleep -Seconds 3
        $service.Refresh()
        
        if ($service.Status -eq "Running") {
            Write-Host "✓ Service erfolgreich neu gestartet" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Service Status: $($service.Status)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Fehler: $_" -ForegroundColor Red
    }
    
    Read-Host "Drücke Enter zum Fortfahren"
}

function Show-Logs-Live {
    Write-Host ""
    Write-Host "📋 SERVICE LOGS (LIVE)" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "(Drücke Ctrl+C zum Beenden)" -ForegroundColor Yellow
    Write-Host ""
    
    if (-not (Test-Path $LogPath)) {
        Write-Host "⚠️  Keine Logs vorhanden - Service wurde noch nie ausgeführt" -ForegroundColor Yellow
        Read-Host "Drücke Enter"
        return
    }
    
    try {
        Get-Content $LogPath -Tail 20 -Wait -ErrorAction SilentlyContinue
    } catch {
        Write-Host "❌ Fehler: $_" -ForegroundColor Red
    }
    
    Read-Host "Drücke Enter zum Fortfahren"
}

function Check-Health {
    Write-Host ""
    Write-Host "💚 SERVER GESUNDHEIT" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "❌ Service nicht installiert" -ForegroundColor Red
        Read-Host "Drücke Enter"
        return
    }
    
    Write-Host ""
    Write-Host "1. Service Status..." -ForegroundColor Yellow
    if ($service.Status -eq "Running") {
        Write-Host "   ✓ Service läuft" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Service nicht aktiv" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "2. HTTP Verbindung..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/api/ping" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✓ Server antwortet (HTTP 200)" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Server antwortet mit Code $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ Server antwortet nicht: $_" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "3. Datenbank..." -ForegroundColor Yellow
    $dbPath = "$PSScriptRoot\lernapp.db"
    if (Test-Path $dbPath) {
        $dbSize = (Get-Item $dbPath).Length
        Write-Host "   ✓ Datenbank existiert ($([math]::Round($dbSize/1KB))KB)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Datenbank nicht gefunden" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "4. Speichernutzung..." -ForegroundColor Yellow
    $disk = Get-PSDrive -Name C | Select-Object Used, Free
    $freePercent = [math]::Round(($disk.Free / ($disk.Free + $disk.Used)) * 100)
    Write-Host "   Verbrauchter Speicher: $freePercent% frei" -ForegroundColor $(if($freePercent -gt 20) { "Green" } else { "Yellow" })
    
    Write-Host ""
    Write-Host "5. Netzwerk..." -ForegroundColor Yellow
    $cloudflared = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
    if ($cloudflared) {
        Write-Host "   ✓ Cloudflared Tunnel läuft" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Cloudflared Tunnel nicht aktiv" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Read-Host "Drücke Enter zum Fortfahren"
}

function Check-PowerSettings {
    Write-Host ""
    Write-Host "⚡ ENERGIEOPTIONEN" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    $settings = @(
        @{ Name = "Monitor Timeout (AC)"; Command = "powercfg /query scheme_current sub_video videoidle" },
        @{ Name = "Disk Timeout (AC)"; Command = "powercfg /query scheme_current sub_disk diskidle" },
        @{ Name = "Sleep Timeout (AC)"; Command = "powercfg /query scheme_current sub_sleep standbyidle" }
    )
    
    foreach ($setting in $settings) {
        Write-Host "$($setting.Name):" -ForegroundColor Green
        $result = Invoke-Expression $setting.Command
        if ($result -like "*Possible Setting Index:*") {
            Write-Host "  ✓ Konfigurierbar" -ForegroundColor Green
        } else {
            Write-Host "  $result" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    Write-Host "💡 Empfehlung:" -ForegroundColor Yellow
    Write-Host "  - Monitor: 0 (nie ausschalten)" -ForegroundColor White
    Write-Host "  - Disk: 0 (nie ausschalten)" -ForegroundColor White
    Write-Host "  - Sleep: Deaktiviert" -ForegroundColor White
    Write-Host ""
    
    Read-Host "Drücke Enter zum Fortfahren"
}

function Reinstall-Service {
    Write-Host ""
    Write-Host "Starte Service-Installation..." -ForegroundColor Yellow
    & "$PSScriptRoot\install_service.ps1"
    Read-Host "Drücke Enter zum Fortfahren"
}

# ═══════════════════════════════════════════════════════════════════════════════
# HAUPTPROGRAMM
# ═══════════════════════════════════════════════════════════════════════════════

if ($Action -eq "menu" -or $Action -eq "") {
    while ($true) {
        Show-Menu
        $input = Read-Host "Wahl eingeben"
        
        switch ($input) {
            "1" { Show-Status }
            "2" { Start-Service-Safe }
            "3" { Stop-Service-Safe }
            "4" { Restart-Service-Safe }
            "5" { Show-Logs-Live }
            "6" { Check-Health }
            "7" { Check-PowerSettings }
            "8" { Reinstall-Service }
            "0" { break }
            default { Write-Host "Ungültige Eingabe" -ForegroundColor Red; Read-Host "Drücke Enter" }
        }
    }
} else {
    switch ($Action) {
        "status" { Show-Status }
        "start" { Start-Service-Safe }
        "stop" { Stop-Service-Safe }
        "restart" { Restart-Service-Safe }
        "logs" { Show-Logs-Live }
        "health" { Check-Health }
        default { Write-Host "Unbekannte Aktion: $Action" -ForegroundColor Red }
    }
}
