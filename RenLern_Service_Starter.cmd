@echo off
REM RenLern Server Starter - Windows Service Batch Script
REM This script starts the Flask server for RenLern Portal

setlocal enabledelayedexpansion

REM Set UTF-8 code page for proper Unicode handling
chcp 65001 > nul

REM Set Python encoding to UTF-8
set PYTHONIOENCODING=utf-8

REM Set working directory
cd /d "c:\Users\Administrator\Desktop\Repo clone\lernapp-apk"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Log the start time
echo [%date% %time%] RenLern Service starting >> logs\service.log

REM Start the Python server with UTF-8 IO encoding
REM Using full path to python.exe
"C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe" -X utf8 server_v2.py >> logs\service.log 2>&1

REM If script reaches here, server stopped
echo [%date% %time%] RenLern Service stopped >> logs\service.log
