@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ═════════════════════════════════════════════════════════════════════════════
REM  RenLern Server - Alle Services Stopper
REM ═════════════════════════════════════════════════════════════════════════════

cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                  🛑 RenLern Server - Alle Services Stopper                ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

echo [*] Beende alle RenLern Services...
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 1. Flask Server beenden
REM ─────────────────────────────────────────────────────────────────────────────

echo [1/3] 🐍 Beende Flask Server...
taskkill /FI "WINDOWTITLE eq RenLern Server*" /F >nul 2>&1
if errorlevel 1 (
    echo     ℹ️  Flask Server bereits beendet oder nicht aktiv
) else (
    echo     ✓ Flask Server beendet
)
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 2. Cloudflared Tunnel beenden (falls nicht als Service läuft)
REM ─────────────────────────────────────────────────────────────────────────────

echo [2/3] ☁️  Beende Cloudflared Tunnel (falls als Prozess läuft)...
taskkill /IM cloudflared.exe /F >nul 2>&1
if errorlevel 1 (
    echo     ℹ️  Cloudflared bereits beendet oder läuft als Service
) else (
    echo     ✓ Cloudflared beendet
)
echo.

REM ─────────────────────────────────────────────────────────────────────────────
REM 3. SSH Service - Optional zum Stoppen
REM ─────────────────────────────────────────────────────────────────────────────

echo [3/3] 🔐 SSH Service Status...
sc query sshd | find "RUNNING" >nul 2>&1
if errorlevel 1 (
    echo     ℹ️  SSH Service ist nicht aktiv
) else (
    echo     ℹ️  SSH Service läuft noch (wird NICHT gestoppt - benötig für Admin)
    echo        Zum Stoppen: net stop sshd
)
echo.

echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                      ✅ Services beendet                                  ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
pause

endlocal
