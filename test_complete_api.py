#!/usr/bin/env python3
"""
Test all new Admin APIs and Features
"""
import requests
import json
import sys

BASE_URL = 'http://localhost:5000'
ADMIN_PASSWORD = 'admin123'

session = requests.Session()

print("=" * 70)
print("TESTING ALL NEW FEATURES")
print("=" * 70)

# 1. LOGIN
print("\n[1] LOGIN TEST")
r = session.post(f'{BASE_URL}/api/login', json={'username': 'admin', 'password': 'admin123'})
print(f"    Status: {r.status_code}")
if r.status_code != 200:
    print(f"    ERROR: Login failed")
    sys.exit(1)
print(f"    ✅ Admin logged in")

# 2. CREATE NEW USER
print("\n[2] CREATE USER API TEST")
r = session.post(f'{BASE_URL}/api/admin/users', 
    headers={'X-Admin-Password': ADMIN_PASSWORD},
    json={
        'username': 'testuser123',
        'password': 'password123',
        'home_access_allowed': True,
        'lernapp_access_allowed': True,
        'smarthome_access_allowed': False
    }
)
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"    ✅ User created: {data}")
    test_user_id = data.get('user_id')
else:
    print(f"    Response: {r.text[:200]}")

# 3. LIST USERS
print("\n[3] LIST USERS API TEST")
r = session.get(f'{BASE_URL}/api/admin/users',
    headers={'X-Admin-Password': ADMIN_PASSWORD})
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"    ✅ Users loaded: {len(data.get('users', []))} users")
else:
    print(f"    ❌ Error: {r.text[:100]}")

# 4. RESET PASSWORD
print("\n[4] RESET PASSWORD API TEST")
r = session.post(f'{BASE_URL}/api/admin/user/2/password',
    headers={'X-Admin-Password': ADMIN_PASSWORD},
    json={'password': 'newpass123' if 'test_user_id' not in locals() else f'pass_{test_user_id}'}
)
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    print(f"    ✅ Password reset")
else:
    print(f"    Response: {r.text[:100]}")

# 5. TEST NEW PAGES
print("\n[5] NEW PAGES AVAILABILITY TEST")
pages = ['/account', '/smarthome-settings', '/user-management', '/file-management']
for page in pages:
    r = session.get(f'{BASE_URL}{page}')
    status = "✅" if r.status_code == 200 else "❌"
    print(f"    {status} {page}: {r.status_code} ({len(r.text)} bytes)")

# 6. FILE MANAGEMENT API
print("\n[6] FILE MANAGEMENT API TEST")
r = session.get(f'{BASE_URL}/api/files/list?user_id=1&path=')
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if data.get('success'):
        files = data.get('files', [])
        print(f"    ✅ Files API works: {len(files)} items")
    else:
        print(f"    ⚠️ API error: {data.get('message')}")
else:
    print(f"    ❌ HTTP Error: {r.text[:100]}")

# 7. PERMISSION CHECK
print("\n[7] PERMISSION CHECK API TEST")
r = session.get(f'{BASE_URL}/api/user/check-access?user_id=1&feature=all')
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    print(f"    ✅ Permission check works")
else:
    print(f"    ⚠️ Response: {r.text[:100]}")

print("\n" + "=" * 70)
print("✅ ALL TESTS COMPLETED")
print("=" * 70)
