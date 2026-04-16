# 🔒 RenLern - Sicherheitskonfiguration & Administrative Anleitung

## Überblick der implementierten Sicherheitsmaßnahmen

### 1. Authentifizierung & Zugriffskontrolle

#### Login-Sicherheit
- **Rate Limiting**: max. 5 Versuche pro IP-Adresse in 15 Minuten
- **Brute-Force-Schutz**: Fehlgeschlagene Versuche werden protokolliert
- **Passwort-Hashing**: PBKDF2-SHA256 via Werkzeug
- **Passwort-Anforderungen**: Mindestens 6 Zeichen

#### Benutzerzugriff
- **Home Cloud Zugriffskontrolle**: Nur autorisierte Benutzer können auf Home Cloud zugreifen
- **Nicht autorisierte Benutzer** sehen nach Login nur die Lernapp
- **Admin-Panel** zum Freigeben/Sperren von Benutzern

### 2. Datenschutz & Dateiverwaltung

#### Sichere Dateispeicherung
- **Path Traversal Protection**: `safe_path()` validiert alle Pfade
- **Benutzer-Isolierung**: Jeder Benutzer hat eigenes Verzeichnis (`user_storage/{user_id}/`)
- **Automatische Kategorisierung**: Dateien nach Typ organisiert
- **Sichere Dateinamen**: `secure_filename()` normalisiert Namen

#### Unterstützte Dateitypen
```
Bilder:    jpg, jpeg, png, gif, webp, svg, bmp, ico, tiff, raw, heic
Musik:     mp3, wav, flac, ogg, m4a, aac, wma, opus, aiff
Videos:    mp4, webm, mkv, avi, mov, wmv, flv, ts, m4v, mpeg, mpg
Dokumente: pdf, doc, docx, txt, md, odt, xls, xlsx, csv, ppt, pptx, rtf, xml, json, yaml, yml
Archive:   zip, rar, 7z, tar, gz, iso, exe, apk, dmg, msi, app
```

#### Speichergrenzen
- **Max. Dateigröße**: 4 GB
- **Max. Upload-Größe**: 4 GB

### 3. Session & Datenbank-Sicherheit

#### Session Management
- **Stateless Design**: Benutzer sendet `user_id` bei jedem Request
- **IP-Tracking**: Letzte Anmeldungs-IP wird protokolliert
- **User-Agent-Tracking**: Browser-Info wird gespeichert
- **Letzter Zugriff**: Timestamp wird aktualisiert

#### Datenbankschutz
- **Prepared Statements**: Alle SQL-Queries verwenden Parameter (kein SQL Injection möglich)
- **SQLite3**: Datenbankdatei sollte außerhalb von Web-Root sein
- **Backups**: Regelmäßige Backups empfohlen

### 4. Netzwerk & Remote Access

#### SSH
- **OpenSSH Server**: Läuft auf Port 22
- **Authentifizierung**: Password + Public Key
- **IP-Whitelist** bei Bedarf aktivierbar
- **SSH-Konfiguration**: `/etc/ssh/sshd_config` (Linux) oder `C:\ProgramData\ssh\sshd_config` (Windows)

#### HTTPS
- **Cloudflare Tunnel**: Externe Verbindungen über `renlern.org`
- **Canonical Host**: Automatisches Redirect von www
- **CORS**: Eingestellt (später restriktiver machen wenn nötig)

### 5. Admin-Funktionen

#### Benutzerverwaltung

**Alle Benutzer auflisten:**
```bash
curl -H "X-Admin-Password: admin123" https://renlern.org/api/admin/users
```

**Home Cloud Zugriff für Benutzer gewähren:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Admin-Password: admin123" \
  -d '{"user_id": 2, "allowed": true}' \
  https://renlern.org/api/admin/home-access/set
```

**Home Cloud Zugriff für Benutzer sperren:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Admin-Password: admin123" \
  -d '{"user_id": 2, "allowed": false}' \
  https://renlern.org/api/admin/home-access/set
```

**Admin-Passwort ändern:**
Umgebungsvariable `ADMIN_PASSWORD` setzen (Standard: `admin123`)

### 6. Konfiguration

#### Umgebungsvariablen

```bash
# SECRET_KEY für Flask Session
export SECRET_KEY="your-secret-key-here"

# Admin-Passwort für Admin APIs
export ADMIN_PASSWORD="secure-admin-passwort"

# Cloudflare Tunnel Token (falls auto-start aktiviert)
export CLOUDFLARE_TUNNEL_TOKEN="your-token-here"
```

#### Datei-Größenlimit

In `server_v2.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 * 1024  # 4 GB
```

#### Login-Versuche begrenzen

In `server_v2.py`:
```python
MAX_LOGIN_ATTEMPTS = 5           # Max attempts
LOGIN_ATTEMPT_TIMEOUT = 900      # 15 minutes
```

### 7. Überwachung & Logging

#### Log-Informationen
- IP-Adressen aller Logins werden gespeichert
- Failed & successful login attempts werden protokolliert
- User-Agent (Browser) wird trackiert
- Letzter Zugriff wird aktualisiert

#### Databankabfrage für Logins
```sql
SELECT * FROM login_attempts WHERE attempted_at > '2024-01-01' ORDER BY attempted_at DESC;
```

### 8. Bestpraktiken

#### Für Server-Admin
1. **Regelmäßige Backups**: `lernapp.db` täglich sichern
2. **Logs prüfen**: `login_attempts` Tabelle regelmäßig überprüfen
3. **Passwörter**: Admin-Passwort ändern (nicht Standard)
4. **Firewall**: SSH Port 22 nur für vertrauenswürdige IPs öffnen
5. **Updates**: Python & Abhängigkeiten regelmäßig aktualisieren

#### Für Benutzer
1. **Starke Passwörter**: Mindestens 8 Zeichen mit Groß-, Kleinbuchstaben, Zahlen
2. **Nicht am fremden Computer**: Private Daten nicht auf öffentlichen PCs hochladen
3. **HTTPS nutzen**: Immer verschlüsselte Verbindung verwenden
4. **Logout**: Nach Gebrauch abmelden

### 9. Häufig gestellte Fragen

**F: Wie kann ich einen Benutzer entsperren, der zu oft falsche Passwörter eingegeben hat?**

A: Die Speerre ist zeitlich begrenzt (15 Minuten). Nach dieser Zeit können sie sich wieder anmelden versuchen.

**F: Wie ändere ich das Admin-Passwort?**

A: Setzen Sie die Umgebungsvariable `ADMIN_PASSWORD` vor dem Start:
```bash
set ADMIN_PASSWORD="neues-passwort"  # Windows
export ADMIN_PASSWORD="neues-passwort"  # Linux
```

**F: Kann ich nur bestimmte Dateitypen erlauben?**

A: Ja, bearbeiten Sie `EXT_CATEGORY` in `server_v2.py` und ändern Sie die Dateitypen pro Kategorie.

**F: Ist meine Datei sicher verschlüsselt?**

A: Server speichert Dateien unverschlüsselt. Für extra Sicherheit: Vor Upload selbst verschlüsseln (7Zip, WinRAR, Veracrypt)

### 10. ⚠️ WICHTIGE SICHERHEITSWARNUNGEN

1. **SECRET_KEY**: MUSS in Produktion ein starkes Passwort sein!
2. **ADMIN_PASSWORD**: NICHT in Code commit, nutze Umgebungsvariablen!
3. **SSH**: Port 22 sollte geschlossen sein für Internet-Zugriff (hinter Firewall/VPN)
4. **SSL/TLS**: In Produktion IMMER HTTPS verwenden!
5. **Datenschutz**: DB-Datei nicht in öffentlichen Verzeichnisse speichern

---

**Letzte Aktualisierung**: 15. April 2026
**Version**: RenLern Server v2.1 (Security Edition)
