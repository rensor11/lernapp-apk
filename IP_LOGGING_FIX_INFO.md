## 🌐 IP-Logging FIX - RenLern Server v2

### Das Problem
Die Flask Server Logs zeigten `127.0.0.1` weil:
- Der Server läuft lokal auf Port 5000
- Cloudflared (Reverse Proxy) verbindet sich von localhost zu diesem Server
- Flask sah nur die lokale Verbindung

### Die Lösung ✅
Es wurde die **Werkzeug ProxyFix Middleware** installiert:

```python
from werkzeug.proxy_fix import ProxyFix

# Nach Flask App Erstellung:
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
```

### Wie es jetzt funktioniert

1. **Cloudflared sendet die echte IP** in den `X-Forwarded-For` Header
2. **ProxyFix extrahiert diese Header** und setzt sie in `request.remote_addr`
3. **Flask loggt jetzt die echte IP** statt `127.0.0.1`

### Beispiel - Vorher vs Nachher

**VORHER:**
```
127.0.0.1 - - [16/Apr/2026 08:10:11] "GET /home HTTP/1.1" 200 -
127.0.0.1 - - [16/Apr/2026 08:10:11] "GET /api/user/check-home-access HTTP/1.1" 200 -
```

**NACHHER (mit echtem Zugriff von außen):**
```
203.45.67.89 - - [16/Apr/2026 08:10:11] "GET /home HTTP/1.1" 200 -
203.45.67.89 - - [16/Apr/2026 08:10:11] "GET /api/user/check-home-access HTTP/1.1" 200 -
```

### Gemachte Änderungen in `server_v2.py`

1. ✅ **Import hinzugefügt:**
   ```python
   from werkzeug.proxy_fix import ProxyFix
   ```

2. ✅ **ProxyFix Middleware aktiviert:**
   ```python
   app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
   ```

3. ✅ **Request Logger hinzugefügt:**
   ```python
   @app.before_request
   def log_request_info():
       """Log request with real client IP (from Cloudflared)"""
       client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
       request.real_ip = client_ip
   ```

### Sicherheitshinweis ⚠️

**ProxyFix Parameter:**
- `x_for=1` - Vertraut auf den X-Forwarded-For Header (1 Proxy-Ebene)
- `x_proto=1` - HTTP/HTTPS Protocol korrekt setzen
- `x_host=1` - Hostname korrekt setzen
- `x_port=1` - Port Information verwalten

Diese Einstellung ist sicher, da nur Cloudflared diese Header setzt und vollständig vertrauenswürdig ist.

### Test

Nach dem Neustart des Servers:
1. Greife auf https://renlern.org zu (von außen)
2. Überprüfe die Logs - sollte deine echte IP zeigen
3. Login versuche werden mit echter IP geloggt
4. Security-Logs zeigen echte IPs für Brute-Force-Protection

---

**Version:** v2.0 mit IP-Logging Fix  
**Datum:** 16. April 2026
