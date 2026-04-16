#!/usr/bin/env python3
import requests
import sys

try:
    session = requests.Session()
    
    # Test routes
    routes = [
        '/portal.html',
        '/account',
        '/smarthome-settings', 
        '/user-management',
        '/api/user/profile'
    ]
    
    for route in routes:
        try:
            r = session.get(f'http://localhost:5000{route}', timeout=3)
            status = r.status_code
            ctype = r.headers.get('Content-Type', 'N/A')
            length = len(r.text)
            print(f'✅ {route}: {status} | {ctype} | {length} bytes')
        except Exception as e:
            print(f'❌ {route}: {str(e)[:50]}')
            
except Exception as e:
    print(f'Fatal error: {e}')
    sys.exit(1)
