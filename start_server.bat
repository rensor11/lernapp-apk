@echo off
REM === RenLern Portal + Home Cloud + Lernapp Server ===

REM 1. Alten Server-Prozess beenden (falls laufend)
taskkill /FI "WINDOWTITLE eq RenLern Server" /F >nul 2>&1

REM 2. Neuen Server starten (server_v2.py im Root)
start "RenLern Server" cmd /k py "%~dp0server_v2.py"

REM 3. Cloudflared Tunnel laeuft bereits als Windows-Dienst

echo.
echo ======================================
echo   RenLern Server v2 gestartet!
echo   Portal:   https://renlern.org
echo   Home:     https://renlern.org/home
echo   Lernapp:  https://renlern.org/lernapp
echo ======================================
echo   Cloudflared laeuft als Dienst.
echo ======================================
pause
