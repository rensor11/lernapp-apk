#!/usr/bin/env python3
"""
Fritz!Box API Debug - Teste die Geräte-Steuerung
"""
import requests
import socket
import xml.etree.ElementTree as ET

FRITZ_IP = "192.168.178.1"
FRITZ_PORT = 49000

print("=" * 70)
print("FRITZ!BOX API DEBUGGING")
print("=" * 70)

# 1. Fritz!Box Verbindung
print("\n[1] FRITZ!BOX VERBINDUNG")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    result = s.connect_ex((FRITZ_IP, FRITZ_PORT))
    s.close()
    
    if result == 0:
        print(f"    ✅ Port {FRITZ_PORT} offen - Fritz!Box erreichbar")
    else:
        print(f"    ❌ Port {FRITZ_PORT} nicht erreichbar")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 2. UPnP Beschreibung abrufen
print("\n[2] UPnP BESCHREIBUNG")
try:
    url = f"http://{FRITZ_IP}:{FRITZ_PORT}/upnp/device.xml"
    r = requests.get(url, timeout=5)
    
    if r.status_code == 200:
        print(f"    ✅ Device-Beschreibung abrufbar ({len(r.text)} bytes)")
        
        # Parse XML
        try:
            root = ET.fromstring(r.text)
            # Finde Modell-Info
            namespaces = {'upnp': 'urn:Belkin:device-1-0'}
            model = root.find('.//model', namespaces) or root.find('.//modelName')
            if model is not None:
                print(f"    ℹ️ Modell: {model.text}")
        except:
            print(f"    ⚠️ XML Parse Fehler")
    else:
        print(f"    ❌ HTTP {r.status_code}")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 3. Teste TR-064 Schnittstelle
print("\n[3] TR-064 SCHNITTSTELLE")
try:
    # SOAP Request für WLAN Status
    soap_action = "urn:FRITZ:service:WANDevice:1#GetCommonLinkProperties"
    
    soap_body = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:GetCommonLinkProperties xmlns:u="urn:FRITZ:service:WANDevice:1">
    </u:GetCommonLinkProperties>
  </s:Body>
</s:Envelope>"""
    
    headers = {
        'Content-Type': 'text/xml; charset="utf-8"',
        'SOAPAction': soap_action
    }
    
    url = f"http://{FRITZ_IP}:49000/upnp/control/WANDevice1"
    r = requests.post(url, data=soap_body, headers=headers, timeout=5)
    
    if r.status_code == 200:
        print(f"    ✅ SOAP Request erfolgreich")
        if 'NewWANAccessType' in r.text:
            print(f"    ℹ️ Fritz!Box antwortet auf SOAP-Befehle")
    else:
        print(f"    ⚠️ HTTP {r.status_code} - SOAP möglicherweise nicht verfügbar")
except requests.exceptions.Timeout:
    print(f"    ⚠️ Timeout - Fritz!Box antwortet langsam")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 4. Netzwerk-Info
print("\n[4] NETZWERK STATUS")
try:
    # Versuche Status zu ermitteln via HTML-Interface
    url = f"http://{FRITZ_IP}/home/home.html"
    r = requests.get(url, timeout=3)
    
    if r.status_code == 200:
        print(f"    ✅ Web-Interface erreichbar")
    else:
        print(f"    ⚠️ Web-Interface HTTP {r.status_code}")
except requests.exceptions.Timeout:
    print(f"    ⚠️ Web-Interface Timeout")
except Exception as e:
    print(f"    ⚠️ Web Interface nicht erreichbar: {type(e).__name__}")

# 5. Empfehlungen
print("\n[5] EMPFEHLUNGEN FÜR SMART HOME STEUERUNG")
print("""
    Option A: TR-064/SOAP API (funktioniert oft nicht ohne Auth)
    - ✅ Nützlich für: Netzwerk-Infos, Verbindungsstatus
    - ❌ Problem: Benötigt oft Passwort
    
    Option B: Home Automation HTTP Interface  
    - Benötigte Parameter: nicht standardisiert
    - Variiert je nach Fritz!Box Modell
    
    Option C: AHA (AVM Home Automation)
    - ✅ Für: Smart Home Geräte (FRITZ!DECT, FRITZ!Powerline)
    - Parameter: /home/home.html?sid=...
    - Benötigt: Session-ID (Login erforderlich)
    
    Option D: Externe Integrationen
    - ✅ Home Assistant Integration
    - ✅ Node-RED Nodes
    - ✅ HTTP API Wrapper
""")

print("\n" + "=" * 70)
