#!/bin/bash
# ============================================================
# setup_env.sh
# Richtet die Build-Umgebung für die LernApp APK ein.
# Nur einmal ausführen!
# ============================================================

set -e
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   🔧 LernApp APK - Build-Umgebung Setup      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Betriebssystem erkennen ──────────────────────────────────
OS="$(uname -s)"
case "$OS" in
    Linux*)  PLATFORM="linux";;
    Darwin*) PLATFORM="mac";;
    *)       PLATFORM="unknown";;
esac

echo "📌 Plattform erkannt: $PLATFORM"
echo ""

# ── Python prüfen ────────────────────────────────────────────
echo "🐍 Prüfe Python..."
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 nicht gefunden!"
    echo "   → Bitte installieren: https://www.python.org"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
echo "   ✅ $PYTHON_VERSION"

# ── pip Pakete installieren ──────────────────────────────────
echo ""
echo "📦 Installiere Python-Abhängigkeiten..."
pip3 install flask werkzeug kivy buildozer --quiet
echo "   ✅ Flask, Kivy, Buildozer installiert"

# ── Java prüfen (für Buildozer) ──────────────────────────────
echo ""
echo "☕ Prüfe Java (für APK-Build)..."
if command -v java &>/dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -1)
    echo "   ✅ $JAVA_VERSION"
else
    echo "   ⚠️  Java nicht gefunden - wird für APK-Build benötigt"
    if [ "$PLATFORM" = "linux" ]; then
        echo "   → Installieren mit: sudo apt install default-jdk"
    elif [ "$PLATFORM" = "mac" ]; then
        echo "   → Installieren mit: brew install openjdk"
    fi
fi

# ── Android SDK/NDK (Buildozer lädt automatisch) ─────────────
echo ""
echo "📱 Android SDK: Buildozer lädt automatisch beim ersten Build"

# ── Projektstruktur prüfen ───────────────────────────────────
echo ""
echo "📁 Prüfe Projektstruktur..."

if [ ! -f "app/main.py" ]; then
    echo "❌ app/main.py fehlt!"
    exit 1
fi
echo "   ✅ app/main.py"

if [ ! -f "app/flask_server.py" ]; then
    echo "❌ app/flask_server.py fehlt!"
    exit 1
fi
echo "   ✅ app/flask_server.py"

if [ ! -f "buildozer.spec" ]; then
    echo "❌ buildozer.spec fehlt!"
    exit 1
fi
echo "   ✅ buildozer.spec"

# ── fragenpool.json kopieren ─────────────────────────────────
echo ""
echo "📚 Fragenpool prüfen..."
if [ -f "fragenpool__2_.json" ]; then
    cp fragenpool__2_.json app/fragenpool.json
    echo "   ✅ fragenpool__2_.json → app/fragenpool.json kopiert"
elif [ -f "fragenpool.json" ]; then
    cp fragenpool.json app/fragenpool.json
    echo "   ✅ fragenpool.json → app/fragenpool.json kopiert"
else
    echo "   ⚠️  Keine fragenpool.json gefunden - App startet mit leerer DB"
fi

# ── lernapp.html kopieren ────────────────────────────────────
if [ -f "lernapp.html" ]; then
    cp lernapp.html app/lernapp.html
    echo "   ✅ lernapp.html → app/lernapp.html kopiert"
fi

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅ Setup abgeschlossen!                     ║"
echo "╠══════════════════════════════════════════════╣"
echo "║                                              ║"
echo "║  Nächste Schritte:                           ║"
echo "║                                              ║"
echo "║  1. APK bauen:                               ║"
echo "║     bash build.sh debug                      ║"
echo "║                                              ║"
echo "║  2. Lokal testen (ohne APK):                 ║"
echo "║     python3 app/main_desktop.py              ║"
echo "║                                              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
