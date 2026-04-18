@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ═════════════════════════════════════════════════════════════════════════════
REM  RenLern Server - Alle Services Starter v3.0
REM  ═════════════════════════════════════════════════════════════════════════════
REM  Startet:
REM    1. Flask Server (server_v2.py) - Portal, Home Cloud, Lernapp
REM    2. SSH Service (sshd) - Windows SSH Server
REM    3. Cloudflared Tunnel - Sichere Verbindung zu renlern.org
REM ═════════════════════════════════════════════════════════════════════════════

cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                  🚀 RenLern Server - Alle Services                        ║
echo ║                                                                           ║
echo ║  Startet:                                                                 ║
echo ║    • Flask Server (Portal, Home Cloud, Lernapp)                           ║
echo ║    • SSH Service (Fernzugriff)                                            ║
echo ║    • Cloudflared Tunnel (Sichere Verbindung)                              ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM Konfiguration
REM ─────────────────────────────────────────────────────────────────────────────

cd /d "%~dp0"

set SERVER_DIR=C:\Users\Administrator\Desktop\Repo clone\lernapp-apk
set PYTHON_EXE=py
set SERVER_SCRIPT=server_v2.py
set SSH_SERVICE=sshd

echo [*] Initialisiere Services...
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 1. Beende alte Flask Server Prozesse
REM ─────────────────────────────────────────────────────────────────────────────

echo [1/5] 🛑 Beende alte Flask Server Prozesse...
taskkill /FI "WINDOWTITLE eq RenLern Server*" /F >nul 2>&1
taskkill /IM python.exe /FI "MEMUSAGE gt 50000" /F >nul 2>&1
echo     ✓ Alte Prozesse beendet
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 2. Prüfe ob Dateien existieren
REM ─────────────────────────────────────────────────────────────────────────────

echo [2/5] 📁 Überprüfe erforderliche Dateien...
if not exist "%SERVER_DIR%\%SERVER_SCRIPT%" (
    echo.
    echo ❌ FEHLER: %SERVER_SCRIPT% nicht gefunden!
    echo    Pfad: %SERVER_DIR%\%SERVER_SCRIPT%
    echo.
    pause
    exit /b 1
)
echo     ✓ %SERVER_SCRIPT% gefunden
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 3. Starte Flask Server (server_v2.py)
REM ─────────────────────────────────────────────────────────────────────────────

REM Setze Home Assistant Umgebungsvariablen für Smart Home Integration  
echo [3a/5] 🏠 Konfiguriere Home Assistant Integration...
set HOMEASSISTANT_URL=http://localhost:8123
set HOMEASSISTANT_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJNb2NrIEhBIiwiaWF0IjoxNzQ1MDAwMDAwfQ.mock_token_for_testing
echo     ✓ HOMEASSISTANT_URL=%HOMEASSISTANT_URL%
echo     ✓ HOMEASSISTANT_TOKEN gesetzt
echo.

REM Starte Mock Home Assistant (separat)
echo [3b/5] 🏠 Starte Mock Home Assistant Server (Port 8123)...
if exist "%SERVER_DIR%\mock_homeassistant.py" (
    start "Mock Home Assistant" cmd /k %PYTHON_EXE% "%SERVER_DIR%\mock_homeassistant.py"
    timeout /t 3 >nul
    echo     ✓ Mock Home Assistant gestartet
) else (
    echo     ⚠️  mock_homeassistant.py nicht gefunden - übersprungen
)
echo.

echo [3c/5] 🐍 Starte Flask Server (server_v2.py)...
start "RenLern Server" cmd /k %PYTHON_EXE% "%SERVER_DIR%\%SERVER_SCRIPT%"
if errorlevel 1 (
    echo     ❌ Fehler beim Starten des Flask Servers
    echo        Stelle sicher, dass Python installiert ist
    echo        und "py" Befehl verfügbar ist
) else (
    echo     ✓ Flask Server gestartet
    echo        🌐 Smart Home Portal: http://localhost:5000/smarthome-portal
    echo        🏠 Home:     http://localhost:5000/home
    echo        🎓 Lernapp:  http://localhost:5000/lernapp
    echo        📊 Login: admin / admin123
)
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 4. Starte/Prüfe SSH Service
REM ─────────────────────────────────────────────────────────────────────────────

echo [4/5] 🔐 Starte SSH Service (sshd)...
sc query "%SSH_SERVICE%" >nul 2>&1
if errorlevel 1 (
    echo     ⚠️  SSH Service nicht installiert
    echo        Installiere mit: Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
) else (
    net start "%SSH_SERVICE%" >nul 2>&1
    if errorlevel 1 (
        REM Service ist wahrscheinlich bereits laufend
        sc query "%SSH_SERVICE%" | find "RUNNING" >nul 2>&1
        if errorlevel 1 (
            echo     ❌ Fehler beim Starten des SSH Services
        ) else (
            echo     ✓ SSH Service läuft bereits
            echo        SSH Port: 22
            echo        Lokal (nur admin):
            echo        $ ssh -i C:\Users\Administrator\.ssh\id_rsa_renlern Administrator@localhost
        )
    ) else (
        echo     ✓ SSH Service gestartet
        echo        SSH Port: 22
        echo        Lokal (nur admin):
        echo        $ ssh -i C:\Users\Administrator\.ssh\id_rsa_renlern Administrator@localhost
    )
)
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 5. Prüfe Cloudflared Tunnel Service
REM ─────────────────────────────────────────────────────────────────────────────

echo [5/5] ☁️  Prüfe Cloudflared Tunnel Service...
sc query "cloudflared" >nul 2>&1
if errorlevel 1 (
    echo     ⚠️  Cloudflared Service nicht installiert
    echo        Installation möglich mit: C:\path\to\cloudflared-windows-amd64.exe install --config C:\Users\Administrator\.cloudflared\config.yml --logfile C:\Users\Administrator\.cloudflared\cloudflared.log
    
    REM Versuche Cloudflared als Hintergrund-Prozess zu starten
    echo.
    echo     Versuche Cloudflared als Hintergrund-Prozess zu starten...
    if exist "C:\Program Files (x86)\cloudflared\cloudflared.exe" (
        start "Cloudflared Tunnel" "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --config "%USERPROFILE%\.cloudflared\config.yml" run renlern
        echo     ✓ Cloudflared versucht zu starten
    ) else if exist "C:\Program Files\cloudflared\cloudflared.exe" (
        start "Cloudflared Tunnel" "C:\Program Files\cloudflared\cloudflared.exe" tunnel --config "%USERPROFILE%\.cloudflared\config.yml" run renlern
        echo     ✓ Cloudflared versucht zu starten
    ) else (
        echo     ❌ Cloudflared Executable nicht gefunden
        echo        Bitte installiere Cloudflared oder füge es zum PATH hinzu
    )
) else (
    net start "cloudflared" >nul 2>&1
    if errorlevel 1 (
        REM Service ist wahrscheinlich bereits laufend
        sc query "cloudflared" | find "RUNNING" >nul 2>&1
        if errorlevel 1 (
            echo     ❌ Fehler beim Starten des Cloudflared Services
        ) else (
            echo     ✓ Cloudflared Tunnel läuft bereits
            echo        Domain: https://renlern.org
            echo        Secure Tunnel verbunden
        )
    ) else (
        echo     ✓ Cloudflared Tunnel gestartet
        echo        Domain: https://renlern.org
        echo        Secure Tunnel verbunden
    )
)
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM Zusammenfassung
REM ─────────────────────────────────────────────────────────────────────────────

echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                     ✅ Alle Services initialisiert                       ║
echo ║                                                                           ║
echo ║  Zugriff:                                                                 ║
echo ║    🌐 https://renlern.org          (Portal, Login)                       ║
echo ║    ☁️  https://renlern.org/home    (Home Cloud Storage)                  ║
echo ║    📚 https://renlern.org/lernapp  (Lernapp Quiz)                        ║
echo ║    🔐 SSH auf Port 22              (mit SSH Key)                         ║
echo ║                                                                           ║
echo ║  Services:                                                                ║
echo ║    1. Flask Server (server_v2.py)   - Port 5000 (intern)                 ║
echo ║    2. SSH Service (sshd)            - Port 22                            ║
echo ║    3. Cloudflared Tunnel            - Reverse Proxy zu renlern.org       ║
echo ║                                                                           ║
echo ║  Fenster:                                                                 ║
echo ║    • Diesen Command Prompt OFFENLASSEN - zeigt Status                    ║
echo ║    • RenLern Server Fenster - Flask Server Logs                          ║
echo ║    • Cloudflared Fenster (falls nicht als Service) - Tunnel Logs         ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo Drücke eine Taste, um zu beenden (wechsle zu anderen Fenstern um Services zu sehen)...
pause

endlocal
