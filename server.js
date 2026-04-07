const express = require('express');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const app = express();
const PORT = 3000;

const FRAGENPOOL_PATH = path.join(__dirname, 'fragenpool.json');
const USERS_PATH = path.join(__dirname, 'users.json');
const PROGRESS_PATH = path.join(__dirname, 'user_progress.json');

app.use(express.json());
app.use(express.static(__dirname));

function ensureFile(filePath, defaultData) {
    if (!fs.existsSync(filePath)) {
        fs.writeFileSync(filePath, JSON.stringify(defaultData, null, 2), 'utf8');
    }
}

function readJson(filePath, fallback) {
    try {
        const raw = fs.readFileSync(filePath, 'utf8');
        return JSON.parse(raw);
    } catch (error) {
        return fallback;
    }
}

function writeJson(filePath, data) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
}

function hashPassword(password, salt) {
    return crypto.pbkdf2Sync(password, salt, 100000, 64, 'sha512').toString('hex');
}

ensureFile(USERS_PATH, []);
ensureFile(PROGRESS_PATH, []);

// Haupt-Route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'lernapp.html'));
});

// Speichere die aktualisierten Fragen
app.post('/api/save-fragenpool', (req, res) => {
    try {
        const fragenpool = req.body;
        writeJson(FRAGENPOOL_PATH, fragenpool);
        
        res.json({ success: true, message: 'Fragenpool erfolgreich gespeichert!' });
    } catch (error) {
        console.error('Fehler beim Speichern:', error);
        res.status(500).json({ success: false, message: 'Fehler beim Speichern: ' + error.message });
    }
});

// Hole den aktuellen Fragenpool
app.get('/api/load-fragenpool', (req, res) => {
    try {
        const data = readJson(FRAGENPOOL_PATH, null);
        if (!data || typeof data !== 'object') {
            return res.status(404).json({ success: false, message: 'Fragenpool nicht gefunden' });
        }
        res.json(data);
    } catch (error) {
        console.error('Fehler beim Laden:', error);
        res.status(500).json({ success: false, message: 'Fragenpool nicht gefunden' });
    }
});

app.post('/api/register', (req, res) => {
    try {
        const username = (req.body?.username || '').trim();
        const password = (req.body?.password || '').trim();

        if (username.length < 3 || password.length < 6) {
            return res.status(400).json({ success: false, message: 'Benutzername mind. 3 Zeichen, Passwort mind. 6 Zeichen.' });
        }

        const users = readJson(USERS_PATH, []);
        const existing = users.find(u => u.username.toLowerCase() === username.toLowerCase());
        if (existing) {
            return res.status(400).json({ success: false, message: 'Benutzername existiert bereits.' });
        }

        const salt = crypto.randomBytes(16).toString('hex');
        const passwordHash = hashPassword(password, salt);
        const newUser = {
            id: Date.now(),
            username,
            salt,
            passwordHash,
            createdAt: new Date().toISOString()
        };

        users.push(newUser);
        writeJson(USERS_PATH, users);

        res.json({ success: true, user: { id: newUser.id, username: newUser.username } });
    } catch (error) {
        console.error('Fehler bei Registrierung:', error);
        res.status(500).json({ success: false, message: 'Serverfehler bei Registrierung.' });
    }
});

app.post('/api/login', (req, res) => {
    try {
        const username = (req.body?.username || '').trim();
        const password = (req.body?.password || '').trim();
        const users = readJson(USERS_PATH, []);
        const user = users.find(u => u.username.toLowerCase() === username.toLowerCase());

        if (!user) {
            return res.status(401).json({ success: false, message: 'Ungueltiger Benutzername oder Passwort.' });
        }

        const candidateHash = hashPassword(password, user.salt);
        if (candidateHash !== user.passwordHash) {
            return res.status(401).json({ success: false, message: 'Ungueltiger Benutzername oder Passwort.' });
        }

        res.json({ success: true, user: { id: user.id, username: user.username } });
    } catch (error) {
        console.error('Fehler bei Login:', error);
        res.status(500).json({ success: false, message: 'Serverfehler bei Anmeldung.' });
    }
});

app.post('/api/progress', (req, res) => {
    try {
        const userId = req.body?.user_id;
        const questionId = req.body?.question_id;
        const correct = !!req.body?.correct;

        if (!userId || !questionId) {
            return res.status(400).json({ success: false, message: 'user_id und question_id erforderlich.' });
        }

        const progressRows = readJson(PROGRESS_PATH, []);
        progressRows.push({
            id: Date.now() + Math.floor(Math.random() * 1000),
            user_id: userId,
            question_id: questionId,
            answered: 1,
            correct: correct ? 1 : 0,
            created_at: new Date().toISOString()
        });
        writeJson(PROGRESS_PATH, progressRows);
        res.json({ success: true });
    } catch (error) {
        console.error('Fehler bei Progress-Speicherung:', error);
        res.status(500).json({ success: false, message: 'Progress konnte nicht gespeichert werden.' });
    }
});

app.get('/api/progress', (req, res) => {
    try {
        const userId = Number(req.query.user_id);
        if (!userId) {
            return res.status(400).json({ success: false, message: 'user_id erforderlich.' });
        }
        const progressRows = readJson(PROGRESS_PATH, []);
        const filtered = progressRows.filter(row => Number(row.user_id) === userId);
        res.json(filtered);
    } catch (error) {
        console.error('Fehler beim Laden von Progress:', error);
        res.status(500).json({ success: false, message: 'Progress konnte nicht geladen werden.' });
    }
});

// Google Gemini API - KI-Fragen generieren basierend auf Datenbank
app.post('/api/ai-generate', async (req, res) => {
    try {
        const { apiKey, category } = req.body;
        
        // Lade aktuelle Fragenpool
        const fragenpool = readJson(FRAGENPOOL_PATH, {});
        
        // Analysiere bestehende Fragen in der Kategorie
        const existingQuestions = fragenpool[category] || [];
        const sampleQuestions = existingQuestions.slice(0, 3);
        
        // Erstelle Prompt mit Datenbank-Kontext
        const prompt = `Du bist ein Linux Quiz-Experte. Analysiere diese bestehenden Fragen in der Kategorie "${category}":

${sampleQuestions.map(q => `- ${q.question}`).join('\n')}

Generiere 3 NEUE Fragen im EXAKTEN JSON-Format (jede Zeile separat):
{"category": "${category}", "type": "multiple", "question": "Neue Frage?", "options": [{"text": "Option1", "correct": true}, {"text": "Option2", "correct": false}, {"text": "Option3", "correct": false}]}

Wichtig: Gleiches Schwierigkeitsniveau und ähnliches Format wie die bestehenden Fragen!`;

        const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=' + apiKey, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contents: [{
                    parts: [{ text: prompt }]
                }]
            })
        });

        const data = await response.json();
        
        if (data.error) {
            return res.status(400).json({ error: 'API-Fehler: ' + data.error.message });
        }

        const generatedText = data.candidates[0].content.parts[0].text;
        res.json({ response: generatedText });
        
    } catch (error) {
        console.error('KI-Fehler:', error);
        res.status(500).json({ error: 'KI-Fehler: ' + error.message });
    }
});

app.use('/api', (req, res) => {
    res.status(404).json({ success: false, message: 'API-Endpunkt nicht gefunden.' });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`\n🚀 Lernapp Server läuft auf http://localhost:${PORT}`);
    console.log('✅ Die Fragen werden automatisch in fragenpool.json gespeichert!');
    console.log('📱 Mit Tailscale auf allen Geräten erreichbar!\n');
});
