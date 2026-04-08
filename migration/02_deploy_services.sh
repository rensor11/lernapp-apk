#!/bin/bash
###############################################################################
# 02_deploy_services.sh
# Kopiert App-Dateien und richtet systemd-Dienste ein.
# Ausfuehren als root:  bash 02_deploy_services.sh
#
# WICHTIG: Jeder Dienst (Flask, Cloudflared, etc.) bekommt seinen eigenen
# systemd-Service.  Damit laufen sie in eigenen Prozessen (= "eigenes Terminal"),
# starten automatisch bei Boot, und koennen einzeln gesteuert werden:
#   systemctl start|stop|restart|status lernapp-flask
###############################################################################
set -euo pipefail

APP_USER="lernapp"
APP_DIR="/opt/lernapp"
FLASK_PORT=5000
SSH_PORT=8022

echo "=== Dienste-Deployment gestartet: $(date) ==="

###############################################################################
# 1. App-Dateien kopieren
###############################################################################
echo "[1/5] App-Dateien kopieren..."
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Nur wenn von lokalem Repo ausgefuehrt
if [ -f "$SCRIPT_DIR/server_neu.py" ]; then
  cp "$SCRIPT_DIR/server_neu.py"      "$APP_DIR/"
  cp "$SCRIPT_DIR/flask_server.py"    "$APP_DIR/"
  cp "$SCRIPT_DIR/fragenpool.json"    "$APP_DIR/"
  cp "$SCRIPT_DIR/lernapp.html"       "$APP_DIR/"
  [ -f "$SCRIPT_DIR/server.js" ]     && cp "$SCRIPT_DIR/server.js"     "$APP_DIR/"
  [ -f "$SCRIPT_DIR/package.json" ]  && cp "$SCRIPT_DIR/package.json"  "$APP_DIR/"
  chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
  echo "  -> Dateien von $SCRIPT_DIR kopiert."
else
  echo "  -> WARNUNG: Quelldateien nicht gefunden. Dateien muessen manuell nach $APP_DIR kopiert werden."
fi

###############################################################################
# 2. systemd: LernApp Flask Server
###############################################################################
echo "[2/5] systemd-Service: lernapp-flask..."
cat > /etc/systemd/system/lernapp-flask.service <<EOF
[Unit]
Description=LernApp Flask Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$APP_DIR/venv/bin/python3 $APP_DIR/server_neu.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lernapp-flask

[Install]
WantedBy=multi-user.target
EOF

###############################################################################
# 3. systemd: Cloudflared Tunnel
###############################################################################
echo "[3/5] systemd-Service: cloudflared-tunnel..."
cat > /etc/systemd/system/cloudflared-tunnel.service <<EOF
[Unit]
Description=Cloudflare Tunnel fuer renlern.org
After=network-online.target lernapp-flask.service
Wants=network-online.target
Requires=lernapp-flask.service

[Service]
Type=simple
User=$APP_USER
ExecStart=/usr/local/bin/cloudflared tunnel run
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cloudflared-tunnel

# Cloudflared-Konfiguration erwartet:
#   /home/$APP_USER/.cloudflared/config.yml
# Erstelle diese Datei mit deinem Tunnel-Token/Secret!

[Install]
WantedBy=multi-user.target
EOF

###############################################################################
# 4. systemd: Node.js Express Server (optional)
###############################################################################
echo "[4/5] systemd-Service: lernapp-node (optional)..."
cat > /etc/systemd/system/lernapp-node.service <<EOF
[Unit]
Description=LernApp Node.js Express Server (optional)
After=network-online.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/node $APP_DIR/server.js
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lernapp-node

[Install]
WantedBy=multi-user.target
EOF

###############################################################################
# 5. Dienste aktivieren und starten (richtige Reihenfolge)
###############################################################################
echo "[5/5] Dienste laden, aktivieren, starten..."
systemctl daemon-reload

# --- Reihenfolge: ---
# 1. SSH (laeuft bereits)
# 2. Flask-Server
# 3. Cloudflared (wartet auf Flask)
# 4. Node.js (optional, deaktiviert by default)

systemctl enable --now lernapp-flask.service
echo "  -> lernapp-flask gestartet."

systemctl enable --now cloudflared-tunnel.service
echo "  -> cloudflared-tunnel gestartet."

# Node-Server ist optional - nur aktivieren wenn gewuenscht:
# systemctl enable --now lernapp-node.service
echo "  -> lernapp-node NICHT aktiviert (optional). Zum Aktivieren:"
echo "     systemctl enable --now lernapp-node.service"

echo ""
echo "=========================================="
echo " Alle Dienste deployed!"
echo ""
echo " Status pruefen:"
echo "   systemctl status lernapp-flask"
echo "   systemctl status cloudflared-tunnel"
echo "   systemctl status sshd"
echo ""
echo " Logs anschauen:"
echo "   journalctl -u lernapp-flask -f"
echo "   journalctl -u cloudflared-tunnel -f"
echo ""
echo " Dienste neustarten:"
echo "   systemctl restart lernapp-flask"
echo "   systemctl restart cloudflared-tunnel"
echo "=========================================="
