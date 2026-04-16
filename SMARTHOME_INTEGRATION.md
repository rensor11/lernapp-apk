## 🏠 Smart Home Integration - RenLern Server

Vollständiges Smart Home System mit Fritz!Box Unterstützung und automatischer Netzwerk-Geräte-Erkennung.

### ✨ Features

#### ✅ Automatische Netzwerk-Erkennung
- **Keine IP/Port Eingabe nötig** - Alles wird automatisch gescannt
- **Fritz!Box Auto-Connect** - Verbindet sich automatisch zu 192.168.1.1
- **Alle Geräte finden** - Smart Plugs, Lampen, Temperatur-Sensoren, Router, etc.
- **Schneller Scan** - Inklusive Port-Erkennung

#### ✅ Geräte-Verwaltung
- **Online/Offline Status** - Live Überwachung
- **Geräteverwaltung** - Hinzufügen/Löschen von Geräten
- **Steuerung** - Ein/Aus schalten für kontrollierbare Geräte
- Unterstützung für **Smart Plugs**, **Lampen**, **Temperatur-Sensoren**, **Alle Netzwerk-Geräte**

#### ✅ Fritz!Box Integration (7530 AX)
- TR-064 API Unterstützung
- Smart Home Device Detection
- Sichere Verbindung
- Authentifizierung (optional)

---

### 🚀 Verwendung

#### 1. **Smart Home Seite öffnen**
```
https://renlern.org/smarthome
```

#### 2. **Fritz!Box verbinden**
- Klick: "✨ Fritz!Box Setup"
- Klick: "🚀 Verbindung testen"
- Die Fritz!Box wird automatisch ermittelt (192.168.1.1)

#### 3. **Netzwerk scannen**
- Klick: "🔍 Scan Netzwerk"
- Alle Geräte im Netzwerk werden ermittelt
- Smart Plugs, Lampen, etc. werden automatisch erkannt

#### 4. **Geräte steuern**
```
- ➕ Hinzufügen     - Gerät speichern
- 💡 An            - Gerät anschalten (wenn unterstützt)
- 🌑 Aus           - Gerät ausschalten (wenn unterstützt)
```

---

### 📱 Unterstützte Geräte

| Gerät | Status | Steuerbar | Port |
|-------|--------|-----------|------|
| Fritz!Box | Auto | ✅ Ja | 49153 |
| Smart Plug | Auto | ✅ Ja | 80, 8080 |
| Smart Lampe | Auto | ✅ Ja | 80, 8080 |
| Temperatur-Sensor | Auto | ❌ Nein | 8000 |
| IP Kamera | Auto | - | 80, 8080 |
| MQTT Broker | Auto | - | 1883, 8883 |
| Drucker | Auto | - | 80 |
| Router | Auto | - | 80, 443 |

---

### 🔧 Technische Details

#### API Endpoints

```
GET /api/smarthome/devices
  → Alle Geräte des Users laden

GET /api/smarthome/scan?user_id=1
  → Netzwerk scannen nach Geräten
  
POST /api/smarthome/fritzbox/connect
  → Mit Fritz!Box verbinden
  {
    "user_id": 1,
    "fritzbox_ip": "192.168.1.1"
  }

POST /api/smarthome/device/add
  → Neues Gerät hinzufügen
  {
    "user_id": 1,
    "device_name": "Wohnzimmer Lampe",
    "device_type": "Lampe",
    "ip_address": "192.168.1.50",
    "port": 80,
    "protocol": "http"
  }

POST /api/smarthome/device/control
  → Gerät steuern
  {
    "user_id": 1,
    "device_id": 5,
    "command": "power",
    "value": 1  # 1 = an, 0 = aus
  }
```

#### Datenbank Schema

```sql
CREATE TABLE smarthome_devices (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    device_name TEXT,
    device_type TEXT,          -- Lampe, Stecker, Sensor, etc.
    ip_address TEXT,
    port INTEGER,
    protocol TEXT,             -- http, https, mqtt
    auth_token TEXT,           -- Optional für APIs mit Auth
    status TEXT,               -- online, offline
    last_seen TEXT,
    created_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

### 🛠️ Setup für Fritz!Box 7530 AX

#### 1. **Default-Einstellungen**
- **IP:** 192.168.1.1 (automatisch erkannt)
- **HTTP Port:** 49000 (UPnP)
- **Zugriff:** Ohne Password (lokal)

#### 2. **Smart Home Aktivieren**
- Fritz!Box Weboberfläche: `http://192.168.1.1`
- "Smart Home" im Menü aktivieren
- Geräte werden automatisch erkannt

#### 3. **Smart Devices koppeln**
```
- Fritz DECT 200 (Smart Plug)
- Fritz DECT 301 (Thermo)
- Fritz DECT 310 (Thermo)
```

---

### 🔒 Sicherheit

✅ **Authentifizierung:**
- Nur angemeldete Benutzer können auf Smart Home zugreifen
- Jeder Benutzer sieht nur seine eigenen Geräte

✅ **Netzwerk-Sicherheit:**
- Lokales Netzwerk (192.168.x.x)
- Keine externen Zugriffe auf Rohe Geräte
- Nur über RenLern Portal (mit Cloudflared)

✅ **Verbindungs-Sicherheit:**
- HTTP für lokale Verbindungen OK
- HTTPS für externe Verbindungen (via Cloudflared)
- Optionale API-Authentifizierung

---

### 🎯 Beispiel-Szenarien

#### Szenario 1: Lichter & Steckdosen steuern
```
1. Smart Home öffnen
2. Netzwerk scannen
3. "Wohnzimmer Lampe" hinzufügen
4. "Schlafzimmer Stecker" hinzufügen
5. 💡 Lampen an / 🌑 Lampen aus
```

#### Szenario 2: Temperatur überwachen
```
1. Fritz DECT 310 mit Fritz!Box koppeln
2. Smart Home Seite - Scan
3. Temperatur-Sensoren werden angezeigt
4. Live Temperatur-Anzeige
5. Historische Daten speichern
```

#### Szenario 3: Automatisierung (Zukunft)
```
- Szene "Gute Nacht": Alle Lichter aus
- Szene "Nach Hause": Lichter hell
- Zeitplan: Lichter um 18:00 ein
- Temperatur-Alarm: SMS wenn zu kalt
```

---

### 📊 Netzwerk-Scan Details

#### Scan-Prozess:
1. **Lokale IP ermitteln:** 192.168.1.x
2. **Ping Scan:** Alle 50 IPs im lokalen Netz
3. **Port-Scan:** Häufige Smart Home Ports
   - 80 / 8080  (HTTP Services)
   - 443        (HTTPS)
   - 1883 / 8883 (MQTT)
   - 49153      (Fritz!Box UPnP)
   - etc.
4. **Geräte identifizieren:** Hostname + Service-Typ
5. **Status Collect:** Online/Offline

#### Scan-Zeit:
- Durchschnitt: 10-30 Sekunden
- Abhängig von Netzwerk-Größe
- Multi-threaded für Geschwindigkeit

---

### ⚡ Schnellstart

```bash
# 1. Server starten
py server_v2.py

# 2. Browser öffnen
https://renlern.org

# 3. Login
Username: test
Password: test

# 4. Smart Home
Klick auf "Smart Home" im Menü

# 5. Scan
Klick "🔍 Scan Netzwerk"

# 6. Geräte
Alle Geräte erscheinen in der Liste

# 7. Steuern
Klick auf "💡 An" / "🌑 Aus"
```

---

### 🐛 Troubleshooting

#### Problem: "Netzwerk-Scan fehlgeschlagen"
- **Lösung:** Firewall zulassen (Ping + Port Scanning)
- Oder: Manuell IP/Port eingeben

#### Problem: "Fritz!Box nicht gefunden"
- **Lösung:** In Router: http://192.168.1.1 prüfen
- Oder: Smart Home im Fritzbox-Menü aktivieren

#### Problem: "Gerät ist offline"
- **Lösung:** Gerät prüfen - Stromversorgung?
- Oder: Gerät aus/an Netzwerk neu verbinden

#### Problem: "Keine Steuerung möglich"
- **Lösung:** Nicht alle Geräte sind steuerbar
- Nur Smart Plugs / Lampen können geschaltet werden
- Sensoren / Router nur Überwachung

---

### 📝 Protokoll-Unterstützung

```
HTTP  - Smart Plugs, Lampen, Server
HTTPS - Sichere Verbindungen
MQTT  - IoT Brokers
UPnP  - Fritz!Box, Netzwerk-Geräte
```

---

### 🔌 Port-Erkennungs-Logik

| Port | Service | Gerättyp | Steuerbar |
|------|---------|----------|-----------|
| 80 | HTTP | Smart Device | ✅ |
| 8080 | HTTP Alt | Smart Device | ✅ |
| 443 | HTTPS | Secure Service | - |
| 1883 | MQTT | IoT Broker | - |
| 8883 | MQTT-TLS | IoT Broker | - |
| 49153 | UPnP | Fritz!Box | ✅ |

---

**Version:** 1.0  
**Datum:** 16. April 2026  
**Fritz!Box Modell:** 7530 AX  
**Kompatibilität:** Windows 10/11, Python 3.8+
