@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ═════════════════════════════════════════════════════════════════════════════
REM  RenLern Server - Alle Dienste Starter
REM  ═════════════════════════════════════════════════════════════════════════════
REM  Startet:
REM    1. Flask Server (Portal + Home Cloud + Lernapp)
REM    2. SSH Zugang zur Debian VM
REM    3. Cloudflared Tunnel
REM ═════════════════════════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║     🚀 RenLern Server - Alle Dienste werden gestartet     ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Pfade
set SERVER_DIR=C:\Users\Administrator\Desktop\Repo clone\lernapp-apk
set SETUP_SCRIPT=%SERVER_DIR%\setup_services.ps1
set START_SERVER=%SERVER_DIR%\start_server.bat

REM ─────────────────────────────────────────────────────────────────────────────
REM 1. Prüfe ob die Skripte existieren
REM ─────────────────────────────────────────────────────────────────────────────

echo [1/3] Überprüfe Dateien...
if not exist "%SERVER_DIR%" (
    echo ❌ FEHLER: Server-Verzeichnis nicht gefunden: %SERVER_DIR%
    pause
    exit /b 1
)

if not exist "%SETUP_SCRIPT%" (
    echo ❌ FEHLER: setup_services.ps1 nicht gefunden
    echo    Speicherort: %SETUP_SCRIPT%
    pause
    exit /b 1
)

if not exist "%START_SERVER%" (
    echo ❌ FEHLER: start_server.bat nicht gefunden
    echo    Speicherort: %START_SERVER%
    pause
    exit /b 1
)

echo ✅ Alle erforderlichen Dateien gefunden
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 2. Führe PowerShell Setup Skript aus (mit Admin-Rechten)
REM ─────────────────────────────────────────────────────────────────────────────

echo [2/3] Starte Dienste-Setup (PowerShell)...
echo.

REM Prüfe ob PowerShell läuft
where /q powershell
if errorlevel 1 (
    echo ❌ PowerShell nicht gefunden!
    pause
    exit /b 1
)

REM Führe das Setup-Skript aus
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '%SETUP_SCRIPT%'"

if errorlevel 1 (
    echo ⚠️  Setup-Skript hatte Fehler, aber fahre fort...
)

echo.
echo ✅ Setup-Skript abgeschlossen
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 3. Starte Flask Server
REM ─────────────────────────────────────────────────────────────────────────────

echo [3/3] Starte Flask Server...
echo.

cd /d "%SERVER_DIR%"
call "%START_SERVER%"

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║              ✅ ALLE DIENSTE GESTARTET!                   ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo 🌐 Öffne deinen Browser:
echo    http://localhost:5000
echo    oder
echo    https://renlern.org (über Cloudflare Tunnel)
echo.
echo 📍 Services:
echo    Portal:   http://localhost:5000
echo    Home:     http://localhost:5000/home
echo    Lernapp:  http://localhost:5000/lernapp
echo.
echo 🐧 Debian VM (falls eingerichtet):
echo    SSH:      ssh root@<vm-ip>
echo    ttyd:     http://<vm-ip>:7681
echo.
echo 🛑 Server beenden: Schließe dieses Fenster oder drücke Ctrl+C
echo.
pause
