#!/usr/bin/env pwsh
<#
  RenLern Debian VM Setup für Hyper-V
  ═════════════════════════════════════
  - VM-Image erstellen oder einbinden
  - SSH-Zugang konfigurieren
  - yt-dlp installieren
  - Web-Terminal (ttyd) installieren
  - Automatische Startup-Startup konfigurieren
#>

param(
    [string]$VMName = "RenLern-Debian",
    [string]$VHDX = "C:\Hyper-V\RenLern-Debian.vhdx",
    [string]$VHDSize = 100GB,
    [string]$NetworkSwitch = "Default Switch"
)

Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Debian VM Setup für RenLern Server                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════════════
# HYPER-V CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host "⏳ Überprüfe Hyper-V..." -ForegroundColor Yellow
$hypervFeature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V
if ($hypervFeature.State -ne "Enabled") {
    Write-Host "❌ Hyper-V ist nicht aktiviert!" -ForegroundColor Red
    Write-Host "Aktiviere es mit: Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Hyper-V ist aktiviert" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════════════════
# VM PRÜFUNG
# ═══════════════════════════════════════════════════════════════════════════════

$vm = Get-VM -Name $VMName -ErrorAction SilentlyContinue
if ($vm) {
    Write-Host "ℹ️  VM '$VMName' existiert bereits" -ForegroundColor Cyan
    Write-Host "Starte die VM und fahre fort..." -ForegroundColor Cyan
    Start-VM -Name $VMName -ErrorAction SilentlyContinue
} else {
    Write-Host "⚠️  VM '$VMName' nicht gefunden - Download ISO unter:" -ForegroundColor Yellow
    Write-Host "   https://www.debian.org/download" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Anleitung:" -ForegroundColor Yellow
    Write-Host "1. ISO herunterladen (Debian 12 Bookworm)" -ForegroundColor White
    Write-Host "2. Neue VM in Hyper-V Manager erstellen" -ForegroundColor White
    Write-Host "3. Debian installieren (minimal, SSH während Installation aktivieren)" -ForegroundColor White
    Write-Host "4. Dieses Skript erneut ausführen" -ForegroundColor White
    Read-Host "Drücke Enter wenn VM ready ist..."
}

# ═══════════════════════════════════════════════════════════════════════════════
# SSH VORBEREITUNG (Windows-seitig für Remote-Zugriff)
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "🔑 SSH Zugang konfigurieren..." -ForegroundColor Yellow

# VM-IP auslesen
$vmAdapter = Get-VMNetworkAdapter -VMName $VMName
if ($vmAdapter.IPAddresses) {
    $vmIP = $vmAdapter.IPAddresses[0]
    Write-Host "✅ VM-IP: $vmIP" -ForegroundColor Green
} else {
    Write-Host "⚠️  VM-IP konnte nicht automatisch ausgelesen werden" -ForegroundColor Yellow
    Write-Host "In der VM: ip addr show" -ForegroundColor Cyan
    $vmIP = Read-Host "Gib die VM-IP manuell ein"
}

# SSH Key für Windows (falls nicht vorhanden)
$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"
if (-not (Test-Path $sshKeyPath)) {
    Write-Host ""
    Write-Host "🔐 Erstelle SSH-Keys..." -ForegroundColor Yellow
    ssh-keygen -t rsa -N "" -f $sshKeyPath -C "renlern@$env:COMPUTERNAME"
    Write-Host "✅ SSH-Keys erstellt" -ForegroundColor Green
    Write-Host "Öffentlicher Key:" -ForegroundColor Cyan
    Get-Content "$sshKeyPath.pub"
}

# ═══════════════════════════════════════════════════════════════════════════════
# DEBIAN-SEITIGES SETUP (per SSH)
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "📦 Installiere Software auf Debian..." -ForegroundColor Yellow
Write-Host "Benutzer: root oder sudo-Benutzer?" -ForegroundColor Cyan
$sshUser = Read-Host "Benutzername (default: root)"
if (-not $sshUser) { $sshUser = "root" }

# SSH-Credentials für automatisierte Verbindung
# (Manueller SSH-Zugang wird empfohlen für bessere Sicherheit)

Write-Host ""
Write-Host "💡 Führe diese Befehle auf der Debian-VM aus:" -ForegroundColor Yellow
$setupScript = @"
#!/bin/bash
set -e

echo "🔄 Update Paketlisten..."
sudo apt-get update

echo "📦 Installiere Basis-Tools..."
sudo apt-get install -y curl wget git openssh-server openssh-client

echo "📥 Installiere yt-dlp..."
sudo apt-get install -y yt-dlp

echo "🌐 Installiere Web-Terminal (ttyd)..."
# Aus Quellen bauen (einfache Alternative)
sudo apt-get install -y build-essential cmake git libwebsockets-dev libjson-c-dev libssl-dev
git clone https://github.com/tsl0922/ttyd.git /tmp/ttyd
cd /tmp/ttyd
mkdir build && cd build
cmake ..
make && sudo make install

echo "🖥️  Starte ttyd Web-Terminal..."
ttyd -p 7681 /bin/bash &

echo "📝 Erstelle Systemd-Service für ttyd..."
sudo tee /etc/systemd/system/ttyd.service > /dev/null <<'EOF'
[Unit]
Description=TTY Daemon Web Terminal
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/ttyd -p 7681 /bin/bash
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ttyd
sudo systemctl start ttyd

echo "✅ Debian-Setup abgeschlossen!"
echo ""
echo "Services laufen auf:"
echo "  SSH:        $vmIP:22"
echo "  ttyd-Web:   http://$vmIP:7681"
echo "  yt-dlp:     yt-dlp [options] <URL>"
"@

Write-Host $setupScript -ForegroundColor Cyan
Write-Host ""

# Option: Script direkt ausführen falls SSH verfügbar
$choice = Read-Host "Script direkt ausführen? (j/n)"
if ($choice -eq 'j' -or $choice -eq 'y') {
    Write-Host ""
    Write-Host "⏳ Verbinde zu VM ($vmIP)..." -ForegroundColor Yellow
    
    # Script in Datei schreiben und üertragen
    $scriptPath = "$env:TEMP\debian_setup.sh"
    Set-Content -Path $scriptPath -Value $setupScript
    
    try {
        # SCP zum Übertragen (erfordert SSH-Zugang)
        & scp -o StrictHostKeyChecking=no "$scriptPath" "${sshUser}@${vmIP}:/tmp/setup.sh"
        & ssh -o StrictHostKeyChecking=no "${sshUser}@${vmIP}" "bash /tmp/setup.sh"
        Write-Host "✅ Setup erfolgreich abgeschlossen!" -ForegroundColor Green
    } catch {
        Write-Host "❌ SSH-Fehler: $_" -ForegroundColor Red
        Write-Host "Kopiere das Script manuell auf die VM" -ForegroundColor Yellow
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# HYPER-V AUTOSTART
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "⚡ Konfiguriere Autostart..." -ForegroundColor Yellow

$vm = Get-VM -Name $VMName
$vm | Set-VM -AutomaticStartAction Start -AutomaticStartDelay 10 -AutomaticStopAction SaveState

Write-Host "✅ VM startet automatisch mit Windows" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ═══════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          ✅ Setup Abgeschlossen!                   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "VM Details:" -ForegroundColor Cyan
Write-Host "  Name:      $VMName" -ForegroundColor White
Write-Host "  IP:        $vmIP" -ForegroundColor White
Write-Host "  SSH:       ssh root@$vmIP" -ForegroundColor White
Write-Host ""
Write-Host "Dienste:" -ForegroundColor Cyan
Write-Host "  Web-Terminal: http://$vmIP:7681" -ForegroundColor White
Write-Host "  yt-dlp:       Zur Download von Videos/Audio" -ForegroundColor White
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Yellow
Write-Host "  1. SSH-Zugang testen: ssh root@$vmIP" -ForegroundColor White
Write-Host "  2. Web-Terminal öffnen: http://$vmIP:7681" -ForegroundColor White
Write-Host "  3. Videos downloaden: yt-dlp -f best https://..." -ForegroundColor White
Write-Host ""
