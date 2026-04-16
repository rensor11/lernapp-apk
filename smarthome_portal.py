#!/usr/bin/env python3
"""
Smart Home Portal Backend Integration
Combines Fritz!Box + Home Assistant + Device Discovery
"""

import requests
import json

class SmartHomePortal:
    """Central Smart Home Control - Router + Home Assistant + Discovery"""
    
    def __init__(self, fritzbox_url="http://192.168.178.1", 
                 homeassistant_url=None, homeassistant_token=None):
        self.fritzbox_url = fritzbox_url
        self.homeassistant_url = homeassistant_url or "http://localhost:8123"
        self.homeassistant_token = homeassistant_token
        self.devices = []
        
        print(f"[INFO] Smart Home Portal initialized")
        print(f"       Fritz!Box: {fritzbox_url}")
        print(f"       Home Assistant: {homeassistant_url}")
    
    def get_network_devices(self):
        """Get all devices from Fritz!Box network scan"""
        try:
            from fritzbox_proxy import FritzBoxProxy
            proxy = FritzBoxProxy(router_url=self.fritzbox_url)
            devices = proxy.get_connected_devices()
            
            result = []
            for device in devices:
                result.append({
                    'id': device.get('ip', '').replace('.', '_'),
                    'name': device.get('hostname', device.get('ip', 'Unknown')),
                    'ip': device.get('ip'),
                    'mac': device.get('mac', 'unknown'),
                    'status': device.get('status', 'unknown'),
                    'type': 'network_device',
                    'controllable': False,
                    'domain': 'fritzbox'
                })
            
            return result
        except Exception as e:
            print(f"[ERROR] Network scan failed: {e}")
            return []
    
    def get_homeassistant_entities(self):
        """Get all controllable entities from Home Assistant"""
        if not self.homeassistant_token:
            print("[WARN] Home Assistant token not configured - skipping HA entities")
            return []
        
        try:
            headers = {
                "Authorization": f"Bearer {self.homeassistant_token}",
                "Content-Type": "application/json"
            }
            
            # Get all states
            response = requests.get(
                f"{self.homeassistant_url}/api/states",
                headers=headers,
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"[WARN] Home Assistant API error: {response.status_code}")
                return []
            
            states = response.json()
            devices = []
            
            # Filter controllable entities
            controllable_domains = ['light', 'switch', 'climate', 'cover', 'lock', 'fan', 'vacuum']
            
            for state in states:
                entity_id = state.get('entity_id', '')
                domain = entity_id.split('.')[0] if '.' in entity_id else ''
                
                if domain in controllable_domains:
                    devices.append({
                        'id': entity_id,
                        'name': state.get('attributes', {}).get('friendly_name', entity_id),
                        'type': domain,
                        'state': state.get('state'),
                        'attributes': state.get('attributes', {}),
                        'controllable': True,
                        'domain': 'homeassistant'
                    })
            
            return devices
        
        except Exception as e:
            print(f"[ERROR] Home Assistant entities fetch failed: {e}")
            return []
    
    def get_all_devices(self):
        """Get combined list of all discoverable and controllable devices"""
        devices = []
        
        # Add Home Assistant entities first (controllable)
        ha_devices = self.get_homeassistant_entities()
        devices.extend(ha_devices)
        
        # Add network devices (informational)
        network_devices = self.get_network_devices()
        devices.extend(network_devices)
        
        return devices
    
    def send_command(self, device_id, command, value=None):
        """Send control command to a device"""
        
        # Determine if it's HA or network device
        if device_id.startswith('light.') or device_id.startswith('switch.') or '.' in device_id:
            # Home Assistant entity
            return self._send_ha_command(device_id, command, value)
        else:
            # Network/Fritz!Box device
            return self._send_network_command(device_id, command, value)
    
    def _send_ha_command(self, entity_id, command, value=None):
        """Send command via Home Assistant"""
        if not self.homeassistant_token:
            return {'success': False, 'error': 'Home Assistant not configured'}
        
        try:
            domain = entity_id.split('.')[0]
            headers = {
                "Authorization": f"Bearer {self.homeassistant_token}",
                "Content-Type": "application/json"
            }
            
            # Map commands to HA services
            if command in ['on', 'turn_on']:
                service = f"{domain}/turn_on"
                data = {"entity_id": entity_id}
            elif command in ['off', 'turn_off']:
                service = f"{domain}/turn_off"
                data = {"entity_id": entity_id}
            elif command == 'toggle':
                service = f"{domain}/toggle"
                data = {"entity_id": entity_id}
            elif command == 'brightness' and domain == 'light':
                service = f"{domain}/turn_on"
                data = {"entity_id": entity_id, "brightness": int(value or 255)}
            else:
                return {'success': False, 'error': f'Unknown command: {command}'}
            
            response = requests.post(
                f"{self.homeassistant_url}/api/services/{service}",
                headers=headers,
                json=data,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                return {'success': True, 'message': f'Command sent to {entity_id}'}
            else:
                return {'success': False, 'error': f'HA API error: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_network_command(self, device_id, command, value=None):
        """Send command to network device (limited functionality)"""
        
        if command == 'wake':
            # Wake-on-LAN
            import socket
            import struct
            
            # TODO: Implement WoL
            return {'success': False, 'error': 'Wake-on-LAN not yet implemented'}
        
        elif command == 'block':
            return {'success': False, 'error': 'Device blocking requires admin authentication'}
        
        else:
            return {'success': False, 'error': 'Network devices are read-only (use Home Assistant for control)'}

if __name__ == '__main__':
    # Test
    portal = SmartHomePortal()
    
    print("\nNetwork Devices:")
    for device in portal.get_network_devices():
        print(f"  - {device['name']} ({device['ip']}): {device['status']}")
