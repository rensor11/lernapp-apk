#!/usr/bin/env python3
"""
Schneller TV/Gerätescan - findet Fernseher und Smart-Home Geräte
"""
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress

def check_port(ip, port, timeout=0.3):
    """Teste ob Port offen ist"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, int(port)))
        sock.close()
        return result == 0
    except:
        return False

def scan_device(ip, ports):
    """Scanne einzelnes Gerät"""
    open_ports = []
    for port in ports:
        if check_port(ip, port):
            open_ports.append(port)
    return (ip, open_ports) if open_ports else None

def main():
    # Bestimme lokales Netzwerk
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Extrahiere Netzwerk-Base
        parts = local_ip.split('.')
        network = '.'.join(parts[:3])
        print(f"Lokale IP: {local_ip}")
        print(f"Scanne Netzwerk: {network}.0/24\n")
    except:
        print("FEHLER: Netzwerkverbindung fehlgeschlagen")
        return
    
    # Ports zu Testing
    # 80: HTTP, 8080: Webserver, 3000: Node.js, 9000: Smart-Home Devices
    # 5000: Flask/Python, 8888: Jupyter/Tools
    ports = [80, 8080, 9000, 3000, 5000, 8888, 443]
    
    found_devices = []
    
    print(f"Teste Ports: {ports}\n")
    print("Scanning...")
    
    # Paralleles Scannen
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {}
        for i in range(1, 255):
            ip = f"{network}.{i}"
            future = executor.submit(scan_device, ip, ports)
            futures[future] = ip
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                ip, open_ports = result
                found_devices.append((ip, open_ports))
                print(f"[{i}/254] GEFUNDEN: {ip} - Ports: {open_ports}")
            elif i % 50 == 0:
                print(f"[{i}/254] Weiterhin scanning...")
    
    # Ergebnisse
    print("\n" + "="*50)
    print("ERGEBNISSE")
    print("="*50)
    
    if not found_devices:
        print("Keine Geräte gefunden")
    else:
        print(f"\nInsgesamt {len(found_devices)} Gerät(e) gefunden:\n")
        for ip, ports in sorted(found_devices):
            ports_str = ", ".join(map(str, ports))
            print(f"  {ip} : {ports_str}")
        
        print("\n" + "-"*50)
        print("TIPPS ZUM FINDEN DEINES FERNSEHERS:")
        print("-"*50)
        print("- Port 80/443: Web-Browser Interface")
        print("- Port 8080, 9000: Smart-Home / MediaServer")
        print("- Bekannte TVs: LG WebOS, Samsung (Port 80), Sony")
        print("\nWaehle eine IP und teste sie in Smart-Home!")

if __name__ == "__main__":
    main()
