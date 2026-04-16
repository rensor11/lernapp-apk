@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo [*] Erstelle Desktop-Verknüpfungen...
echo.

REM Get paths
set "DESKTOP=%USERPROFILE%\Desktop"
set "RENLERN_FOLDER=%DESKTOP%\RenLern"
set "BATCH_FILE=%~f0"
set "BATCH_FILE=!BATCH_FILE:create_shortcuts.bat=RUN_LERNAPP.bat!"

REM Create folder
if not exist "%RENLERN_FOLDER%" (
    mkdir "%RENLERN_FOLDER%"
    echo [+] Ordner erstellt: %RENLERN_FOLDER%
)

REM Create shortcuts using VBScript
set "VBSCRIPT=%TEMP%\create_lernapp_shortcuts.vbs"

(
    echo ' Create shortcuts for RenLern
    echo Set shell = CreateObject("WScript.Shell"^)
    echo Set fso = CreateObject("Scripting.FileSystemObject"^)
    echo.
    echo folderPath = "%RENLERN_FOLDER%"
    echo batchFile = "%BATCH_FILE%"
    echo.
    echo ' Array of shortcuts: Name, Arguments
    echo shortcuts = Array( _
    echo   Array("01 Start",          "start"^), _
    echo   Array("02 Restart",        "restart"^), _
    echo   Array("03 Autostart",      "autostart_enable"^), _
    echo   Array("04 Shutdown",       "stop"^) _
    echo )
    echo.
    echo ' Create each shortcut
    echo For i = 0 To UBound(shortcuts^)
    echo   shortcutPath = folderPath ^& "\" ^& shortcuts(i^)(0^) ^& ".lnk"
    echo   Set shortcut = shell.CreateShortcut(shortcutPath^)
    echo   shortcut.TargetPath = batchFile
    echo   shortcut.Arguments = shortcuts(i^)(1^)
    echo   shortcut.WorkingDirectory = fso.GetParentFolderName(batchFile^)
    echo   shortcut.Description = "RenLern Service Manager - " ^& shortcuts(i^)(0^)
    echo   shortcut.WindowStyle = 1
    echo   shortcut.Save
    echo   WScript.Echo "  ✓ Verknüpfung erstellt: " ^& shortcuts(i^)(0^)
    echo Next
) > "%VBSCRIPT%"

echo.
cscript.exe "%VBSCRIPT%"
del /f /q "%VBSCRIPT%" 2>nul

echo.
echo [✓] Desktop-Verknüpfungen erfolgreich erstellt!
echo     Ordner: %RENLERN_FOLDER%
echo.
pause


