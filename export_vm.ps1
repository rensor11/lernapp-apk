#!/usr/bin/env pwsh
<#
  RenLern Debian VM - Export für Hyper-V
  ════════════════════════════════════════════════════════════════════════════════
  
  Exportiert eine komplette Hyper-V VM mit allen Konfigurationen für:
  - Backup & Wiederherstellung
  - Transfer auf andere Hosts
  - Snapshot für schnelle Rollbacks
  
  Verwendung:
    .\export_vm.ps1 -VMName "RenLern-Debian" -ExportPath "D:\Backups"
#>

param(
    [string]$VMName = "RenLern-Debian",
    [string]$ExportPath = "C:\Hyper-V\Exports",
    [switch]$Compress,
    [switch]$NoCleanup
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$exportDir = Join-Path $ExportPath "RenLern_Export_$timestamp"

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RenLern VM Export - Hyper-V                                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# VORBEREITUNG
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[1/5] Prüfe Hyper-V Administratorzugang..." -ForegroundColor Yellow
try {
    $vm = Get-VM -Name $VMName -ErrorAction Stop
    Write-Host "✓ VM '$VMName' gefunden" -ForegroundColor Green
} catch {
    Write-Host "✗ VM '$VMName' nicht gefunden oder kein Adminzugang" -ForegroundColor Red
    exit 1
}

# Erstelle Export-Verzeichnis
Write-Host "[2/5] Erstelle Export-Verzeichnis..." -ForegroundColor Yellow
if (-not (Test-Path $exportDir)) {
    New-Item -ItemType Directory -Path $exportDir -Force | Out-Null
    Write-Host "✓ Verzeichnis erstellt: $exportDir" -ForegroundColor Green
} else {
    Write-Host "✓ Verzeichnis existiert bereits" -ForegroundColor Green
}

# ═══════════════════════════════════════════════════════════════════════════════
# VM SNAPSHOT & EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[3/5] Snapshot für sichere Export erstelltellen..." -ForegroundColor Yellow

# Fahre VM herunter wenn sie läuft
$vmState = $vm.State
if ($vmState -eq "Running") {
    Write-Host "  ⏹ Fahre VM herunter..." -ForegroundColor Yellow
    Stop-VM -Name $VMName -Force
    Start-Sleep -Seconds 5
}

# Erstelle Snapshot
$snapshotName = "Export_$timestamp"
try {
    Checkpoint-VM -Name $VMName -SnapshotName $snapshotName -ErrorAction SilentlyContinue
    Write-Host "✓ Snapshot erstellt: $snapshotName" -ForegroundColor Green
} catch {
    Write-Host "⚠ Snapshot konnte nicht erstellt werden (nicht kritisch)" -ForegroundColor Yellow
}

# Exportiere VM
Write-Host "[4/5] Exportiere VM..." -ForegroundColor Yellow
try {
    Export-VM -Name $VMName -Path $exportDir
    Write-Host "✓ VM exportiert nach: $exportDir" -ForegroundColor Green
} catch {
    Write-Host "✗ Export fehlgeschlagen: $_" -ForegroundColor Red
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════════════
# METADATEN SPEICHERN
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "[5/5] Speichere Konfigurationsmetadaten..." -ForegroundColor Yellow

$vmConfig = @{
    VMName = $VMName
    ExportTime = Get-Date
    State = $vmState
    ProcessorCount = $vm.ProcessorCount
    MemoryStartup = $vm.MemoryStartup
    MemoryMinimum = $vm.MemoryMinimum
    MemoryMaximum = $vm.MemoryMaximum
    AutomaticStartAction = $vm.AutomaticStartAction
    AutomaticStopAction = $vm.AutomaticStopAction
    IntegrationServices = @($vm.IntegrationServices | Select-Object -ExpandProperty Name)
    NetworkAdapters = @($vm | Get-VMNetworkAdapter | Select-Object -Property Name, SwitchName, MacAddress)
    StorageControllers = @($vm | Get-VMScsiController | Select-Object -Property ControllerNumber, @{N="Drives";E={@($_ | Get-VMHardDiskDrive | Select-Object -ExpandProperty Path)}})
}

$configPath = Join-Path $exportDir "RenLern_VM_Config.json"
$vmConfig | ConvertTo-Json -Depth 10 | Set-Content -Path $configPath
Write-Host "✓ Konfiguration gespeichert: RenLern_VM_Config.json" -ForegroundColor Green

# Speichere auch als Markdown-Übersicht
$readmePath = Join-Path $exportDir "README.md"
@"
# RenLern Debian VM - Export Information

**Exportiert am:** $(Get-Date)

## VM-Konfiguration
- **Name:** $($vmConfig.VMName)
- **Prozessoren:** $($vmConfig.ProcessorCount)
- **RAM:** $([math]::Round($vmConfig.MemoryStartup / 1GB))GB (Min: $([math]::Round($vmConfig.MemoryMinimum / 1GB))GB, Max: $([math]::Round($vmConfig.MemoryMaximum / 1GB))GB)

## VM-Zustand bei Export
- **Status:** $vmState
- **Autostart:** $($vmConfig.AutomaticStartAction)
- **Auto-Stop:** $($vmConfig.AutomaticStopAction)

## Netzwerk
$($vmConfig.NetworkAdapters | ForEach-Object { "- Switch: $($_.SwitchName), MAC: $($_.MacAddress)" } -join "`n")

## Speichergeräte
$($vmConfig.StorageControllers | ForEach-Object { "- SCSI Controller $($_.ControllerNumber): $($_.Drives -join ', ')" } -join "`n")

## Import-Anweisung
Verwende \`import_vm.ps1\` zum Importieren dieser VM:
\`\`\`powershell
.\import_vm.ps1 -VMName "RenLern-Debian" -ImportPath "$(Split-Path $exportDir)" -StartVM
\`\`\`

## Dateien
- \`Virtual Machines/\` - VM-Konfiguration und Runtime-Daten
- \`Virtual Hard Disks/\` - VHDX-Festplattendateien
- \`RenLern_VM_Config.json\` - Detaillierte Konfiguration
- \`README.md\` - Diese Datei
"@ | Set-Content -Path $readmePath
Write-Host "✓ README.md erstellt" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════════════════
# OPTIONAL: KOMPRIMIERUNG
# ═══════════════════════════════════════════════════════════════════════════════

if ($Compress) {
    Write-Host ""
    Write-Host "Komprimiere Export (kann 10-30min dauern)..." -ForegroundColor Yellow
    
    $zipPath = Join-Path $ExportPath "RenLern_Export_$timestamp.zip"
    Compress-Archive -Path $exportDir -DestinationPath $zipPath -CompressionLevel Optimal
    
    Write-Host "✓ Komprimiert: $(([math]::Round((Get-Item $zipPath).Length / 1GB, 2))GB)" -ForegroundColor Green
    Write-Host "  Pfad: $zipPath" -ForegroundColor Cyan
    
    if (-not $NoCleanup) {
        Remove-Item $exportDir -Recurse -Force
        Write-Host "✓ Original-Ordner gelöscht (ZIP erspart Speicherplatz)" -ForegroundColor Green
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# STARTE VM NEU (falls sie ursprünglich lief)
# ═══════════════════════════════════════════════════════════════════════════════

if ($vmState -eq "Running") {
    Write-Host ""
    Write-Host "Starte VM erneut auf..." -ForegroundColor Yellow
    Start-VM -Name $VMName
    Start-Sleep -Seconds 2
    Write-Host "✓ VM läuft wieder" -ForegroundColor Green
}

# ═══════════════════════════════════════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓ VM EXPORT ERFOLGREICH ABGESCHLOSSEN                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

$exportSize = (Get-ChildItem -Path $exportDir -Recurse | Measure-Object -Property Length -Sum).Sum
Write-Host "Export-Informationen:" -ForegroundColor Cyan
Write-Host "  📍 Speicherort: $exportDir" -ForegroundColor Cyan
Write-Host "  💾 Größe: $(([math]::Round($exportSize / 1GB, 2))GB)" -ForegroundColor Cyan
Write-Host "  🕐 Zeit: $timestamp" -ForegroundColor Cyan
Write-Host "  📋 Metadaten: RenLern_VM_Config.json" -ForegroundColor Cyan
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Yellow
Write-Host "  1. Speichere Export an sicherem Ort (USB, Cloud, etc.)"
Write-Host "  2. Zum Importieren: .\import_vm.ps1 -VMName 'RenLern-Debian' -ImportPath '$ExportPath'"
Write-Host "  3. Optional: Backup zum Wiederherstellen nach Änderungen"
Write-Host ""
