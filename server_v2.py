#!/usr/bin/env python3
"""
RenLern Server v2 - Portal + Home Cloud + Lernapp
================================================
- Portal Login auf /
- Home Cloud auf /home (Dateispeicher mit Kategorien)
- Lernapp auf /lernapp (Quiz)
"""

import os
import sqlite3
import json
import shutil
import mimetypes
import re
import hashlib
import requests
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Flask, request, jsonify, redirect, send_from_directory, g, send_file, abort, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Import Fritz!Box Proxy
try:
    from fritzbox_proxy import FritzBoxProxy
    FRITZBOX_PROXY = FritzBoxProxy(router_url="http://192.168.178.1")
    print("[SETUP] Fritz!Box Proxy initialized")
except Exception as e:
    print(f"[WARN] Fritz!Box Proxy error: {e}")
    FRITZBOX_PROXY = None

# Import Smart Home Portal
try:
    from smarthome_portal import SmartHomePortal
    SMARTHOME_PORTAL = SmartHomePortal(
        fritzbox_url="http://192.168.178.1",
        homeassistant_url=os.getenv('HOMEASSISTANT_URL', 'http://localhost:8123'),
        homeassistant_token=os.getenv('HOMEASSISTANT_TOKEN')
    )
    print("[SETUP] Smart Home Portal initialized")
except Exception as e:
    print(f"[WARN] Smart Home Portal error: {e}")
    SMARTHOME_PORTAL = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'lernapp.db')
QUESTIONPOOL_FILE = os.path.join(BASE_DIR, 'fragenpool.json')
CANONICAL_HOST = 'renlern.org'
CANONICAL_URL = f'https://{CANONICAL_HOST}'

# Home Cloud Speicher
STORAGE_ROOT = os.path.join(BASE_DIR, 'user_storage')
CATEGORIES = ['bilder', 'musik', 'videos', 'dokumente', 'sonstiges']

# Security Configuration
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_TIMEOUT = 900  # 15 minutes
MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4 GB
MIN_PASSWORD_LENGTH = 6
ALLOWED_FILE_EXTENSIONS = set()
for exts in {'bilder': ['jpg','jpeg','png','gif','webp','svg','bmp','ico','tiff','raw','heic'],
             'musik': ['mp3','wav','flac','ogg','m4a','aac','wma','opus','aiff'],
             'videos': ['mp4','webm','mkv','avi','mov','wmv','flv','ts','m4v','mpeg','mpg'],
             'dokumente': ['pdf','doc','docx','txt','md','odt','xls','xlsx','csv','ppt','pptx','rtf','xml','json','yaml','yml'],
             'sonstiges': ['zip','rar','7z','tar','gz','iso','exe','apk','dmg','msi','app']}.values():
    ALLOWED_FILE_EXTENSIONS.update(exts)

EXT_CATEGORY = {
    'bilder':    ['jpg','jpeg','png','gif','webp','svg','bmp','ico','tiff','raw','heic'],
    'musik':     ['mp3','wav','flac','ogg','m4a','aac','wma','opus','aiff'],
    'videos':    ['mp4','webm','mkv','avi','mov','wmv','flv','ts','m4v','mpeg','mpg'],
    'dokumente': ['pdf','doc','docx','txt','md','odt','xls','xlsx','csv','ppt','pptx','rtf','xml','json','yaml','yml'],
    'sonstiges': ['zip','rar','7z','tar','gz','iso','exe','apk','dmg','msi','app'],
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_category_for_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    for cat, exts in EXT_CATEGORY.items():
        if ext in exts:
            return cat
    return 'sonstiges'

def format_size(size_bytes):
    for unit in ['B','KB','MB','GB','TB']:
        if size_bytes < 1024:
            return f'{size_bytes:.1f} {unit}' if unit != 'B' else f'{int(size_bytes)} B'
        size_bytes /= 1024
    return f'{size_bytes:.1f} PB'

def get_user_storage(user_id):
    path = os.path.join(STORAGE_ROOT, str(user_id))
    os.makedirs(path, exist_ok=True)
    for cat in CATEGORIES:
        os.makedirs(os.path.join(path, cat), exist_ok=True)
    return path

def safe_path(user_id, rel_path):
    base = get_user_storage(user_id)
    target = os.path.normpath(os.path.join(base, rel_path)) if rel_path else base
    if not target.startswith(base):
        return None
    return target

def get_client_ip():
    """Get client IP from request, considering X-Forwarded-For header."""
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

def check_login_attempts(ip_address):
    """Check if IP has exceeded max login attempts."""
    db = get_db()
    cutoff_time = (datetime.now(timezone.utc) - timedelta(seconds=LOGIN_ATTEMPT_TIMEOUT)).isoformat()
    recent_attempts = db.execute(
        'SELECT COUNT(*) as fail_count FROM login_attempts WHERE ip_address = ? AND success = 0 AND attempted_at > ?',
        (ip_address, cutoff_time)
    ).fetchone()['fail_count']
    
    return recent_attempts >= MAX_LOGIN_ATTEMPTS

def record_login_attempt(ip_address, username, success):
    """Record a login attempt."""
    db = get_db()
    db.execute(
        'INSERT INTO login_attempts (ip_address, attempted_username, success, attempted_at) VALUES (?, ?, ?, ?)',
        (ip_address, username, 1 if success else 0, datetime.now(timezone.utc).isoformat())
    )
    db.commit()

def validate_password_strength(password):
    """Validate password meets minimum security requirements."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f'Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein'
    
    # Could add more checks here: uppercase, lowercase, numbers, special chars, etc.
    return True, None

# ═══════════════════════════════════════════════════════════════════════════════
# FLASK APP SETUP
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-renlern-2024')
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 * 1024  # 4 GB

# Middleware für Reverse Proxy (Cloudflared) - um echte IP zu loggen
# ProxyFix wird nicht verwendet da die werkzeug Version zu alt ist
# app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# Session Configuration
app.config['SESSION_COOKIE_SECURE'] = False  # Allow http (change to True for HTTPS only)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JS access to cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts 7 days

@app.before_request
def redirect_www_to_canonical_host():
    host = (request.headers.get('Host') or '').split(':', 1)[0].lower()
    if host == f'www.{CANONICAL_HOST}':
        target = request.full_path if request.query_string else request.path
        return redirect(f'{CANONICAL_URL}{target}', code=301)

@app.before_request
def log_request_info():
    """Log request with real client IP (from Cloudflared)"""
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    # Store real IP in request context for use in routes
    request.real_ip = client_ip

@app.before_request
def load_user_from_session():
    """Lade User aus Flask-Session und setze g.user"""
    g.user = None
    
    # Prüfe ob user_id in Session
    if 'user_id' in session:
        db = get_db()
        user = db.execute('SELECT id, username FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if user:
            g.user = dict(user)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.errorhandler(Exception)
def handle_error(error):
    """Convert all errors to JSON to avoid HTML response errors"""
    import traceback
    tb = traceback.format_exc()
    error_msg = str(error) or 'Unknown error'
    
    # Return JSON error response
    return jsonify({
        'success': False,
        'message': error_msg,
        'error': type(error).__name__,
        'traceback': tb if app.debug else None
    }), 500

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def get_user_columns(db):
    return [row[1] for row in db.execute('PRAGMA table_info(users)').fetchall()]

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_ip TEXT,
            last_user_agent TEXT,
            last_seen_at TEXT
        );
    """)
    user_columns = get_user_columns(db)
    if 'last_ip' not in user_columns:
        db.execute('ALTER TABLE users ADD COLUMN last_ip TEXT')
        db.commit()
    if 'last_user_agent' not in user_columns:
        db.execute('ALTER TABLE users ADD COLUMN last_user_agent TEXT')
        db.commit()
    if 'last_seen_at' not in user_columns:
        db.execute('ALTER TABLE users ADD COLUMN last_seen_at TEXT')
        db.commit()
    if 'home_access_allowed' not in user_columns:
        db.execute('ALTER TABLE users ADD COLUMN home_access_allowed INTEGER DEFAULT 0')
        db.commit()
    if 'smarthome_access_allowed' not in user_columns:
        db.execute('ALTER TABLE users ADD COLUMN smarthome_access_allowed INTEGER DEFAULT 0')
        db.commit()
    if 'lernapp_access_allowed' not in user_columns:
        db.execute('ALTER TABLE users ADD COLUMN lernapp_access_allowed INTEGER DEFAULT 0')
        db.commit()
    
    # Stelle sicher, dass alle Benutzer standardmäßig keinen Zugriff haben (außer wenn sie vom Admin freigegeben wurden)
    # Setze alle existierenden Benutzer auf 0 wenn sie noch 1 haben
    db.execute('UPDATE users SET home_access_allowed = 0 WHERE home_access_allowed IS NULL OR home_access_allowed = 1')
    db.execute('UPDATE users SET smarthome_access_allowed = 0 WHERE smarthome_access_allowed IS NULL')
    db.execute('UPDATE users SET lernapp_access_allowed = 0 WHERE lernapp_access_allowed IS NULL OR lernapp_access_allowed = 1')
    db.commit()
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            type TEXT,
            question TEXT NOT NULL,
            answer TEXT,
            options TEXT,
            created_at TEXT NOT NULL
        );
    """)
    question_columns = [row[1] for row in db.execute('PRAGMA table_info(questions)').fetchall()]
    if 'answer' not in question_columns:
        db.execute('ALTER TABLE questions ADD COLUMN answer TEXT')
        db.commit()
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answered INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mode TEXT,
            total_questions INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            wrong INTEGER NOT NULL,
            percentage REAL NOT NULL,
            created_at TEXT NOT NULL,
            ip TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            attempted_username TEXT,
            success INTEGER NOT NULL DEFAULT 0,
            attempted_at TEXT NOT NULL
        );
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS smarthome_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            port INTEGER NOT NULL,
            protocol TEXT DEFAULT 'http',
            auth_token TEXT,
            status TEXT DEFAULT 'offline',
            last_seen TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    
    db.commit()

def load_questions_from_json():
    if not os.path.exists(QUESTIONPOOL_FILE):
        return
    with open(QUESTIONPOOL_FILE, 'r', encoding='utf-8') as f:
        try:
            pool = json.load(f)
        except Exception:
            return
    db = get_db()
    for category, qs in (pool.items() if isinstance(pool, dict) else []):
        for q in qs:
            if not q or 'question' not in q:
                continue
            question_text = q.get('question')
            qtype = q.get('type', '')
            answer_text = q.get('answer')
            options = q.get('options')
            options_text = json.dumps(options, ensure_ascii=False) if options is not None else None
            exists = db.execute('SELECT id FROM questions WHERE category=? AND question=?', (category, question_text)).fetchone()
            if exists:
                if answer_text:
                    db.execute('UPDATE questions SET answer = COALESCE(answer, ?) WHERE id = ? AND (answer IS NULL OR answer = "")', (answer_text, exists['id']))
                continue
            db.execute('INSERT INTO questions (category, type, question, answer, options, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                       (category, qtype, question_text, answer_text, options_text, datetime.utcnow().isoformat()))
    db.commit()

def setup_app():
    init_db()
    load_questions_from_json()
    os.makedirs(STORAGE_ROOT, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES - PAGES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def root():
    """Portal-Login"""
    return send_from_directory(BASE_DIR, 'portal.html')

@app.route('/home')
def home_page():
    """Home Cloud"""
    return send_from_directory(BASE_DIR, 'home.html')

@app.route('/lernapp')
def lernapp_page():
    """Lernapp"""
    return send_from_directory(BASE_DIR, 'lernapp.html')

@app.route('/smarthome')
def smarthome_page():
    """Smart Home"""
    return send_from_directory(BASE_DIR, 'smarthome.html')

@app.route('/account')
def account_page():
    """Kontoeinstellungen"""
    return send_from_directory(os.path.join(BASE_DIR, 'pages'), 'account_settings.html')

@app.route('/smarthome-settings')
def smarthome_settings_page():
    """Smart Home Einstellungen und Geräte-Verwaltung"""
    return send_from_directory(os.path.join(BASE_DIR, 'pages'), 'smarthome_settings.html')

@app.route('/smarthome-portal')
def smarthome_portal_page():
    """Smart Home Portal - Alle Geräte steuern"""
    return send_from_directory(os.path.join(BASE_DIR, 'pages'), 'smarthome_portal.html')

@app.route('/user-management')
def user_management_page():
    """Benutzerverwaltung (Admin only)"""
    return send_from_directory(os.path.join(BASE_DIR, 'pages'), 'user_management.html')

@app.route('/file-management')
def file_management_page():
    """Dateiverwaltung für Home Cloud"""
    return send_from_directory(os.path.join(BASE_DIR, 'pages'), 'file_management.html')

@app.route('/admin')
def admin_page():
    """Admin Panel - nur für Admin-Benutzer"""
    # Prüfe ob Benutzer eingeloggt ist
    if 'user_id' not in session:
        return redirect('/portal.html', 302)
    
    # Prüfe ob es der Admin-Benutzer ist
    db = get_db()
    user = db.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if not user or user['username'] != 'admin':
        return redirect('/portal.html', 302)
    
    return send_from_directory(BASE_DIR, 'admin.html')

@app.route('/<path:path>')
def static_proxy(path):
    if path in ('home', 'lernapp', 'portal', 'smarthome', 'admin'):
        return redirect('/' + path, 302)
    full = os.path.join(BASE_DIR, path)
    if os.path.exists(full) and os.path.isfile(full):
        return send_from_directory(BASE_DIR, path)
    return send_from_directory(BASE_DIR, 'portal.html')

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH API
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    
    # Validate input
    if len(username) < 3:
        return jsonify({'success': False, 'message': 'Benutzername muss mindestens 3 Zeichen lang sein.'}), 400
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Check username availability
    db = get_db()
    existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        return jsonify({'success': False, 'message': 'Benutzername existiert bereits.'}), 400
    
    # Create user
    password_hash = generate_password_hash(password)
    db.execute('INSERT INTO users (username, password_hash, created_at, home_access_allowed, smarthome_access_allowed, lernapp_access_allowed) VALUES (?, ?, ?, ?, ?, ?)',
               (username, password_hash, datetime.now(timezone.utc).isoformat(), 0, 0, 0))
    db.commit()
    
    user_id = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()['id']
    return jsonify({'success': True, 'user': {'id': user_id, 'username': username}})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    
    # Get client IP
    client_ip = get_client_ip()
    
    # Check rate limiting
    if check_login_attempts(client_ip):
        return jsonify({'success': False, 'message': 'Zu viele Anmeldeversuche. Bitte warten Sie 15 Minuten.'}), 429
    
    # Log attempt
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if not user or not check_password_hash(user['password_hash'], password):
        record_login_attempt(client_ip, username, False)
        return jsonify({'success': False, 'message': 'Ungültige Anmeldedaten.'}), 401
    
    # Successful login
    record_login_attempt(client_ip, username, True)
    
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    user_cols = get_user_columns(db)
    sets, params = [], []
    if 'last_ip' in user_cols:
        sets.append('last_ip = ?')
        params.append(ip)
    if 'last_user_agent' in user_cols:
        sets.append('last_user_agent = ?')
        params.append(user_agent)
    if 'last_seen_at' in user_cols:
        sets.append('last_seen_at = ?')
        params.append(datetime.now(timezone.utc).isoformat())
    if sets:
        params.append(user['id'])
        db.execute(f'UPDATE users SET {", ".join(sets)} WHERE id = ?', tuple(params))
        db.commit()
    
    # Setze Session Cookie (persistent)
    session.permanent = True
    session['user_id'] = user['id']
    
    return jsonify({'success': True, 'user': {'id': user['id'], 'username': user['username']}})

# ═══════════════════════════════════════════════════════════════════════════════
# LERNAPP API
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/load-fragenpool', methods=['GET'])
def load_fragenpool():
    db = get_db()
    rows = db.execute('SELECT * FROM questions').fetchall()
    pool = {}
    for row in rows:
        category = row['category'] or 'Unbekannt'
        answer_value = row['answer'] if 'answer' in row.keys() else None
        q = {
            'id': row['id'],
            'category': category,
            'type': row['type'],
            'question': row['question'],
            'answer': answer_value,
            'options': json.loads(row['options']) if row['options'] else None,
            'created_at': row['created_at']
        }
        pool.setdefault(category, []).append(q)
    return jsonify(pool)

@app.route('/api/save-fragenpool', methods=['POST'])
def save_fragenpool():
    data = request.json or {}
    try:
        with open(QUESTIONPOOL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500
    db = get_db()
    db.execute('DELETE FROM questions')
    for category, qs in data.items():
        for q in (qs or []):
            question_text = q.get('question')
            if not question_text:
                continue
            qtype = q.get('type', '')
            answer_text = q.get('answer')
            options_text = json.dumps(q.get('options', []), ensure_ascii=False)
            db.execute('INSERT INTO questions (category, type, question, answer, options, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                       (category, qtype, question_text, answer_text, options_text, datetime.utcnow().isoformat()))
    db.commit()
    return jsonify({'success': True, 'message': 'Fragenpool gespeichert'})

@app.route('/api/questions', methods=['GET'])
def get_questions():
    category = request.args.get('category')
    db = get_db()
    if category:
        rows = db.execute('SELECT * FROM questions WHERE category = ?', (category,)).fetchall()
    else:
        rows = db.execute('SELECT * FROM questions').fetchall()
    questions = []
    for row in rows:
        answer_value = row['answer'] if 'answer' in row.keys() else None
        questions.append({
            'id': row['id'],
            'category': row['category'],
            'type': row['type'],
            'question': row['question'],
            'answer': answer_value,
            'options': json.loads(row['options']) if row['options'] else None,
            'created_at': row['created_at']
        })
    return jsonify(questions)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    db = get_db()
    rows = db.execute('SELECT category, COUNT(*) as count FROM questions GROUP BY category ORDER BY category').fetchall()
    return jsonify([{'name': r['category'], 'count': r['count']} for r in rows])

@app.route('/api/health', methods=['GET'])
def health():
    db = get_db()
    q_count = db.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
    u_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    return jsonify({'status': 'ok', 'questions': q_count, 'users': u_count, 'version': '2.0-portal'})

@app.route('/api/progress', methods=['GET', 'POST'])
def progress():
    db = get_db()
    if request.method == 'POST':
        data = request.json or {}
        user_id = data.get('user_id')
        question_id = data.get('question_id')
        correct = 1 if data.get('correct') else 0
        if not user_id or not question_id:
            return jsonify({'success': False, 'message': 'user_id und question_id erforderlich.'}), 400
        db.execute('INSERT INTO user_progress (user_id, question_id, answered, correct, created_at) VALUES (?, ?, 1, ?, ?)',
                   (user_id, question_id, correct, datetime.now(timezone.utc).isoformat()))
        db.commit()
        return jsonify({'success': True})
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id erforderlich.'}), 400
    rows = db.execute('SELECT * FROM user_progress WHERE user_id = ?', (user_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/quiz-attempt', methods=['POST'])
def quiz_attempt():
    data = request.json or {}
    user_id = data.get('user_id')
    total_questions = int(data.get('total_questions') or 0)
    correct = int(data.get('correct') or 0)
    wrong = int(data.get('wrong') or 0)
    mode = (data.get('mode') or 'test').strip()
    if not user_id or total_questions <= 0:
        return jsonify({'success': False, 'message': 'Ungültige Daten.'}), 400
    percentage = round((correct / total_questions) * 100, 2)
    db = get_db()
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    db.execute('INSERT INTO quiz_attempts (user_id, mode, total_questions, correct, wrong, percentage, created_at, ip, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
               (user_id, mode, total_questions, correct, wrong, percentage, datetime.utcnow().isoformat(), ip, user_agent))
    db.commit()
    return jsonify({'success': True})

# ═══════════════════════════════════════════════════════════════════════════════
# HOME CLOUD FILE API
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/files/list', methods=['GET'])
def files_list():
    user_id_str = request.args.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    rel_path = (request.args.get('path') or '').strip('/')
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id fehlt'}), 400
    target = safe_path(user_id, rel_path)
    if not target:
        return jsonify({'success': False, 'message': 'Ungültiger Pfad'}), 400
    if not os.path.exists(target):
        os.makedirs(target, exist_ok=True)
    entries = []
    try:
        for entry in sorted(os.scandir(target), key=lambda e: (not e.is_dir(), e.name.lower())):
            stat = entry.stat()
            entries.append({
                'name': entry.name,
                'is_dir': entry.is_dir(),
                'size': stat.st_size if not entry.is_dir() else 0,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    except PermissionError:
        return jsonify({'success': False, 'message': 'Kein Zugriff'}), 403
    user_root = get_user_storage(user_id)
    counts = {}
    total_bytes = 0
    for cat in CATEGORIES:
        cat_dir = os.path.join(user_root, cat)
        cnt = 0
        if os.path.exists(cat_dir):
            for _, _, fnames in os.walk(cat_dir):
                cnt += len(fnames)
        counts[cat] = cnt
    for dirpath, _, fnames in os.walk(user_root):
        for fname in fnames:
            try:
                total_bytes += os.path.getsize(os.path.join(dirpath, fname))
            except Exception:
                pass
    return jsonify({
        'success': True,
        'files': entries,
        'counts': counts,
        'storage_used': format_size(total_bytes)
    })

@app.route('/api/files/upload', methods=['POST'])
def files_upload():
    user_id_str = request.form.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    rel_path = (request.form.get('path') or '').strip('/')
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id fehlt'}), 400
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Keine Datei'}), 400
    file = request.files['file']
    orig_name = file.filename or 'upload'
    safe_name = secure_filename(orig_name)
    if not safe_name:
        safe_name = 'upload'
    if not rel_path:
        rel_path = get_category_for_file(safe_name)
    target_dir = safe_path(user_id, rel_path)
    if not target_dir:
        return jsonify({'success': False, 'message': 'Ungültiger Pfad'}), 400
    os.makedirs(target_dir, exist_ok=True)
    dest = os.path.join(target_dir, safe_name)
    if os.path.exists(dest):
        base, ext = os.path.splitext(safe_name)
        i = 1
        while os.path.exists(dest):
            dest = os.path.join(target_dir, f'{base}_{i}{ext}')
            i += 1
    file.save(dest)
    return jsonify({'success': True, 'filename': os.path.basename(dest)})

@app.route('/api/files/download', methods=['GET'])
def files_download():
    user_id_str = request.args.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    rel_path = (request.args.get('path') or '').strip('/')
    if not user_id or not rel_path:
        return abort(400)
    target = safe_path(user_id, rel_path)
    if not target or not os.path.isfile(target):
        return abort(404)
    mime, _ = mimetypes.guess_type(target)
    return send_file(target, mimetype=mime or 'application/octet-stream',
                     as_attachment=False, download_name=os.path.basename(target))

@app.route('/api/files/delete', methods=['POST'])
def files_delete():
    data = request.json or {}
    user_id = data.get('user_id')
    rel_path = (data.get('path') or '').strip('/')
    if not user_id or not rel_path:
        return jsonify({'success': False, 'message': 'user_id und path erforderlich'}), 400
    target = safe_path(user_id, rel_path)
    if not target:
        return jsonify({'success': False, 'message': 'Ungültiger Pfad'}), 400
    if not os.path.exists(target):
        return jsonify({'success': False, 'message': 'Nicht gefunden'}), 404
    user_root = get_user_storage(user_id)
    if target == user_root or (os.path.basename(target) in CATEGORIES and os.path.dirname(target) == user_root):
        return jsonify({'success': False, 'message': 'Systemordner können nicht gelöscht werden'}), 403
    try:
        if os.path.isdir(target):
            shutil.rmtree(target)
        else:
            os.remove(target)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/files/mkdir', methods=['POST'])
def files_mkdir():
    data = request.json or {}
    user_id = data.get('user_id')
    rel_path = (data.get('path') or '').strip('/')
    if not user_id or not rel_path:
        return jsonify({'success': False, 'message': 'user_id und path erforderlich'}), 400
    target = safe_path(user_id, rel_path)
    if not target:
        return jsonify({'success': False, 'message': 'Ungültiger Pfad'}), 400
    os.makedirs(target, exist_ok=True)
    return jsonify({'success': True})

@app.route('/api/files/storage', methods=['GET'])
def files_storage_info():
    user_id_str = request.args.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    if not user_id:
        return jsonify({'success': False}), 400
    user_root = get_user_storage(user_id)
    total = 0
    for dirpath, _, fnames in os.walk(user_root):
        for fname in fnames:
            try:
                total += os.path.getsize(os.path.join(dirpath, fname))
            except Exception:
                pass
    return jsonify({'success': True, 'bytes': total, 'formatted': format_size(total)})

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN API - HOME ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════════════════════

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

def verify_admin(request):
    """Verify admin credentials from request header or POST data."""
    admin_pwd = request.headers.get('X-Admin-Password') or (request.json or {}).get('admin_password')
    return admin_pwd == ADMIN_PASSWORD

@app.route('/api/admin/users', methods=['GET'])
def admin_list_users():
    """List all users with their access permissions."""
    if not verify_admin(request):
        return jsonify({'success': False, 'message': 'Admin-Passwort erforderlich'}), 401
    
    db = get_db()
    rows = db.execute(
        'SELECT id, username, home_access_allowed, smarthome_access_allowed, lernapp_access_allowed, created_at FROM users ORDER BY id'
    ).fetchall()
    
    users = []
    for row in rows:
        users.append({
            'id': row['id'],
            'username': row['username'],
            'home_access_allowed': bool(row['home_access_allowed']),
            'smarthome_access_allowed': bool(row['smarthome_access_allowed']),
            'lernapp_access_allowed': bool(row['lernapp_access_allowed']),
            'created_at': row['created_at']
        })
    
    return jsonify({'success': True, 'users': users})

@app.route('/api/admin/users', methods=['POST'])
def admin_create_user():
    """Create a new user (admin only)."""
    if not verify_admin(request):
        return jsonify({'success': False, 'message': 'Admin-Passwort erforderlich'}), 401
    
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    home_access = data.get('home_access_allowed', True)
    smarthome_access = data.get('smarthome_access_allowed', False)
    lernapp_access = data.get('lernapp_access_allowed', False)
    
    # Validierung
    if not username:
        return jsonify({'success': False, 'message': 'Benutzername erforderlich'}), 400
    
    if not password:
        return jsonify({'success': False, 'message': 'Passwort erforderlich'}), 400
    
    # Passwort-Validierung
    valid, msg = validate_password_strength(password)
    if not valid:
        return jsonify({'success': False, 'message': msg}), 400
    
    # Überprüfe ob Benutzer bereits existiert
    db = get_db()
    existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        return jsonify({'success': False, 'message': 'Benutzername existiert bereits'}), 400
    
    # Erstelle neuen Benutzer
    try:
        password_hash = generate_password_hash(password)
        db.execute(
            'INSERT INTO users (username, password, password_hash, home_access_allowed, smarthome_access_allowed, lernapp_access_allowed, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (username, password_hash, password_hash, 1 if home_access else 0, 1 if smarthome_access else 0, 1 if lernapp_access else 0, datetime.now().isoformat())
        )
        db.commit()
        
        # Erstelle user_storage Verzeichnis
        user_id = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()['id']
        for category in CATEGORIES:
            cat_dir = os.path.join(STORAGE_ROOT, str(user_id), category)
            os.makedirs(cat_dir, exist_ok=True)
        
        return jsonify({
            'success': True,
            'message': f'Benutzer "{username}" erstellt',
            'user_id': user_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler beim Erstellen: {str(e)}'}), 500

@app.route('/api/admin/user/permission', methods=['POST'])
def admin_set_permission():
    """Set user permission for a feature (home, smarthome, lernapp)."""
    if not verify_admin(request):
        return jsonify({'success': False, 'message': 'Admin-Passwort erforderlich'}), 401
    
    data = request.json or {}
    user_id = data.get('user_id')
    feature = data.get('feature')  # 'home', 'smarthome', 'lernapp'
    allowed = data.get('allowed', False)
    
    if not user_id or not feature:
        return jsonify({'success': False, 'message': 'user_id und feature erforderlich'}), 400
    
    if feature not in ['home', 'smarthome', 'lernapp']:
        return jsonify({'success': False, 'message': 'Ungültiges Feature'}), 400
    
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    # Update the appropriate column
    column_map = {
        'home': 'home_access_allowed',
        'smarthome': 'smarthome_access_allowed',
        'lernapp': 'lernapp_access_allowed'
    }
    column = column_map[feature]
    
    db.execute(f'UPDATE users SET {column} = ? WHERE id = ?', (1 if allowed else 0, user_id))
    db.commit()
    
    return jsonify({
        'success': True,
        'message': f'{feature.upper()} für Benutzer {"freigegeben" if allowed else "gesperrt"}'
    })

@app.route('/api/user/check-access', methods=['GET'])
def check_user_access():
    """Check if user has access to specific features."""
    user_id_str = request.args.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    feature = request.args.get('feature', 'all')  # 'all', 'home', 'smarthome', 'lernapp'
    
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id erforderlich'}), 400
    
    db = get_db()
    user = db.execute(
        'SELECT home_access_allowed, smarthome_access_allowed, lernapp_access_allowed FROM users WHERE id = ?', 
        (user_id,)
    ).fetchone()
    
    if not user:
        return jsonify({'success': False, 'allowed': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    if feature == 'all':
        return jsonify({
            'success': True,
            'home': bool(user['home_access_allowed']),
            'smarthome': bool(user['smarthome_access_allowed']),
            'lernapp': bool(user['lernapp_access_allowed'])
        })
    elif feature in ['home', 'smarthome', 'lernapp']:
        col = f'{feature}_access_allowed'
        return jsonify({
            'success': True,
            'allowed': bool(user[col]),
            'feature': feature
        })
    else:
        return jsonify({'success': False, 'message': 'Ungültiges Feature'}), 400

@app.route('/api/user/check-home-access', methods=['GET'])
def check_home_access():
    """Check if user has home access."""
    user_id_str = request.args.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id erforderlich'}), 400
    
    db = get_db()
    user = db.execute('SELECT home_access_allowed FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'success': False, 'allowed': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    allowed = bool(user['home_access_allowed'])
    return jsonify({'success': True, 'allowed': allowed})

# ───────────────────────────────────────────────────────────────────────────────
# ADMIN APIs - Passwort & Statistiken Management
# ───────────────────────────────────────────────────────────────────────────────

@app.route('/api/admin/stats', methods=['GET'])
def admin_get_stats():
    """Get comprehensive statistics for admin dashboard."""
    if not verify_admin(request):
        return jsonify({'success': False, 'message': 'Admin-Passwort erforderlich'}), 401
    
    db = get_db()
    
    # Benutzerstatistiken
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    home_access_count = db.execute('SELECT COUNT(*) FROM users WHERE home_access_allowed = 1').fetchone()[0]
    
    try:
        # Quiz-Statistiken (falls quiz_results existiert)
        total_quizzes = db.execute('SELECT COUNT(*) FROM quiz_results').fetchone()[0]
        avg_score = db.execute('SELECT AVG(score) FROM quiz_results').fetchone()[0] or 0
    except:
        total_quizzes = 0
        avg_score = 0
    
    return jsonify({
        'success': True,
        'total_users': total_users,
        'home_access_count': home_access_count,
        'total_quizzes': total_quizzes,
        'avg_score': round(avg_score, 2) if avg_score else 0,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/admin/user/<int:user_id>', methods=['GET'])
def admin_get_user(user_id):
    """Get detailed user information."""
    if not verify_admin(request):
        return jsonify({'success': False, 'message': 'Admin-Passwort erforderlich'}), 401
    
    db = get_db()
    user = db.execute(
        'SELECT id, username, email, created_at, home_access_allowed FROM users WHERE id = ?', 
        (user_id,)
    ).fetchone()
    
    if not user:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at'],
            'home_access_allowed': bool(user['home_access_allowed'])
        }
    })

@app.route('/api/admin/user/<int:user_id>/password', methods=['POST'])
def admin_change_password(user_id):
    """Admin endpoint to change user password."""
    if not verify_admin(request):
        return jsonify({'success': False, 'message': 'Admin-Passwort erforderlich'}), 401
    
    data = request.json or {}
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({'success': False, 'message': 'Neues Passwort erforderlich'}), 400
    
    # Passwort-Validierung
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Passwort muss mindestens 6 Zeichen lang sein'}), 400
    
    db = get_db()
    user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    # Passwort hashen
    password_hash = generate_password_hash(new_password)
    
    db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
    db.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Passwort von {user["username"]} wurde aktualisiert'
    })

@app.route('/api/admin/user/<int:user_id>/edit', methods=['POST'])
def admin_edit_user(user_id):
    """Admin endpoint to edit user information."""
    if not verify_admin(request):
        return jsonify({'success': False, 'message': 'Admin-Passwort erforderlich'}), 401
    
    data = request.json or {}
    
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    # Erlaube nur bestimmte Felder zu ändern
    updates = {}
    if 'email' in data:
        updates['email'] = data['email']
    
    if updates:
        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        db.execute(f'UPDATE users SET {set_clause} WHERE id = ?', values)
        db.commit()
    
    return jsonify({
        'success': True,
        'message': 'Benutzer aktualisiert'
    })

@app.route('/api/admin/user/<int:user_id>/delete', methods=['POST'])
def admin_delete_user(user_id):
    """Admin endpoint to delete a user."""
    if not verify_admin(request):
        return jsonify({'success': False, 'message': 'Admin-Passwort erforderlich'}), 401
    
    # Verhindere Admin-Löschung
    db = get_db()
    user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    if user['username'] == 'admin':
        return jsonify({'success': False, 'message': 'Admin-Account kann nicht gelöscht werden'}), 403
    
    # Lösche Benutzer und zugehörige Daten
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.execute('DELETE FROM quiz_results WHERE user_id = ? OR username = ?', (user_id, user['username']))
    db.commit()
    
    return jsonify({
        'success': True,
        'message': f'Benutzer {user["username"]} gelöscht'
    })

@app.route('/api/admin/user/<int:user_id>/stats', methods=['GET'])
def admin_get_user_stats(user_id):
    """Get statistics for a specific user."""
    if not verify_admin(request):
        return jsonify({'success': False, 'message': 'Admin-Passwort erforderlich'}), 401
    
    db = get_db()
    user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    try:
        # Quiz-Statistiken für diesen Benutzer
        quiz_count = db.execute(
            'SELECT COUNT(*) FROM quiz_results WHERE user_id = ? OR username = ?', 
            (user_id, user['username'])
        ).fetchone()[0]
        
        avg_score = db.execute(
            'SELECT AVG(score) FROM quiz_results WHERE user_id = ? OR username = ?', 
            (user_id, user['username'])
        ).fetchone()[0] or 0
        
        last_quiz = db.execute(
            'SELECT MAX(attempted_at) FROM quiz_results WHERE user_id = ? OR username = ?', 
            (user_id, user['username'])
        ).fetchone()[0]
    except:
        quiz_count = 0
        avg_score = 0
        last_quiz = None
    
    return jsonify({
        'success': True,
        'username': user['username'],
        'quiz_count': quiz_count,
        'avg_score': round(avg_score, 2) if avg_score else 0,
        'last_quiz': last_quiz,
        'home_access_allowed': bool(db.execute(
            'SELECT home_access_allowed FROM users WHERE id = ?', (user_id,)
        ).fetchone()[0])
    })

# ═══════════════════════════════════════════════════════════════════════════════
# USER SELF-SERVICE (Password Change, Profile Edit, Delete Account)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/user/profile', methods=['GET'])
def user_get_profile():
    """Get current user profile"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    db = get_db()
    user = db.execute('SELECT id, username, created_at FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    
    if not user:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'created_at': user['created_at']
        }
    })

@app.route('/api/user/password/change', methods=['POST'])
def user_change_password():
    """Change password for logged-in user"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    data = request.json or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    # Validierung
    if not all([current_password, new_password, confirm_password]):
        return jsonify({'success': False, 'message': 'Alle Felder sind erforderlich'}), 400
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Neue Passwörter stimmen nicht überein'}), 400
    
    valid, msg = validate_password_strength(new_password)
    if not valid:
        return jsonify({'success': False, 'message': msg}), 400
    
    # Überprüfe aktuelles Passwort
    db = get_db()
    user = db.execute('SELECT password_hash FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    
    if not user or not check_password_hash(user['password_hash'], current_password):
        return jsonify({'success': False, 'message': 'Aktuelles Passwort ist falsch'}), 401
    
    # Update password
    new_hash = generate_password_hash(new_password)
    db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, g.user['id']))
    db.commit()
    
    return jsonify({'success': True, 'message': 'Passwort erfolgreich geändert'})

@app.route('/api/user/profile/edit', methods=['POST'])
def user_edit_profile():
    """Edit user profile details"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    data = request.json or {}
    # Für jetzt nur Username update - kann erweitert werden
    
    return jsonify({
        'success': True,
        'message': 'Profil konnte aktualisiert werden (in Planung)'
    })

@app.route('/api/user/delete', methods=['DELETE', 'POST'])
def user_delete_account():
    """Delete user account"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    data = request.json or {}
    password = data.get('password')
    
    if not password:
        return jsonify({'success': False, 'message': 'Passwort ist erforderlich'}), 400
    
    # Verify password
    db = get_db()
    user = db.execute('SELECT password_hash FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'message': 'Passwort ist falsch'}), 401
    
    # Don't allow admin to delete themselves
    if user_is_admin(g.user['id']):
        return jsonify({'success': False, 'message': 'Admin-Konten können nicht gelöscht werden'}), 403
    
    # Delete user and all associated data
    try:
        user_id = g.user['id']
        db.execute('DELETE FROM quiz_results WHERE user_id = ? OR username = ?', (user_id, g.user['username']))
        db.execute('DELETE FROM smarthome_devices WHERE user_id = ?', (user_id,))
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
        
        # Clean up user storage
        import shutil
        user_storage = os.path.join(STORAGE_ROOT, str(user_id))
        if os.path.exists(user_storage):
            shutil.rmtree(user_storage)
        
        return jsonify({'success': True, 'message': 'Konto erfolgreich gelöscht'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler beim Löschen: {str(e)}'}), 500

def user_is_admin(user_id):
    """Check if user is admin"""
    db = get_db()
    user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    return user and user['username'] == 'admin'

# ═══════════════════════════════════════════════════════════════════════════════
# SMART HOME DEVICE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/smarthome/devices', methods=['GET'])
def smarthome_get_devices():
    """Get all ONLINE smart home devices for logged-in user."""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    db = get_db()
    # Only return online devices
    devices = db.execute(
        'SELECT id, device_name, device_type, ip_address, port, status, last_seen FROM smarthome_devices WHERE user_id = ? AND status = ? ORDER BY created_at DESC',
        (g.user['id'], 'online')
    ).fetchall()
    
    return jsonify({
        'success': True,
        'devices': [dict(d) for d in devices]
    })

@app.route('/api/smarthome/device/add', methods=['POST'])
def smarthome_add_device():
    """Add a new smart home device."""
    try:
        if not g.user:
            return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
        
        data = request.get_json() or {}
        device_name = (data.get('device_name') or '').strip()
        device_type = (data.get('device_type') or '').strip()
        ip_address = (data.get('ip_address') or '').strip()
        port = data.get('port', 80)
        protocol = (data.get('protocol') or 'http').lower()
        auth_token = (data.get('auth_token') or '').strip()
        
        if not device_name or not device_type or not ip_address:
            return jsonify({'success': False, 'message': 'Gerätename, Typ und IP erforderlich'}), 400
        
        # Konvertiere port zu int
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 80
        
        if not (0 < port < 65536):
            return jsonify({'success': False, 'message': 'Port muss zwischen 1 und 65535 liegen'}), 400
        
        db = get_db()
        
        # Check user permissions
        user = db.execute('SELECT username, smarthome_access_allowed FROM users WHERE id = ?', (g.user['id'],)).fetchone()
        if not user or not user['smarthome_access_allowed']:
            return jsonify({'success': False, 'message': 'Smart Home Zugriff nicht erlaubt'}), 403
        
        # Determine which user account to add device to
        target_user_id = g.user['id']
        if user['username'] != 'admin':
            # Non-admin users add devices to admin's account
            admin_user = db.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
            if admin_user:
                target_user_id = admin_user['id']
        
        # Test connectivity - nur speichern wenn verfügbar
        status = 'offline'
        try:
            url = f'{protocol}://{ip_address}:{port}/'
            response = requests.get(url, timeout=2, verify=False, allow_redirects=True)
            # Akzeptiere jeden Status-Code der nicht 50x ist
            if response.status_code < 500:
                status = 'online'
        except requests.exceptions.Timeout:
            status = 'offline'
        except requests.exceptions.ConnectionError:
            status = 'offline'
        except Exception as e:
            status = 'offline'
        
        # Nur online-Geräte speichern
        if status == 'offline':
            return jsonify({
                'success': False,
                'message': f'Gerät "{device_name}" ({ip_address}:{port}) ist nicht erreichbar. Bitte überprüfen Sie die Verbindung.'
            }), 400
        
        # Speichere Gerät
        db.execute(
            'INSERT INTO smarthome_devices (user_id, device_name, device_type, ip_address, port, protocol, auth_token, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (target_user_id, device_name, device_type, ip_address, port, protocol, auth_token, status, datetime.utcnow().isoformat())
        )
        db.commit()
        
        device_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        return jsonify({
            'success': True,
            'message': f'Gerät "{device_name}" hinzugefügt!',
            'device_id': device_id
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'Fehler beim Hinzufügen: {str(e)}',
            'error_type': type(e).__name__
        }), 500

@app.route('/api/smarthome/device/<int:device_id>/edit', methods=['POST'])
def smarthome_edit_device(device_id):
    """Edit smart home device details."""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    db = get_db()
    device = db.execute('SELECT * FROM smarthome_devices WHERE id = ? AND user_id = ?', 
                       (device_id, g.user['id'])).fetchone()
    
    if not device:
        return jsonify({'success': False, 'message': 'Gerät nicht gefunden oder kein Zugriff'}), 404
    
    data = request.json or {}
    
    # Update editable fields
    device_name = data.get('device_name', device['device_name'])
    device_type = data.get('device_type', device['device_type'])
    auth_token = data.get('auth_token', device['auth_token'])
    
    try:
        db.execute(
            'UPDATE smarthome_devices SET device_name = ?, device_type = ?, auth_token = ? WHERE id = ?',
            (device_name, device_type, auth_token, device_id)
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Gerät aktualisiert',
            'device_id': device_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Aktualisieren: {str(e)}'
        }), 500

@app.route('/api/smarthome/device/<int:device_id>/status', methods=['GET'])
def smarthome_get_device_status(device_id):
    """Get smart home device status."""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    db = get_db()
    device = db.execute(
        'SELECT * FROM smarthome_devices WHERE id = ? AND user_id = ?',
        (device_id, g.user['id'])
    ).fetchone()
    
    if not device:
        return jsonify({'success': False, 'message': 'Gerät nicht gefunden'}), 404
    
    # Try to ping device
    import requests
    try:
        url = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/'
        response = requests.get(url, timeout=2, verify=False, allow_redirects=False)
        status = 'online'
        last_seen = datetime.utcnow().isoformat()
        db.execute(
            'UPDATE smarthome_devices SET status = ?, last_seen = ? WHERE id = ?',
            (status, last_seen, device_id)
        )
        db.commit()
    except:
        status = 'offline'
    
    return jsonify({
        'success': True,
        'device_id': device_id,
        'device_name': device['device_name'],
        'device_type': device['device_type'],
        'status': status,
        'last_seen': device['last_seen'],
        'ip_address': device['ip_address'],
        'port': device['port']
    })

@app.route('/api/smarthome/device/<int:device_id>/command', methods=['POST'])
def smarthome_send_command(device_id):
    """Send command to smart home device."""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    data = request.get_json() or {}
    command = (data.get('command') or '').strip()
    value = data.get('value')
    
    if not command:
        return jsonify({'success': False, 'message': 'Befehl erforderlich'}), 400
    
    db = get_db()
    
    # Check if user has smarthome access
    user = db.execute('SELECT username, smarthome_access_allowed FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    if not user or not user['smarthome_access_allowed']:
        return jsonify({'success': False, 'message': 'Smart Home Zugriff nicht erlaubt'}), 403
    
    # Find device - either owned by user or admin's device (for authorized users)
    device = None
    if user['username'] == 'admin':
        # Admin can control their own devices
        device = db.execute(
            'SELECT * FROM smarthome_devices WHERE id = ? AND user_id = ?',
            (device_id, g.user['id'])
        ).fetchone()
    else:
        # Non-admin users can control admin's devices if they have access
        admin_user = db.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
        if admin_user:
            device = db.execute(
                'SELECT * FROM smarthome_devices WHERE id = ? AND user_id = ?',
                (device_id, admin_user['id'])
            ).fetchone()
    
    if not device:
        return jsonify({'success': False, 'message': 'Gerät nicht gefunden'}), 404
    
    # Send command to device
    import requests
    try:
        # Construct request based on device type
        if device['device_type'].lower() in ['philips_hue', 'light', 'lamp']:
            # Generic REST API for lights
            if command == 'power':
                state = 'on' if value else 'off'
                endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/control'
                payload = {'action': 'power', 'state': state}
            elif command == 'brightness':
                endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/control'
                payload = {'action': 'brightness', 'value': int(value or 100)}
            elif command == 'color':
                endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/control'
                payload = {'action': 'color', 'value': value}
            else:
                endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/control'
                payload = {'action': command, 'value': value}
        elif device['device_type'].lower() in ['television', 'tv', 'fernseher']:
            # TV-specific commands
            if command == 'power':
                state = 'on' if value else 'off'
                endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/tv/power'
                payload = {'state': state}
            elif command == 'volume':
                endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/tv/volume'
                payload = {'action': value}  # 'up' or 'down'
            elif command == 'channel':
                endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/tv/channel'
                payload = {'channel': int(value or 1)}
            elif command == 'command':
                endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/tv/command'
                payload = {'command': value}  # 'mute', 'play', 'pause', etc.
            else:
                endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/tv/control'
                payload = {'action': command, 'value': value}
        else:
            # Generic command endpoint
            endpoint = f'{device["protocol"]}://{device["ip_address"]}:{device["port"]}/api/command'
            payload = {'command': command, 'value': value}
        
        headers = {'Content-Type': 'application/json'}
        if device['auth_token']:
            headers['Authorization'] = f'Bearer {device["auth_token"]}'
        
        response = requests.post(endpoint, json=payload, timeout=5, verify=False, headers=headers)
        
        if response.status_code in [200, 201, 204]:
            result = response.json() if response.text else {'success': True}
            return jsonify({
                'success': True,
                'message': f'Befehl "{command}" gesendet',
                'device_response': result
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Gerät antwortet mit Status {response.status_code}',
                'error': response.text
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Befehl konnte nicht gesendet werden',
            'error': str(e)
        }), 500

@app.route('/api/smarthome/device/<int:device_id>/delete', methods=['DELETE'])
def smarthome_delete_device(device_id):
    """Delete smart home device."""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    db = get_db()
    
    # Check user permissions
    user = db.execute('SELECT username, smarthome_access_allowed FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    if not user or not user['smarthome_access_allowed']:
        return jsonify({'success': False, 'message': 'Smart Home Zugriff nicht erlaubt'}), 403
    
    # Find device - either owned by user or admin's device (for authorized users)
    device = None
    if user['username'] == 'admin':
        # Admin can delete their own devices
        device = db.execute(
            'SELECT device_name FROM smarthome_devices WHERE id = ? AND user_id = ?',
            (device_id, g.user['id'])
        ).fetchone()
    else:
        # Non-admin users can delete admin's devices if they have access
        admin_user = db.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
        if admin_user:
            device = db.execute(
                'SELECT device_name FROM smarthome_devices WHERE id = ? AND user_id = ?',
                (device_id, admin_user['id'])
            ).fetchone()
    
    if not device:
        return jsonify({'success': False, 'message': 'Gerät nicht gefunden'}), 404
    
    db.execute('DELETE FROM smarthome_devices WHERE id = ?', (device_id,))
    db.commit()
    
    return jsonify({
        'success': True,
        'message': f'Gerät "{device["device_name"]}" gelöscht'
    })

@app.route('/api/smarthome/discover', methods=['POST'])
def smarthome_discover_devices():
    """Discover smart home devices on network (fast scan for responsive hosts)."""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    data = request.get_json() or {}
    network_range = (data.get('network_range') or '192.168.1').strip()  # e.g., "192.168.1"
    
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    found_devices = {}  # Use dict to avoid duplicates {ip: port}
    common_ports = [80, 8080, 8000, 8888, 3000, 5000, 9000, 11000]
    
    def check_host(ip, port):
        """Check if a host is reachable on a specific port."""
        try:
            response = requests.get(
                f'http://{ip}:{port}/',
                timeout=1.5,
                verify=False,
                allow_redirects=False
            )
            # Check if device responds (any 2xx, 3xx, 4xx)
            if response.status_code < 500:
                return (ip, port, True)
        except:
            pass
        return None
    
    # Scan IPs in the network range with threading
    try:
        base_ip = '.'.join(network_range.split('.')[:3])
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            
            for i in range(2, 255):  # Skip .0 and .1
                ip = f'{base_ip}.{i}'
                for port in common_ports:
                    futures.append(executor.submit(check_host, ip, port))
            
            # Collect results
            for future in as_completed(futures):
                result = future.result()
                if result:
                    ip, port, found = result
                    found_devices[ip] = port
        
        # Convert back to list format
        devices_list = [{'ip': ip, 'port': port, 'detected': True} for ip, port in found_devices.items()]
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Netzwerk-Scan fehlgeschlagen',
            'error': str(e)
        }), 400
    
    return jsonify({
        'success': True,
        'devices_found': devices_list,
        'count': len(devices_list),
        'network': base_ip + '.0/24'
    })

# ═══════════════════════════════════════════════════════════════════════════════
# SMART HOME - NETZWERK SCAN
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/smarthome/scan', methods=['GET'])
def smarthome_network_scan():
    """Scanne Netzwerk nach Smart Home Geräten (vereinfachte Version ohne Auth)"""
    print("Scan-Route aufgerufen!")
    try:
        import subprocess
        import socket
        from datetime import datetime, timezone
        
        # Get local network info
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "192.168.178.100"
        
        network_base = ".".join(local_ip.split(".")[:3]) + "."
        print(f"Scanne Netzwerk: {network_base}0/24")
        
        # ARP scan only
        active_ips = []
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            timeout=5,
            encoding='utf-8'
        )
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and not line.startswith('Schnittstelle') and not line.startswith('Interface'):
                parts = line.split()
                if len(parts) >= 2:
                    ip_candidate = parts[0]
                    if ip_candidate.count('.') == 3 and ip_candidate.startswith(network_base[:-1]):
                        try:
                            socket.inet_aton(ip_candidate)
                            if ip_candidate not in active_ips and ip_candidate != local_ip:
                                active_ips.append(ip_candidate)
                                print(f"ARP: {ip_candidate}")
                        except:
                            pass
        
        print(f"ARP gefunden: {len(active_ips)} IPs")
        
        # Create simple device list
        devices = []
        for ip in active_ips[:5]:  # Limit to 5 devices
            hostname = f"Device-{ip.split('.')[-1]}"
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                pass
            
            device_type = "Netzwerk-Gerät"
            if ip.endswith('.1'):
                device_type = "Router/Gateway"
            elif ip == "192.168.178.1":
                device_type = "Fritz!Box Router"
            
            devices.append({
                'id': f'{ip}:80',
                'name': hostname,
                'device_type': device_type,
                'ip_address': ip,
                'port': 80,
                'status': 'online',
                'is_controllable': False,
                'manufacturer': 'Unbekannt',
                'last_seen': datetime.now(timezone.utc).isoformat()
            })
        
        print(f"Scan abgeschlossen: {len(devices)} Geräte")
        
        return jsonify({
            'success': True,
            'devices': devices,
            'count': len(devices),
            'local_network': network_base + "0/24",
            'local_ip': local_ip,
            'scan_type': 'local'
        })
        
    except Exception as e:
        print(f"Scan-Fehler: {e}")
        return jsonify({
            'success': False,
            'message': f'Scan fehlgeschlagen: {str(e)}'
        })
    
    # If user is not admin but has access, return admin's devices
    else:
        try:
            admin_user = db.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
            if not admin_user:
                return jsonify({'success': False, 'message': 'Admin-Benutzer nicht gefunden'}), 404
            
            admin_devices = db.execute(
                'SELECT id, device_name as name, device_type, ip_address, port, status, last_seen FROM smarthome_devices WHERE user_id = ? ORDER BY created_at DESC',
                (admin_user['id'],)
            ).fetchall()
            
            devices = []
            for device in admin_devices:
                devices.append({
                    'id': str(device['id']),
                    'name': device['name'],
                    'device_type': device['device_type'],
                    'ip_address': device['ip_address'],
                    'port': device['port'],
                    'mac_address': 'Remote',
                    'status': device['status'] or 'unknown',
                    'is_controllable': True,
                    'manufacturer': 'Admin Network',
                    'last_seen': device['last_seen']
                })
            
            return jsonify({
                'success': True,
                'devices': devices,
                'count': len(devices),
                'scan_type': 'remote',
                'message': 'Admin-Geräte (Remote-Zugriff)'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Remote Scan fehlgeschlagen: {str(e)}'
            })

@app.route('/api/smarthome/fritzbox/connect', methods=['POST'])
def smarthome_connect_fritzbox():
    """Verbinde mit Fritz!Box und erkenne Smart Home Geräte"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentifizierung erforderlich'}), 401
    
    data = request.json or {}
    user_id_str = data.get('user_id')
    user_id = int(user_id_str) if user_id_str and str(user_id_str).isdigit() else None
    fritzbox_ip = data.get('fritzbox_ip', '').strip()
    
    if not user_id or user_id != g.user['id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Wenn keine IP angegeben, versuche gängige Fritz!Box IPs
    if not fritzbox_ip:
        common_fritzbox_ips = ['192.168.178.1', '192.168.1.1', '192.168.0.1', 'fritz.box']
        fritzbox_ip = None
        
        for ip in common_fritzbox_ips:
            try:
                print(f"Versuche Fritz!Box unter {ip}...")
                response = requests.get(
                    f'http://{ip}:80/',
                    timeout=5,  # Erhöhtes Timeout
                    verify=False,
                    allow_redirects=True
                )
                
                if response.status_code < 500:
                    fritzbox_ip = ip
                    print(f"Fritz!Box gefunden unter {ip}")
                    break
                    
            except requests.exceptions.Timeout:
                print(f"Timeout bei {ip}, versuche nächste...")
                continue
            except requests.exceptions.ConnectionError:
                print(f"Verbindung fehlgeschlagen bei {ip}, versuche nächste...")
                continue
            except Exception as e:
                print(f"Fehler bei {ip}: {e}, versuche nächste...")
                continue
        
        if not fritzbox_ip:
            return jsonify({
                'success': False,
                'message': 'Fritz!Box nicht gefunden. Gängige IPs versucht: 192.168.178.1, 192.168.1.1, 192.168.0.1, fritz.box. Bitte geben Sie die korrekte IP-Adresse manuell an.'
            }), 400
    else:
        # Manuell angegebene IP testen
        try:
            print(f"Teste manuell angegebene Fritz!Box IP: {fritzbox_ip}")
            response = requests.get(
                f'http://{fritzbox_ip}:80/',
                timeout=8,  # Längeres Timeout für manuelle Eingabe
                verify=False,
                allow_redirects=True
            )
            
            if response.status_code >= 500:
                return jsonify({
                    'success': False,
                    'message': f'Fritz!Box unter {fritzbox_ip} antwortet nicht (Status: {response.status_code})'
                }), 400
                
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'message': f'Verbindung zu Fritz!Box {fritzbox_ip} timeoutet. Bitte überprüfen Sie die IP-Adresse.'
            }), 400
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'message': f'Verbindung zu Fritz!Box {fritzbox_ip} fehlgeschlagen. Bitte überprüfen Sie die IP-Adresse und Netzwerkverbindung.'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Fehler bei Verbindung zu Fritz!Box {fritzbox_ip}: {str(e)}'
            }), 400
    
    try:
        # Fritz!Box ist erreichbar, speichere Verbindung
        db = get_db()
        
        # Prüfe ob bereits eine Fritz!Box für diesen User existiert
        existing = db.execute(
            'SELECT id FROM smarthome_devices WHERE user_id = ? AND device_type = ?',
            (g.user['id'], 'Fritz!Box')
        ).fetchone()
        
        if existing:
            # Update existing Fritz!Box
            db.execute(
                'UPDATE smarthome_devices SET ip_address = ?, status = ?, last_seen = ? WHERE id = ?',
                (fritzbox_ip, 'online', datetime.now(timezone.utc).isoformat(), existing['id'])
            )
        else:
            # Add new Fritz!Box
            db.execute(
                'INSERT INTO smarthome_devices (user_id, device_name, device_type, ip_address, port, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (g.user['id'], 'Fritz!Box Router', 'Fritz!Box', fritzbox_ip, 49000, 'online', datetime.now(timezone.utc).isoformat())
            )
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'Fritz!Box erfolgreich verbunden unter {fritzbox_ip}',
            'fritzbox_ip': fritzbox_ip
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Speichern der Fritz!Box-Verbindung: {str(e)}'
        }), 500

# ═══════════════════════════════════════════════════════════════════════════════
# SMART HOME DISCOVERY (All Devices - Network + Home Assistant)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/smarthome/discover', methods=['GET'])
def smarthome_discover_all():
    """Discover ALL devices: network devices + Home Assistant entities"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Check smart home access
    db = get_db()
    user = db.execute('SELECT smarthome_access_allowed FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    
    if not user or not user['smarthome_access_allowed']:
        return jsonify({'success': False, 'message': 'Smart Home access denied'}), 403
    
    if not SMARTHOME_PORTAL:
        return jsonify({
            'success': False,
            'message': 'Smart Home Portal not available',
            'devices': []
        }), 503
    
    try:
        devices = SMARTHOME_PORTAL.get_all_devices()
        return jsonify({
            'success': True,
            'devices': devices,
            'total': len(devices),
            'network_devices': len([d for d in devices if d.get('domain') == 'fritzbox']),
            'homeassistant_devices': len([d for d in devices if d.get('domain') == 'homeassistant']),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Discovery error: {str(e)}',
            'devices': []
        }), 500

@app.route('/api/smarthome/device/<device_id>/control', methods=['POST'])
def smarthome_control_device(device_id):
    """Control any discovered device (network or HA)"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Check smart home access
    db = get_db()
    user = db.execute('SELECT username, smarthome_access_allowed FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    
    if not user or not user['smarthome_access_allowed']:
        return jsonify({'success': False, 'message': 'Smart Home access denied'}), 403
    
    if not SMARTHOME_PORTAL:
        return jsonify({'success': False, 'message': 'Smart Home Portal not available'}), 503
    
    try:
        data = request.get_json() or {}
        command = (data.get('command') or '').strip().lower()
        value = data.get('value')
        
        if not command:
            return jsonify({'success': False, 'message': 'Command required'}), 400
        
        result = SMARTHOME_PORTAL.send_command(device_id, command, value)
        
        if result.get('success'):
            return jsonify({'success': True, 'message': result.get('message')})
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Unknown error')
            }), 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════════════
# FRITZ!BOX ROUTER CONTROL (Direct Proxy Integration)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/smarthome/router/status', methods=['GET'])
def router_get_status():
    """Get router and network status"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Check admin access
    db = get_db()
    user = db.execute('SELECT smarthome_access_allowed FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    
    if not user or not user['smarthome_access_allowed']:
        return jsonify({'success': False, 'message': 'Smart Home access denied'}), 403
    
    if not FRITZBOX_PROXY:
        return jsonify({'success': False, 'message': 'Fritz!Box Proxy not available'}), 503
    
    try:
        status = FRITZBOX_PROXY.get_network_status()
        return jsonify({
            'success': True,
            'router': status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/smarthome/router/devices', methods=['GET'])
def router_get_devices():
    """Get all devices connected to router"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Check admin access
    db = get_db()
    user = db.execute('SELECT smarthome_access_allowed FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    
    if not user or not user['smarthome_access_allowed']:
        return jsonify({'success': False, 'message': 'Smart Home access denied'}), 403
    
    if not FRITZBOX_PROXY:
        return jsonify({'success': False, 'message': 'Fritz!Box Proxy not available'}), 503
    
    try:
        devices = FRITZBOX_PROXY.get_connected_devices()
        return jsonify({
            'success': True,
            'devices': devices,
            'count': len(devices),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/smarthome/router/control', methods=['POST'])
def router_control():
    """Control router functions"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Check admin access only
    db = get_db()
    user = db.execute('SELECT username, smarthome_access_allowed FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    
    if user['username'] != 'admin' or not user['smarthome_access_allowed']:
        return jsonify({'success': False, 'message': 'Admin access required for router control'}), 403
    
    if not FRITZBOX_PROXY:
        return jsonify({'success': False, 'message': 'Fritz!Box Proxy not available'}), 503
    
    try:
        data = request.get_json() or {}
        action = (data.get('action') or '').strip().lower()
        
        if action == 'reboot':
            result = FRITZBOX_PROXY.reboot_router()
            return jsonify({'success': result.get('success', False), 'result': result})
        
        elif action == 'block_device':
            mac = data.get('mac', '').strip()
            result = FRITZBOX_PROXY.control_device_by_mac(mac, 'block')
            return jsonify({'success': result.get('success', False), 'result': result})
        
        elif action == 'unblock_device':
            mac = data.get('mac', '').strip()
            result = FRITZBOX_PROXY.control_device_by_mac(mac, 'allow')
            return jsonify({'success': result.get('success', False), 'result': result})
        
        else:
            return jsonify({'success': False, 'message': f'Unknown action: {action}'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/smarthome/router/wifi', methods=['POST'])
def router_wifi():
    """Control WiFi (requires authentication)"""
    if not g.user:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    # Check admin access
    db = get_db()
    user = db.execute('SELECT username, smarthome_access_allowed FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    
    if user['username'] != 'admin' or not user['smarthome_access_allowed']:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    if not FRITZBOX_PROXY:
        return jsonify({'success': False, 'message': 'Fritz!Box Proxy not available'}), 503
    
    try:
        data = request.get_json() or {}
        state = (data.get('state') or 'toggle').strip().lower()
        
        # TODO: Implement WiFi toggle when authentication available
        return jsonify({
            'success': False,
            'message': 'WiFi control requires router authentication',
            'note': 'Set router password in fritzbox_proxy.py to enable'
        }), 501
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print(f'''
╔══════════════════════════════════════════════════════════════╗
║           🎓 RenLern Server v2 - Portal Edition              ║
╚══════════════════════════════════════════════════════════════╝

✅ Server startet!

📍 Seiten:
   /          → Portal Login
   /home      → Home Cloud (Persönlicher Dateispeicher)
   /lernapp   → Quiz Lernapp

🌐 URLs:
   Lokal:     http://localhost:5000
   Öffentlich: {CANONICAL_URL}

💾 Speicher:   {STORAGE_ROOT}
📊 Datenbank:  {DATABASE}

🛑 Beenden: Ctrl+C
''')
    with app.app_context():
        setup_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
