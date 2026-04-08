#!/bin/bash
###############################################################################
# 01_setup_debian_server.sh
# Richtet einen frischen Debian-12-Server (Bare-Metal / VM) komplett ein.
# Ausfuehren als root:  bash 01_setup_debian_server.sh
###############################################################################
set -euo pipefail

LOG="/var/log/lernapp_setup.log"
exec > >(tee -a "$LOG") 2>&1
echo "=== LernApp Server-Setup gestartet: $(date) ==="

# ---------- Variablen (bei Bedarf anpassen) ----------
APP_USER="lernapp"
APP_DIR="/opt/lernapp"
DOMAIN="renlern.org"
SSH_PORT=8022
FLASK_PORT=5000

###############################################################################
# 1. System-Update & Grundpakete
###############################################################################
echo "[1/8] System-Update & Grundpakete installieren..."
apt-get update -y
apt-get upgrade -y
apt-get install -y \
  curl wget git sudo ufw fail2ban htop tmux unzip \
  python3 python3-pip python3-venv python3-dev \
  sqlite3 \
  build-essential libffi-dev libssl-dev \
  ca-certificates gnupg lsb-release \
  openssh-server

###############################################################################
# 2. SSH haerten
###############################################################################
echo "[2/8] SSH auf Port $SSH_PORT konfigurieren..."
sed -i "s/^#\?Port .*/Port $SSH_PORT/" /etc/ssh/sshd_config
sed -i "s/^#\?PermitRootLogin .*/PermitRootLogin no/" /etc/ssh/sshd_config
sed -i "s/^#\?PasswordAuthentication .*/PasswordAuthentication yes/" /etc/ssh/sshd_config
systemctl restart sshd

###############################################################################
# 3. Firewall
###############################################################################
echo "[3/8] Firewall einrichten..."
ufw default deny incoming
ufw default allow outgoing
ufw allow "$SSH_PORT"/tcp comment "SSH"
ufw allow 80/tcp comment "HTTP"
ufw allow 443/tcp comment "HTTPS"
ufw --force enable

###############################################################################
# 4. App-User & Verzeichnis
###############################################################################
echo "[4/8] Benutzer '$APP_USER' und App-Verzeichnis anlegen..."
if ! id "$APP_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$APP_USER"
fi
mkdir -p "$APP_DIR"
chown "$APP_USER":"$APP_USER" "$APP_DIR"

###############################################################################
# 5. Python-Umgebung
###############################################################################
echo "[5/8] Python-venv & Abhaengigkeiten installieren..."
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install \
  flask werkzeug jinja2 requests gunicorn

###############################################################################
# 6. Node.js (optional, fuer server.js)
###############################################################################
echo "[6/8] Node.js 20 LTS installieren..."
if ! command -v node &>/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

###############################################################################
# 7. Cloudflared installieren
###############################################################################
echo "[7/8] Cloudflared installieren..."
if ! command -v cloudflared &>/dev/null; then
  curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
  dpkg -i /tmp/cloudflared.deb
  rm -f /tmp/cloudflared.deb
fi

###############################################################################
# 8. yt-dlp installieren
###############################################################################
echo "[8/8] yt-dlp installieren..."
if ! command -v yt-dlp &>/dev/null; then
  curl -fsSL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
  chmod a+rx /usr/local/bin/yt-dlp
fi

echo ""
echo "=========================================="
echo " Setup abgeschlossen!"
echo " SSH-Port:       $SSH_PORT"
echo " App-Verzeichnis: $APP_DIR"
echo " Python-venv:    $APP_DIR/venv"
echo " Naechster Schritt: App-Dateien nach $APP_DIR kopieren,"
echo "   dann 02_deploy_services.sh ausfuehren."
echo "=========================================="
