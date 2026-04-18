@echo off
REM ════════════════════════════════════════════════════════════════════════════
REM   🏠 SMART HOME PORTAL - Master Starter (Alle Dienste)
REM ════════════════════════════════════════════════════════════════════════════
REM
REM   Startet:
REM     1. Mock Home Assistant (Port 8123) - 8 Demo Geräte
REM     2. Lernapp Server (Port 5000) - Portal & API
REM   
REM   Zugriff:
REM     - Portal: http://localhost:5000/smarthome-portal
REM     - Login: admin / admin123
REM ════════════════════════════════════════════════════════════════════════════

chcp 65001 >nul
setlocal enabledelayedexpansion
cls

cd /d "%~dp0"

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║        🏠 SMART HOME PORTAL - Master Starter v1.0                         ║
echo ║                                                                           ║
echo ║  Startet automatisch:                                                     ║
echo ║    1. Mock Home Assistant   (Port 8123) - 8 Demo Geräte                   ║
echo ║    2. Lernapp Server        (Port 5000) - Portal & API                    ║
echo ║                                                                           ║
echo ║  📍 Zugriff nach Start:                                                   ║
echo ║    🌐 Portal:  http://localhost:5000/smarthome-portal                     ║
echo ║    👤 Login:   admin / admin123                                           ║
echo ║                                                                           ║
echo ║  💡 Demo Geräte:                                                          ║
echo ║    • 2x Lichter (Wohnzimmer, Schlafzimmer)                                ║
echo ║    • 2x Schalter (Küche, Flur)                                            ║
echo ║    • 1x Heizung (Temperatur)                                              ║
echo ║    • 1x Rolladen                                                          ║
echo ║    • 1x Haustür (Schloss)                                                 ║
echo ║    • 1x Ventilator                                                        ║
echo ║    + Alle Netzwerk-Geräte (automatisch erkannt)                           ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM STEP 1: Beende alte Prozesse
REM ════════════════════════════════════════════════════════════════════════════

echo [1/4] 🛑 Beende alte Prozesse...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 >nul
echo     ✓ Alte Python Prozesse beendet
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM STEP 2: Setze Umgebungsvariablen für Home Assistant Integration
REM ════════════════════════════════════════════════════════════════════════════

echo [2/4] 🔐 Setze Umgebungsvariablen...
set HOMEASSISTANT_URL=http://localhost:8123
set HOMEASSISTANT_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJNb2NrIEhBIiwiaWF0IjoxNzQ1MDAwMDAwfQ.mock_token_for_testing
echo     ✓ HOMEASSISTANT_URL=%HOMEASSISTANT_URL%
echo     ✓ HOMEASSISTANT_TOKEN=%HOMEASSISTANT_TOKEN:~0,30%...
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM STEP 3: Starte Mock Home Assistant (Port 8123)
REM ════════════════════════════════════════════════════════════════════════════

echo [3/4] 🏠 Starte Mock Home Assistant (Port 8123)...
if not exist "mock_homeassistant.py" (
    echo     ❌ Fehler: mock_homeassistant.py nicht gefunden!
    pause
    exit /b 1
)

start "Mock Home Assistant" cmd /k py mock_homeassistant.py
timeout /t 3 >nul
echo     ✓ Mock Home Assistant gestartet
echo     ✓ Adresse: http://localhost:8123
echo     ✓ Demo Entities verfügbar
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM STEP 4: Starte Lernapp Server (Port 5000)
REM ════════════════════════════════════════════════════════════════════════════

echo [4/4] 🚀 Starte Lernapp Server (Port 5000)...
if not exist "server_v2.py" (
    echo     ❌ Fehler: server_v2.py nicht gefunden!
    pause
    exit /b 1
)

start "Lernapp Server" cmd /k py server_v2.py
timeout /t 3 >nul
echo     ✓ Lernapp Server gestartet
echo     ✓ Adresse: http://localhost:5000
echo     ✓ Mit Home Assistant Integration
echo.

REM ════════════════════════════════════════════════════════════════════════════
REM SUCCESS
REM ════════════════════════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║        ✅ ALLE DIENSTE GESTARTET!                                         ║
echo ║                                                                           ║
echo ║  🌐 Portal öffnen:                                                        ║
echo ║     http://localhost:5000/smarthome-portal                                ║
echo ║                                                                           ║
echo ║  👤 Login-Daten:                                                          ║
echo ║     Benutzer: admin                                                       ║
echo ║     Passwort: admin123                                                    ║
echo ║                                                                           ║
echo ║  🔌 Services:                                                             ║
echo ║     Home Assistant API:  http://localhost:8123/api/states                ║
echo ║     Lernapp Portal:      http://localhost:5000/portal                     ║
echo ║     Smart Home Portal:   http://localhost:5000/smarthome-portal           ║
echo ║                                                                           ║
echo ║  💡 Demo Geräte:                                                          ║
echo ║     light.wohnzimmer - Wohnzimmer Licht (an)                              ║
echo ║     light.schlafzimmer - Schlafzimmer Licht (aus)                         ║
echo ║     switch.kuche - Küche Schalter (an)                                    ║
echo ║     switch.flur - Flur Schalter (aus)                                     ║
echo ║     climate.heizung - Heizung (21.5°C)                                    ║
echo ║     cover.rolladen_wohnzimmer - Rolladen (offen)                          ║
echo ║     lock.haustuer - Haustür (gesperrt)                                    ║
echo ║     fan.ventilator - Ventilator (aus)                                     ║
echo ║                                                                           ║
echo ║  ⏹️  Zum Beenden: Schließe beide Console-Fenster                           ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo Fenster können minimiert werden - Dienste laufen im Hintergrund!
echo.
pause
