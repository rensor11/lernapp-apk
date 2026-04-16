# RenLern VM Management - Hyper-V Tools
## Vollständiges Backup & Restore System

---

## 📋 Übersicht

Diese Tools ermöglichen **vollständige Verwaltung** einer RenLern Debian VM in Hyper-V:

| Skript | Funktion |
|--------|----------|
| **export_vm.ps1** | Exportiert VM mit allen Konfigurationen |
| **import_vm.ps1** | Importiert VM und stellt Zustand wieder her |
| **vm_manager.ps1** | Interaktives Management-Menü |

---

## 🚀 Schnellstart

### 1. **Backup erstellen**
```powershell
.\export_vm.ps1 -VMName "RenLern-Debian" -ExportPath "C:\Hyper-V\Exports"
```

### 2. **Backup wiederherstellen**
```powershell
.\import_vm.ps1 -VMName "RenLern-Debian-Restored" -ImportPath "C:\Hyper-V\Exports\RenLern_Export_*" -StartVM
```

### 3. **Interaktives Menü öffnen**
```powershell
.\vm_manager.ps1 -VMName "RenLern-Debian" -BackupPath "C:\Hyper-V\Backups"
```
Wähle eine Option:
- [1] Backup erstellen
- [2] Aus Backup wiederherstellen
- [3] VM klonen
- [4] Scheduled Backup
- [5] Alte Backups löschen
- [6] Backup-Info

---

## 📦 export_vm.ps1 - VM Exportieren

### Funktion
- Exportiert eine komplette Hyper-V VM mit allen Einstellungen
- Erstellt Snapshot für konsistente Sicherung
- Speichert Konfigurationsmetadaten
- Optional: Komprimierung für schnellere Übertragung

### Verwendung
```powershell
# Einfaches Backup
.\export_vm.ps1 -VMName "RenLern-Debian" -ExportPath "D:\Backups"

# Mit Komprimierung (ZIP-Datei)
.\export_vm.ps1 -VMName "RenLern-Debian" -ExportPath "D:\Backups" -Compress

# Ohne Cleanup (komprimierte Dateien behalten)
.\export_vm.ps1 -VMName "RenLern-Debian" -ExportPath "D:\Backups" -Compress -NoCleanup
```

### Output
```
Export-Verzeichnis:
  ├── RenLern_Export_20260415_120000/
  │   ├── Virtual Machines/
  │   ├── Virtual Hard Disks/
  │   ├── RenLern_VM_Config.json  (Konfigurationen)
  │   └── README.md
```

### Parameter
| Parameter | Default | Beschreibung |
|-----------|---------|-------------|
| VMName | RenLern-Debian | Name der zu exportierenden VM |
| ExportPath | C:\Hyper-V\Exports | Zielverzeichnis für Export |
| Compress | - | ZIP-Komprimierung aktivieren |
| NoCleanup | - | Original-Dateien nach ZIP behalten |

---

## ↩️ import_vm.ps1 - VM Importieren

### Funktion
- Importiert exportierte VM
- Stellt alle Konfigurationen wieder her (RAM, CPU, Network)
- Optional: Automatisches Starten nach Import
- Neue MAC-Adresse zur Vermeidung von Konflikten

### Verwendung
```powershell
# Grundimport (ohne automatisches Starten)
.\import_vm.ps1 -VMName "RenLern-Restored" -ImportPath "C:\Hyper-V\Exports\RenLern_Export_*"

# Mit automatischem Starten
.\import_vm.ps1 -VMName "RenLern-Restored" -ImportPath "C:\Hyper-V\Exports\RenLern_Export_*" -StartVM

# Ohne Konfigurationswiederherstellung (schneller)
.\import_vm.ps1 -VMName "RenLern-Restored" -ImportPath "C:\Hyper-V\Exports" -SkipConfiguration
```

### Import-Prozess
1. ✓ Export-Verzeichnis findet (neusten, wenn nicht spezifiziert)
2. ✓ Konfigurationsmetadaten lädt
3. ✓ Namenskonflikte prüft
4. ✓ VM importiert
5. ✓ CPU, RAM, Netzwerk konfiguriert
6. ✓ Integration Services aktiviert
7. ✓ Optional: VM startet mit IP-Ausgabe

### Parameter
| Parameter | Default | Beschreibung |
|-----------|---------|-------------|
| VMName | RenLern-Debian-Restored | Name der neuen VM |
| ImportPath | C:\Hyper-V\Exports | Verzeichnis mit Export |
| StartVM | - | VM nach Import starten |
| SkipConfiguration | - | Konfiguration nicht wiederherstellen |

---

## 🎛️ vm_manager.ps1 - Interaktives Management

### Menü-Optionen

#### [1] 📦 Backup erstellen
Erstellt sofortiges Backup der aktuellen VM:
- Fährt VM herunter (wenn läuft)
- Exportiert mit Snapshot
- Speichert mit Timestamp
- Startet VM wieder auf

```powershell
.\vm_manager.ps1 -VMName "RenLern-Debian" -Action "backup"
```

#### [2] ↩️ Aus Backup wiederherstellen
Interaktive Wiederherstellung:
- Listet alle verfügbaren Backups
- Zeigt Größe und Alter
- Ermöglicht Namen für neue VM
- Startet neu

```powershell
.\vm_manager.ps1 -VMName "RenLern-Debian" -Action "restore"
```

#### [3] 🔀 VM klonen
Erstellt identische Kopie der VM:
- Exportiert Original-VM
- Importiert mit neuem Namen
- Separate MAC-Adresse
- Beide VMs können parallel laufen

```powershell
.\vm_manager.ps1 -VMName "RenLern-Debian" -Action "clone"
```

#### [4] ⏰ Scheduled Backup
Automatische Backups nach Zeitplan:
- Täglich um 02:00 Uhr
- Wöchentlich Sonntag 03:00
- Monatlich am 1. um 04:00

Windows Task Scheduler wird automatisch konfiguriert.

#### [5] 🗑️ Alte Backups löschen
Speicherplatz freigeben:
- Backups älter als 30/90 Tage
- Oder: Behalte nur die letzten 5

#### [6] 📋 Backup-Info
Zeigt Backup-Übersicht:
- Dateiname, Größe, Alter
- Gesamter belegter Speicher
- Zeitstempel

---

## 💾 Backup-Strategien

### Empfohlener Workflow (Produktion)

```powershell
# 1. Täglich: Automatisches Backup vor Shutdown
.\vm_manager.ps1 -VMName "RenLern-Debian" -BackupPath "C:\Hyper-V\Backups" -Action "backup"

# 2. Wöchentlich: Scheduled Task (via vm_manager.ps1 Option 4)
# -> Läuft automatisch Sonntag 03:00

# 3. Monatlich: Archivierung auf externem Speicher
robocopy C:\Hyper-V\Backups \\NAS\RenLern_Backups /MIR

# 4. Vierteljährlich: Komprimierte Archivierung
.\export_vm.ps1 -VMName "RenLern-Debian" -ExportPath "C:\Hyper-V\Archive" -Compress
```

### Notfallwiederherstellung (Worst-Case)

```powershell
# 1. Backup-Datei ausfinden
Get-ChildItem C:\Hyper-V\Backups -Directory | Sort-Object CreationTime -Descending | Select -First 5

# 2. Alle laufenden RenLern-VMs stoppen
Get-VM | Where { $_.Name -like "RenLern*" } | Stop-VM -Force

# 3. Importieren unter neuem Namen
.\import_vm.ps1 -VMName "RenLern-Debian-Recovery" -ImportPath "C:\Hyper-V\Backups\RenLern_Export_20260415_120000" -StartVM

# 4. Nach Wiederherstellung: Alte VM löschen (falls nötig)
Remove-VM -Name "RenLern-Debian-Corrupted" -Force
```

---

## 🔐 Sicherheit & Best Practices

### 1. **Backup-Speicherort**
- ✓ Extern: USB, NAS, Cloud
- ✗ Nicht: Auf gleicher Festplatte wie VM
- ✓ Empfohlen: Mehrere Kopien

### 2. **Verschlüsselung**
Sensible Backups verschlüsseln:
```powershell
# Nach dem Export
$backup = "C:\Hyper-V\Backups\RenLern_Export_*"
Protect-CmsMessage -Path $backup -To "Admin@RenLern" -OutFile "$backup.cms"
```

### 3. **Backup-Häufigkeit**
| Szenario | Häufigkeit |
|----------|-----------|
| Produktion | Täglich |
| Test-VM | Wöchentlich |
| Archiv | Monatlich |

### 4. **Alte Backups löschen**
```powershell
# Speicher sparen - nur letzte 10 Backups behalten
.\vm_manager.ps1 -BackupPath "C:\Hyper-V\Backups" -Action "cleanup"
```

---

## 🐛 Troubleshooting

### Problem: "VM not found"
```powershell
# Überprüfe verfügbare VMs
Get-VM | Select-Object Name, State

# Überprüfe Hyper-V Admin-Rechte
Test-Path "\\.\pipe\vmcompute"  # Sollte True sein
```

### Problem: "Nicht genug Speicherplatz"
```powershell
# Backup-Komprimierung nutzen
.\export_vm.ps1 -VMName "RenLern-Debian" -ExportPath "C:\Hyper-V\Exports" -Compress

# Alte Backups löschen
robocopy C:\Hyper-V\Backups D:\Archive_Backup /MOVE
```

### Problem: "Import fehlgeschlagen"
```powershell
# Versuche mit Skip-Configuration
.\import_vm.ps1 -VMName "RenLern-Test" -ImportPath "C:\Hyper-V\Exports" -SkipConfiguration

# Prüfe VHDX-Integrität
Repair-VirtualDisk -Path "C:\Hyper-V\RenLern\Virtual Hard Disks\*.vhdx"
```

### Problem: "VM startet nicht nach Import"
```powershell
# Überprüfe Integration Services
Get-VM "RenLern-Debian-Restored" | Get-VMIntegrationService

# Aktiviere alle Services
Get-VM "RenLern-Debian-Restored" | Get-VMIntegrationService | Enable-VMIntegrationService
```

---

## 📊 Performance-Tipps

### Export optimieren (schneller)
```powershell
# Ohne Snapshot (schneller, aber weniger sicher)
# Beende VM vorher manuell
Stop-VM -Name "RenLern-Debian"
```

### Import optimieren (schneller)
```powershell
# Skip-Configuration für Test-Wiederherstellungen
.\import_vm.ps1 -VMName "RenLern-Test" -ImportPath "..." -SkipConfiguration
```

### Scheduled Backups optimieren
Setze auf off-peak-Zeiten:
```powershell
# Option 4 im vm_manager.ps1 Menü wählen
# -> Zeitplan auf 02:00 Uhr setzen (nachts)
```

---

## 📞 Häufig gestellte Fragen

**F: Kann ich eine VM während eines Backups ändern?**  
A: Nein, die VM wird heruntergefahren. Das komplette Backup dauert typisch 5-15 Minuten je Größe.

**F: Wie lange sind Backups gültig?**  
A: Indefiniert, solange die Festplatte intakt ist. Regelmäßig wiederherstellen (Quartal) um Sicherung zu validieren.

**F: Kann ich mehrere VMs klonen?**  
A: Ja! Option [3] im vm_manager erlaubt unbegrenzte Klone.

**F: Welche Festplatte für Backups?**  
A: Externe USB 3.0+ oder NAS mit Gigabit-Netzwerk empfohlen.

---

## 📝 Changelog

**v1.0** (April 2026)
- Export mit Snapshot & Metadaten
- Import mit Konfigurationswiederherstellung
- VM Kloning Funktion
- Scheduled Backups via Task Scheduler
- Backup-Management & Cleanup
- Umfassende Fehlerbehandlung
