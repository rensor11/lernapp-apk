#!/usr/bin/env python3
"""
Smart Home Scan Debug Script
Teste die einzelnen Komponenten der Netzwerk-Scanning
"""
import socket
import subprocess
import sys
import os

print("=" * 70)
print("SMART HOME SCAN - DEBUGGING")
print("=" * 70)

# 1. Test lokal IP
print("\n[1] LOKALE IP ADRESSEN")
hostname = socket.gethostname()
local_ips = socket.gethostbyname_ex(hostname)[2]
print(f"    Hostname: {hostname}")
print(f"    IPs: {local_ips}")

# 2. Test Router Erreichbarkeit
print("\n[2] ROUTER PING TEST")
router_ip = "192.168.178.1"
try:
    result = subprocess.run(
        f"ping -n 1 {router_ip}",
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        print(f"    ✅ Router {router_ip} ist erreichbar")
    else:
        print(f"    ❌ Router {router_ip} antwortet nicht")
        print(f"    Output: {result.stdout}")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 3. Test ARP Scan
print("\n[3] ARP TABLE SCAN")
try:
    result = subprocess.run(
        "arp -a",
        capture_output=True,
        text=True,
        timeout=5
    )
    lines = result.stdout.split('\n')
    devices = []
    for line in lines:
        if '192.168.178' in line:
            devices.append(line.strip())
    
    print(f"    Geräte im Netzwerk:")
    for device in devices[:10]:
        print(f"    {device}")
    
    if len(devices) > 0:
        print(f"    ✅ ARP Scan erfolgreich: {len(devices)} Geräte gefunden")
    else:
        print(f"    ⚠️ Keine Geräte in ARP-Tabelle")
        
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 4. Test DNS Reverse Lookup
print("\n[4] REVERSE DNS TEST")
test_ips = ["192.168.178.1", "192.168.178.51"]
for ip in test_ips:
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        print(f"    ✅ {ip} → {hostname}")
    except socket.herror:
        print(f"    ⚠️ {ip} → (kein DNS)")
    except Exception as e:
        print(f"    ❌ {ip} → Error: {e}")

# 5. Test Port Scanning auf Router
print("\n[5] PORT TEST AUF ROUTER")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    result = s.connect_ex(("192.168.178.1", 80))
    if result == 0:
        print(f"    ✅ Port 80 (HTTP) auf Router offen")
    else:
        print(f"    ⚠️ Port 80 nicht erreichbar")
    s.close()
except Exception as e:
    print(f"    ❌ Fehler: {e}")

print("\n" + "=" * 70)
