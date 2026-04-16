# RenLern Portal + Home Cloud + Lernapp - Deployment Guide

## 📋 Übersicht

Das System besteht aus 3 integrierten Komponenten:

```
renlern.org
├── / (Portal Login)
├── /home (Home Cloud - Persönlicher Dateispeicher)
└── /lernapp (Quiz Lernapp)

DEBIAN VM (optional)
├── SSH (Port 22)
├── ttyd Web-Terminal (Port 7681)
└── yt-dlp (Video-Download)
```

---

## 🚀 Schnellstart

### 1. Server starten (Windows)

```bash
cd "C:\Users\Administrator\Desktop\Repo clone\lernapp-apk"
.\start_server.bat
```

Dies startet:
- **server_v2.py** auf http://localhost:5000 (→ renlern.org über Cloudflare)
- **Cloudflared Tunnel** (bereits als Windows-Dienst aktiv)

### 2. Testen

- **Portal Login**: https://renlern.org (oder http://localhost:5000)
- **Nach Login**:
  - 🏠 Home Cloud: https://renlern.org/home
  - 📚 Lernapp: https://renlern.org/lernapp

---

## 🔐 Authentifizierung

### Login-Flow

1. Nutzer öffnet **renlern.org** → `portal.html`
2. Einloggen oder Registrieren
3. Session wird lokal in `localStorage` gespeichert (`portalUser`)
4. Weiterleitung zu **Dashboard** mit 2 Karten:
   - 🏠 Home (Dateispeicher)
   - 📚 Lernapp (Quiz)

### Session-Persistence

- **Portal**: Speichert `portalUser` in localStorage
- **Home**: Liest `portalUser` automatisch aus
- **Lernapp**: Kompatibel mit existentem System (liest `lernappUser`)

---

## 📁 Projektstruktur

```
lernapp-apk/
├── server_v2.py                 ← Neuer Hauptserver (Portal + Home + Lernapp)
├── start_server.bat             ← Windows Startup-Skript
├── portal.html                  ← Login-Seite
├── home.html                    ← Cloud-Dateispeicher
├── lernapp.html                 ← Quiz-Lernapp
├── fragenpool.json              ← Fragendatenbank
├── lernapp.db                   ← SQLite Datenbank
├── user_storage/                ← Home Cloud Dateien pro User
│   └── {user_id}/
│       ├── bilder/
│       ├── musik/
│       ├── videos/
│       ├── dokumente/
│       └── sonstiges/
├── setup_debian_vm.ps1          ← Debian-VM Setup (optional)
└── README_DEPLOYMENT.md         ← Diese Datei
```

---

## 🏠 Home Cloud Features

### Kategorien (automatisch)
- **bilder**: jpg, png, gif, webp, svg, etc.
- **musik**: mp3, wav, flac, ogg, m4a, etc.
- **videos**: mp4, webm, mkv, avi, mov, etc.
- **dokumente**: pdf, doc, xls, txt, md, etc.
- **sonstiges**: Alles andere

### API-Endpunkte

```
GET  /api/files/list              Liste Dateien
POST /api/files/upload            Datei hochladen
GET  /api/files/download          Datei herunterladen
POST /api/files/delete            Datei löschen
POST /api/files/mkdir             Ordner erstellen
GET  /api/files/storage           Speicherinfo
```

### Speicherverwaltung

- **Automatische Kategorisierung**: Dateien werden nach Typ in Ordner sortiert
- **Path-Traversal Protection**: Sichere Validierung aller Pfade
- **Unbegrenzte Unterdatenordner**: Beliebig viele Ordner pro Kategorie
- **Speicher-Limits**: Konfigurierbar im Code

---

## 📚 Lernapp API

### Auth
```
POST /api/register     Registrierung
POST /api/login        Login
```

### Fragen
```
GET  /api/load-fragenpool          Alle Fragen laden
GET  /api/questions?category=X     Fragen einer Kategorie
POST /api/save-fragenpool          Fragenpool speichern
GET  /api/categories               Kategorien-Übersicht
```

### Progress
```
GET  /api/progress?user_id=X       Nutzerprogress laden
POST /api/progress                 Antwort speichern
POST /api/quiz-attempt             Quiz-Versuch speichern
```

---

## 🐧 Debian-VM Setup (Optional)

Die VM wird für folgende Zwecke eingerichtet:

1. **yt-dlp**: Videos/Audio downloaden
2. **ttyd Web-Terminal**: Remote-Zugriff auf Terminal (Port 7681)
3. **Logs**: Systemüberwachung unterwegs

### Installation

```powershell
# Im PowerShell als Administrator:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_debian_vm.ps1
```

Dies:
- Prüft Hyper-V Installation
- Führt Debian-Setup durch
- Installiert yt-dlp, ttyd, SSH
- Konfiguriert Autostart

### Nach Setup

```bash
# Web-Terminal öffnen
http://<debian-vm-ip>:7681

# SSH-Zugang
ssh root@<debian-vm-ip>

# Videos downloaden
yt-dlp -f best <URL>
```

---

## 🔒 Sicherheit

### Implementiert
- ✅ Password-Hashing (PBKDF2)
- ✅ Path-Traversal Prevention
- ✅ Dateiname-Sanitization
- ✅ CORS Headers
- ✅ Session in localStorage (client-side)
- ✅ IP/User-Agent Logging (für Admin)

### Empfehlungen
- 🔐 SSL/TLS über Cloudflare (aktiviert)
- 🔐 regelmäßige Backups von `lernapp.db`
- 🔐 `SECRET_KEY` Umgebungsvariable setzen
- 🔐 Passwort-Mindestlänge enforced (6 Zeichen)
- 🔐 Admin-Benutzer separat schützen

---

## 📊 Datenbank-Schema

### users
```sql
id                INTEGER PRIMARY KEY
username          TEXT UNIQUE
password_hash     TEXT
created_at        TEXT
last_ip           TEXT
last_user_agent   TEXT
last_seen_at      TEXT
```

### questions
```sql
id                INTEGER PRIMARY KEY
category          TEXT
type              TEXT (multiple|fill)
question          TEXT
answer            TEXT
options           TEXT (JSON)
created_at        TEXT
```

### user_progress
```sql
id                INTEGER PRIMARY KEY
user_id           INTEGER
question_id       INTEGER
answered          INTEGER
correct           INTEGER
created_at        TEXT
```

### quiz_attempts
```sql
id                INTEGER PRIMARY KEY
user_id           INTEGER
mode              TEXT
total_questions   INTEGER
correct           INTEGER
wrong             INTEGER
percentage        REAL
created_at        TEXT
ip                TEXT
user_agent        TEXT
```

---

## 🛠️ Konfiguration

### server_v2.py

```python
# Änderbare Konstanten:
CANONICAL_HOST = 'renlern.org'           # Domain
STORAGE_ROOT = 'user_storage'            # Cloud-Speicher
DATABASE = 'lernapp.db'                  # DB-Datei
MAX_CONTENT_LENGTH = 4GB                 # Max Upload-Größe
SECRET_KEY = 'dev-secret-key-...'        # Session-Secret
```

### Umgebungsvariablen

```bash
# Benutzerdefinierter Secret-Key (empfohlen):
set SECRET_KEY=your-super-secret-key-min-32-zeichen
python server_v2.py
```

---

## 📝 Logs & Debugging

### Server-Logs
```bash
# Terminal wo server_v2.py läuft
# Zeigt:
# - Requests
# - Fehler
# - Dateioperationen
# - Auth-Versuche
```

### DB-Logs (SQL)
```python
# Via Debian-Terminal oder SSH:
sqlite3 lernapp.db
> SELECT * FROM users;
> SELECT ip, user_agent FROM quiz_attempts;
```

### Web-Terminal (Debian)
```
http://<vm-ip>:7681
# Remote-Zugriff auf Debian-System
# Perfekt für Fehlersuche unterwegs
```

---

## 🚨 Troubleshooting

### Server startet nicht
```bash
# Prüfe Python
python --version

# Prüfe Flask
pip list | findstr Flask

# Prüfe Port-Konflikt
netstat -ano | findstr :5000
```

### Home-Upload funktioniert nicht
- Prüfe `user_storage/` Ordner-Rechte
- Prüfe Speicherplatz
- Prüfe Dateiname-Sonderzeichen

### Lernapp zeigt keine Fragen
- Prüfe `fragenpool.json` existiert
- Prüfe `lernapp.db` existiert
- Via Portal-Login in Lernapp einloggen

### VM verbindet nicht
```powershell
# Prüfe VM läuft
Get-VM | Where-Object {$_.Name -like "*Debian*"}

# Prüfe IP
Get-VMNetworkAdapter -VMName RenLern-Debian
```

---

## 📞 Support-Checklist

- [ ] Server läuft: http://localhost:5000
- [ ] Portal erreichbar
- [ ] Login/Registrierung funktioniert
- [ ] Home Cloud Upload funktioniert
- [ ] Lernapp zeigt Fragen
- [ ] Cloudflare Tunnel aktiv
- [ ] DB-Backups eingerichtet
- [ ] SSH-Keys generiert (für Debian)

---

## 🔄 Updates & Wartung

### Neuen Fragenpool laden
```bash
# fragenpool.json aktualisieren
# → Server lädt automatisch beim Start
```

### User-Daten exportieren
```python
import sqlite3
conn = sqlite3.connect('lernapp.db')
rows = conn.execute("SELECT * FROM users").fetchall()
```

### Alte Dateien löschen
```bash
# Manuell im Dateisystem:
rm -r user_storage/{user_id}/sonstiges/alte_datei.txt
```

---

## 📅 Changelog

### v2.0 (Aktuell)
- ✨ Portal-Login eingeführt
- ✨ Home Cloud mit Kategorien
- ✨ Vereinheitlichtes Interface
- ✨ Debian-VM Integration
- ✨ Web-Terminal (ttyd)
- 🔒 Path-Traversal Protection
- 🔧 Verbesserter Code

### v1.0 (Alt)
- Lernapp-Only
- Einfaches HTML-Interface

---

## 📄 Lizenz & Credits

- **Flask**: MIT
- **Werkzeug**: BSD
- **ttyd**: MIT
- **yt-dlp**: Unlicense

---

**Fertig?** 🎉

```bash
cd app
python server_v2.py
```

Öffne https://renlern.org und viel Spaß! 🚀
