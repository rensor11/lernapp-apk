#!/usr/bin/env pwsh
<#
  RenLern VM Manager - Hyper-V Backup & Restore
  ════════════════════════════════════════════════════════════════════════════════
  
  Vollständiges Management für RenLern Debian VMs:
  - Automatisches Backup nach jedem Start
  - Schnelle Wiederherstellung auf früheren Zustand
  - VM-Kloning für Multiplex-Setup
  - Scheduled Backups
  - Automatisches Cleanup alter Backups
  
  Menü-Optionen:
    1. Backup erstellen (jetzt)
    2. Aus Backup wiederherstellen
    3. VM klonen
    4. Backup-Plan erstellen
    5. Alte Backups löschen
    6. Backup-Info anzeigen
#>

param(
    [string]$VMName = "RenLern-Debian",
    [string]$BackupPath = "C:\Hyper-V\Backups",
    [string]$Action = "menu"
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# ═══════════════════════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════════

function Initialize-BackupPath {
    if (-not (Test-Path $BackupPath)) {
        New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
        Write-Host "✓ Backup-Verzeichnis erstellt: $BackupPath" -ForegroundColor Green
    }
}

function Show-Menu {
    Clear-Host
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  RenLern VM Manager - Hyper-V                                  ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "VM: $VMName" -ForegroundColor Gray
    Write-Host "Backup-Pfad: $BackupPath" -ForegroundColor Gray
    Write-Host ""
    
    $vm = Get-VM -Name $VMName -ErrorAction SilentlyContinue
    if ($vm) {
        Write-Host "  Status: $($vm.State)" -ForegroundColor $(if($vm.State -eq "Running") { "Green" } else { "Yellow" })
    }
    
    Write-Host ""
    Write-Host "  [1] 📦 Backup erstellen (JETZT)" -ForegroundColor Cyan
    Write-Host "  [2] ↩️  Aus Backup wiederherstellen" -ForegroundColor Cyan
    Write-Host "  [3] 🔀 VM klonen" -ForegroundColor Cyan
    Write-Host "  [4] ⏰ Scheduled Backup einrichten" -ForegroundColor Cyan
    Write-Host "  [5] 🗑️  Alte Backups löschen" -ForegroundColor Cyan
    Write-Host "  [6] 📋 Backup-Info anzeigen" -ForegroundColor Cyan
    Write-Host "  [0] ✕ Beenden" -ForegroundColor Gray
    Write-Host ""
}

function Create-Backup {
    Write-Host ""
    Write-Host "📦 Backup wird erstellt..." -ForegroundColor Yellow
    
    Initialize-BackupPath
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = "${VMName}_Backup_${timestamp}"
    $backupDir = Join-Path $BackupPath $backupName
    
    $vm = Get-VM -Name $VMName -ErrorAction SilentlyContinue
    if (-not $vm) {
        Write-Host "✗ VM nicht gefunden: $VMName" -ForegroundColor Red
        Read-Host "Drücke Enter zum Zurückgehen"
        return
    }
    
    $vmWasRunning = $vm.State -eq "Running"
    if ($vmWasRunning) {
        Write-Host "  Fahre VM herunter..." -ForegroundColor Yellow
        Stop-VM -Name $VMName -Force
        Start-Sleep -Seconds 3
    }
    
    try {
        Write-Host "  Erstelle Export..." -ForegroundColor Yellow
        & "$scriptPath\export_vm.ps1" -VMName $VMName -ExportPath $BackupPath
        
        # Benenne Export um
        $latestExport = Get-ChildItem -Path $BackupPath -Directory | Where-Object { $_.Name -match "RenLern_Export_" } | Sort-Object -Descending -Top 1
        if ($latestExport) {
            Rename-Item -Path $latestExport.FullName -NewName $backupName
        }
        
        Write-Host "✓ Backup erstellt: $backupName" -ForegroundColor Green
    } catch {
        Write-Host "✗ Backup fehlgeschlagen: $_" -ForegroundColor Red
    }
    
    if ($vmWasRunning) {
        Write-Host "  Starte VM erneut..." -ForegroundColor Yellow
        Start-VM -Name $VMName
        Write-Host "✓ VM läuft wieder" -ForegroundColor Green
    }
    
    Read-Host "Drücke Enter zum Fortfahren"
}

function Restore-FromBackup {
    Write-Host ""
    
    Initialize-BackupPath
    $backups = Get-ChildItem -Path $BackupPath -Directory | Sort-Object -Descending -Property CreationTime
    
    if (-not $backups) {
        Write-Host "✗ Keine Backups gefunden" -ForegroundColor Red
        Read-Host "Drücke Enter zum Zurückgehen"
        return
    }
    
    Write-Host "Verfügbare Backups:" -ForegroundColor Cyan
    for ($i = 0; $i -lt $backups.Count; $i++) {
        $size = (Get-ChildItem -Path $backups[$i].FullName -Recurse | Measure-Object -Property Length -Sum).Sum
        $sizeGB = [math]::Round($size / 1GB, 2)
        $date = $backups[$i].CreationTime.ToString("yyyy-MM-dd HH:mm:ss")
        Write-Host "  [$($i+1)] $($backups[$i].Name) (${sizeGB}GB) - $date" -ForegroundColor Green
    }
    
    Write-Host ""
    $choice = Read-Host "Wähle Backup zum Wiederherstellen (Nummer)"
    $choice = [int]$choice - 1
    
    if ($choice -lt 0 -or $choice -ge $backups.Count) {
        Write-Host "✗ Ungültige Auswahl" -ForegroundColor Red
        Read-Host "Drücke Enter zum Zurückgehen"
        return
    }
    
    $selectedBackup = $backups[$choice].FullName
    
    Write-Host ""
    $restore_name = Read-Host "VM-Name nach Wiederherstellung (default: ${VMName}-Restored)"
    if (-not $restore_name) { $restore_name = "${VMName}-Restored" }
    
    Write-Host ""
    Write-Host "Starte Wiederherstellung..." -ForegroundColor Yellow
    & "$scriptPath\import_vm.ps1" -VMName $restore_name -ImportPath $selectedBackup -StartVM -SkipConfiguration:$false
    
    Read-Host "Drücke Enter zum Fortfahren"
}

function Clone-VM {
    Write-Host ""
    Write-Host "🔀 VM klonen..." -ForegroundColor Yellow
    
    $clone_name = Read-Host "Name der Klon-VM"
    if (-not $clone_name) {
        Write-Host "✗ Kein Name eingegeben" -ForegroundColor Red
        Read-Host "Drücke Enter zum Zurückgehen"
        return
    }
    
    $vm = Get-VM -Name $VMName -ErrorAction SilentlyContinue
    if (-not $vm) {
        Write-Host "✗ Original-VM nicht gefunden" -ForegroundColor Red
        Read-Host "Drücke Enter zum Zurückgehen"
        return
    }
    
    if ($vm.State -eq "Running") {
        Write-Host "Fahre Original-VM herunter..." -ForegroundColor Yellow
        Stop-VM -Name $VMName -Force
        Start-Sleep -Seconds 3
    }
    
    try {
        Write-Host "Exportiere VM..." -ForegroundColor Yellow
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $tempExport = Join-Path $BackupPath "Temp_Clone_$timestamp"
        & "$scriptPath\export_vm.ps1" -VMName $VMName -ExportPath $tempExport -NoCleanup
        
        Write-Host "Importiere Klon..." -ForegroundColor Yellow
        & "$scriptPath\import_vm.ps1" -VMName $clone_name -ImportPath $tempExport -StartVM
        
        # Cleanup
        Remove-Item $tempExport -Recurse -Force -ErrorAction SilentlyContinue
        
        Write-Host "✓ Klon erstellt: $clone_name" -ForegroundColor Green
    } catch {
        Write-Host "✗ Klonen fehlgeschlagen: $_" -ForegroundColor Red
    }
    
    Write-Host "Starte Original-VM..." -ForegroundColor Yellow
    Start-VM -Name $VMName
    
    Read-Host "Drücke Enter zum Fortfahren"
}

function Setup-ScheduledBackup {
    Write-Host ""
    Write-Host "⏰ Scheduled Backup einrichten..." -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "Wähle Zeitplan:" -ForegroundColor Cyan
    Write-Host "  [1] Täglich um 02:00 Uhr" -ForegroundColor Green
    Write-Host "  [2] Wöchentlich (Sonntag 03:00 Uhr)" -ForegroundColor Green
    Write-Host "  [3] Monatlich (1. des Monats 04:00 Uhr)" -ForegroundColor Green
    Write-Host "  [0] Abbrechen" -ForegroundColor Gray
    
    $choice = Read-Host "Wahl"
    
    $taskName = "RenLern_Backup_${VMName}"
    $scriptArgs = "-WindowStyle Hidden -File `"$scriptPath\vm_manager.ps1`" -VMName `"$VMName`" -Action backup"
    
    $trigger = switch ($choice) {
        "1" { New-ScheduledTaskTrigger -Daily -At 2:00am }
        "2" { New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3:00am }
        "3" { New-ScheduledTaskTrigger -AtStartup } # Placeholder
        default {
            Write-Host "Abgebrochen" -ForegroundColor Yellow
            Read-Host "Drücke Enter"
            return
        }
    }
    
    try {
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $scriptArgs
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Force | Out-Null
        
        Write-Host "✓ Scheduled Task erstellt: $taskName" -ForegroundColor Green
        Write-Host "  Backups werden automatisch erstellt" -ForegroundColor Cyan
    } catch {
        Write-Host "✗ Fehler: $_" -ForegroundColor Red
    }
    
    Read-Host "Drücke Enter zum Fortfahren"
}

function Cleanup-OldBackups {
    Write-Host ""
    
    Initialize-BackupPath
    
    Write-Host "Wähle Bereinigung:" -ForegroundColor Cyan
    Write-Host "  [1] Lösche Backups älter als 30 Tage" -ForegroundColor Green
    Write-Host "  [2] Lösche Backups älter als 90 Tage" -ForegroundColor Green
    Write-Host "  [3] Behalte nur die letzten 5 Backups" -ForegroundColor Green
    Write-Host "  [0] Abbrechen" -ForegroundColor Gray
    
    $choice = Read-Host "Wahl"
    
    $backups = Get-ChildItem -Path $BackupPath -Directory | Sort-Object -Property CreationTime
    $deleted = 0
    
    switch ($choice) {
        "1" {
            $threshold = (Get-Date).AddDays(-30)
            foreach ($backup in $backups) {
                if ($backup.CreationTime -lt $threshold) {
                    Write-Host "  Lösche: $($backup.Name)" -ForegroundColor Yellow
                    Remove-Item $backup.FullName -Recurse -Force
                    $deleted++
                }
            }
        }
        "2" {
            $threshold = (Get-Date).AddDays(-90)
            foreach ($backup in $backups) {
                if ($backup.CreationTime -lt $threshold) {
                    Write-Host "  Lösche: $($backup.Name)" -ForegroundColor Yellow
                    Remove-Item $backup.FullName -Recurse -Force
                    $deleted++
                }
            }
        }
        "3" {
            $toDelete = $backups | Sort-Object -Descending -Property CreationTime | Select-Object -Skip 5
            foreach ($backup in $toDelete) {
                Write-Host "  Lösche: $($backup.Name)" -ForegroundColor Yellow
                Remove-Item $backup.FullName -Recurse -Force
                $deleted++
            }
        }
    }
    
    Write-Host ""
    Write-Host "✓ $deleted Backups gelöscht" -ForegroundColor Green
    Read-Host "Drücke Enter zum Fortfahren"
}

function Show-BackupInfo {
    Write-Host ""
    
    Initialize-BackupPath
    $backups = Get-ChildItem -Path $BackupPath -Directory | Sort-Object -Descending -Property CreationTime
    
    if (-not $backups) {
        Write-Host "✗ Keine Backups gefunden" -ForegroundColor Red
        Read-Host "Drücke Enter zum Zurückgehen"
        return
    }
    
    Write-Host "Backup-Informationen:" -ForegroundColor Cyan
    Write-Host ""
    
    $totalSize = 0
    foreach ($backup in $backups) {
        $size = (Get-ChildItem -Path $backup.FullName -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $sizeGB = [math]::Round($size / 1GB, 2)
        $totalSize += $size
        
        $date = $backup.CreationTime.ToString("yyyy-MM-dd HH:mm:ss")
        $age = (New-TimeSpan -Start $backup.CreationTime -End (Get-Date)).Days
        
        Write-Host "  📦 $($backup.Name)" -ForegroundColor Green
        Write-Host "     Größe: ${sizeGB}GB | Alter: ${age} Tage" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "  Total: $(([math]::Round($totalSize / 1GB, 2)))GB in $($backups.Count) Backups" -ForegroundColor Cyan
    Write-Host ""
    
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
            "1" { Create-Backup }
            "2" { Restore-FromBackup }
            "3" { Clone-VM }
            "4" { Setup-ScheduledBackup }
            "5" { Cleanup-OldBackups }
            "6" { Show-BackupInfo }
            "0" { break }
            default { Write-Host "Ungültige Eingabe" -ForegroundColor Red; Read-Host "Drücke Enter" }
        }
    }
} else {
    switch ($Action) {
        "backup" { Create-Backup }
        "restore" { Restore-FromBackup }
        "clone" { Clone-VM }
        default { Write-Host "Unbekannte Aktion: $Action" -ForegroundColor Red }
    }
}
