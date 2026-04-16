import requests
import json

resp = requests.get('http://localhost:5000/api/smarthome/scan', timeout=5)
if resp.status_code == 200:
    data = resp.json()
    print('Scan erfolgreich!')
    print(f'Geräte gefunden: {len(data.get("devices", []))}')
    print(f'Netzwerk: {data.get("local_network")}')
    print()
    print('Geräte:')
    for device in data.get('devices', []):
        print(f'  - {device["name"]} ({device["ip_address"]}) - {device["device_type"]}')
else:
    print(f'Fehler: {resp.status_code}')