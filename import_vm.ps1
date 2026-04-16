#!/usr/bin/env pwsh
<#
  RenLern Debian VM - Import für Hyper-V
  ════════════════════════════════════════════════════════════════════════════════
  
  Importiert eine exportierte Hyper-V VM und restellt alle Konfigurationen wieder her:
  - VM-Einstellungen (RAM, CPU, Network)
  - Autostart-Konfiguration
  - Optional: Automatisches Starten nach Import
  - Optional: IP-Netzwerk neu konfigurieren
  
  Verwendung:
    .\import_vm.ps1 -VMName "RenLern-Debian" -ImportPath "D:\Backups\RenLern_Export_*" -StartVM
#>

param(
    [string]$VMName = "RenLern-Debian-Restored",
    [string]$ImportPath = "C:\Hyper-V\Exports",
    [switch]$StartVM,
    [switch]$SkipConfiguration
)

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RenLern VM Import - Hyper-V                                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# VORBEREITUNG
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[1/6] Suche Export-Verzeichnis..." -ForegroundColor Yellow

# Wenn genaues Verzeichnis angegeben, nutze es
if (Test-Path (Join-Path $ImportPath "Virtual Machines")) {
    $sourceDir = $ImportPath
    Write-Host "✓ Export gefunden: $ImportPath" -ForegroundColor Green
} 
# Sonst suche nach dem neuesten Export
elseif (Test-Path $ImportPath) {
    $exports = Get-ChildItem -Path $ImportPath -Directory | Where-Object { $_.Name -match "RenLern_Export_" } | Sort-Object -Descending -Property LastWriteTime
    if ($exports) {
        $sourceDir = $exports[0].FullName
        Write-Host "✓ Neueste Export gefunden: $(Split-Path $sourceDir -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "✗ Keinen RenLern-Export in $ImportPath gefunden" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ Import-Pfad nicht gefunden: $ImportPath" -ForegroundColor Red
    exit 1
}

# Lade Konfigurationsdatei
Write-Host "[2/6] Lade Konfigurationsmetadaten..." -ForegroundColor Yellow
$configPath = Join-Path $sourceDir "RenLern_VM_Config.json"
if (Test-Path $configPath) {
    $origConfig = Get-Content $configPath | ConvertFrom-Json
    Write-Host "✓ Konfiguration geladen (Original-VM: $($origConfig.VMName))" -ForegroundColor Green
} else {
    Write-Host "⚠ Keine Konfigurationsdatei gefunden (verwendet Defaults)" -ForegroundColor Yellow
    $origConfig = $null
}

# ═══════════════════════════════════════════════════════════════════════════════
# PRÜFE ZIELKONFLIKT
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[3/6] Prüfe Zielkonflikt..." -ForegroundColor Yellow
$existingVM = Get-VM -Name $VMName -ErrorAction SilentlyContinue
if ($existingVM) {
    Write-Host "⚠ VM '$VMName' existiert bereits" -ForegroundColor Yellow
    $choice = Read-Host "Überschreiben? (j/n)"
    if ($choice -ne 'j' -and $choice -ne 'y') {
        $VMName = Read-Host "Gib neuen VM-Namen ein"
        Write-Host "  Verwende neuen Namen: $VMName" -ForegroundColor Cyan
    } else {
        Write-Host "  Lösche alte VM..." -ForegroundColor Yellow
        Remove-VM -Name $VMName -Force
        Start-Sleep -Seconds 2
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTIERE VM
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[4/6] Importiere VM aus Export..." -ForegroundColor Yellow
try {
    $importedVM = Import-VM -Path (Join-Path $sourceDir "Virtual Machines" "*" "*.vmcx" -Resolve) -Copy -VirtualMachinePath "C:\Hyper-V\$VMName" -SnapshotFilePath "C:\Hyper-V\$VMName" -SmartPagingFilePath "C:\Hyper-V\$VMName"
    
    # Benenne VM um falls unterschiedlich
    if ($importedVM.Name -ne $VMName) {
        Rename-VM -VM $importedVM -NewName $VMName
        $importedVM = Get-VM -Name $VMName
    }
    
    Write-Host "✓ VM importiert: $VMName" -ForegroundColor Green
} catch {
    Write-Host "✗ Import fehlgeschlagen: $_" -ForegroundColor Red
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════════════
# KONFIGURATION WIEDERHERSTELLEN
# ═══════════════════════════════════════════════════════════════════════════════

if (-not $SkipConfiguration -and $origConfig) {
    Write-Host "[5/6] Wende Konfiguration an..." -ForegroundColor Yellow
    
    try {
        # CPU & RAM
        if ($origConfig.ProcessorCount) {
            Set-VMProcessor -VM $importedVM -Count $origConfig.ProcessorCount
            Write-Host "  ✓ Prozessoren: $($origConfig.ProcessorCount)" -ForegroundColor Green
        }
        
        if ($origConfig.MemoryStartup) {
            Set-VMMemory -VM $importedVM -StartupBytes $origConfig.MemoryStartup -DynamicMemoryEnabled $true `
                -MinimumBytes $origConfig.MemoryMinimum -MaximumBytes $origConfig.MemoryMaximum
            
            $ramGB = [math]::Round($origConfig.MemoryStartup / 1GB)
            Write-Host "  ✓ RAM: ${ramGB}GB" -ForegroundColor Green
        }
        
        # Autostart
        if ($origConfig.AutomaticStartAction) {
            Set-VM -VM $importedVM -AutomaticStartAction $origConfig.AutomaticStartAction `
                -AutomaticStopAction $origConfig.AutomaticStopAction
            Write-Host "  ✓ Autostart: $($origConfig.AutomaticStartAction)" -ForegroundColor Green
        }
        
        # Integration Services aktivieren
        if ($origConfig.IntegrationServices) {
            Get-VMIntegrationService -VM $importedVM | Where-Object { $_.Name -in $origConfig.IntegrationServices } | Enable-VMIntegrationService
            Write-Host "  ✓ Integration Services aktiviert" -ForegroundColor Green
        }
        
    } catch {
        Write-Host "  ⚠ Fehler bei Konfiguration anwenden: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "[5/6] Überspringe Konfiguration (--SkipConfiguration)" -ForegroundColor Yellow
}

# ═══════════════════════════════════════════════════════════════════════════════
# NETZWERK KONFIGURIEREN
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[6/6] Konfiguriere Netzwerk..." -ForegroundColor Yellow

$vmAdapters = Get-VMNetworkAdapter -VM $importedVM
if ($vmAdapters -and $origConfig.NetworkAdapters) {
    foreach ($adapter in $vmAdapters) {
        $origAdapter = $origConfig.NetworkAdapters | Select-Object -First 1
        if ($origAdapter.SwitchName) {
            Connect-VMNetworkAdapter -VMNetworkAdapter $adapter -SwitchName $origAdapter.SwitchName -ErrorAction SilentlyContinue
            Write-Host "  ✓ Netzwerk-Switch verbunden" -ForegroundColor Green
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# STARTEN (OPTIONAL)
# ═══════════════════════════════════════════════════════════════════════════════

if ($StartVM) {
    Write-Host ""
    Write-Host "Starte VM..." -ForegroundColor Yellow
    Start-VM -VM $importedVM
    
    Write-Host "✓ VM wird gestartet" -ForegroundColor Green
    Write-Host "  Warte auf Netzwerk-Verbindung..." -ForegroundColor Cyan
    
    # Versuche VM-IP zu bekommen (mit Timeout)
    $maxAttempts = 30
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        $vmAdapter = Get-VMNetworkAdapter -VM $importedVM | Select-Object -First 1
        if ($vmAdapter -and $vmAdapter.IPAddresses) {
            $vmIP = $vmAdapter.IPAddresses[0]
            Write-Host "  ✓ VM-IP: $vmIP" -ForegroundColor Green
            break
        }
        Start-Sleep -Seconds 2
        $attempt++
    }
    
    if (-not $vmIP) {
        Write-Host "  ⚠ VM-IP konnte nicht automatisch ausgelesen werden" -ForegroundColor Yellow
        Write-Host "     In der VM prüfen: ip addr show" -ForegroundColor Gray
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓ VM IMPORT ERFOLGREICH ABGESCHLOSSEN                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "VM-Informationen:" -ForegroundColor Cyan
Write-Host "  📛 Name: $VMName" -ForegroundColor Cyan
Write-Host "  🔧 Pfad: C:\Hyper-V\$VMName" -ForegroundColor Cyan
Write-Host "  💾 Quelle: $(Split-Path $sourceDir -Leaf)" -ForegroundColor Cyan
Write-Host ""

$vm_final = Get-VM -Name $VMName
Write-Host "VM-Status:" -ForegroundColor Cyan
Write-Host "  Zustand: $($vm_final.State)" -ForegroundColor Cyan
Write-Host "  Autostart: $($vm_final.AutomaticStartAction)" -ForegroundColor Cyan

if ($StartVM -and $vmIP) {
    Write-Host ""
    Write-Host "Verbindung:" -ForegroundColor Yellow
    Write-Host "  SSH: ssh root@$vmIP" -ForegroundColor Cyan
    Write-Host "  Web-Terminal: http://${vmIP}:7681" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Tipps:" -ForegroundColor Yellow
Write-Host "  • Neuer Snapshot: Checkpoint-VM -Name '$VMName' -SnapshotName 'Working'"
Write-Host "  • VM stoppen: Stop-VM -Name '$VMName'"
Write-Host "  • VM starten: Start-VM -Name '$VMName'"
Write-Host "  • In Hyper-V Manager öffnen: virtmgmt.msc"
Write-Host ""
