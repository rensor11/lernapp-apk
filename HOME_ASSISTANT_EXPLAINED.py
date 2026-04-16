#!/usr/bin/env python3
"""
HOME ASSISTANT INTEGRATION - SCHRITT-FÜR-SCHRITT ERKLÄRUNG
"""

print("""
╔════════════════════════════════════════════════════════════════════════╗
║              HOME ASSISTANT FÜR ROUTER + NETZWERK-GERÄTE              ║
╚════════════════════════════════════════════════════════════════════════╝

📋 WAS WIRD GENAU GEMACHT?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Architektur mit Home Assistant:

    ┌─ Dein Laptop/PC
    │
    ├─→ LernApp Server (:5000) ← Du willst von hier Geräte steuern
    │    └──→ REST API Aufrufe
    │
    ├─→ Home Assistant Server (:8123)  ← NEUE KOMPONENTE
    │    └──→ Integration zur Fritz!Box
    │    └──→ Hat ALLE Router-Infos + Netzwerk-Status
    │
    └─→ Fritz!Box Router (:80, :49000)  ← Wird von Home Assistant "überwacht"
         └──→ AVM HomeAutomation API
         └──→ Smart Home Geräte Management
         └──→ WLAN Control
         └──→ Gast-Netzwerk Control


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 WAS WIRD KONKRET MÖGLICH?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  ROUTER SELBST STEUERN:
    ✅ WLAN An/Aus
    ✅ Gast-Netzwerk An/Aus
    ✅ USB-Geräte An/Aus (z.B. externe Festplatte)
    ✅ DECT Repeater Control
    ✅ Mesh Network Status
    ✅ WPS aktivieren/deaktivieren

2️⃣  VERBUNDENE GERÄTE ÜBERWACHEN:
    ✅ Live Device List (Wer ist im Netzwerk online?)
    ✅ MAC-Adressen
    ✅ Hostnames
    ✅ IP-Adressen
    ✅ Verbindungstyp (WiFi 2.4GHz / 5GHz / LAN / DECT)
    ✅ Signal-Stärke (WiFi Devices)
    ✅ Bandbreite-Nutzung

3️⃣  ERWEITERTE NETZWERK-KONTROLLE:
    ✅ Wake-on-LAN (Geräte vom PC aus aufwecken)
    ✅ MAC-Filtering (Geräte blockieren/erlauben)
    ✅ Priorisierung (Gaming PC Priorität geben)
    ✅ Gastnetzwerk-Profil erstellen
    ✅ WLAN-Zeitplan (z.B. WLAN nachts ausschalten)

4️⃣  HEIMAUTOMATION VORBEREITUNG:
    ✅ Zigbee Stick anschließbar (für echte Smart Home Devices später)
    ✅ Z-Wave Geräte support
    ✅ MQTT Integration (für weitere IoT Geräte)
    ✅ HTTP/REST Webhooks für Custom Devices

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  WICHTIG: WAS IST **NICHT** MÖGLICH?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Ein EINZELNES GERÄT direkt "ansteuern"
   → Router ist nur Gateway, kein Command-Center
   → Du kannst den PC nicht vom Router anschalten (nur Wake-on-LAN)
   → Du kannst das Handy vom Router nicht steuern
   
   ABER: Du kannst überwachen & blockieren!

❌ Betriebssystem-Befehle remote ausführen
   → "Herunterfahren" oder "Reboot" ist nicht möglich
   → Router kann das nicht

✅ WAS ABER FUNKTIONIERT:
   → "Ist Laptop online?" → Home Assistant weiß das
   → "Laptop aufwecken" → Wake-on-LAN funktioniert
   → "WLAN des Laptops trennen" → Durch Blockieren via MAC-Filter

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 SCHRITT-FÜR-SCHRITT IMPLEMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCHRITT 1: Home Assistant INSTALLIEREN
────────────────────────────────────────
Option A: Docker (EMPFOHLEN - Schnellste)
    docker run -d \\
      --name homeassistant \\
      -e TZ=Europe/Berlin \\
      -v homeassistant_config:/config \\
      -p 8123:8123 \\
      homeassistant/home-assistant:latest

Option B: Als Service auf Windows/Linux
    pip install homeassistant
    hass --config ~/homeassistant --open-ui

Option C: Raspberry Pi (Traditionell)
    # Auf Raspberry Pi installieren (separater Computer)
    # Dann über Netzwerk ansprechen


SCHRITT 2: Home Assistant STARTEN
────────────────────────────────────
    http://localhost:8123
    → Create Account
    → Name: Dein Name
    → Username: dein_username
    → Password: dein_passwort


SCHRITT 3: FritzBox Integration AKTIVIEREN
────────────────────────────────────────────
    In Home Assistant Web-UI:
    
    Settings
    → Devices & Services
    → Create Automation
    → Search: "Fritz!Box"
    → Klick auf "Fritz!Box Home Network"
    
    Dann:
    - Hostname: 192.168.178.1 oder fritz.box
    - Username: admin (meistens leer!)
    - Password: Dein Router-Passwort
    
    → FERTIG! Home Assistant verbunden


SCHRITT 4: LernApp MIT Home Assistant verbinden
─────────────────────────────────────────────────

    In LernApp Code (server_v2.py):
    
    SCHRITTE:
    a) Home Assistant REST API Token generieren
       Settings → Automations & Scenes
       → Create Token
       → Copy Token
    
    b) In server_v2.py neu hinzufügen:
    
        HOME_ASSISTANT_URL = "http://localhost:8123"
        HOME_ASSISTANT_TOKEN = "eyJhbGciOi..."  # Token von oben
        
        def control_device_via_ha(device_id, action):
            headers = {
                "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}",
                "content-type": "application/json",
            }
            
            # Beispiel: WLAN ausschalten
            data = {
                "entity_id": "switch.fritz3490_pro_guest_wifi",
                "service": "switch.turn_off"
            }
            
            response = requests.post(
                f"{HOME_ASSISTANT_URL}/api/services/switch/turn_off",
                json=data,
                headers=headers
            )


SCHRITT 5: API Routes in LernApp ANPASSEN
───────────────────────────────────────────

    @app.route('/api/smarthome/device/<int:device_id>/command', methods=['POST'])
    def control_device(device_id):
        data = request.get_json() or {}
        command = data.get('command')
        
        if command == 'wlan_toggle':
            # Home Assistant aufrufen
            response = ha_control_wlan(state=data.get('state'))
            return jsonify({'success': True, 'result': response})
        
        elif command == 'guest_wifi':
            response = ha_control_guest_wifi(state=data.get('state'))
            return jsonify({'success': True, 'result': response})
        
        elif command == 'get_devices':
            response = ha_get_connected_devices()
            return jsonify({'success': True, 'devices': response})


SCHRITT 6: UI UPDATE (SmartHome Page)
──────────────────────────────────────
    Buttons in smarthome.html:
    
    <button onclick="toggleWLAN()">WLAN An/Aus</button>
    <button onclick="toggleGuestWiFi()">Gast-Netzwerk</button>
    <button onclick="getDevices()">Verbundene Geräte anzeigen</button>
    
    Script:
    
    async function getDevices() {
        const res = await fetch('/api/smarthome/device/1/command', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                command: 'get_devices'
            })
        });
        const data = await res.json();
        
        console.log('Geräte im Netzwerk:', data.devices);
        // Tabelle anzeigen mit allen Online-Geräten
    }


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 VERFÜGBARE ENTITIES IN HOME ASSISTANT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Nach Integration siehst du Diese Entities:

    ✅ switch.fritz3490_pro_wifi
       → An: WLAN einschalten
       → Aus: WLAN ausschalten
    
    ✅ switch.fritz3490_pro_guest_wifi
       → Gast-Netzwerk steuern
    
    ✅ switch.fritz3490_pro_usb1
       → USB Port 1 (externe Festplatte, etc.)
    
    ✅ device_tracker.fritz3490_pro
       → Alle verbundenen Geräte
       → Live-Status wer online ist
    
    ✅ binary_sensor.fritz3490_pro_internet_access
       → Internet aktiv? Ja/Nein
    
    ✅ sensor.fritz3490_pro_downstream_speed
    ✅ sensor.fritz3490_pro_upstream_speed
       → Aktuelle Internet-Geschwindigkeit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 KONKRETE CODE-BEISPIELE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEISPIEL 1: WLAN alle Geräte abschalten
─────────────────────────────────────────
    
    # Home Assistant REST API
    curl -X POST http://localhost:8123/api/services/switch/turn_off \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"entity_id": "switch.fritz3490_pro_wifi"}'


BEISPIEL 2: Alle verbundenen Geräte auflisten
──────────────────────────────────────────────
    
    # Home Assistant REST API
    curl http://localhost:8123/api/states \\
      -H "Authorization: Bearer YOUR_TOKEN" | grep device_tracker


BEISPIEL 3: Gast-Netzwerk einschalten + Zeitplan
─────────────────────────────────────────────────
    
    # Home Assistant REST API
    curl -X POST http://localhost:8123/api/services/switch/turn_on \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"entity_id": "switch.fritz3490_pro_guest_wifi"}'
    
    # Dann automatisierung: Gast-Netzwerk täglich um 18 Uhr ausschalten
    # → Via Home Assistant UI konfigurierbar


BEISPIEL 4: MAC-Blockieren (Device trennen)
─────────────────────────────────────────
    
    # Via Home Assistant Script:
    device_mac = "AA:BB:CC:DD:EE:FF"
    action = "block"  # oder "allow"
    
    # Home Assistant triggert Fritz!Box-Befehl
    # Device wird vom Netzwerk getrennt


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️  TIMELINE & AUFWAND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ⏱️  5 Min:   Docker Home Assistant installieren
    ⏱️  5 Min:   Home Assistant Setup (Account)
    ⏱️  10 Min:  Fritz!Box Integration konfigurieren
    ⏱️  15 Min:  API Token generieren
    ⏱️  30 Min:  LernApp Code anpassen (server_v2.py)
    ⏱️  20 Min:  UI Update (smarthome.html)
    ⏱️  10 Min:  Testen & Debuggen
    ────────────────────
    ≈ 95 Min: Fertig! 🎉


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 NÄCHSTE SCHRITTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENTSCHEIDUNG:

Option A: "Ja, lass mich Home Assistant jetzt installieren!"
→ Ich zeige dir Docker-Befehl & setup

Option B: "Ich will das JETZT implementieren"
→ Ich schreibe dir den kompletten Code

Option C: "Ich möchte erst testen"
→ Ich zeig dir ein Test-Setup auf Windows

Option D: "Zu kompliziert, gibt es EINFACHER?"
→ Ja! Dann machen wir einen HTTP-Proxy (aber begrenzte Features)

Sag Bescheid was du willst! 🚀
""")
