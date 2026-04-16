#!/usr/bin/env python3
"""
Mock Home Assistant Server for testing Smart Home Portal integration
Provides REST API compatible with real Home Assistant
"""

from flask import Flask, request, jsonify
from datetime import datetime
import uuid
import json

app = Flask(__name__)

# Generated token (use this in HOMEASSISTANT_TOKEN env var)
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJNb2NrIEhBIiwiaWF0IjoxNzQ1MDAwMDAwfQ.mock_token_for_testing"

# Demo Home Assistant Entities
ENTITIES = {
    "light.wohnzimmer": {
        "entity_id": "light.wohnzimmer",
        "state": "on",
        "attributes": {
            "friendly_name": "Wohnzimmer Licht",
            "brightness": 255,
            "color_name": "white"
        }
    },
    "light.schlafzimmer": {
        "entity_id": "light.schlafzimmer",
        "state": "off",
        "attributes": {
            "friendly_name": "Schlafzimmer Licht",
            "brightness": 0,
            "color_name": "white"
        }
    },
    "switch.kuche": {
        "entity_id": "switch.kuche",
        "state": "on",
        "attributes": {
            "friendly_name": "Küche Schalter",
            "icon": "mdi:lightbulb"
        }
    },
    "switch.flur": {
        "entity_id": "switch.flur",
        "state": "off",
        "attributes": {
            "friendly_name": "Flur Schalter",
            "icon": "mdi:lightbulb"
        }
    },
    "climate.heizung": {
        "entity_id": "climate.heizung",
        "state": "heat",
        "attributes": {
            "friendly_name": "Raumheizung",
            "temperature": 21.5,
            "target_temperature": 20.0,
            "unit_of_measurement": "°C"
        }
    },
    "cover.rolladen_wohnzimmer": {
        "entity_id": "cover.rolladen_wohnzimmer",
        "state": "open",
        "attributes": {
            "friendly_name": "Rolladen Wohnzimmer",
            "position": 100
        }
    },
    "lock.haustuer": {
        "entity_id": "lock.haustuer",
        "state": "locked",
        "attributes": {
            "friendly_name": "Haustür",
            "icon": "mdi:lock"
        }
    },
    "fan.ventilator": {
        "entity_id": "fan.ventilator",
        "state": "off",
        "attributes": {
            "friendly_name": "Ventilator",
            "speed": 0,
            "speed_list": ["off", "low", "medium", "high"]
        }
    }
}

# ============================================================================
# MIDDLEWARE & AUTH
# ============================================================================

def check_token():
    """Verify Bearer token"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header.replace('Bearer ', '').strip()
    return token == API_TOKEN

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/')
def api_home():
    """Home endpoint"""
    return jsonify({
        "message": "Mock Home Assistant API",
        "version": "2024.1.0",
        "requires_auth": True,
        "token": API_TOKEN  # For demo purposes only!
    })

@app.route('/api/states', methods=['GET'])
def get_states():
    """Get all entity states (Home Assistant compatible)"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify(list(ENTITIES.values()))

@app.route('/api/states/<entity_id>', methods=['GET'])
def get_state(entity_id):
    """Get single entity state"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    if entity_id not in ENTITIES:
        return jsonify({"error": "Entity not found"}), 404
    
    return jsonify(ENTITIES[entity_id])

@app.route('/api/services/light/turn_on', methods=['POST'])
def light_turn_on():
    """Turn on light"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('light.'):
        entity['state'] = 'on'
        if 'brightness' in entity['attributes']:
            entity['attributes']['brightness'] = 255
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a light"}), 400

@app.route('/api/services/light/turn_off', methods=['POST'])
def light_turn_off():
    """Turn off light"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('light.'):
        entity['state'] = 'off'
        if 'brightness' in entity['attributes']:
            entity['attributes']['brightness'] = 0
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a light"}), 400

@app.route('/api/services/switch/turn_on', methods=['POST'])
def switch_turn_on():
    """Turn on switch"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('switch.'):
        entity['state'] = 'on'
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a switch"}), 400

@app.route('/api/services/switch/turn_off', methods=['POST'])
def switch_turn_off():
    """Turn off switch"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('switch.'):
        entity['state'] = 'off'
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a switch"}), 400

@app.route('/api/services/climate/set_temperature', methods=['POST'])
def climate_set_temperature():
    """Set climate temperature"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    temperature = data.get('temperature')
    
    if not entity_id or entity_id not in ENTITIES or temperature is None:
        return jsonify({"error": "Invalid input"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('climate.'):
        entity['attributes']['target_temperature'] = float(temperature)
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a climate entity"}), 400

@app.route('/api/services/cover/open_cover', methods=['POST'])
def cover_open():
    """Open cover"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('cover.'):
        entity['state'] = 'open'
        entity['attributes']['position'] = 100
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a cover"}), 400

@app.route('/api/services/cover/close_cover', methods=['POST'])
def cover_close():
    """Close cover"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('cover.'):
        entity['state'] = 'closed'
        entity['attributes']['position'] = 0
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a cover"}), 400

@app.route('/api/services/lock/lock', methods=['POST'])
def lock_lock():
    """Lock a lock entity"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('lock.'):
        entity['state'] = 'locked'
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a lock"}), 400

@app.route('/api/services/lock/unlock', methods=['POST'])
def lock_unlock():
    """Unlock a lock entity"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('lock.'):
        entity['state'] = 'unlocked'
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a lock"}), 400

@app.route('/api/services/fan/turn_on', methods=['POST'])
def fan_turn_on():
    """Turn on fan"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('fan.'):
        entity['state'] = 'on'
        entity['attributes']['speed'] = 2
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a fan"}), 400

@app.route('/api/services/fan/turn_off', methods=['POST'])
def fan_turn_off():
    """Turn off fan"""
    if not check_token():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    entity_id = data.get('entity_id')
    
    if not entity_id or entity_id not in ENTITIES:
        return jsonify({"error": "Invalid entity"}), 400
    
    entity = ENTITIES[entity_id]
    if entity['entity_id'].startswith('fan.'):
        entity['state'] = 'off'
        entity['attributes']['speed'] = 0
        return jsonify({"success": True, "entity": entity})
    
    return jsonify({"error": "Not a fan"}), 400

# Health check endpoint
@app.route('/status', methods=['GET'])
@app.route('/ping', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "running", "service": "Mock Home Assistant"})

if __name__ == '__main__':
    print("=" * 70)
    print("🏠 MOCK HOME ASSISTANT SERVER")
    print("=" * 70)
    print(f"\n✅ Server läuft auf: http://localhost:8123")
    print(f"✅ Token: {API_TOKEN}")
    print(f"\n📝 Umgebungsvariablen setzen:")
    print(f"   HOMEASSISTANT_URL=http://localhost:8123")
    print(f"   HOMEASSISTANT_TOKEN={API_TOKEN}")
    print(f"\n🎮 Demo-Geräte:")
    print(f"   - 2x Lichter (Wohnzimmer, Schlafzimmer)")
    print(f"   - 2x Schalter (Küche, Flur)")
    print(f"   - 1x Heizung/Klima")
    print(f"   - 1x Rolladen")
    print(f"   - 1x Türschloss")
    print(f"   - 1x Ventilator")
    print("=" * 70)
    print()
    
    app.run(host='127.0.0.1', port=8123, debug=False)
