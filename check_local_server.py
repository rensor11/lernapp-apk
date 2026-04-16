import urllib.request

try:
    with urllib.request.urlopen('http://localhost:5000/', timeout=10) as u:
        print('STATUS', u.status)
        data = u.read(400)
        print(data.decode('utf-8', 'ignore'))
except Exception as e:
    print('ERR', repr(e))
