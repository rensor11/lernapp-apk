@echo off
setlocal enabledelayedexpansion
cls

REM ════════════════════════════════════════════════════════════════════════
REM           🎓 RenLern - Service Manager v2.0
REM ════════════════════════════════════════════════════════════════════════
REM
REM   Verfügbare Befehle:
REM   - keine Argumente oder "menu"  → Interaktives Menü
REM   - start                        → Starten
REM   - stop                         → Stoppen
REM   - restart                      → Neustart
REM   - status                       → Status anzeigen
REM   - autostart_enable              → Autostart aktivieren (Admin erforderlich)
REM   - autostart_disable             → Autostart deaktivieren (Admin erforderlich)
REM ════════════════════════════════════════════════════════════════════════

cd /d "%~dp0"
set PYTHON_EXE=C:\Users\Administrator\AppData\Local\Programs\Python\Launcher\py.exe
set SERVER_SCRIPT=server_v2.py
set SSH_SERVICE=sshd
set CLOUDFLARE_CMD=cloudflared tunnel --config C:\Users\Administrator\.cloudflared\config.yml run renlern

REM Colors für Output (fallback zu reiner Text wenn nicht unterstützt)
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "RESET=[0m"

REM ──────────────────────────────────────────────────────────────────────

if "%1"=="" goto menu
if /i "%1"=="menu" goto menu
if /i "%1"=="start" goto start_service
if /i "%1"=="stop" goto stop_service
if /i "%1"=="restart" goto restart_service
if /i "%1"=="status" goto check_status
if /i "%1"=="autostart_enable" goto enable_autostart
if /i "%1"=="autostart_disable" goto disable_autostart
goto unknown

REM ──────────────────────────────────────────────────────────────────────
:menu
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║       🎓 RenLern - Service Manager                             ║
echo ║                                                                ║
echo ║   Portal (Login):  https://renlern.org/                       ║
echo ║   Home Cloud:      https://renlern.org/home                   ║
echo ║   Lernapp:         https://renlern.org/lernapp                ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo   [1] ▶ Dienste starten
echo   [2] ⏹ Dienste stoppen
echo   [3] 🔄 Dienste neu starten
echo   [4] ℹ Status anzeigen
echo   [5] ⚙ Autostart aktivieren (Admin)
echo   [6] ⚙ Autostart deaktivieren (Admin)
echo   [0] ✕ Beenden
echo.
set /p choice="Auswahl (0-6): "

if "%choice%"=="1" goto start_service
if "%choice%"=="2" goto stop_service
if "%choice%"=="3" goto restart_service
if "%choice%"=="4" goto check_status
if "%choice%"=="5" goto enable_autostart
if "%choice%"=="6" goto disable_autostart
if "%choice%"=="0" exit /b 0
goto menu

REM ──────────────────────────────────────────────────────────────────────
:start_service
echo.
echo [*] Starte RenLern Dienste...
echo.

REM SSH Service
echo [1/3] Prüfe SSH-Dienst...
net start %SSH_SERVICE% >nul 2>&1
if errorlevel 0 (
    echo        ✓ SSH-Dienst läuft
) else (
    echo        ⚠ SSH-Dienst konnte nicht gestartet werden
)

REM Flask Server
echo [2/3] Starte Flask Server...
if not exist "%PYTHON_EXE%" (
    echo        ✗ Python nicht gefunden: %PYTHON_EXE%
    goto menu
)
taskkill /FI "WINDOWTITLE eq RenLern Server" /F >nul 2>&1
timeout /t 1 >nul
start "RenLern Server" /MIN cmd /k "%PYTHON_EXE%" "server_v2.py"
timeout /t 3 >nul
echo        ✓ Flask Server gestartet (Port 5000)

REM Cloudflared Tunnel
echo [3/3] Starte Cloudflare Tunnel...
taskkill /FI "WINDOWTITLE eq Cloudflare Tunnel" /F >nul 2>&1
timeout /t 1 >nul
start "Cloudflare Tunnel" /MIN cmd /k "%CLOUDFLARE_CMD%"
timeout /t 2 >nul
echo        ✓ Cloudflare Tunnel gestartet

echo.
echo [✓] Alle Dienste gestartet!
echo.
pause
goto menu

REM ──────────────────────────────────────────────────────────────────────
:stop_service
echo.
echo [*] Stoppe RenLern Dienste...
echo.

echo [1/2] Stoppe Flask Server...
taskkill /FI "WINDOWTITLE eq RenLern Server" /F >nul 2>&1
echo        ✓ Flask Server gestoppt

echo [2/2] Stoppe Cloudflare Tunnel...
taskkill /FI "WINDOWTITLE eq Cloudflare Tunnel" /F >nul 2>&1
echo        ✓ Cloudflare Tunnel gestoppt

echo.
echo [✓] Alle Dienste gestoppt!
echo.
pause
goto menu

REM ──────────────────────────────────────────────────────────────────────
:restart_service
echo.
echo [*] Starten RenLern Dienste neu...
echo.
call :stop_service_quiet
timeout /t 2 >nul
call :start_service_quiet
echo.
echo [✓] Neustart abgeschlossen!
echo.
pause
goto menu

REM ──────────────────────────────────────────────────────────────────────
:check_status
echo.
echo [*] Überprüfe Service-Status...
echo.

REM Check SSH
echo SSH-Dienst:
net start %SSH_SERVICE% >nul 2>&1
if errorlevel 0 (
    echo   ✓ Läuft
) else (
    echo   ✗ Nicht aktiv
)

REM Check Flask
echo.
echo Flask Server:
tasklist /FI "WINDOWTITLE eq RenLern Server" 2>nul | find /I /N "cmd.exe" >nul
if "%errorlevel%"=="0" (
    echo   ✓ Läuft
) else (
    echo   ✗ Nicht aktiv
)

REM Check Cloudflare
echo.
echo Cloudflare Tunnel:
tasklist /FI "WINDOWTITLE eq Cloudflare Tunnel" 2>nul | find /I /N "cmd.exe" >nul
if "%errorlevel%"=="0" (
    echo   ✓ Läuft
) else (
    echo   ✗ Nicht aktiv
)

echo.
pause
goto menu

REM ──────────────────────────────────────────────────────────────────────
:enable_autostart
echo.
echo [*] Aktiviere Autostart...
echo.
echo    Dieses Skript erfordert Admin-Rechte!
echo    Sie werden aufgefordert, als Administrator bestätigt zu werden.
echo.

REM Check if admin
net session >nul 2>&1
if errorlevel 1 (
    echo    ✗ Fehler: Admin-Rechte erforderlich!
    echo    Bitte starten Sie die Eingabeaufforderung als Administrator!
    echo.
    pause
    goto menu
)

echo [1/2] Erstelle Autostart-Batch-Datei...
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set STARTUP_BATCH=%STARTUP_FOLDER%\RenLern_AutoStart.bat

(
    echo @echo off
    echo cd /d "%~dp0"
    echo start "RenLern Auto-Start" /b "%~f0" start
) > "%STARTUP_BATCH%"

echo        ✓ Autostart-Datei erstellt

echo [2/2] Registriere in Registry...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v RenLern /t REG_SZ /d "\"%~f0\" start" /f >nul 2>&1

echo        ✓ Registry aktualisiert

echo.
echo [✓] Autostart aktiviert!
echo    RenLern startet beim nächsten Hochfahren automatisch.
echo.
pause
goto menu

REM ──────────────────────────────────────────────────────────────────────
:disable_autostart
echo.
echo [*] Deaktiviere Autostart...
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo    ✗ Fehler: Admin-Rechte erforderlich!
    echo    Bitte starten Sie die Eingabeaufforderung als Administrator!
    echo.
    pause
    goto menu
)

set STARTUP_BATCH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\RenLern_AutoStart.bat
if exist "%STARTUP_BATCH%" del "%STARTUP_BATCH%"

reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v RenLern /f >nul 2>&1

echo    ✓ Autostart deaktiviert

echo.
pause
goto menu

REM ──────────────────────────────────────────────────────────────────────
:stop_service_quiet
taskkill /FI "WINDOWTITLE eq RenLern Server" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Cloudflare Tunnel" /F >nul 2>&1
exit /b 0

REM ──────────────────────────────────────────────────────────────────────
:start_service_quiet
net start %SSH_SERVICE% >nul 2>&1
start "RenLern Server" /b cmd /k "%PYTHON_EXE%" "%SERVER_SCRIPT%"
timeout /t 3 >nul
start "Cloudflare Tunnel" /b cmd /k "%CLOUDFLARE_CMD%"
exit /b 0

REM ──────────────────────────────────────────────────────────────────────
:unknown
echo.
echo Unbekannter Befehl: %1
echo.
echo Verwendung: %0 [start|stop|restart|status|autostart_enable|autostart_disable|menu]
echo.
goto menu

endlocal
