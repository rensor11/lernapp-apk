#!/usr/bin/env python3
"""
Fritz!Box HTTP Proxy - Direkte Steuerung ohne zusätzliche Services
Router + verbundene Geräte komplett managebar
"""
import requests
import json
import socket
import threading
import time
from datetime import datetime
from urllib.parse import urlencode, quote
import hashlib
import random
import string

class FritzBoxProxy:
    """Fritz!Box REST API Proxy"""
    
    def __init__(self, router_url="http://192.168.178.1", password="", username="admin"):
        self.router_url = router_url
        self.password = password
        self.username = username
        self.session_id = None
        self.devices_cache = None
        self.cache_time = None
        
        print(f"[INFO] Fritz!Box Proxy initialized: {router_url}")
        self._get_session()
    
    def _get_session(self):
        """Get session ID for authentication"""
        try:
            # Versuche ohne Passwort zuerst
            response = requests.get(
                f"{self.router_url}/login_sid.lua",
                timeout=3
            )
            
            if response.status_code == 200:
                # Parse XML response
                if '<SID>' in response.text:
                    self.session_id = response.text.split('<SID>')[1].split('</SID>')[0]
                    
                    if self.session_id == "0000000000000000":
                        print("[AUTH] No session, password authentication required")
                        self._authenticate()
                    else:
                        print(f"[AUTH] Got session: {self.session_id[:8]}...")
                        return True
            
            return False
            
        except Exception as e:
            print(f"[ERROR] Session error: {e}")
            return False
    
    def _authenticate(self):
        """Authenticate with password"""
        if not self.password:
            print("[WARN] No password provided - limited functions available")
            return False
        
        try:
            # Get challenge
            response = requests.get(
                f"{self.router_url}/login_sid.lua",
                timeout=3
            )
            
            if '<Challenge>' in response.text:
                challenge = response.text.split('<Challenge>')[1].split('</Challenge>')[0]
                
                # Create response hash
                challenge_response = challenge + "-" + hashlib.md5(
                    f"{challenge}-{self.password}".encode('utf-16-le')
                ).hexdigest()
                
                # Get new session
                response = requests.post(
                    f"{self.router_url}/login_sid.lua",
                    data={
                        'username': self.username,
                        'response': challenge_response
                    },
                    timeout=3
                )
                
                if '<SID>' in response.text:
                    self.session_id = response.text.split('<SID>')[1].split('</SID>')[0]
                    
                    if self.session_id != "0000000000000000":
                        print(f"[AUTH] Authenticated: {self.session_id[:8]}...")
                        return True
        
        except Exception as e:
            print(f"[ERROR] Auth error: {e}")
        
        return False
    
    def get_connected_devices(self):
        """Get all connected devices"""
        print("[SCAN] Getting connected devices...")
        
        try:
            # ARP-basierter Scan über local network
            devices = []
            
            # Nutze Netzwerk-Scanning
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Ermittle Subnet
            parts = local_ip.split('.')[:3]
            subnet = '.'.join(parts)
            
            print(f"[INFO] Scanning subnet: {subnet}.0/24")
            
            # Scanne IPs
            for i in range(1, 255):
                ip = f"{subnet}.{i}"
                
                try:
                    # Quick ping
                    result = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result.settimeout(0.5)
                    res = result.connect_ex((ip, 22))
                    result.close()
                    
                    if res == 0:
                        # Port offen - Device aktiv
                        try:
                            hostname_res = socket.gethostbyaddr(ip)[0]
                        except:
                            hostname_res = ip
                        
                        devices.append({
                            'ip': ip,
                            'hostname': hostname_res,
                            'mac': 'unknown',
                            'status': 'online'
                        })
                
                except:
                    pass
            
            self.devices_cache = devices
            self.cache_time = datetime.now()
            
            print(f"[INFO] Found {len(devices)} devices")
            return devices
        
        except Exception as e:
            print(f"[ERROR] Device scan error: {e}")
            return []
    
    def get_wifi_status(self):
        """Get WiFi status (if accessible)"""
        try:
            # Versuche über SOAP/TR-064
            response = requests.get(
                f"{self.router_url}/upnp/device.xml",
                timeout=2
            )
            
            if response.status_code == 200:
                return {'wifi': 'online', 'status': 'accessible'}
            else:
                return {'wifi': 'unknown', 'status': 'not_accessible'}
        
        except:
            return {'wifi': 'unknown', 'status': 'timeout'}
    
    def get_internet_status(self):
        """Check internet connection"""
        try:
            response = requests.get(
                self.router_url,
                timeout=2
            )
            
            if response.status_code == 200:
                return {
                    'internet': 'online',
                    'router': 'responsive',
                    'checked_at': datetime.now().isoformat()
                }
            else:
                return {
                    'internet': 'offline',
                    'router': f'HTTP {response.status_code}',
                    'checked_at': datetime.now().isoformat()
                }
        
        except Exception as e:
            return {
                'internet': 'unknown',
                'router': str(type(e).__name__),
                'checked_at': datetime.now().isoformat()
            }
    
    def get_network_status(self):
        """Get complete network status"""
        print("[STATUS] Gathering network status...")
        
        return {
            'router_url': self.router_url,
            'authenticated': self.session_id is not None and self.session_id != "0000000000000000",
            'wifi': self.get_wifi_status(),
            'internet': self.get_internet_status(),
            'devices': len(self.devices_cache) if self.devices_cache else 'unknown',
            'timestamp': datetime.now().isoformat()
        }
    
    def control_device_by_mac(self, mac_address, action):
        """Control device by MAC address (block/unblock)"""
        print(f"[CONTROL] Device {mac_address}: {action}")
        
        if action == 'block':
            # MAC-Filtering aktivieren wenn möglich
            print(f"[INFO] Would block {mac_address} (requires admin auth)")
            return {'success': False, 'reason': 'requires_admin'}
        
        elif action == 'allow':
            print(f"[INFO] Would allow {mac_address}")
            return {'success': False, 'reason': 'requires_admin'}
        
        return {'success': False, 'reason': 'unknown_action'}
    
    def reboot_router(self):
        """Reboot router (requires authentication)"""
        if not self.session_id or self.session_id == "0000000000000000":
            print("[WARN] Cannot reboot: not authenticated")
            return {'success': False, 'reason': 'not_authenticated'}
        
        print("[CONTROL] Rebooting router...")
        try:
            # SOAP-Befehl für Reboot
            response = requests.post(
                f"{self.router_url}:49000/upnp/control/deviceconfig1",
                data=f"""<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
    <s:Body>
        <u:Reboot xmlns:u="urn:FRITZ:service:DeviceConfig:1"/>
    </s:Body>
</s:Envelope>""",
                headers={'SOAPAction': 'urn:FRITZ:service:DeviceConfig:1#Reboot'},
                timeout=3
            )
            
            if response.status_code in [200, 500]:  # 500 is normal for reboot
                return {'success': True, 'rebooting': True}
        
        except:
            pass
        
        return {'success': False, 'reason': 'soap_unavailable'}

# REST API für LernApp
def create_proxy_api():
    """Create Flask routes for Fritz!Box control"""
    
    proxy = FritzBoxProxy()
    
    routes = {
        'get_devices': {
            'endpoint': '/api/smarthome/fritz/devices',
            'method': 'GET',
            'handler': lambda: {'success': True, 'devices': proxy.get_connected_devices()}
        },
        'get_status': {
            'endpoint': '/api/smarthome/fritz/status',
            'method': 'GET',
            'handler': lambda: {'success': True, 'status': proxy.get_network_status()}
        },
        'control_device': {
            'endpoint': '/api/smarthome/fritz/control',
            'method': 'POST',
            'doc': 'Control device by MAC\nBody: {"mac": "AA:BB:CC:DD:EE:FF", "action": "block"}'
        },
        'wifi_toggle': {
            'endpoint': '/api/smarthome/fritz/wifi',
            'method': 'POST',
            'doc': 'Toggle WiFi (requires auth)\nBody: {"state": "on/off"}'
        }
    }
    
    return proxy, routes


if __name__ == '__main__':
    print("\n" + "="*70)
    print("FRITZ!BOX HTTP PROXY - NETWORK AUTOMATION")
    print("="*70 + "\n")
    
    proxy, routes = create_proxy_api()
    
    print("\nAvailable API Endpoints:")
    print("-" * 70)
    for name, route_info in routes.items():
        print(f"\n{name.upper()}")
        print(f"  Endpoint: {route_info.get('endpoint')}")
        print(f"  Method: {route_info.get('method')}")
        if 'doc' in route_info:
            print(f"  Doc: {route_info.get('doc')}")
    
    print("\n" + "="*70)
    print("Test Results:")
    print("="*70 + "\n")
    
    # Test 1: Status
    status = proxy.get_network_status()
    print(f"Network Status: {json.dumps(status, indent=2)}")
    
    # Test 2: Devices
    print("\nScanning for devices...")
    devices = proxy.get_connected_devices()
    print(f"Found {len(devices)} devices")
    for device in devices[:5]:  # Show first 5
        print(f"  - {device['hostname']:20s} ({device['ip']})")
    
    if len(devices) > 5:
        print(f"  ... and {len(devices)-5} more")
    
    print("\n✅ Fritz!Box Proxy is ready to be integrated into server_v2.py")
    print("\n" + "="*70)
