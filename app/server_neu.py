import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify, redirect, send_from_directory, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# On Android, BASE_DIR is read-only. Use a writable data directory for DB.
DATA_DIR = os.environ.get('LERNAPP_DATA_DIR', BASE_DIR)

DATABASE = os.path.join(DATA_DIR, 'lernapp.db')
QUESTIONPOOL_FILE = os.path.join(BASE_DIR, 'fragenpool.json')
CANONICAL_HOST = 'renlern.org'
CANONICAL_URL = f'https://{CANONICAL_HOST}'

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')


@app.before_request
def redirect_www_to_canonical_host():
    host = (request.headers.get('Host') or '').split(':', 1)[0].lower()
    if host == f'www.{CANONICAL_HOST}':
        target = request.full_path if request.query_string else request.path
        return redirect(f'{CANONICAL_URL}{target}', code=301)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response



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
    # last_ip Spalte nachruesten falls DB bereits existiert
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
    # answer Spalte nachruesten falls DB bereits existiert
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
                    db.execute('UPDATE questions SET answer = COALESCE(answer, ?) WHERE id = ? AND (answer IS NULL OR answer = "")',
                               (answer_text, exists['id']))
                continue

            db.execute(
                'INSERT INTO questions (category, type, question, answer, options, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (category, qtype, question_text, answer_text, options_text, datetime.utcnow().isoformat())
            )
    db.commit()

def setup_app():
    init_db()
    load_questions_from_json()

@app.route('/')
def root():
    return send_from_directory(BASE_DIR, 'lernapp.html')

@app.route('/<path:path>')
def static_proxy(path):
    if os.path.exists(os.path.join(BASE_DIR, path)):
        return send_from_directory(BASE_DIR, path)
    return send_from_directory(BASE_DIR, 'lernapp.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if len(username) < 3 or len(password) < 6:
        return jsonify({'success': False, 'message': 'Benutzername muss mind. 3 Zeichen und Passwort mind. 6 Zeichen haben.'}), 400

    db = get_db()
    existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        return jsonify({'success': False, 'message': 'Benutzername existiert bereits.'}), 400

    password_hash = generate_password_hash(password)
    created_at = datetime.utcnow().isoformat()
    db.execute('INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)', (username, password_hash, created_at))
    db.commit()

    user_id = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()['id']
    return jsonify({'success': True, 'user': {'id': user_id, 'username': username}})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'message': 'Ungültiger Benutzername oder Passwort.'}), 401

    # IP und Gerät beim Login speichern
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    user_cols = get_user_columns(db)
    sets = []
    params = []
    if 'last_ip' in user_cols:
        sets.append('last_ip = ?')
        params.append(ip)
    if 'last_user_agent' in user_cols:
        sets.append('last_user_agent = ?')
        params.append(user_agent)
    if 'last_seen_at' in user_cols:
        sets.append('last_seen_at = ?')
        params.append(datetime.utcnow().isoformat())
    if sets:
        params.append(user['id'])
        db.execute(f'UPDATE users SET {", ".join(sets)} WHERE id = ?', tuple(params))
        db.commit()
    return jsonify({'success': True, 'user': {'id': user['id'], 'username': user['username']}})

@app.route('/api/load-fragenpool', methods=['GET'])
def load_fragenpool():
    db = get_db()
    rows = db.execute('SELECT * FROM questions').fetchall()
    pool = {}
    # Include empty categories from fragenpool.json
    try:
        with open(QUESTIONPOOL_FILE, 'r', encoding='utf-8') as f:
            file_pool = json.load(f)
        for cat in file_pool:
            pool.setdefault(cat, [])
    except Exception:
        pass
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
        return jsonify({'success': False, 'message': f'Fehler beim Speichern der JSON-Datei: {str(e)}'}), 500

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
    rows = db.execute(
        'SELECT category, COUNT(*) as count FROM questions GROUP BY category ORDER BY category'
    ).fetchall()
    return jsonify([{'name': r['category'], 'count': r['count']} for r in rows])

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Return vendor > cert > topic hierarchy with question counts."""
    db = get_db()
    rows = db.execute(
        'SELECT category, COUNT(*) as count FROM questions GROUP BY category ORDER BY category'
    ).fetchall()
    # Build counts from DB
    db_counts = {}
    for r in rows:
        db_counts[r['category']] = r['count']
    # Merge with fragenpool.json to include empty categories
    all_categories = set(db_counts.keys())
    try:
        with open(QUESTIONPOOL_FILE, 'r', encoding='utf-8') as f:
            pool = json.load(f)
        all_categories.update(pool.keys())
    except Exception:
        pass
    vendors = {}
    for cat in sorted(all_categories):
        count = db_counts.get(cat, 0)
        parts = [p.strip() for p in cat.split('>')]
        if len(parts) >= 3:
            vendor, cert, topic = parts[0], parts[1], ' > '.join(parts[2:])
        elif len(parts) == 2:
            vendor, cert, topic = parts[0], parts[1], 'Allgemein'
        else:
            continue  # Skip uncategorized entries
        if vendor not in vendors:
            vendors[vendor] = {'name': vendor, 'certs': {}, 'total': 0}
        if cert not in vendors[vendor]['certs']:
            vendors[vendor]['certs'][cert] = {'name': cert, 'topics': [], 'total': 0}
        vendors[vendor]['certs'][cert]['topics'].append({'name': topic, 'full_category': cat, 'count': count})
        vendors[vendor]['certs'][cert]['total'] += count
        vendors[vendor]['total'] += count
    # Convert to list
    result = []
    for v in vendors.values():
        certs = []
        for c in v['certs'].values():
            certs.append({'name': c['name'], 'topics': c['topics'], 'total': c['total']})
        result.append({'name': v['name'], 'certs': certs, 'total': v['total']})
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health():
    db = get_db()
    q_count = db.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
    u_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    return jsonify({'status': 'ok', 'questions': q_count, 'users': u_count, 'version': 'apk-test'})

@app.route('/api/progress', methods=['GET', 'POST'])
def progress():
    db = get_db()
    if request.method == 'POST':
        data = request.json or {}
        user_id = data.get('user_id')
        question_id = data.get('question_id')
        answered = 1
        correct = 1 if data.get('correct') else 0

        if not user_id or not question_id:
            return jsonify({'success': False, 'message': 'user_id und question_id erforderlich.'}), 400

        db.execute('INSERT INTO user_progress (user_id, question_id, answered, correct, created_at) VALUES (?, ?, ?, ?, ?)',
                   (user_id, question_id, answered, correct, datetime.utcnow().isoformat()))
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        user_cols = get_user_columns(db)
        sets = []
        params = []
        if 'last_ip' in user_cols:
            sets.append('last_ip = ?')
            params.append(ip)
        if 'last_user_agent' in user_cols:
            sets.append('last_user_agent = ?')
            params.append(user_agent)
        if 'last_seen_at' in user_cols:
            sets.append('last_seen_at = ?')
            params.append(datetime.utcnow().isoformat())
        if sets:
            params.append(user_id)
            db.execute(f'UPDATE users SET {", ".join(sets)} WHERE id = ?', tuple(params))
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
        return jsonify({'success': False, 'message': 'Ungültige Prüfungsdaten.'}), 400

    percentage = round((correct / total_questions) * 100, 2)
    db = get_db()
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    db.execute(
        '''
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
        )
        '''
    )
    db.execute(
        'INSERT INTO quiz_attempts (user_id, mode, total_questions, correct, wrong, percentage, created_at, ip, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (user_id, mode, total_questions, correct, wrong, percentage, datetime.utcnow().isoformat(), ip, user_agent)
    )
    db.commit()
    return jsonify({'success': True})

@app.route('/api/ai-generate', methods=['POST'])
def ai_generate():
    data = request.get_json() or {}
    api_key = data.get('apiKey')
    category = data.get('category')

    if not api_key or not category:
        return jsonify({'error': 'apiKey und category erforderlich'}), 400

    db = get_db()
    rows = db.execute('SELECT question FROM questions WHERE category = ? LIMIT 3', (category,)).fetchall()
    sample_questions = [row['question'] for row in rows]

    prompt = f"Du bist ein Linux Quiz-Experte. Analysiere diese bestehenden Fragen in der Kategorie '{category}':\n\n"
    prompt += '\n'.join(f'- {q}' for q in sample_questions)
    prompt += "\n\nGeneriere 3 NEUE Fragen im EXAKTEN JSON-Format (jede Zeile separat):\n"
    prompt += json.dumps({
        'category': category,
        'type': 'multiple',
        'question': 'Neue Frage?',
        'options': [
            {'text': 'Option1', 'correct': True},
            {'text': 'Option2', 'correct': False},
            {'text': 'Option3', 'correct': False}
        ]
    }, ensure_ascii=False)
    prompt += "\n"

    request_body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}]
    }).encode('utf-8')

    try:
        from urllib.request import Request, urlopen
        req = Request(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}',
            data=request_body,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urlopen(req, timeout=30) as resp:
            response_json = json.loads(resp.read().decode('utf-8'))

        if 'error' in response_json:
            return jsonify({'error': response_json['error'].get('message', 'Unbekannter Fehler')}), 400

        generatedText = ''
        if response_json.get('candidates'):
            candidate = response_json['candidates'][0]
            if candidate.get('content') and candidate['content'][0].get('parts'):
                generatedText = candidate['content'][0]['parts'][0].get('text', '')

        return jsonify({'response': generatedText})
    except Exception as e:
        return jsonify({'error': 'KI-Fehler: ' + str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    requesting_user = request.headers.get('X-Admin-User', '')
    if requesting_user.lower() != 'admin':
        return jsonify({'success': False, 'message': 'Kein Zugriff.'}), 403

    db = get_db()
    user_cols = get_user_columns(db)
    select_cols = ['id', 'username', 'created_at', 'password_hash']
    if 'last_ip' in user_cols:
        select_cols.append('last_ip')
    if 'last_user_agent' in user_cols:
        select_cols.append('last_user_agent')
    if 'last_seen_at' in user_cols:
        select_cols.append('last_seen_at')
    users = db.execute(f"SELECT {', '.join(select_cols)} FROM users").fetchall()
    result = []
    db.execute(
        '''
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
        )
        '''
    )
    for u in users:
        progress = db.execute(
            'SELECT COALESCE(SUM(correct),0) as correct, COALESCE(SUM(1-correct),0) as wrong, COUNT(*) as total FROM user_progress WHERE user_id = ?',
            (u['id'],)
        ).fetchone()
        exams_taken = db.execute('SELECT COUNT(*) as cnt FROM quiz_attempts WHERE user_id = ?', (u['id'],)).fetchone()['cnt']
        attempt_meta = db.execute(
            'SELECT GROUP_CONCAT(DISTINCT ip) as ips, GROUP_CONCAT(DISTINCT user_agent) as uas FROM quiz_attempts WHERE user_id = ?',
            (u['id'],)
        ).fetchone()

        # Beste/schlechteste Kategorie nach Trefferquote
        cat_rows = db.execute(
            '''
            SELECT q.category as category,
                   COUNT(*) as total,
                   SUM(CASE WHEN up.correct = 1 THEN 1 ELSE 0 END) as correct
            FROM user_progress up
            JOIN questions q ON q.id = up.question_id
            WHERE up.user_id = ?
            GROUP BY q.category
            ''',
            (u['id'],)
        ).fetchall()

        best_category = None
        worst_category = None
        if cat_rows:
            ratios = []
            for r in cat_rows:
                total = r['total'] or 0
                corr = r['correct'] or 0
                ratio = (corr / total) if total > 0 else 0.0
                ratios.append((r['category'], ratio, corr, total))
            best = max(ratios, key=lambda x: x[1])
            worst = min(ratios, key=lambda x: x[1])
            best_category = f"{best[0]} ({round(best[1]*100)}%, {best[2]}/{best[3]})"
            worst_category = f"{worst[0]} ({round(worst[1]*100)}%, {worst[2]}/{worst[3]})"

        result.append({
            'id': u['id'],
            'username': u['username'],
            'created_at': u['created_at'],
            'password_hash': u['password_hash'] if 'password_hash' in u.keys() else None,
            'last_ip': u['last_ip'] if 'last_ip' in u.keys() else None,
            'last_user_agent': u['last_user_agent'] if 'last_user_agent' in u.keys() else None,
            'last_seen_at': u['last_seen_at'] if 'last_seen_at' in u.keys() else None,
            'known_ips': attempt_meta['ips'] if attempt_meta and attempt_meta['ips'] else None,
            'known_devices': attempt_meta['uas'] if attempt_meta and attempt_meta['uas'] else None,
            'correct': progress['correct'] or 0,
            'wrong': progress['wrong'] or 0,
            'total_answers': progress['total'] or 0,
            'exams_taken': exams_taken or 0,
            'best_category': best_category,
            'worst_category': worst_category
        })

    return jsonify({'success': True, 'users': result})

@app.route('/api/admin/set-password', methods=['POST'])
def admin_set_password():
    requesting_user = request.headers.get('X-Admin-User', '')
    if requesting_user.lower() != 'admin':
        return jsonify({'success': False, 'message': 'Kein Zugriff.'}), 403

    data = request.json or {}
    user_id = data.get('user_id')
    new_password = (data.get('new_password') or '').strip()
    if not user_id or len(new_password) < 4:
        return jsonify({'success': False, 'message': 'Ungültige Daten. Passwort min. 4 Zeichen.'}), 400

    db = get_db()
    exists = db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
    if not exists:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden.'}), 404

    new_hash = generate_password_hash(new_password)
    db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
    db.commit()
    return jsonify({'success': True, 'message': 'Passwort geändert.'})

if __name__ == '__main__':

    print(f'''\n╔════════════════════════════════════════════════════╗\n║          🎓 Lernapp Server mit Datenbank           ║\n╚════════════════════════════════════════════════════╝\n\n✅ Server läuft!\n\n🌐 Öffentliche Adresse: {CANONICAL_URL}\n🌐 Lokale Adresse:      http://localhost:5000\n\n📱 Zugriff über Cloudflare Tunnel aktiv.\n\nDatenbank: lernapp.db (SQLite)\n- Benutzer: gespeichert\n- Fragen: aus fragenpool.json geladen\n- Fortschritt: wird gespeichert\n\n🛑 Server beenden: Drücke Ctrl+C\n''')
    with app.app_context():
        setup_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
