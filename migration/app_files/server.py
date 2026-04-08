#!/usr/bin/env python3
"""
Einfacher Python Server für die Lernapp
Keine Abhängigkeiten notwendig - Python 3 ist alles was benötigt wird!
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import hashlib
import secrets
from datetime import datetime

USERS_FILE = 'users.json'
PROGRESS_FILE = 'user_progress.json'


def ensure_file(path, default_data):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)


def read_json(path, fallback):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return fallback


def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()


ensure_file(USERS_FILE, [])
ensure_file(PROGRESS_FILE, [])

class LernappHandler(SimpleHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def _read_request_json(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        return json.loads(body.decode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)

        # API: JSON-Datei laden
        if parsed.path == '/api/load-fragenpool':
            try:
                with open('fragenpool.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self._send_json(200, data)
            except FileNotFoundError:
                self._send_json(404, {'success': False, 'message': 'fragenpool.json nicht gefunden'})

        elif parsed.path == '/api/progress':
            query = parse_qs(parsed.query or '')
            user_id = (query.get('user_id') or [None])[0]
            if not user_id:
                self._send_json(400, {'success': False, 'message': 'user_id erforderlich.'})
                return

            rows = read_json(PROGRESS_FILE, [])
            filtered = [r for r in rows if str(r.get('user_id')) == str(user_id)]
            self._send_json(200, filtered)

        elif parsed.path.startswith('/api/'):
            self._send_json(404, {'success': False, 'message': 'API-Endpunkt nicht gefunden.'})
        else:
            # Normale Datei servieren
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        # API: JSON-Datei speichern
        if parsed.path == '/api/save-fragenpool':
            try:
                data = self._read_request_json()
                
                # Speichere die Datei
                with open('fragenpool.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                response = {'success': True, 'message': 'Fragenpool erfolgreich gespeichert!'}
                self._send_json(200, response)
                print('✅ fragenpool.json aktualisiert')
                
            except Exception as e:
                response = {'success': False, 'message': f'Fehler beim Speichern: {str(e)}'}
                self._send_json(500, response)

        elif parsed.path == '/api/register':
            try:
                payload = self._read_request_json()
                username = (payload.get('username') or '').strip()
                password = (payload.get('password') or '').strip()

                if len(username) < 3 or len(password) < 6:
                    self._send_json(400, {'success': False, 'message': 'Benutzername mind. 3 Zeichen, Passwort mind. 6 Zeichen.'})
                    return

                users = read_json(USERS_FILE, [])
                if any((u.get('username', '').lower() == username.lower()) for u in users):
                    self._send_json(400, {'success': False, 'message': 'Benutzername existiert bereits.'})
                    return

                salt = secrets.token_hex(16)
                password_hash = hash_password(password, salt)
                new_user = {
                    'id': int(datetime.utcnow().timestamp() * 1000),
                    'username': username,
                    'salt': salt,
                    'password_hash': password_hash,
                    'created_at': datetime.utcnow().isoformat()
                }
                users.append(new_user)
                write_json(USERS_FILE, users)

                self._send_json(200, {'success': True, 'user': {'id': new_user['id'], 'username': username}})
            except Exception as e:
                self._send_json(500, {'success': False, 'message': f'Serverfehler bei Registrierung: {str(e)}'})

        elif parsed.path == '/api/login':
            try:
                payload = self._read_request_json()
                username = (payload.get('username') or '').strip()
                password = (payload.get('password') or '').strip()

                users = read_json(USERS_FILE, [])
                user = next((u for u in users if u.get('username', '').lower() == username.lower()), None)
                if not user:
                    self._send_json(401, {'success': False, 'message': 'Ungültiger Benutzername oder Passwort.'})
                    return

                check_hash = hash_password(password, user.get('salt', ''))
                if check_hash != user.get('password_hash'):
                    self._send_json(401, {'success': False, 'message': 'Ungültiger Benutzername oder Passwort.'})
                    return

                self._send_json(200, {'success': True, 'user': {'id': user['id'], 'username': user['username']}})
            except Exception as e:
                self._send_json(500, {'success': False, 'message': f'Serverfehler bei Anmeldung: {str(e)}'})

        elif parsed.path == '/api/progress':
            try:
                payload = self._read_request_json()
                user_id = payload.get('user_id')
                question_id = payload.get('question_id')
                correct = 1 if payload.get('correct') else 0

                if not user_id or not question_id:
                    self._send_json(400, {'success': False, 'message': 'user_id und question_id erforderlich.'})
                    return

                rows = read_json(PROGRESS_FILE, [])
                rows.append({
                    'id': int(datetime.utcnow().timestamp() * 1000),
                    'user_id': user_id,
                    'question_id': question_id,
                    'answered': 1,
                    'correct': correct,
                    'created_at': datetime.utcnow().isoformat()
                })
                write_json(PROGRESS_FILE, rows)
                self._send_json(200, {'success': True})
            except Exception as e:
                self._send_json(500, {'success': False, 'message': f'Progress konnte nicht gespeichert werden: {str(e)}'})
        else:
            if parsed.path.startswith('/api/'):
                self._send_json(404, {'success': False, 'message': 'API-Endpunkt nicht gefunden.'})
            else:
                self.send_response(404)
                self.end_headers()

    def do_OPTIONS(self):
        # CORS Support
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        # Bessere Log-Ausgabe
        return super().log_message(format, *args)

if __name__ == '__main__':
    PORT = 3000
    Handler = LernappHandler
    httpd = HTTPServer(('localhost', PORT), Handler)
    
    print(f"""
═══════════════════════════════════════════════════
  🎓 Lernapp Server läuft!
═══════════════════════════════════════════════════
  
  Öffne im Browser: http://localhost:{PORT}/lernapp.html
  
  Die Fragen werden automatisch in fragenpool.json gespeichert!
  
  🛑 Server beenden: Drücke Ctrl+C
═══════════════════════════════════════════════════
""")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n✅ Server beendet')
        httpd.server_close()
