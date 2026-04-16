import requests
url = 'http://localhost:5000/api/login'
body = {'username':'admin','password':'Admin@123'}
try:
    r = requests.post(url, json=body, timeout=10)
    print(r.status_code)
    print(r.text)
except Exception as e:
    print('ERR', e)
