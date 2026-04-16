# Test the scan function directly
import subprocess
import socket
from datetime import datetime, timezone

print('Starte direkten Scan-Test...')

# Get local network info
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    local_ip = s.getsockname()[0]
    s.close()
except:
    local_ip = '192.168.178.100'

network_base = '.'.join(local_ip.split('.')[:3]) + '.'
print(f'Netzwerk: {network_base}0/24 (lokale IP: {local_ip})')

# ARP scan
active_ips = []
result = subprocess.run(['arp', '-a'], capture_output=True, timeout=5, encoding='utf-8')
print('ARP-Ausgabe verarbeitet...')

for line in result.stdout.split('\n'):
    line = line.strip()
    if line and not line.startswith('Schnittstelle') and not line.startswith('Interface'):
        parts = line.split()
        if len(parts) >= 2:
            ip_candidate = parts[0]
            if ip_candidate.count('.') == 3 and ip_candidate.startswith(network_base[:-1]):
                try:
                    socket.inet_aton(ip_candidate)
                    if ip_candidate not in active_ips and ip_candidate != local_ip:
                        active_ips.append(ip_candidate)
                        print(f'ARP: {ip_candidate}')
                except:
                    pass

print(f'ARP gefunden: {len(active_ips)} IPs')

# Process devices
devices = []
for ip in active_ips[:3]:
    hostname = f'Device-{ip.split(".")[-1]}'
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except:
        pass

    device_type = 'Netzwerk-Gerät'
    manufacturer = 'Unbekannt'

    if ip.endswith('.1'):
        device_type = 'Router/Gateway'
        manufacturer = 'Netzwerk-Hardware'
    elif ip == '192.168.178.1':
        device_type = 'Fritz!Box Router'
        manufacturer = 'AVM'

    devices.append({
        'id': f'{ip}:80',
        'name': hostname,
        'device_type': device_type,
        'ip_address': ip,
        'port': 80,
        'status': 'online',
        'is_controllable': False,
        'manufacturer': manufacturer,
        'last_seen': datetime.now(timezone.utc).isoformat()
    })
    print(f'Verarbeitet: {hostname} ({ip})')

print(f'Scan abgeschlossen: {len(devices)} Geräte gefunden')
for device in devices:
    print(f'- {device["name"]} ({device["ip_address"]}) - {device["device_type"]}')