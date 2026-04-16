@echo off
REM ═════════════════════════════════════════════════════════════════════════════
REM  RenLern Server - Automatischer Autostart (Silent Mode)
REM  Verwende diese Datei für den Windows-Autostart
REM ═════════════════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Warte kurz, damit Windows vollständig hochgefahren ist
timeout /t 3 /nobreak >nul 2>&1

REM Starte Flask Server im Hintergrund
start "" /LOW /B py "%~dp0server_v2.py" >nul 2>&1

REM Starte SSH Service
net start sshd >nul 2>&1

REM Starte Cloudflared Service (falls installiert)
net start cloudflared >nul 2>&1

REM Starte Cloudflared als Prozess (falls nicht als Service installiert)
if not exist "%~dp0cloudflared.log" (
    if exist "C:\Program Files (x86)\cloudflared\cloudflared.exe" (
        start "" /LOW /B "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --config "%USERPROFILE%\.cloudflared\config.yml" run renlern
    )
)

endlocal
exit /b 0
