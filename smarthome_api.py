#!/usr/bin/env python3
"""
RenLern Smart Home - Fritz!Box Integration
===========================================
- Automatische Geräteerkennung
- Smart Home Steuerung
- Netzwerk-Scanner
- TR-064 API Integration
"""

import requests
import socket
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class SmartDevice:
    """Smart Home Gerät"""
    id: str
    name: str
    device_type: str  # avm_switch, light, thermometer, camera, other
    ip_address: str
    mac_address: str
    status: bool  # True = an, False = aus
    power: int = 0  # Watt
    temperature: int = 0  # Celsius
    is_controllable: bool = False
    model: str = ""
    manufacturer: str = ""
    last_seen: str = ""

class FritzBoxAPI:
    """Fritz!Box SmartHome API Integration"""
    
    def __init__(self, host: str = "192.168.1.1", username: str = "", password: str = ""):
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"http://{host}:49000"
        self.session = requests.Session()
        
        # TR-064 Service Types
        self.homeautomation_service = "/upnp/control/homeauto"
    
    def get_sid(self) -> Optional[str]:
        """Hole Session ID von Fritz!Box"""
        try:
            url = f"http://{self.host}:49000/upnp/control/homeauto"
            
            # Challenge anfordern
            response = self.session.get(f"http://{self.host}/login_sid.lua")
            root = ET.fromstring(response.text)
            
            challenge = root.find(".//Challenge").text
            
            # Response mit Password berechnen
            from hashlib import md5
            challenge_response = challenge + ":" + password
            response_hash = md5(challenge_response.encode()).hexdigest()
            
            # SID mit Response abfragen
            data = {
                "username": self.username,
                "response": f"{challenge}-{response_hash}"
            }
            
            response = self.session.post(f"http://{self.host}/login_sid.lua", data=data)
            root = ET.fromstring(response.text)
            sid = root.find(".//SessionId").text
            
            return sid if sid != "0000000000000000" else None
        except Exception as e:
            print(f"Fehler beim SID abrufen: {e}")
            return None
    
    def get_devices(self) -> List[Dict]:
        """Hole alle Smart Home Geräte von Fritz!Box"""
        devices = []
        try:
            # TR-064 Request für Geräteliste
            headers = {
                "Content-Type": "text/xml; charset='utf-8'",
                "SOAPACTION": "urn:X_Kontors-de:service:X_AVM-COM:1#GetDeviceListInfoURL"
            }
            
            body = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
            s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:GetDeviceListInfoURL xmlns:u="urn:X_Kontors-de:service:X_AVM-COM:1">
    </u:GetDeviceListInfoURL>
  </s:Body>
</s:Envelope>"""
            
            response = self.session.post(
                f"{self.base_url}{self.homeautomation_service}",
                data=body,
                headers=headers,
                timeout=5
            )
            
            # Parse XML Response
            root = ET.fromstring(response.text)
            
            # Geräte extrahieren
            for device in root.iter():
                if device.tag.endswith("Device"):
                    device_data = {
                        "id": device.find("DeviceId").text or "",
                        "name": device.find("DeviceName").text or "Unknown",
                        "type": device.find("DeviceType").text or "other",
                        "manufacturer": device.find("DeviceManufacturer").text or "",
                        "model": device.find("DeviceModel").text or "",
                        "fw_version": device.find("FirmwareVersion").text or "",
                    }
                    devices.append(device_data)
            
            return devices
        except Exception as e:
            print(f"Fehler beim Abrufen von Geräten: {e}")
            return []
    
    def toggle_device(self, device_id: str, state: bool) -> bool:
        """Schalte Smart Home Gerät ein/aus"""
        try:
            headers = {
                "Content-Type": "text/xml; charset='utf-8'",
                "SOAPACTION": "urn:X_Kontors-de:service:X_AVM-COM:1#SetSwitch State"
            }
            
            state_value = "1" if state else "0"
            
            body = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
            s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:SetSwitchState xmlns:u="urn:X_Kontors-de:service:X_AVM-COM:1">
      <NewAIN>{device_id}</NewAIN>
      <NewSwitchState>{state_value}</NewSwitchState>
    </u:SetSwitchState>
  </s:Body>
</s:Envelope>"""
            
            response = self.session.post(
                f"{self.base_url}{self.homeautomation_service}",
                data=body,
                headers=headers,
                timeout=5
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Fehler beim Schalten: {e}")
            return False

class NetworkScanner:
    """Netzwerk Scanner für Geräte-Discovery"""
    
    @staticmethod
    def get_local_ip() -> str:
        """Hole lokale IP-Adresse"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.1.100"
    
    @staticmethod
    def get_network_devices() -> List[Dict]:
        """Scanne Netzwerk nach aktiven Geräten (ARP Scan)"""
        devices = []
        try:
            import subprocess
            
            # Netzwerk bestimmen
            local_ip = NetworkScanner.get_local_ip()
            network = ".".join(local_ip.split(".")[:3]) + "."
            
            # ARP Scan (schneller als Ping)
            for i in range(1, 255):
                ip = f"{network}{i}"
                try:
                    result = subprocess.run(
                        f"ping -n 1 -w 100 {ip}",
                        capture_output=True,
                        timeout=1
                    )
                    
                    if result.returncode == 0:
                        try:
                            hostname = socket.gethostbyaddr(ip)[0]
                        except:
                            hostname = f"Device-{i}"
                        
                        devices.append({
                            "ip": ip,
                            "hostname": hostname,
                            "status": "online"
                        })
                except:
                    pass
            
            return devices
        except Exception as e:
            print(f"Fehler beim Netzwerk-Scan: {e}")
            return []

if __name__ == "__main__":
    # Test
    fb = FritzBoxAPI()
    print("Verbinde mit Fritz!Box...")
    
    devices = fb.get_devices()
    print(f"Gefundene Geräte: {len(devices)}")
    for device in devices:
        print(f"  - {device['name']} ({device['type']})")
    
    print("\nNetzwerk-Geräte:")
    net_devices = NetworkScanner.get_network_devices()
    for dev in net_devices:
        print(f"  - {dev['hostname']} ({dev['ip']})")
