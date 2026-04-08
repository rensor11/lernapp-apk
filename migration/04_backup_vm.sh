#!/bin/bash
###############################################################################
# 04_backup_vm.sh
# Exportiert alle Daten & Konfigurationen aus der aktuellen VM
# fuer die Migration zum neuen Server.
# Ausfuehren als root auf der ALTEN VM:  bash 04_backup_vm.sh
###############################################################################
set -euo pipefail

BACKUP_DIR="/tmp/lernapp_migration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "=== Migrations-Backup gestartet: $(date) ==="
echo "=== Ziel: $BACKUP_DIR ==="

# 1. App-Dateien
echo "[1/6] App-Dateien sichern..."
if [ -d /opt/lernapp ]; then
  cp -r /opt/lernapp "$BACKUP_DIR/app_files"
  echo "  -> /opt/lernapp gesichert."
fi

# 2. Datenbank
echo "[2/6] SQLite-Datenbank sichern..."
find /opt/lernapp -name "*.db" -exec cp {} "$BACKUP_DIR/" \; 2>/dev/null || true
echo "  -> Datenbanken gesichert."

# 3. Cloudflared-Konfiguration
echo "[3/6] Cloudflared-Konfiguration sichern..."
for USER_HOME in /home/*; do
  if [ -d "$USER_HOME/.cloudflared" ]; then
    cp -r "$USER_HOME/.cloudflared" "$BACKUP_DIR/cloudflared_config"
    echo "  -> $USER_HOME/.cloudflared gesichert."
  fi
done
if [ -d /etc/cloudflared ]; then
  cp -r /etc/cloudflared "$BACKUP_DIR/cloudflared_etc"
fi

# 4. SSH-Schluessel & Konfiguration
echo "[4/6] SSH-Konfiguration sichern..."
mkdir -p "$BACKUP_DIR/ssh"
cp /etc/ssh/sshd_config "$BACKUP_DIR/ssh/" 2>/dev/null || true
# Authorized keys fuer alle User
for USER_HOME in /home/*; do
  USERNAME=$(basename "$USER_HOME")
  if [ -f "$USER_HOME/.ssh/authorized_keys" ]; then
    mkdir -p "$BACKUP_DIR/ssh/$USERNAME"
    cp "$USER_HOME/.ssh/authorized_keys" "$BACKUP_DIR/ssh/$USERNAME/"
  fi
done
echo "  -> SSH-Konfiguration gesichert."

# 5. systemd-Services
echo "[5/6] systemd-Service-Dateien sichern..."
mkdir -p "$BACKUP_DIR/systemd"
cp /etc/systemd/system/lernapp-*.service "$BACKUP_DIR/systemd/" 2>/dev/null || true
cp /etc/systemd/system/cloudflared-*.service "$BACKUP_DIR/systemd/" 2>/dev/null || true
echo "  -> Service-Dateien gesichert."

# 6. Installierte Pakete auflisten
echo "[6/6] Paketliste erstellen..."
dpkg --get-selections > "$BACKUP_DIR/installed_packages.txt"
pip3 list --format=freeze > "$BACKUP_DIR/pip_packages.txt" 2>/dev/null || true
[ -f /opt/lernapp/venv/bin/pip ] && /opt/lernapp/venv/bin/pip list --format=freeze > "$BACKUP_DIR/pip_venv_packages.txt" 2>/dev/null || true
echo "  -> Paketlisten erstellt."

# Archiv erstellen
echo ""
echo "Erstelle Archiv..."
ARCHIVE="/tmp/lernapp_migration_$(date +%Y%m%d).tar.gz"
tar -czf "$ARCHIVE" -C /tmp "$(basename "$BACKUP_DIR")"

echo ""
echo "=========================================="
echo " Backup abgeschlossen!"
echo " Archiv: $ARCHIVE"
echo " Groesse: $(du -h "$ARCHIVE" | cut -f1)"
echo ""
echo " Transfer zum neuen Server:"
echo "   scp -P 8022 $ARCHIVE user@NEUER_SERVER:/tmp/"
echo "=========================================="
