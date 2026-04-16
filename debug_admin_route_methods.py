import requests
url = 'http://localhost:5000/api/admin/user-category-stats?user_id=1'
headers = {'X-Admin-User': 'admin'}
for method in ['GET','POST','OPTIONS']:
    try:
        if method == 'GET': r = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST': r = requests.post(url, headers=headers, timeout=10)
        else: r = requests.options(url, headers=headers, timeout=10)
        print(method, r.status_code, r.headers.get('Allow'), r.text[:200])
    except Exception as e:
        print(method, 'ERR', e)
