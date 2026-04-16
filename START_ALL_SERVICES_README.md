## RenLern Server - Master Batch Dateien

Alle wichtigen Services in einer Datei kombiniert!

### 📁 Verfügbare Dateien

#### 1. **START_ALL_SERVICES.bat** ⭐ (HAUPTDATEI)
- **Verwendung**: Starten Sie diese Datei, um alle RenLern Services zu starten
- **Startet**:
  - 🐍 Flask Server (`server_v2.py`)
  - 🔐 SSH Service (`sshd`)
  - ☁️ Cloudflared Tunnel
- **Besonderheiten**:
  - Interaktives Menü
  - Zeigt Status aller Services
  - Hält das Fenster offen für Logs
  - Beendet automatisch alte Prozesse
  - Nutzt `py` statt `python` ✓

#### 2. **STOP_ALL_SERVICES.bat**
- **Verwendung**: Zum Beenden aller Services
- **Beendet**:
  - Flask Server
  - Cloudflared Tunnel (falls als Prozess)
  - SSH läuft weiter (für Admin-Zugriff)

#### 3. **AUTOSTART_RENLERN.bat**
- **Verwendung**: Für Windows-Autostart/Geplante Aufgaben
- **Besonderheiten**:
  - Silent Mode (keine Fenster)
  - Schnell und leise
  - Ideal für Dienste auf dem Server
  - Wartet 3 Sekunden auf Windows-Start

---

### 🚀 Quick Start

#### Option A: Manuelle Verwendung
```bash
# Alle Services starten
START_ALL_SERVICES.bat

# Alle Services stoppen
STOP_ALL_SERVICES.bat
```

#### Option B: Windows-Autostart einrichten
1. **Drücke**: `Win + R`
2. **Gib ein**: `shell:startup`
3. **Erstelle Verknüpfung** zu `AUTOSTART_RENLERN.bat`
4. **Beim nächsten Neustart** starten die Services automatisch

#### Option C: Geplante Aufgabe erstellen
```powershell
# In PowerShell als Admin:
$action = New-ScheduledTaskAction -Execute "C:\path\to\AUTOSTART_RENLERN.bat"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "RenLern Server" -Description "Starte alle RenLern Services"
```

---

### 📊 Services-Übersicht

| Service | Port | Status | Command | Features |
|---------|------|--------|---------|----------|
| **Flask Server** | 5000 | Started by .bat | `py server_v2.py` | Portal, Home Cloud, Lernapp, Smart Home |
| **SSH (sshd)** | 22 | System Service | `net start sshd` | Remote Admin Access |
| **Cloudflared** | Varies | Service/Process | `cloudflared tunnel run` | renlern.org Domain |

---

### 🌐 Zugriff nach dem Start

Nachdem alle Services laufen:

```
Portal:     https://renlern.org
            - Login
            - Benutzerregistration
            - Admin Panel

Home:       https://renlern.org/home
            - Cloud Storage
            - Dateiverwaltung
            - Kategorien: Bilder, Musik, Videos, Dokumente, Sonstiges

Lernapp:    https://renlern.org/lernapp
            - Quiz System
            - Lernstatistiken
            - Verportfolios

Smart Home: https://renlern.org/smarthome
            - Netzwerk-Scanner
            - Fritz!Box Integration
            - Geräte verwalten
            - Steuerung (Ein/Aus)

SSH:        ssh -i ~/.ssh/id_rsa_renlern Administrator@localhost (port 22)
```

---

### ⚙️ Konfiguration

#### Python-Installation prüfen
Die Dateien nutzen `py` statt `python`:
```bash
# In CMD prüfen:
py --version
```

Falls `py` nicht funktioniert, editiere die Datei und ersetze:
```batch
set PYTHON_EXE=py
# mit:
set PYTHON_EXE=python
```

#### SSH-Service installieren
Falls SSH nicht vorhanden ist, in PowerShell als Admin:
```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
```

#### Cloudflared installieren
1. Download: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. Oder als Service:
```bash
cloudflared-windows-amd64.exe install --config C:\Users\Administrator\.cloudflared\config.yml
```

---

### 🎯 New Features (Integriert)

#### ✅ Smart Home Integration
- **Automatische Netzwerk-Erkennung** - Alle Geräte werden gefunden (keine IP-Eingabe!)
- **Fritz!Box Support** - Fritz!Box 7530 AX unterstützt
- **Geräte-Steuerung** - Smart Plugs, Lampen, Sensoren
- **Live Status** - Online/Offline Überwachung
- **Datenbank-Speicherung** - Geräte pro Benutzer

#### ✅ IP-Logging Fix
- **Echte Client IPs** werden jetzt geloggt
- **ProxyFix Middleware** aktiviert
- **Brute-Force-Protection** funktioniert korrekt
- **Security Logs** zeigen echte IPs

#### ✅ Automatische IP-Erkennung
- **Netzwerk-Scanner** findet alle Geräte
- **Port-Erkennung** identifiziert Services
- **Schneller Scan** (~10-30 Sekunden)
- **Keine Konfiguration** nötig

---

### 🔧 Troubleshooting

#### Problem: Flask Server startet nicht
- **Lösung 1**: Überprüfe, ob `py` installiert ist: `py --version`
- **Lösung 2**: Stelle sicher, dass `server_v2.py` im Verzeichnis existiert
- **Lösung 3**: Überprüfe Python-Abhängigkeiten: `py -m pip install flask`

#### Problem: SSH funktioniert nicht
- **Lösung**: Installiere OpenSSH Server und starte sshd
```powershell
net start sshd
```

#### Problem: Cloudflared verbindet sich nicht
- **Lösung 1**: Prüfe config: `C:\Users\Administrator\.cloudflared\config.yml`
- **Lösung 2**: Starte Cloudflared manuell zur Debugging:
```bash
cloudflared tunnel --config C:\Users\Administrator\.cloudflared\config.yml run renlern
```

#### Problem: Port 5000 ist bereits in Verwendung
```bash
# Finde Prozess, der Port nutzt:
netstat -ano | findstr :5000

# Oder beende alle Python Prozesse:
taskkill /IM python.exe /F
```

#### Problem: Smart Home Geräte werden nicht gefunden
- **Lösung 1**: Überprüfe Firewall (Ping + Port-Scanning zulassen)
- **Lösung 2**: Fritz!Box muss unter 192.168.1.1 erreichbar sein
- **Lösung 3**: Prüfe, dass Netzwerk-Geräte mit WLAN/LAN verbunden sind

---

### 📝 Logs

- **Flask Server Logs**: Im "RenLern Server" CMD-Fenster
- **SSH Logs**: Windows Event Viewer → Windows-Protokolle → System
- **Cloudflared Logs**: Im "Cloudflared Tunnel" Fenster (falls nicht als Service)
- **Smart Home Logs**: Flask Console + Server Log-Datei

---

### 🛡️ Sicherheit

- SSH ist nur mit Key-Authentifizierung möglich
- Flask Server sollte hinter HTTPS/Reverse Proxy (Cloudflared) laufen
- Firewall sollte nur Port 443/80 (extern) und SSH (kontrolliert) zulassen
- Smart Home Geräte sind nur im lokalen Netzwerk erreichbar
- Benutzer können nur auf ihre eigenen Daten zugreifen

---

### 📞 Commands für manuellen Betrieb

```bash
# Flask Server starten (Hintergrund)
py server_v2.py &

# SSH Service starten
net start sshd

# SSH Service stoppen
net stop sshd

# Cloudflared starten (manuell)
cloudflared tunnel --config C:\Users\Administrator\.cloudflared\config.yml run renlern

# Process auf Port prüfen
netstat -ano | findstr :5000

# Prozess beenden
taskkill /PID <PID> /F
```

---

### 📂 Neue/Aktualisierte Dateien

#### Neu hinzugefügt:
- `smarthome.html` - Smart Home UI
- `smarthome_api.py` - Smart Home API Module
- `START_ALL_SERVICES.bat` - Master Service Starter
- `STOP_ALL_SERVICES.bat` - Service Manager
- `AUTOSTART_RENLERN.bat` - Autostart Version
- `CREATE_DESKTOP_SHORTCUTS.ps1` - Desktop Shortcuts
- `SMARTHOME_INTEGRATION.md` - Smart Home Dokumentation
- `IP_LOGGING_FIX_INFO.md` - IP-Logging Fix Dokumentation

#### Aktualisiert:
- `server_v2.py` - Smart Home Routes + ProxyFix + IP-Logging hinzugefügt
- `home.html` - Smart Home Geräte-Sektion hinzugefügt
- Navigation überall konsistent

---

**Version**: 3.0 Mit Smart Home & IP-Fix  
**Zuletzt aktualisiert**: 2026-04-16  
**Kompatibilität**: Windows 10/11, Python 3.8+
