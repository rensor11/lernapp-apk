#!/usr/bin/env python3
"""
Fritz!Box Model Detection und Service Discovery
"""
import requests
import socket
from urllib.parse import urlparse
import struct
import json

FRITZ_IP = "192.168.178.1"

print("=" * 70)
print("FRITZ!BOX MODELL & DIENSTE ERKENNUNG")
print("=" * 70)

# 1. Verschiedene Ports testen
print("\n[1] OFFENE PORTS SCANNEN")
common_ports = {
    80: "HTTP",
    443: "HTTPS",
    49000: "UPnP",
    49200: "SSDP",
    5000: "HTTP Alt",
    8080: "HTTP Alt2",
    8443: "HTTPS Alt"
}

open_ports = []
for port, service in common_ports.items():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex((FRITZ_IP, port))
        s.close()
        if result == 0:
            open_ports.append((port, service))
            print(f"    ✅ Port {port:5d} ({service:12s}) - OFFEN")
    except:
        pass

if not open_ports:
    print("    ❌ Keine offenen Ports gefunden!")

# 2. Versuche Standard URLs
print("\n[2] STANDARD URLS TESTEN")
urls_to_test = [
    ("http://192.168.178.1/", "Haupt-URL"),
    ("http://192.168.178.1:80/", "Port 80"),
    ("http://192.168.178.1:49000/", "Port 49000"),
    ("http://192.168.178.1/cgi-bin/", "CGI Interface"),
    ("http://192.168.178.1/api/", "API Interface"),
    ("http://fritz.box/", "fritz.box Host"),
]

for url, name in urls_to_test:
    try:
        r = requests.get(url, timeout=2)
        print(f"    ✅ {name:20s} HTTP {r.status_code}")
        
        # Versuche Modell zu extrahieren
        if 'FRITZ' in r.text or 'Fritzbox' in r.text or 'fritzbox' in r.text:
            print(f"       → Fritz!Box erwähnt im HTML")
        if 'model' in r.text.lower():
            print(f"       → Model-Info im HTML vorhanden")
    except requests.exceptions.Timeout:
        print(f"    ⏱️  {name:20s} - Timeout")
    except Exception as e:
        print(f"    ⚠️  {name:20s} - {type(e).__name__}")

# 3. Teste SSDP Discovery
print("\n[3] SSDP DISCOVERY")
try:
    # SSDP M-SEARCH für Geräte im Netzwerk
    ssdp_request = b"""M-SEARCH * HTTP/1.1\r
HOST: 239.255.255.250:1900\r
MAN: "ssdp:discover"\r
MX: 2\r
ST: ssdp:all\r
\r
"""
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(2)
    
    sock.sendto(ssdp_request, ("239.255.255.250", 1900))
    
    responses = []
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            responses.append((addr[0], data.decode('utf-8', errors='ignore')))
    except socket.timeout:
        pass
    finally:
        sock.close()
    
    if responses:
        print(f"    ✅ {len(responses)} SSDP Geräte gefunden")
        
        for ip, response in responses:
            if FRITZ_IP in response or 'FRITZ' in response or 'AVM' in response:
                print(f"       → Fritz!Box antwortet: {ip}")
                
                # Extrahiere Modell
                for line in response.split('\r\n'):
                    if 'ST:' in line or 'USN:' in line or 'SERVER:' in line:
                        print(f"         {line.strip()}")
    else:
        print(f"    ❌ Keine SSDP-Antworten")
        
except Exception as e:
    print(f"    ❌ SSDP Error: {e}")

# 4. InfoÄnderungen  
print("\n[4] MÖGLICHE PROBLEME")
print("""
    ⚠️  Port 49000 offen, aber:
    - UPnP device.xml zurückgewiesen (404)
    - SOAP-Befehle zurückgewiesen (500 oder Auth-Error)
    - HTTP-Interface nicht erreichbar (404)
    
    MÖGLICHE URSACHEN:
    
    1️⃣  Gerät ist NICHT die Fritz!Box
       → Könnte sein: Smart Home Hub, Router-Extension, etc.
    
    2️⃣  Fritz!Box ist mit NAT konfiguriert
       → Port 49000 wird nach außen geleitet
       → Interner Service nicht auf 49000
    
    3️⃣  Authentifizierung erforderlich
       → Passwort/Token benötigt für API-Zugriff
       → Standard "Admin" Benutzer deaktiviert
    
    4️⃣  Fritz!Box Model unterstützt APIs nicht
       → Zu alt oder zu neu
       → Home Automation deaktiviert
    
    5️⃣  Router ist im "Gast-Modus"
       → Bestimmte APIs deaktiviert
       → Nur basic WLAN Funktionen
""")

print("\n" + "=" * 70)
print("\n⏭️  NÄCHSTE SCHRITTE:")
print("""
    A) Was ist eigentlich auf Port 49000?
       → sudo netstat -tlnp | grep 49000
    
    B) Admin-Passwort prüfen
       → Für fritz.box Web-Interface
    
    C) Welche Geräte sind EIGENTLICH mit Smart Home konfigurierbar?
       → Bist du sicher, dass fritz.box direkt steuerbar ist?
       → Oder nur spezielle FRITZ!DECT/FRITZ!Powerline Geräte?
    
    D) Alternatives Smart Home Setup
       → Home Assistant als Middleware
       → Node-RED für Device Management
       → Smart Home Bridge für verschiedene Protokolle
""")
