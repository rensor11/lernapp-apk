@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo [*] Erstelle Desktop-Verknüpfungen für RenLern Server...
echo.

REM Pfade
set "DESKTOP=%USERPROFILE%\Desktop"
set "RENLERN_FOLDER=%DESKTOP%\RenLern Server"
set "SERVER_DIR=%~dp0"

REM Erstelle Ordner
if not exist "%RENLERN_FOLDER%" (
    mkdir "%RENLERN_FOLDER%"
    echo [+] Ordner erstellt: %RENLERN_FOLDER%
)

REM Erstelle VBScript für Verknüpfungen
set "VBSCRIPT=%TEMP%\create_renlern_shortcuts.vbs"

(
    echo ' RenLern Server Verknüpfungen
    echo Set shell = CreateObject("WScript.Shell"^)
    echo Set fso = CreateObject("Scripting.FileSystemObject"^)
    echo.
    echo folderPath = "%RENLERN_FOLDER%"
    echo serverDir = "%SERVER_DIR%"
    echo.
    echo ' Array: Name, Batch-Datei, Icon-Index
    echo shortcuts = Array( _
    echo   Array("01 - START Alle Services.lnk",     "START_ALL_SERVICES.bat",    0^), _
    echo   Array("02 - STOP Alle Services.lnk",      "STOP_ALL_SERVICES.bat",     1^), _
    echo   Array("03 - Autostart aktivieren.lnk",    "AUTOSTART_RENLERN.bat",     2^) _
    echo )
    echo.
    echo ' Erstelle Verknüpfungen
    echo For i = LBound(shortcuts^) To UBound(shortcuts^)
    echo   shortcutPath = folderPath ^& "\" ^& shortcuts(i^)(0^)
    echo   batchFile = serverDir ^& shortcuts(i^)(1^)
    echo.
    echo   Set shortcut = shell.CreateShortcut(shortcutPath^)
    echo   shortcut.TargetPath = batchFile
    echo   shortcut.WorkingDirectory = serverDir
    echo   shortcut.WindowStyle = 1
    echo   Select Case shortcuts(i^)(2^)
    echo     Case 0
    echo       shortcut.Description = "RenLern Server - START alle Services"
    echo       shortcut.IconLocation = "C:\Windows\System32\shell32.dll,16"
    echo     Case 1
    echo       shortcut.Description = "RenLern Server - STOP alle Services"
    echo       shortcut.IconLocation = "C:\Windows\System32\shell32.dll,27"
    echo     Case 2
    echo       shortcut.Description = "RenLern Server - Autostart aktivieren"
    echo       shortcut.IconLocation = "C:\Windows\System32\shell32.dll,25"
    echo   End Select
    echo   shortcut.Save
    echo   WScript.Echo "  ✓ Erstellt: " ^& shortcuts(i^)(0^)
    echo Next
    echo.
    echo WScript.Echo ""
    echo.MsgBox "✅ Verknüpfungen erfolgreich erstellt!",vbInformation,"RenLern Server"
) > "%VBSCRIPT%"

REM Führe VBScript aus
cscript.exe "%VBSCRIPT%"

REM Lösche VBScript
del "%VBSCRIPT%"

echo.
echo ✅ Fertig! 
echo.
echo Ordner erstellt auf: %RENLERN_FOLDER%
echo.
pause
