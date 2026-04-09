[app]
# -------------------------------------------
# App-Informationen
# -------------------------------------------
title = LernApp Server APK
package.name = lernappserver
package.domain = de.lernapp

# Haupt-Python-Datei
source.dir = app
source.include_exts = py,json,html,txt

# Version
version = 1.0.0

# -------------------------------------------
# Abhängigkeiten (werden automatisch geladen)
# -------------------------------------------
requirements = python3,kivy,flask==2.3.3,werkzeug==2.3.8,jinja2==3.1.3,markupsafe==2.1.5,click==8.1.7,itsdangerous==2.1.2,blinker==1.7.0,requests,android

# -------------------------------------------
# Android Einstellungen
# -------------------------------------------
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WAKE_LOCK,FOREGROUND_SERVICE
android.accept_sdk_license = True

# Minimale Android Version (5.0+)
android.minapi = 21
android.api = 34
android.ndk = 25b

# Architektur - arm64-v8a für moderne Geräte, armeabi-v7a für ältere
android.archs = arm64-v8a, armeabi-v7a

# App läuft im Hintergrund weiter
android.wakelock = True

# Kein Kivy-Fenster nötig - wir bauen eine Service-App
#android.service = LernappService,app/service.py

# Icon & Splash (optional - leg .png Dateien in assets/)
# icon.filename = %(source.dir)s/../assets/icon.png
# presplash.filename = %(source.dir)s/../assets/splash.png

# Orientierung
orientation = portrait

# -------------------------------------------
# Build-Einstellungen
# -------------------------------------------
[buildozer]
log_level = 2
warn_on_root = 1
