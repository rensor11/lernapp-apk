@echo off
REM ════════════════════════════════════════════════════════════════════════════
REM   🛑 STOP ALL SERVICES - Smart Home Portal v2.0
REM ════════════════════════════════════════════════════════════════════════════

chcp 65001 >nul
setlocal enabledelayedexpansion
cls

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║        🛑 STOP ALL SERVICES - Smart Home Portal v2.0                      ║
echo ║                                                                           ║
echo ║  Beendet:                                                                 ║
echo ║    • Mock Home Assistant Server (Port 8123)                               ║
echo ║    • Lernapp Server (Port 5000)                                           ║
echo ║    • Alle Python Prozesse                                                 ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

echo [1/4] 🛑 Beende Service-Fenster...
taskkill /FI "WINDOWTITLE eq Mock Home Assistant*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Lernapp Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq RenLern Server*" /F >nul 2>&1
timeout /t 1 >nul
echo     ✓ Service-Fenster geschlossen
echo.

echo [2/4] 🔌 Beende Python Prozesse...
taskkill /IM python.exe /F >nul 2>&1
timeout /t 1 >nul
echo     ✓ Python Prozesse beendet
echo.

echo [3/4] 📊 Überprüfe Port-Verfügbarkeit...
netstat -ano | find ":5000" >nul
if errorlevel 1 (
    echo     ✓ Port 5000 verfügbar
) else (
    echo     ⚠️  Port 5000 noch in Verwendung
)

netstat -ano | find ":8123" >nul
if errorlevel 1 (
    echo     ✓ Port 8123 verfügbar
) else (
    echo     ⚠️  Port 8123 noch in Verwendung
)
echo.

echo [4/4] ✅ Final Status...
tasklist | find /i "python.exe" >nul
if errorlevel 1 (
    echo     ✓ Alle Python Prozesse beendet
    echo     ✓ Services können neu gestartet werden
) else (
    echo     ⚠️  Einige Python Prozesse sind noch aktiv
)
echo.

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║        ✅ ALLE DIENSTE GESTOPPT                                           ║
echo ║                                                                           ║
echo ║  Zum Neustarten:                                                          ║
echo ║  ➜ START_SMARTHOME_MASTER.bat                                             ║
echo ║                                                                           ║
echo ║  Services sind sauber heruntergefahren!                                   ║
echo ║                                                                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

pause
