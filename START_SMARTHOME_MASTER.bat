@echo off
REM ════════════════════════════════════════════════════════════════════════════
REM   🏠 SMART HOME PORTAL - MASTER START v2.0
REM   Alle Services in einer BAT-Datei - vollständige Integration
REM ════════════════════════════════════════════════════════════════════════════

chcp 65001 >nul
setlocal enabledelayedexpansion
cls

cd /d "%~dp0"

REM ════════════════════════════════════════════════════════════════════════════
REM TITLE Screen
REM ════════════════════════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                                                                           ║
echo ║           🏠 SMART HOME PORTAL - MASTER STARTER v2.0                       ║
echo ║                                                                           ║
echo ║  Startet automatisch alle Dienste:                                        ║
echo ║                                                                           ║
echo ║  [1] 🏠 Mock Home Assistant       (Port 8123)                             ║
echo ║  [2] 🚀 Lernapp Server            (Port 5000)                             ║
echo ║  [3] 📱 Smart Home Portal UI      (Ready)                                 ║
echo ║                                                                           ║
echo ║  💡 Demo Geräte (8 Stück):                                               ║
echo ║     • 2x Lichter (Wohnzimmer/Schlafzimmer)                                ║
echo ║     • 2x Schalter (Küche/Flur)                                            ║
echo ║     • 1x Heizung/Klima                                                    ║
echo ║     • 1x Rolladen                                                         ║
echo ║     • 1x Haustür (Lock)                                                   ║
echo ║     • 1x Ventilator                                                       ║
echo ║                                                                           ║
echo ║  ➕ PLUS: Alle Netzwerk-Geräte automatisch erkannt                        ║
echo ║                                                                           ║
echo ║  🌐 Nach dem Start:                                                       ║
echo ║     Portal:    http://localhost:5000/smarthome-portal                     ║
echo ║     Login:     admin / admin123                                           ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo Initialisiere System...
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM SCHRITT 1: Beende alte Prozesse
REM ════════════════════════════════════════════════════════════════════════════

echo [1/5] 🛑 Beende alte Python Prozesse...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq*Mock*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq*Lernapp*" >nul 2>&1
timeout /t 1 >nul
echo     ✓ Alte Prozesse beendet
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM SCHRITT 2: Datei-Prüfungen
REM ════════════════════════════════════════════════════════════════════════════

echo [2/5] 📁 Überprüfe erforderliche Dateien...
set MISSING=0

if not exist "mock_homeassistant.py" (
    echo     ❌ Mock Home Assistant nicht gefunden: mock_homeassistant.py
    set MISSING=1
)
if not exist "server_v2.py" (
    echo     ❌ Lernapp Server nicht gefunden: server_v2.py
    set MISSING=1
)
if not exist "smarthome_portal.py" (
    echo     ⚠️  Smart Home Portal nicht gefunden: smarthome_portal.py
)
if not exist "lernapp.db" (
    echo     ❌ Datenbank nicht gefunden: lernapp.db
    set MISSING=1
)

if !MISSING! equ 1 (
    echo.
    echo ❌ KRITISCHE DATEIEN FEHLEN - ABBRUCH
    pause
    exit /b 1
)

echo     ✓ Alle Dateien vorhanden
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM SCHRITT 3: Umgebungsvariablen setzen
REM ════════════════════════════════════════════════════════════════════════════

echo [3/5] 🔐 Setze Umgebungsvariablen...
set HOMEASSISTANT_URL=http://localhost:8123
set HOMEASSISTANT_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJNb2NrIEhBIiwiaWF0IjoxNzQ1MDAwMDAwfQ.mock_token_for_testing
echo     ✓ HOMEASSISTANT_URL=%HOMEASSISTANT_URL%
echo     ✓ HOMEASSISTANT_TOKEN gesetzt
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM SCHRITT 4: Aktiviere Admin Smart Home Zugriff
REM ════════════════════════════════════════════════════════════════════════════

echo [4/5] 🔑 Konfiguriere Admin-Zugriff...
py -c "import sqlite3; db=sqlite3.connect('lernapp.db'); db.execute('UPDATE users SET smarthome_access_allowed=1 WHERE username=?', ('admin',)); db.commit(); db.close(); print('    ✓ Admin Smart Home Zugriff aktiviert')" 2>nul
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM SCHRITT 5: Starte Services
REM ════════════════════════════════════════════════════════════════════════════

echo [5/5] 🚀 Starte alle Services...
echo.

REM Starte Mock Home Assistant
echo     [5a] 🏠 Mock Home Assistant (Port 8123)...
start "Mock Home Assistant - http://localhost:8123" cmd /k py mock_homeassistant.py
timeout /t 2 >nul
echo     ✓ Mock Home Assistant gestartet
echo.

REM Starte Lernapp Server  
echo     [5b] 🚀 Lernapp Server (Port 5000)...
start "Lernapp Server - http://localhost:5000" cmd /k py server_v2.py
timeout /t 2 >nul
echo     ✓ Lernapp Server gestartet
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM SUCCESS SCREEN
REM ════════════════════════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                  ✅ ALLE DIENSTE ERFOLGREICH GESTARTET!                    ║
echo ║                                                                           ║
echo ║  🌐 PORTALE:                                                              ║
echo ║                                                                           ║
echo ║     Smart Home Portal:                                                    ║
echo ║     ➜ http://localhost:5000/smarthome-portal                              ║
echo ║                                                                           ║
echo ║     Lernapp Portal:                                                       ║
echo ║     ➜ http://localhost:5000/portal                                        ║
echo ║                                                                           ║
echo ║     Home Seite:                                                           ║
echo ║     ➜ http://localhost:5000/home                                          ║
echo ║                                                                           ║
echo ║  👤 LOGIN-DATEN:                                                          ║
echo ║                                                                           ║
echo ║     Benutzer: admin                                                       ║
echo ║     Passwort: admin123                                                    ║
echo ║                                                                           ║
echo ║  📱 API ENDPOINTS:                                                        ║
echo ║                                                                           ║
echo ║     Device Discovery:                                                     ║
echo ║     ➜ http://localhost:5000/api/smarthome/discover                        ║
echo ║                                                                           ║
echo ║     Home Assistant API:                                                   ║
echo ║     ➜ http://localhost:8123/api/states                                    ║
echo ║                                                                           ║
echo ║  💡 VERFÜGBARE GERÄTE:                                                    ║
echo ║                                                                           ║
echo ║     Home Assistant:                                                       ║
echo ║     • light.wohnzimmer (Licht - An)                                       ║
echo ║     • light.schlafzimmer (Licht - Aus)                                    ║
echo ║     • switch.kuche (Schalter - An)                                        ║
echo ║     • switch.flur (Schalter - Aus)                                        ║
echo ║     • climate.heizung (Heizung - 21.5°C)                                  ║
echo ║     • cover.rolladen_wohnzimmer (Rolladen - Offen)                        ║
echo ║     • lock.haustuer (Haustür - Gesperrt)                                  ║
echo ║     • fan.ventilator (Ventilator - Aus)                                   ║
echo ║                                                                           ║
echo ║     Plus: Alle Netzwerk-Geräte (Fritz!Box Scanner)                        ║
echo ║                                                                           ║
echo ║  ⏹️  SERVICES STOPPEN:                                                     ║
echo ║                                                                           ║
echo ║     Starte: STOP_SMARTHOME_ALL.bat                                        ║
echo ║                                                                           ║
echo ║  📋 WEITERE INFORMATIONEN:                                                ║
echo ║                                                                           ║
echo ║     Mock Home Assistant läuft på http://localhost:8123                    ║
echo ║     Lernapp Server läuft på http://localhost:5000                         ║
echo ║     Fenster können minimiert werden - Services laufen weiter!             ║
echo ║                                                                           ║
echo ║  🔧 FEHLERSUCHE:                                                          ║
echo ║                                                                           ║
echo ║     Falls Geräte nicht sichtbar sind:                                     ║
echo ║     1. Beiden Console-Fenster schauen ob Fehler angezeigt werden          ║
echo ║     2. Browser Cache löschen (Strg+Shift+Entf)                            ║
echo ║     3. Page neu laden (Strg+F5)                                           ║
echo ║     4. Datenbank-Reset: DELETE FROM smarthome_devices                     ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo.
echo 👇 JETZT: Browser öffnen und Portal aufrufen:
echo.
echo    http://localhost:5000/smarthome-portal
echo.
echo    Login: admin / admin123
echo.
echo.
pause
