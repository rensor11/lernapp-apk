# 🎓 Lernapp mit Datenbankanbindung - Installationsanleitung

## Was ist neu?

✅ **Datenbankunterstützung** - SQLite (keine Installation nötig!)
✅ **Benutzerkonten** - Registrierung & Login mit Benutzername + Passwort
✅ **Sichere Passwörter** - Gehashed mit Werkzeug
✅ **Von überall zugänglich** - Lokales Netzwerk oder Internet
✅ **Automatisches Speichern** - Alle Daten in der Datenbank
✅ **Fragen aus Datenbank** - fragenpool.json wird beim Start geladen

---

## 📋 Voraussetzungen

- Python 3.8 oder höher
- Terminal/Command Prompt
- Ein Texteditor (für Einstellungen)

---

## 🚀 Schritt 1: Flask installieren

**Windows (Command Prompt als Admin):**
```bash
pip install -r requirements.txt
```

Oder einzeln:
```bash
pip install Flask
pip install Werkzeug
```

**Mac/Linux (Terminal):**
```bash
pip3 install -r requirements.txt
```

Oder:
```bash
pip3 install Flask Werkzeug
```

---

## 📁 Schritt 2: Dateien vorbereiten

Du brauchst folgende Dateien im **selben Ordner**:

```
dein-ordner/
├── server_neu.py          ← Server-Programm
├── lernapp_neu.html       ← HTML-Seite
├── fragenpool__2_.json    ← Fragen (wird beim Start geladen)
└── requirements.txt       ← Dependencies (optional)
```

**WICHTIG:** Stelle sicher, dass die Datei `fragenpool__2_.json` im selben Ordner ist!

---

## ▶️ Schritt 3: Server starten

### Windows (Command Prompt):
```bash
cd "C:\pfad\zu\deinem\ordner"
python server_neu.py
```

### Mac/Linux (Terminal):
```bash
cd /pfad/zu/deinem/ordner
python3 server_neu.py
```

Du solltest diese Ausgabe sehen:
```
╔════════════════════════════════════════════════════╗
║          🎓 Lernapp Server mit Datenbank           ║
╚════════════════════════════════════════════════════╝

✅ Server läuft!

🌐 Lokale Adresse:    http://localhost:5000
🌐 Netzwerk-Adresse:  http://192.168.x.x:5000

📱 Zugriff von überall im Netzwerk möglich!

Datenbank: lernapp.db (SQLite)
- Benutzer: gespeichert
- Fragen: aus fragenpool.json geladen
- Fortschritt: wird gespeichert

🛑 Server beenden: Drücke Ctrl+C
```

---

## 🌐 Schritt 4: App öffnen

### Auf diesem Computer:
Öffne deinen Browser und gehe zu:
```
http://localhost:5000
```

### Von anderen Computern im Netzwerk:
Ersetze `192.168.x.x` mit der IP-Adresse deines Computers:
```
http://192.168.1.100:5000
```

(Die IP siehst du in der Server-Ausgabe!)

---

## 👤 Schritt 5: Benutzer erstellen & anmelden

1. **Registrieren:**
   - Klick auf "Registrieren"
   - Gib einen Benutzernamen ein (mind. 3 Zeichen)
   - Gib ein Passwort ein (mind. 6 Zeichen)
   - Klick "Registrieren"

2. **Anmelden:**
   - Klick auf "Anmelden"
   - Gib Benutzername & Passwort ein
   - Klick "Anmelden"

3. **Quiz spielen:**
   - Wähle eine Kategorie
   - Beantworte die Fragen
   - Deine Fortschritt wird gespeichert

---

## 📊 Features der App

### Quiz-Funktionen:
- 📚 Nach Kategorien sortiert
- 📈 Fortschritt & Erfolgsquote
- 💾 Alles wird automatisch gespeichert
- ➕ Neue Fragen hinzufügen

### Datenbankfunktionen:
- 👥 Benutzerkonten mit gehashten Passwörtern
- 📝 Fragen in SQLite-Datenbank
- 📊 Benutzer-Fortschritt wird gespeichert
- 🔄 fragenpool.json wird beim Start in DB geladen

---

## 🔧 Fehlerbehebung

### Problem: "Flask not found"
**Lösung:** Flask installieren
```bash
pip install Flask
# oder
pip3 install Flask
```

### Problem: "Port 5000 wird bereits verwendet"
**Lösung 1:** Anderes Programm beenden (z.B. Spotify, Zoom)
**Lösung 2:** Port ändern in `server_neu.py` letzte Zeile:
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # 5001 statt 5000
```

### Problem: "fragenpool.json nicht gefunden"
**Lösung:** 
- Überprüfe, dass die Datei im selben Ordner ist
- Dateienname muss genau `fragenpool__2_.json` heißen
- Oder ändere den Namen in `server_neu.py` Zeile 101:
```python
DATABASE = 'fragenpool.json'  # <- hier anpassen
```

### Problem: Benutzer können sich nicht registrieren
**Lösung:** 
- Überprüfe die Konsole auf Fehler
- Stelle sicher, dass Python 3.8+ installiert ist
- Lösche die `lernapp.db` Datei und starte neu

### Problem: Benutzer können sich nicht anmelden
**Lösung:**
- Benutzername muss exakt gleich sein (Groß/Kleinschreibung)
- Passwort wird gehashed - "falsch" ist eine Sicherheitsfeature
- Registriere einen neuen Benutzer

---

## 🌍 Von überall zugänglich machen

### Lokales Netzwerk (Empfohlen):
Alle Computer im selben WLAN können zugreifen:
```
http://192.168.1.100:5000
```

### Übers Internet (Port Forwarding nötig):
1. Öffne deinen Router-Admin-Panel
2. Aktiviere Port Forwarding für Port 5000
3. Andere können dann zugreifen über deine öffentliche IP

**SICHERHEIT:** Bevor du das tust:
- ändere den Default Secret Key in `server_neu.py`
- verwende ein sicheres Passwort für Admin-Konten
- überlege ob du wirklich ins Internet freigeben willst

---

## 📚 Datenbank-Struktur

Die `lernapp.db` speichert:

### users (Tabelle)
```
id              - Eindeutige Nummer
username        - Benutzername (einzigartig)
password_hash   - Gehashtes Passwort (NIEMALS Klartext!)
created_at      - Registrierungs-Zeit
```

### questions (Tabelle)
```
id              - Eindeutige Nummer
category        - Kategorie (z.B. "Linux Grundlagen")
type            - Fragetyp (z.B. "multiple")
question        - Die Frage selbst
options         - JSON mit Antwortoptionen
created_at      - Erstellungs-Zeit
```

### user_progress (Tabelle)
```
id              - Eindeutige Nummer
user_id         - Benutzer-ID
question_id     - Frage-ID
answered        - Wurde beantwortet?
correct         - War die Antwort richtig?
created_at      - Zeitstempel
```

---

## 🔐 Sicherheit

✅ **Passwörter:** Mit Werkzeug gehashed (PBKDF2)
✅ **Sessions:** Flask Session-Management
✅ **Datenbank:** SQLite mit Prepared Statements (SQL-Injection-geschützt)
✅ **CORS:** Aktiviert für Netzwerk-Zugriff

**Warnung:** 
- Keine SSL/TLS im Standard (nur lokal sicher)
- Für Internet brauchst du HTTPS!
- Der `secret_key` ist zufällig - perfekt für Lokal-Netzwerk

---

## 💡 Tipps & Tricks

### Alle Daten zurücksetzen:
```bash
# Lösche die Datenbank
rm lernapp.db
# oder auf Windows:
del lernapp.db

# Starte den Server neu - neue leere Datenbank wird erstellt
```

### Backup der Daten:
```bash
# Kopiere einfach die lernapp.db Datei
# Sie enthält alles (Benutzer, Fragen, Fortschritt)
```

### Neue Fragen importieren:
1. Editiere `fragenpool__2_.json`
2. Starte den Server neu
3. Die Fragen werden automatisch in die DB geladen

### Performance:
- SQLite ist perfekt für bis zu 1000 Benutzer
- Bei mehr Benutzern: upgrade auf PostgreSQL/MySQL

---

## 📞 Support

Falls etwas nicht funktioniert:

1. **Prüfe die Konsole** - dort sind die Fehler
2. **Starte neu** - manchmal hilft das
3. **Überprüfe Datei-Namen** - müssen genau stimmen
4. **Python-Version prüfen** - muss 3.8+ sein:
```bash
python --version
# oder
python3 --version
```

---

## 🎉 Fertig!

Deine Lernapp mit Datenbank läuft jetzt!

- Benutzer können sich anmelden/registrieren
- Fragen werden aus der Datenbank geladen
- Alles wird automatisch gespeichert
- Von überall im Netzwerk zugänglich

Viel Spaß beim Lernen! 🚀

