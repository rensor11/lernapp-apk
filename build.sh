#!/bin/bash
# ============================================================
# build.sh [debug|release]
# Baut die LernApp Android APK mit Buildozer.
# ============================================================

set -e
MODE="${1:-debug}"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   📱 LernApp APK Build - Modus: $MODE        "
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Dateien aktualisieren ────────────────────────────────────
echo "📁 Kopiere Ressourcen..."

if [ -f "fragenpool__2_.json" ]; then
    cp fragenpool__2_.json app/fragenpool.json
    echo "   ✅ fragenpool__2_.json kopiert"
elif [ -f "fragenpool.json" ] && [ "$(realpath fragenpool.json)" != "$(realpath app/fragenpool.json 2>/dev/null)" ]; then
    cp fragenpool.json app/fragenpool.json
    echo "   ✅ fragenpool.json kopiert"
fi

if [ -f "lernapp.html" ]; then
    cp lernapp.html app/lernapp.html
    echo "   ✅ lernapp.html kopiert"
fi

if [ -f "server_neu.py" ]; then
    cp server_neu.py app/server_neu.py
    echo "   ✅ server_neu.py kopiert"
fi

echo ""

# ── Build starten ────────────────────────────────────────────
echo "🔨 Starte Buildozer ($MODE)..."
echo "   ⏳ Beim ersten Mal dauert das 10-20 Minuten"
echo "   (Android SDK/NDK wird heruntergeladen)"
echo ""

if [ "$MODE" = "release" ]; then
    buildozer android release
    echo ""
    echo "✅ Release APK gebaut!"
    echo "📦 APK Pfad: bin/lernapserver-1.0-arm64-v8a-release.apk"
    echo ""
    echo "⚠️  Zum Signieren:"
    echo "   jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \\"
    echo "     -keystore mein-schluessel.keystore bin/*.apk mein-schluessel"
else
    buildozer android debug
    echo ""
    echo "✅ Debug APK gebaut!"
    APK=$(ls bin/*.apk 2>/dev/null | head -1)
    echo "📦 APK: $APK"
    echo ""
    echo "📲 Installieren:"
    echo "   adb install -r $APK"
    echo ""
    echo "📋 Logs anschauen:"
    echo "   adb logcat -s python"
fi

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   🎉 Build fertig!                           ║"
echo "╠══════════════════════════════════════════════╣"
echo "║                                              ║"
echo "║  APK auf Handy installieren:                 ║"
echo "║  1. USB-Debugging aktivieren                 ║"
echo "║  2. Handy per USB anschließen                ║"
echo "║  3. Ausführen: bash build.sh debug           ║"
echo "║     dann: adb install -r bin/*.apk           ║"
echo "║                                              ║"
echo "║  Oder: APK-Datei aus bin/ auf Handy kopieren ║"
echo "║  → Einstellungen → Unbekannte Quellen → ✅   ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
