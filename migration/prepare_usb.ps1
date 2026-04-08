# USB-Stick vorbereiten (Windows PowerShell)
# ============================================
# Dieses Skript kopiert alle Migrations-Dateien auf den USB-Stick.
#
# VORAUSSETZUNG:
#   - Debian 12 ISO bereits mit Rufus/balenaEtcher auf den USB geschrieben
#   - ODER: Separater USB-Stick / zweite Partition fuer die Dateien
#
# BENUTZUNG:
#   1. USB-Stick einstecken
#   2. Laufwerksbuchstaben unten anpassen (z.B. D:, E:, F:)
#   3. PowerShell als Admin oeffnen
#   4. Ausfuehren:  .\prepare_usb.ps1
#
# ============================================

# === HIER ANPASSEN ===
$USBDrive = "E:"
# =====================

$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetDir = "$USBDrive\migrations_guide"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " LernApp USB-Stick Vorbereitung" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle:  $SourceDir"
Write-Host "Ziel:    $TargetDir"
Write-Host ""

# Sicherheitsabfrage
$confirm = Read-Host "USB-Stick Laufwerk ist $USBDrive - korrekt? (j/n)"
if ($confirm -ne "j") {
    Write-Host "Abgebrochen. Bitte USB-Laufwerk oben anpassen." -ForegroundColor Yellow
    exit
}

# Zielordner erstellen
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
New-Item -ItemType Directory -Path "$TargetDir\app_files" -Force | Out-Null

# Skripte kopieren
Write-Host ""
Write-Host "[1/3] Skripte kopieren..." -ForegroundColor Green
$scripts = @(
    "INSTALL.sh",
    "01_setup_debian_server.sh",
    "02_deploy_services.sh",
    "03_service_manager.sh",
    "04_backup_vm.sh",
    "cloudflared_config_template.yml",
    "MIGRATION_GUIDE.md",
    "KURZANLEITUNG.txt"
)
foreach ($file in $scripts) {
    $src = Join-Path $SourceDir $file
    if (Test-Path $src) {
        Copy-Item $src "$TargetDir\$file" -Force
        Write-Host "  OK: $file" -ForegroundColor Gray
    } else {
        Write-Host "  SKIP: $file (nicht gefunden)" -ForegroundColor Yellow
    }
}

# App-Dateien kopieren
Write-Host ""
Write-Host "[2/3] App-Dateien kopieren..." -ForegroundColor Green
$appFiles = @(
    "server_neu.py",
    "flask_server.py",
    "fragenpool.json",
    "lernapp.html",
    "server.js",
    "package.json",
    "server.py"
)
foreach ($file in $appFiles) {
    $src = Join-Path "$SourceDir\app_files" $file
    if (Test-Path $src) {
        Copy-Item $src "$TargetDir\app_files\$file" -Force
        Write-Host "  OK: app_files\$file" -ForegroundColor Gray
    } else {
        Write-Host "  SKIP: app_files\$file (nicht gefunden)" -ForegroundColor Yellow
    }
}

# Backup von alter VM (falls vorhanden)
Write-Host ""
Write-Host "[3/3] Backup-Archiv suchen..." -ForegroundColor Green
$backups = Get-ChildItem -Path $SourceDir -Filter "lernapp_migration_*.tar.gz" -ErrorAction SilentlyContinue
if ($backups) {
    foreach ($bak in $backups) {
        Copy-Item $bak.FullName "$TargetDir\" -Force
        Write-Host "  OK: $($bak.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "  Kein Backup-Archiv gefunden (optional)." -ForegroundColor Yellow
}

# Fertig
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " USB-Stick ist bereit!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Nach Debian-Installation auf dem Laptop:" -ForegroundColor Cyan
Write-Host "  1. USB einstecken" -ForegroundColor White
Write-Host "  2. mount /dev/sdb1 /mnt" -ForegroundColor White
Write-Host "  3. cd /mnt/migrations_guide" -ForegroundColor White
Write-Host "  4. bash INSTALL.sh" -ForegroundColor White
Write-Host ""
Write-Host "Das war's! Alles andere macht das Skript." -ForegroundColor Green
