REM ════════════════════════════════════════════════════════════════════════════
REM SSH Server - Windows Configuration Guide für RenLern
REM ════════════════════════════════════════════════════════════════════════════
REM
REM SSH ist bereits installiert und läuft. Diese Konfiguration optimiert ihn.
REM
REM ════════════════════════════════════════════════════════════════════════════

@echo off
setlocal enabledelayedexpansion
cls

echo.
echo [*] Überprüfe SSH Server Konfiguration...
echo.

REM SSH-Konfiguration ist unter: C:\ProgramData\ssh\sshd_config
set "SSHD_CONFIG=C:\ProgramData\ssh\sshd_config"

if not exist "%SSHD_CONFIG%" (
    echo [!] WARNUNG: sshd_config nicht gefunden!
    echo     Pfad: %SSHD_CONFIG%
    echo     SSH Server liefert Standard-Konfiguration.
    echo.
) else (
    echo [✓] sshd_config gefunden
    echo.
    echo Wichtige Sicherheitseinstellungen laut Konfiguration:
    echo.
    find /i "PermitRootLogin" "%SSHD_CONFIG%" && echo       ✓ PermitRootLogin konfiguriert
    find /i "PasswordAuthentication" "%SSHD_CONFIG%" && echo  ✓ PasswordAuthentication konfiguriert
    find /i "PubkeyAuthentication" "%SSHD_CONFIG%" && echo    ✓ PubkeyAuthentication konfiguriert
    find /i "Port 22" "%SSHD_CONFIG%" && echo                 ✓ Port 22 aktiv
    echo.
)

echo Empfohlene SSH Konfiguration:
echo ─────────────────────────────────────────────
echo Port 22
echo PermitRootLogin no
echo PasswordAuthentication yes
echo PubkeyAuthentication yes
echo StrictModes yes
echo MaxAuthTries 3
echo MaxSessions 10
echo AuthorizedKeysFile .ssh/authorized_keys
echo.

echo SSH Dienststatus:
net start sshd >nul 2>&1
if errorlevel 0 (
    echo [✓] SSH Server läuft
) else (
    echo [!] SSH Server läuft nicht
)

echo.
echo Verbindungstest:
echo ─────────────────────────────────────────────
echo Um sich per SSH zu verbinden, verwende:
echo   ssh -l Administrator localhost -p 22
echo   oder
echo   ssh Administrator@^<Ihre-IP^>
echo.

REM Get IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find /i "IPv4"') do (
    set "IP=%%a"
    set "IP=!IP:~1!"
)

if defined IP (
    echo Ihre IP-Adressen:
    echo.
    ipconfig | find /i "IPv4" | find /i " ."
    echo.
)

echo SSH-Schlüssel generieren (optional):
echo ─────────────────────────────────────────────
echo Zum Erstellen eines SSH-Schlüsselpaars (Public Key Auth):
echo   ssh-keygen -t ed25519 -f C:\Users\Administrator\.ssh\id_ed25519
echo.

pause
