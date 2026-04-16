import requests
url = 'http://localhost:5000/api/admin/user-category-stats?user_id=1'
headers = {'X-Admin-User': 'admin'}
try:
    r = requests.get(url, headers=headers, timeout=10)
    print('status', r.status_code)
    print('allow', r.headers.get('Allow'))
    print(r.text)
except Exception as e:
    print('ERR', e)
