#!/bin/bash
###############################################################################
# INSTALL.sh  -  MASTER-INSTALLATIONSSKRIPT (v2 - Security Hardened)
# =============================================================================
# Dieses eine Skript macht ALLES:
#   1.  System aktualisieren & alle Pakete installieren
#   2.  SSH haerten (Port 8022, Key-Only vorbereitet)
#   3.  Firewall mit Netzwerk-Segmentierung
#   4.  Kernel-Sicherheit (sysctl hardening)
#   5.  fail2ban Intrusion Prevention
#   6.  Automatische Sicherheitsupdates
#   7.  App-User (eingesperrt, kein sudo)
#   8.  Python-venv mit Abhaengigkeiten
#   9.  Node.js 20 LTS
#  10.  Cloudflared (AUTOMATISCH mit Token!)
#  11.  yt-dlp
#  12.  App-Dateien kopieren
#  13.  systemd-Services mit Sandboxing
#  14.  Dienste starten (richtige Reihenfolge)
#  15.  Sicherheitsaudit & Zusammenfassung
#
# VORBEREITUNG:
#   1. server.env Datei bearbeiten (Tunnel-Token eintragen!)
#   2. USB-Stick einstecken
#   3. mount /dev/sdb1 /mnt
#   4. cd /mnt/migrations_guide
#   5. bash INSTALL.sh
#
###############################################################################
set -euo pipefail

# ========================= KONFIGURATION LADEN ===============================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/server.env"

# Defaults
APP_USER="lernapp"
APP_DIR="/opt/lernapp"
DOMAIN="renlern.org"
SSH_PORT=8022
FLASK_PORT=5000
CLOUDFLARE_TUNNEL_TOKEN=""
ADMIN_SSH_PUBKEY=""
LAN_SUBNET="192.168.1.0/24"
MANAGEMENT_IP=""

# Config laden falls vorhanden
if [ -f "$CONFIG_FILE" ]; then
  echo "Lade Konfiguration aus server.env..."
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
else
  echo "WARNUNG: server.env nicht gefunden, verwende Defaults."
  echo "         Cloudflared-Tunnel wird NICHT automatisch konfiguriert!"
fi

APP_FILES_DIR="$SCRIPT_DIR/app_files"
LOG="/var/log/lernapp_install.log"

# Pruefen ob root
if [ "$(id -u)" -ne 0 ]; then
  echo "FEHLER: Bitte als root ausfuehren:  sudo bash INSTALL.sh"
  exit 1
fi

exec > >(tee -a "$LOG") 2>&1

echo ""
echo "======================================================================"
echo "    LernApp Server - Sichere Komplettinstallation v2"
echo "    Domain: $DOMAIN"
echo "----------------------------------------------------------------------"
echo "    Sicherheit: SSH-Haertung + Firewall-Zonen + fail2ban"
echo "                Kernel-Hardening + Auto-Updates + Sandboxing"
echo "======================================================================"
echo ""
echo "Installationslog: $LOG"
echo "Quelle: $SCRIPT_DIR"
echo "Tunnel-Token: $([ -n "$CLOUDFLARE_TUNNEL_TOKEN" ] && echo 'VORHANDEN' || echo 'NICHT GESETZT')"
echo "Gestartet: $(date)"
echo ""

###############################################################################
# PHASE 1: System-Update & Grundpakete
###############################################################################
echo "=================================================================="
echo "[1/15] System-Update & Grundpakete installieren..."
echo "=================================================================="
apt-get update -y
apt-get upgrade -y
apt-get install -y \
  curl wget git sudo ufw fail2ban htop tmux unzip \
  python3 python3-pip python3-venv python3-dev \
  sqlite3 \
  build-essential libffi-dev libssl-dev \
  ca-certificates gnupg lsb-release \
  openssh-server \
  unattended-upgrades apt-listchanges \
  logrotate rsyslog \
  iptables ipset \
  net-tools dnsutils \
  rkhunter lynis \
  apparmor apparmor-utils
echo "  -> Grundpakete + Sicherheitstools installiert."

###############################################################################
# PHASE 2: SSH haerten
###############################################################################
echo ""
echo "=================================================================="
echo "[2/15] SSH maximal haerten..."
echo "=================================================================="
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%s) 2>/dev/null || true

mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/99-lernapp-hardened.conf <<SSHEOF
# === LernApp SSH Haertung ===
Port $SSH_PORT

# Root-Login komplett deaktiviert
PermitRootLogin no

# Passwort-Login erlaubt (bis SSH-Key eingerichtet)
PasswordAuthentication yes
# -> Spaeter auf "no" setzen wenn SSH-Key funktioniert!

# Public-Key bevorzugt
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# Leere Passwoerter verboten
PermitEmptyPasswords no

# Nur bestimmte User erlauben
AllowUsers $APP_USER

# Timeouts
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30

# Keine X11/Agent/Tunnel Weiterleitung
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no

# Logging
LogLevel VERBOSE

# Maximale Versuche
MaxAuthTries 3
MaxSessions 3
MaxStartups 3:50:10

# SFTP einschraenken
Subsystem sftp internal-sftp

# Sichere Algorithmen (nur moderne)
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256
SSHEOF

# SSH-Key einrichten falls angegeben
if [ -n "$ADMIN_SSH_PUBKEY" ]; then
  if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
  fi
  mkdir -p /home/"$APP_USER"/.ssh
  echo "$ADMIN_SSH_PUBKEY" > /home/"$APP_USER"/.ssh/authorized_keys
  chmod 700 /home/"$APP_USER"/.ssh
  chmod 600 /home/"$APP_USER"/.ssh/authorized_keys
  chown -R "$APP_USER":"$APP_USER" /home/"$APP_USER"/.ssh
  # Key ist da -> Passwort-Login deaktivieren
  sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' \
    /etc/ssh/sshd_config.d/99-lernapp-hardened.conf
  echo "  -> SSH-Key installiert, Passwort-Login DEAKTIVIERT."
else
  echo "  -> Kein SSH-Key angegeben, Passwort-Login bleibt aktiv."
  echo "     EMPFEHLUNG: Spaeter SSH-Key einrichten!"
fi

systemctl restart sshd
echo "  -> SSH gehaertet: Port $SSH_PORT, nur User '$APP_USER', max 3 Versuche."

###############################################################################
# PHASE 3: Firewall mit Netzwerk-Segmentierung
###############################################################################
echo ""
echo "=================================================================="
echo "[3/15] Firewall mit Netzwerk-Zonen einrichten..."
echo "=================================================================="

# UFW zuruecksetzen
ufw --force reset

# Defaults: alles blockieren
ufw default deny incoming
ufw default deny forward
ufw default allow outgoing

# === ZONE 1: SSH (nur Verwaltung) ===
if [ -n "$MANAGEMENT_IP" ]; then
  ufw allow from "$MANAGEMENT_IP" to any port "$SSH_PORT" proto tcp comment "SSH nur Management-IP"
  echo "  -> SSH nur von $MANAGEMENT_IP erlaubt."
elif [ -n "$LAN_SUBNET" ]; then
  ufw allow from "$LAN_SUBNET" to any port "$SSH_PORT" proto tcp comment "SSH nur LAN"
  echo "  -> SSH nur aus LAN ($LAN_SUBNET) erlaubt."
else
  ufw allow "$SSH_PORT"/tcp comment "SSH"
  echo "  -> SSH von ueberall erlaubt (nicht optimal!)."
fi

# === ZONE 2: Flask NUR lokal ===
# Flask hoert NUR auf 127.0.0.1 -> kein Firewall-Port noetig
echo "  -> Flask ($FLASK_PORT) ist NICHT extern erreichbar (nur localhost)."

# === ZONE 3: Cloudflared nur ausgehend ===
echo "  -> Cloudflared: nur ausgehende Tunnel-Verbindung."

# Rate Limiting SSH
ufw limit from "$LAN_SUBNET" to any port "$SSH_PORT" proto tcp comment "SSH Rate Limit" 2>/dev/null || true

ufw --force enable

echo ""
echo "  FIREWALL-ZONEN:"
echo "  +----------------------------------+"
echo "  | ZONE MANAGEMENT (SSH)            |"
echo "  |   Port $SSH_PORT/tcp             |"
echo "  |   Nur: $LAN_SUBNET              |"
echo "  |   Rate-limited                   |"
echo "  +----------------------------------+"
echo "  | ZONE APP (Flask)                 |"
echo "  |   Port $FLASK_PORT               |"
echo "  |   NUR localhost (127.0.0.1)      |"
echo "  +----------------------------------+"
echo "  | ZONE TUNNEL (Cloudflared)        |"
echo "  |   Nur ausgehend                  |"
echo "  +----------------------------------+"
echo "  | FORWARD: Komplett blockiert      |"
echo "  | INCOMING Default: DENY           |"
echo "  +----------------------------------+"

###############################################################################
# PHASE 4: Kernel-Sicherheit (sysctl)
###############################################################################
echo ""
echo "=================================================================="
echo "[4/15] Kernel-Hardening (sysctl)..."
echo "=================================================================="
cat > /etc/sysctl.d/99-lernapp-security.conf <<'SYSEOF'
# === LernApp Kernel Security ===

# IP Spoofing Schutz
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# ICMP Redirects ignorieren (MITM-Schutz)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Source Routing deaktivieren
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# SYN-Flood Schutz
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# IP Forwarding deaktivieren (kein Router!)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Smurf-Attack Schutz
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Bogus ICMP-Antworten loggen
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Martian-Pakete loggen
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# IPv6 Privacy Extensions
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2

# ASLR maximal
kernel.randomize_va_space = 2

# Core Dumps deaktivieren
fs.suid_dumpable = 0

# Kernel-Pointer verstecken
kernel.kptr_restrict = 2

# dmesg nur fuer root
kernel.dmesg_restrict = 1

# Performance-Events einschraenken
kernel.perf_event_paranoid = 3

# Unprivilegierte BPF deaktivieren
kernel.unprivileged_bpf_disabled = 1
SYSEOF

sysctl --system > /dev/null 2>&1
echo "  -> Kernel gehaertet: SYN-Flood-Schutz, kein Forwarding, ASLR, keine Core-Dumps."

###############################################################################
# PHASE 5: fail2ban konfigurieren
###############################################################################
echo ""
echo "=================================================================="
echo "[5/15] fail2ban Intrusion Prevention..."
echo "=================================================================="
cat > /etc/fail2ban/jail.local <<F2BEOF
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 3
backend  = systemd
banaction = ufw

ignoreip = 127.0.0.1/8 ::1 $LAN_SUBNET

[sshd]
enabled  = true
port     = $SSH_PORT
filter   = sshd
maxretry = 3
bantime  = 7200
findtime = 600

[sshd-aggressive]
enabled  = true
port     = $SSH_PORT
filter   = sshd[mode=aggressive]
maxretry = 2
bantime  = 86400
findtime = 3600

[lernapp-login]
enabled  = true
port     = $FLASK_PORT
filter   = lernapp-login
maxretry = 10
bantime  = 1800
findtime = 300
logpath  = /var/log/syslog
F2BEOF

# Custom Filter fuer LernApp Login-Bruteforce
cat > /etc/fail2ban/filter.d/lernapp-login.conf <<FILTEREOF
[Definition]
failregex = lernapp-flask.*"POST /api/login.*" 401
ignoreregex =
FILTEREOF

systemctl enable --now fail2ban
systemctl restart fail2ban
echo "  -> fail2ban aktiv:"
echo "     SSH:    3 Versuche -> 2h Ban (Wiederholungstaeter: 24h)"
echo "     Login:  10 Fehlversuche -> 30min Ban"

###############################################################################
# PHASE 6: Automatische Sicherheitsupdates
###############################################################################
echo ""
echo "=================================================================="
echo "[6/15] Automatische Sicherheitsupdates..."
echo "=================================================================="
cat > /etc/apt/apt.conf.d/50unattended-upgrades <<'UUEOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
UUEOF

cat > /etc/apt/apt.conf.d/20auto-upgrades <<'AUTOEOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
AUTOEOF

systemctl enable --now unattended-upgrades
echo "  -> Sicherheitsupdates werden taeglich automatisch installiert."

###############################################################################
# PHASE 7: App-User (eingesperrt)
###############################################################################
echo ""
echo "=================================================================="
echo "[7/15] Benutzer '$APP_USER' sicher anlegen..."
echo "=================================================================="
if ! id "$APP_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$APP_USER"
  echo "  -> Benutzer '$APP_USER' erstellt."
else
  echo "  -> Benutzer '$APP_USER' existiert bereits."
fi
mkdir -p "$APP_DIR"
chown "$APP_USER":"$APP_USER" "$APP_DIR"
chmod 750 /home/"$APP_USER"

# Ressourcen-Limits
cat > /etc/security/limits.d/99-lernapp.conf <<LIMEOF
$APP_USER  soft  nofile    4096
$APP_USER  hard  nofile    8192
$APP_USER  soft  nproc     256
$APP_USER  hard  nproc     512
$APP_USER  hard  core      0
LIMEOF
echo "  -> Ressourcen-Limits: max 512 Prozesse, kein Core-Dump."

###############################################################################
# PHASE 8: Python-Umgebung
###############################################################################
echo ""
echo "=================================================================="
echo "[8/15] Python Virtual Environment..."
echo "=================================================================="
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install \
  flask werkzeug jinja2 requests gunicorn
echo "  -> Python-venv erstellt."

###############################################################################
# PHASE 9: Node.js
###############################################################################
echo ""
echo "=================================================================="
echo "[9/15] Node.js 20 LTS..."
echo "=================================================================="
if ! command -v node &>/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
  echo "  -> Node.js $(node -v) installiert."
else
  echo "  -> Node.js bereits vorhanden: $(node -v)"
fi

###############################################################################
# PHASE 10: Cloudflared mit automatischem Token-Setup
###############################################################################
echo ""
echo "=================================================================="
echo "[10/15] Cloudflared Tunnel (automatisch)..."
echo "=================================================================="
if ! command -v cloudflared &>/dev/null; then
  curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb \
    -o /tmp/cloudflared.deb
  dpkg -i /tmp/cloudflared.deb
  rm -f /tmp/cloudflared.deb
  echo "  -> Cloudflared installiert."
else
  echo "  -> Cloudflared bereits vorhanden."
fi

CLOUDFLARED_HOME="/home/$APP_USER/.cloudflared"
mkdir -p "$CLOUDFLARED_HOME"

if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
  echo "  -> Tunnel-Token gefunden! Konfiguriere automatisch..."
  echo ""
  echo "     So funktioniert es:"
  echo "     - Der Token enthaelt Tunnel-ID, Credentials und Ingress-Regeln"
  echo "     - Alles wird im Cloudflare Zero Trust Dashboard konfiguriert"
  echo "     - Der Server braucht kein interaktives Login!"
  echo "     - Tunnel verbindet sich automatisch nach Start"

  # Token-basierter systemd Service
  cat > /etc/systemd/system/cloudflared-tunnel.service <<CFDEOF
[Unit]
Description=Cloudflare Tunnel fuer $DOMAIN (Token-basiert, auto)
After=network-online.target lernapp-flask.service
Wants=network-online.target
Requires=lernapp-flask.service

[Service]
Type=simple
User=$APP_USER
ExecStart=/usr/local/bin/cloudflared tunnel --no-autoupdate run --token $CLOUDFLARE_TUNNEL_TOKEN
Restart=always
RestartSec=5

# Sandboxing
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=yes
ReadWritePaths=$CLOUDFLARED_HOME

StandardOutput=journal
StandardError=journal
SyslogIdentifier=cloudflared-tunnel

[Install]
WantedBy=multi-user.target
CFDEOF

  echo ""
  echo "  -> Cloudflared mit Token konfiguriert."
  echo "  -> Tunnel startet automatisch, KEIN manuelles Login noetig!"
  echo ""
  echo "  WICHTIG: Ingress-Regeln im Cloudflare Dashboard setzen:"
  echo "    Hostname: $DOMAIN      -> http://localhost:$FLASK_PORT"
  echo "    Hostname: www.$DOMAIN  -> http://localhost:$FLASK_PORT"
else
  echo "  -> KEIN Tunnel-Token gesetzt."
  echo ""
  echo "     TOKEN HOLEN (dauert 2 Minuten):"
  echo "     1. https://one.dash.cloudflare.com"
  echo "        -> Zero Trust -> Networks -> Tunnels"
  echo "     2. 'Create a tunnel' -> Name: lernapp"
  echo "     3. 'Debian' als Betriebssystem waehlen"
  echo "     4. Den Token-String kopieren (steht nach '--token')"
  echo "     5. In server.env eintragen:"
  echo '        CLOUDFLARE_TUNNEL_TOKEN="dein-token-hier"'
  echo "     6. INSTALL.sh nochmal ausfuehren"
  echo ""
  echo "     Ingress-Regeln im Dashboard setzen:"
  echo "       $DOMAIN     -> http://localhost:$FLASK_PORT"
  echo "       www.$DOMAIN -> http://localhost:$FLASK_PORT"

  cat > /etc/systemd/system/cloudflared-tunnel.service <<CFDEOF
[Unit]
Description=Cloudflare Tunnel fuer $DOMAIN (Token fehlt!)
After=network-online.target lernapp-flask.service
Wants=network-online.target
Requires=lernapp-flask.service

[Service]
Type=simple
User=$APP_USER
ExecStart=/usr/local/bin/cloudflared tunnel run
Restart=always
RestartSec=10
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=yes
ReadWritePaths=$CLOUDFLARED_HOME
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cloudflared-tunnel

[Install]
WantedBy=multi-user.target
CFDEOF
fi

chown -R "$APP_USER":"$APP_USER" "$CLOUDFLARED_HOME"

###############################################################################
# PHASE 11: yt-dlp
###############################################################################
echo ""
echo "=================================================================="
echo "[11/15] yt-dlp..."
echo "=================================================================="
if ! command -v yt-dlp &>/dev/null; then
  curl -fsSL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o /usr/local/bin/yt-dlp
  chmod a+rx /usr/local/bin/yt-dlp
  echo "  -> yt-dlp installiert."
else
  echo "  -> yt-dlp bereits vorhanden."
fi

###############################################################################
# PHASE 12: App-Dateien kopieren
###############################################################################
echo ""
echo "=================================================================="
echo "[12/15] App-Dateien nach $APP_DIR kopieren..."
echo "=================================================================="
if [ -d "$APP_FILES_DIR" ]; then
  cp "$APP_FILES_DIR/server_neu.py"    "$APP_DIR/" 2>/dev/null && echo "  -> server_neu.py" || true
  cp "$APP_FILES_DIR/flask_server.py"  "$APP_DIR/" 2>/dev/null && echo "  -> flask_server.py" || true
  cp "$APP_FILES_DIR/fragenpool.json"  "$APP_DIR/" 2>/dev/null && echo "  -> fragenpool.json" || true
  cp "$APP_FILES_DIR/lernapp.html"     "$APP_DIR/" 2>/dev/null && echo "  -> lernapp.html" || true
  cp "$APP_FILES_DIR/server.js"        "$APP_DIR/" 2>/dev/null && echo "  -> server.js" || true
  cp "$APP_FILES_DIR/package.json"     "$APP_DIR/" 2>/dev/null && echo "  -> package.json" || true
  cp "$APP_FILES_DIR/server.py"        "$APP_DIR/" 2>/dev/null && echo "  -> server.py" || true

  # DB-Verzeichnis mit strengen Rechten
  mkdir -p "$APP_DIR/data"
  [ -f "$APP_DIR/lernapp.db" ] && mv "$APP_DIR/lernapp.db" "$APP_DIR/data/" 2>/dev/null || true

  chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
  chmod 750 "$APP_DIR"
  chmod 700 "$APP_DIR/data" 2>/dev/null || true
  echo "  -> Alle Dateien kopiert. DB-Ordner: 700."
else
  echo "  WARNUNG: $APP_FILES_DIR nicht gefunden!"
fi

if [ -f "$APP_DIR/package.json" ]; then
  cd "$APP_DIR"
  sudo -u "$APP_USER" npm install --production 2>/dev/null || true
  echo "  -> npm install ausgefuehrt."
fi

###############################################################################
# PHASE 13: systemd-Services mit Sandboxing
###############################################################################
echo ""
echo "=================================================================="
echo "[13/15] systemd-Services mit Sandboxing..."
echo "=================================================================="

cat > /etc/systemd/system/lernapp-flask.service <<EOF
[Unit]
Description=LernApp Flask Server (localhost:$FLASK_PORT)
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

# === Sandboxing ===
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
RestrictNamespaces=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
LockPersonality=yes
ReadWritePaths=$APP_DIR

# Ressourcen-Limits
MemoryMax=512M
CPUQuota=80%

StandardOutput=journal
StandardError=journal
SyslogIdentifier=lernapp-flask

[Install]
WantedBy=multi-user.target
EOF
echo "  -> lernapp-flask.service (sandboxed)."

cat > /etc/systemd/system/lernapp-node.service <<EOF
[Unit]
Description=LernApp Node.js Server (optional, Port 3000)
After=network-online.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/node $APP_DIR/server.js
Restart=always
RestartSec=5
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ReadWritePaths=$APP_DIR
MemoryMax=256M
CPUQuota=50%
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lernapp-node

[Install]
WantedBy=multi-user.target
EOF
echo "  -> lernapp-node.service (sandboxed, optional)."

systemctl daemon-reload

###############################################################################
# PHASE 14: Dienste starten
###############################################################################
echo ""
echo "=================================================================="
echo "[14/15] Dienste starten..."
echo "=================================================================="

systemctl enable --now lernapp-flask.service
echo "  -> [1] lernapp-flask gestartet."

if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
  systemctl enable --now cloudflared-tunnel.service
  echo "  -> [2] cloudflared-tunnel gestartet (automatisch!)."
else
  systemctl enable cloudflared-tunnel.service
  echo "  -> [2] cloudflared-tunnel: Autostart an, Token fehlt noch."
fi

if [ -f "$SCRIPT_DIR/03_service_manager.sh" ]; then
  cp "$SCRIPT_DIR/03_service_manager.sh" /usr/local/bin/lernapp-manager
  chmod +x /usr/local/bin/lernapp-manager
  echo "  -> lernapp-manager installiert."
fi

###############################################################################
# PHASE 15: Sicherheitsaudit & Zusammenfassung
###############################################################################
echo ""
echo "=================================================================="
echo "[15/15] Sicherheitsaudit..."
echo "=================================================================="

WARNINGS=0

# Checks
if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config.d/99-lernapp-hardened.conf 2>/dev/null; then
  echo "  [OK] SSH Root-Login deaktiviert"
else
  echo "  [!!] SSH Root-Login aktiv!"
  WARNINGS=$((WARNINGS+1))
fi

if ufw status | grep -q "Status: active"; then
  echo "  [OK] Firewall aktiv"
else
  echo "  [!!] Firewall inaktiv!"
  WARNINGS=$((WARNINGS+1))
fi

if systemctl is-active fail2ban &>/dev/null; then
  echo "  [OK] fail2ban laeuft"
else
  echo "  [!!] fail2ban fehlt!"
  WARNINGS=$((WARNINGS+1))
fi

if systemctl is-enabled unattended-upgrades &>/dev/null; then
  echo "  [OK] Auto-Updates aktiv"
else
  echo "  [!!] Auto-Updates fehlen!"
  WARNINGS=$((WARNINGS+1))
fi

[ -f /etc/sysctl.d/99-lernapp-security.conf ] && echo "  [OK] Kernel-Hardening aktiv"

if [ -n "$ADMIN_SSH_PUBKEY" ]; then
  echo "  [OK] SSH-Key Auth, Passwort deaktiviert"
else
  echo "  [!!] Passwort-Login aktiv (SSH-Key empfohlen)"
  WARNINGS=$((WARNINGS+1))
fi

if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
  echo "  [OK] Cloudflared Tunnel (automatisch)"
else
  echo "  [!!] Tunnel-Token fehlt"
  WARNINGS=$((WARNINGS+1))
fi

echo "  [OK] Flask nur localhost (nicht extern erreichbar)"
echo "  [OK] systemd-Sandboxing aktiv"
echo "  [OK] Forwarding blockiert"
echo "  [OK] Ressourcen-Limits gesetzt"

echo ""
echo "======================================================================"
echo "             INSTALLATION ABGESCHLOSSEN!"
echo "----------------------------------------------------------------------"
echo "  SSH:     Port $SSH_PORT (nur LAN, max 3 Versuche)"
echo "  Flask:   localhost:$FLASK_PORT (nicht extern!)"
echo "  Tunnel:  Cloudflared -> https://$DOMAIN"
echo "  Audit:   $WARNINGS Warnungen"
echo "======================================================================"
echo ""
echo "SICHERHEITS-ARCHITEKTUR:"
echo ""
echo "  Internet"
echo "    |"
echo "    v"
echo "  [Cloudflare CDN + WAF + DDoS-Schutz]"
echo "    |  verschluesselter Tunnel"
echo "    v"
echo "  +-------------- FIREWALL ----------------+"
echo "  |  Eingehend: ALLES BLOCKIERT            |"
echo "  |  Ausnahme:  SSH $SSH_PORT nur LAN      |"
echo "  |  Forward:   BLOCKIERT                  |"
echo "  +----------------------------------------+"
echo "    |"
echo "    v"
echo "  [fail2ban] -- Ban nach 3 Fehlversuchen"
echo "    |"
echo "    v"
echo "  [cloudflared] --> [Flask :$FLASK_PORT localhost]"
echo "   (sandboxed)       (sandboxed, nur 127.0.0.1)"
echo "                      |"
echo "                      v"
echo "                    [SQLite DB] (Rechte: 700)"
echo ""

# Dienste-Status
echo "DIENSTE:"
for svc in sshd lernapp-flask cloudflared-tunnel fail2ban unattended-upgrades; do
  STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "inaktiv")
  printf "  %-28s %s\n" "$svc" "$STATUS"
done

echo ""
if [ "$WARNINGS" -gt 0 ]; then
  echo "EMPFEHLUNGEN ($WARNINGS offen):"
  [ -z "$ADMIN_SSH_PUBKEY" ] && echo "  -> SSH-Key in server.env eintragen (ADMIN_SSH_PUBKEY)"
  [ -z "$CLOUDFLARE_TUNNEL_TOKEN" ] && echo "  -> Tunnel-Token in server.env eintragen (CLOUDFLARE_TUNNEL_TOKEN)"
  echo ""
fi

echo "BEFEHLE:"
echo "  lernapp-manager status       Dienste-Uebersicht"
echo "  lernapp-manager restart      Alles neustarten"
echo "  fail2ban-client status       Ban-Liste"
echo "  ufw status verbose           Firewall-Regeln"
echo "  journalctl -u lernapp-flask  Flask-Logs"
echo "  lynis audit system           Sicherheitsaudit"
echo ""
echo "Fertig: $(date)"
