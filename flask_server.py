"""
Flask Server Modul für die LernApp APK
=======================================
Dieser Server läuft direkt im Android-Prozess.
Zugriff: http://<Gerät-IP>:5000
"""

import os
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file, session

# ─── Pfade ────────────────────────────────────────────────────────────────────

def get_app_dir():
    """
    Gibt den App-Datenordner zurück.
    Android: /data/data/de.lernapp.lernapserver/files/
    Desktop: ./data/
    """
    try:
        # Android-Pfad (Kivy setzt ANDROID_ARGUMENT)
        from android.storage import app_storage_path
        return app_storage_path()
    except ImportError:
        # Desktop-Fallback
        data_dir = Path(__file__).parent.parent / 'data'
        data_dir.mkdir(exist_ok=True)
        return str(data_dir)

def get_fragenpool_path():
    """Sucht die fragenpool.json in verschiedenen Orten."""
    candidates = [
        Path(get_app_dir()) / 'fragenpool.json',
        Path(__file__).parent / 'fragenpool.json',
        Path(__file__).parent.parent / 'fragenpool.json',
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    # Fallback: leerer Pool
    return str(Path(get_app_dir()) / 'fragenpool.json')


# ─── Datenbank ────────────────────────────────────────────────────────────────

def get_db_path():
    return os.path.join(get_app_dir(), 'lernapp.db')

def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Erstellt die Datenbank-Tabellen wenn sie nicht existieren."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                type TEXT DEFAULT 'multiple',
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answered INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    print("[DB] Datenbank initialisiert")

def load_fragenpool_into_db():
    """Lädt fragenpool.json in die SQLite-Datenbank."""
    pool_path = get_fragenpool_path()
    if not os.path.exists(pool_path):
        print(f"[DB] Kein Fragenpool gefunden: {pool_path}")
        return 0

    try:
        with open(pool_path, 'r', encoding='utf-8') as f:
            pool = json.load(f)
    except Exception as e:
        print(f"[DB] Fehler beim Laden: {e}")
        return 0

    count = 0
    with get_db() as conn:
        # Nur laden wenn DB leer
        existing = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if existing > 0:
            print(f"[DB] {existing} Fragen bereits in DB")
            return existing

        for category, questions in pool.items():
            for q in questions:
                options_json = json.dumps(q.get('options', []), ensure_ascii=False)
                conn.execute(
                    "INSERT INTO questions (category, type, question, options) VALUES (?, ?, ?, ?)",
                    (category, q.get('type', 'multiple'), q.get('question', ''), options_json)
                )
                count += 1
        conn.commit()

    print(f"[DB] {count} Fragen geladen")
    return count


# ─── Flask App Factory ────────────────────────────────────────────────────────

def create_app():
    app = Flask(__name__, static_folder=None)
    app.secret_key = secrets.token_hex(32)

    # DB initialisieren
    init_db()
    load_fragenpool_into_db()

    # ── Hilfsfunktionen ───────────────────────────────────────────────────────

    def hash_pw(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100_000
        ).hex()

    def send_json(data, status=200):
        r = jsonify(data)
        r.headers['Access-Control-Allow-Origin'] = '*'
        return r, status

    # ── CORS ──────────────────────────────────────────────────────────────────

    @app.after_request
    def add_cors(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    @app.route('/api/<path:p>', methods=['OPTIONS'])
    def options_handler(p):
        return send_json({})

    # ── Health Check ──────────────────────────────────────────────────────────

    @app.route('/api/health')
    def health():
        with get_db() as conn:
            q_count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
            u_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        return send_json({
            'status': 'ok',
            'questions': q_count,
            'users': u_count,
            'version': '1.0-apk'
        })

    # ── Haupt-HTML ────────────────────────────────────────────────────────────

    @app.route('/')
    def index():
        html_candidates = [
            Path(__file__).parent / 'lernapp.html',
            Path(__file__).parent.parent / 'lernapp.html',
            Path(get_app_dir()) / 'lernapp.html',
        ]
        for p in html_candidates:
            if p.exists():
                return send_file(str(p))
        return "<h1>LernApp Server läuft! ✅</h1><p>lernapp.html nicht gefunden.</p>"

    # ── Fragen API ────────────────────────────────────────────────────────────

    @app.route('/api/questions')
    def get_questions():
        category = request.args.get('category')
        with get_db() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM questions WHERE category = ?", (category,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM questions").fetchall()

        result = {}
        for row in rows:
            cat = row['category']
            if cat not in result:
                result[cat] = []
            result[cat].append({
                'id': row['id'],
                'category': cat,
                'type': row['type'],
                'question': row['question'],
                'options': json.loads(row['options'])
            })
        return send_json(result)

    @app.route('/api/categories')
    def get_categories():
        with get_db() as conn:
            rows = conn.execute(
                "SELECT category, COUNT(*) as count FROM questions GROUP BY category ORDER BY category"
            ).fetchall()
        return send_json([{'name': r['category'], 'count': r['count']} for r in rows])

    # ── Fragenpool speichern/laden ────────────────────────────────────────────

    @app.route('/api/load-fragenpool')
    def load_fragenpool():
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM questions").fetchall()
        result = {}
        for row in rows:
            cat = row['category']
            if cat not in result:
                result[cat] = []
            result[cat].append({
                'id': row['id'],
                'category': cat,
                'type': row['type'],
                'question': row['question'],
                'options': json.loads(row['options'])
            })
        return send_json(result)

    @app.route('/api/save-fragenpool', methods=['POST'])
    def save_fragenpool():
        data = request.get_json()
        if not data:
            return send_json({'success': False, 'message': 'Kein JSON'}, 400)

        # In DB speichern
        with get_db() as conn:
            conn.execute("DELETE FROM questions")
            count = 0
            for category, questions in data.items():
                for q in questions:
                    options_json = json.dumps(q.get('options', []), ensure_ascii=False)
                    conn.execute(
                        "INSERT INTO questions (category, type, question, options) VALUES (?, ?, ?, ?)",
                        (category, q.get('type', 'multiple'), q.get('question', ''), options_json)
                    )
                    count += 1
            conn.commit()

        # Auch als JSON-Datei sichern
        pool_path = os.path.join(get_app_dir(), 'fragenpool.json')
        with open(pool_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return send_json({'success': True, 'message': f'{count} Fragen gespeichert'})

    # ── Auth: Register ────────────────────────────────────────────────────────

    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()

        if len(username) < 3 or len(password) < 6:
            return send_json({'success': False, 'message': 'Benutzername ≥ 3 Zeichen, Passwort ≥ 6 Zeichen'}, 400)

        salt = secrets.token_hex(16)
        pw_hash = hash_pw(password, salt)

        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                    (username, pw_hash, salt)
                )
                conn.commit()
                user_id = conn.execute(
                    "SELECT id FROM users WHERE username = ?", (username,)
                ).fetchone()['id']
            return send_json({'success': True, 'user': {'id': user_id, 'username': username}})
        except sqlite3.IntegrityError:
            return send_json({'success': False, 'message': 'Benutzername existiert bereits'}, 400)

    # ── Auth: Login ───────────────────────────────────────────────────────────

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,)
            ).fetchone()

        if not user:
            return send_json({'success': False, 'message': 'Ungültige Anmeldedaten'}, 401)

        if hash_pw(password, user['salt']) != user['password_hash']:
            return send_json({'success': False, 'message': 'Ungültige Anmeldedaten'}, 401)

        return send_json({'success': True, 'user': {'id': user['id'], 'username': user['username']}})

    # ── Progress ──────────────────────────────────────────────────────────────

    @app.route('/api/progress', methods=['GET'])
    def get_progress():
        user_id = request.args.get('user_id')
        if not user_id:
            return send_json({'success': False, 'message': 'user_id fehlt'}, 400)
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM user_progress WHERE user_id = ?", (user_id,)
            ).fetchall()
        return send_json([dict(r) for r in rows])

    @app.route('/api/progress', methods=['POST'])
    def save_progress():
        data = request.get_json() or {}
        user_id = data.get('user_id')
        question_id = data.get('question_id')
        correct = 1 if data.get('correct') else 0

        if not user_id or not question_id:
            return send_json({'success': False, 'message': 'user_id und question_id erforderlich'}, 400)

        with get_db() as conn:
            conn.execute(
                "INSERT INTO user_progress (user_id, question_id, answered, correct) VALUES (?, ?, 1, ?)",
                (user_id, question_id, correct)
            )
            conn.commit()
        return send_json({'success': True})

    # ── Shutdown (für sauberes Beenden) ───────────────────────────────────────

    @app.route('/api/shutdown', methods=['POST'])
    def shutdown():
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()
        return send_json({'success': True})

    return app


# ─── Desktop-Test ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app = create_app()
    print("\n🚀 LernApp Server läuft!")
    print(f"🌐 http://localhost:5000")
    print("🛑 Beenden: Ctrl+C\n")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
