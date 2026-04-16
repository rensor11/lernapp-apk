#!/usr/bin/env python3
import requests
import json

session = requests.Session()

# Test User Login
login_data = {
    'username': 'admin',
    'password': 'admin123'
}

print("=" * 60)
print("TESTING NEW APIs & PAGES")
print("=" * 60)

# 1. Login
print("\n1️⃣ LOGIN TEST")
r = session.post('http://localhost:5000/api/login', json=login_data, timeout=5)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   ✅ Login erfolgreich")
    
    # 2. Get Profile
    print("\n2️⃣ GET PROFILE")
    r = session.get('http://localhost:5000/api/user/profile', timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Profile: {data.get('user', {}).get('username', 'N/A')}")
    
    # 3. Test Password Change API
    print("\n3️⃣ PASSWORD CHANGE API (should fail - weak password)")
    r = session.post('http://localhost:5000/api/user/password/change', 
                     json={
                         'current_password': 'admin123',
                         'new_password': 'weak',
                         'confirm_password': 'weak'
                     }, timeout=5)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
    
    # 4. Test Get Pages
    print("\n4️⃣ HTML PAGES TEST")
    pages = ['/account', '/smarthome-settings', '/user-management']
    for page in pages:
        r = session.get(f'http://localhost:5000{page}', timeout=5)
        size = len(r.text)
        print(f"   {page}: {r.status_code} ({size} bytes)")
    
else:
    print(f"   ❌ Login failed: {r.text}")

print("\n" + "=" * 60)
