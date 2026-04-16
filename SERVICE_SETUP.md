# RenLern Server - Dauerhafter Service Setup
## Der Server läuft jetzt immer - auch wenn du den Laptop zuklappt!

---

## 🚀 **SCHNELLSTART (3 einfache Schritte)**

### Schritt 1: Öffne PowerShell als Administrator
```powershell
# Rechtsklick auf PowerShell → "Als Administrator ausführen"
PS C:\Users\Administrator\Desktop\Repo clone\lernapp-apk>
```

### Schritt 2: Installiere Service
```powershell
.\install_service.ps1
```
✅ Fertig! Der Service wird installiert und Energieoptionen konfiguriert

### Schritt 3: Starte Service Management
```powershell
.\service_manager.ps1
```
Wähle:
- [2] Service starten
- [6] Gesundheit prüfen

---

## ✅ **Was passiert jetzt?**

| Vorher | Nachher |
|--------|---------|
| ❌ Server läuft nur wenn PowerShell offen ist | ✅ Server läuft immer im Hintergrund |
| ❌ Laptop zumachen = Server stopp | ✅ Laptop zumachen = Server läuft weiter |
| ❌ PC neustarten = manuell Server starten | ✅ PC startet automatisch mit Server |
| ❌ Admin abzumelden = Server weg | ✅ Server läuft auch ohne Benutzer |

---

## 🎯 **Was wurde gemacht?**

### 1. **Windows Service erstellt**
- Service Name: `RenLernServer`
- Display Name: `RenLern Flask Server`
- Autostart: **JA**
- Automatischer Neustart: **JA**

### 2. **Energieoptionen angepasst**
- Bildschirm: **Nie ausschalten**
- Festplatte: **Nie ausschalten**
- Sleep/Suspend: **Deaktiviert**
- Laptop-Zuklappen: **Server läuft weiter**

### 3. **Logging eingerichtet**
- Log-Datei: `logs\service.log`
- Permanente Aufzeichnung aller Server-Aktivitäten

---

## 🛠️ **Tägliche Verwendung**

### Menü öffnen (einfach so!)
```powershell
.\service_manager.ps1
```

### Optionen:
```
  [1] 📊 Service Status          → Server Status anschauen
  [2] ▶️  Service starten        → Server manuell starten
  [3] ⏹️  Service stoppen        → Server manuell stoppen
  [4] 🔄 Service neu starten     → Server neustarten (z.B. nach Update)
  [5] 📋 Logs anzeigen (live)    → Fehler debuggen
  [6] 💚 Gesundheit prüfen       → Alles OK? (HTTP, DB, Memory)
  [7] ⚡ Energieoptionen prüfen  → Sleep-Modus Status
  [8] 🛠️  Service neu installieren → Falls Problem
```

---

## 💻 **Windows Commands (Alternative)**

Wenn du PowerShell-Menü nicht brauchst:

```powershell
# Status prüfen
Get-Service RenLernServer

# Starten
Start-Service RenLernServer

# Stoppen
Stop-Service RenLernServer

# Neu starten
Restart-Service RenLernServer

# In Services.msc öffnen
services.msc
```

---

## 📊 **Service Eigenschaften**

Öffne Datei-Manager und navigiere zu:
```
Services.msc → RenLern Flask Server
```

| Eigenschaft | Wert |
|-------------|------|
| Service Name | RenLernServer |
| Display Name | RenLern Flask Server |
| Status | Automatic / Running |
| Start-Typ | Automatic |
| Recovery | Neu starten nach 10s |

---

## 🔍 **Überprüfung**

### Test 1: Service läuft?
```powershell
.\service_manager.ps1
[6] Gesundheit prüfen
```
Sollte zeigen: ✓ Service läuft, ✓ Server antwortet

### Test 2: Nach PC-Neustartstart?
1. PC neustarten
2. Warten 30 Sekunden
3. Browser: `http://localhost:5000`
4. Server sollte sofort antworten!

### Test 3: Laptop zumachen?
1. Laptop zumachen (Sleep)
2. Wieder öffnen
3. Server läuft noch immer!

---

## 📋 **Logs prüfen**

### Live-Logs anschauen
```powershell
.\service_manager.ps1
[5] Logs anzeigen
# Live-Ausgabe mit Ctrl+C beenden
```

### Letzte 50 Zeilen
```powershell
Get-Content logs\service.log -Tail 50
```

### Fehlersuche
```powershell
# Suche nach Fehlern in Logs
Select-String "ERROR" logs\service.log | Select Line, LineNumber
```

---

## ⚠️ **Häufige Probleme**

### Problem: Service startet nicht
```powershell
# Lösung 1: Service deinstallieren & neu installieren
.\install_service.ps1 -Uninstall
.\install_service.ps1

# Lösung 2: Check Logs
Get-Content logs\service.log
```

### Problem: "Admin required" beim Start
```powershell
# Lösung: PowerShell als Admin öffnen
# Rechtsklick PowerShell → "Als Administrator ausführen"
```

### Problem: Port 5000 wird benutzt
```powershell
# Finde was den Port nutzt
netstat -ano | findstr :5000

# Stoppe den Prozess
Stop-Process -Id <PID> -Force
```

### Problem: Server antwortet nicht
```powershell
.\service_manager.ps1
[6] Gesundheit prüfen
# Zeigt alle Probleme auf
```

---

## 🔐 **Sicherheit**

### Nur Admin kann ändern
- Service Installieren/Deinstallieren: **Admin needed**
- Service Starten/Stoppen: **Admin needed**
- Server selbst nutzen: Alle User können zugreifen

### Logging
- Alle Server-Aktivitäten in `logs\service.log` gespeichert
- Nicht gelöscht automatisch
- Wann du möchtest: löschen oder archivieren

---

## 🚀 **Updates & Neustarts**

### Nach Code-Update:
```powershell
# Service neu starten (lädt neue Dateien)
.\service_manager.ps1
[4] Service neu starten
```

### Nach Python-Update:
```powershell
# Service Deinstallation/Neu-Installation
.\install_service.ps1 -Uninstall
# Starten Services.msc und löschen alte Service-Prozesse
.\install_service.ps1
```

---

## 📞 **Support Commands**

```powershell
# Alle Prozesse die "python" enthalten
Get-Process | Where-Object { $_.Name -like "*python*" }

# Alle running Services mit "Ren"
Get-Service | Where-Object { $_.Name -like "*Ren*" }

# Event Viewer für Service-Fehler
eventvwr.msc
# → Suche in "Application" Log nach "RenLern"
```

---

## ✓ **Checklist für Produktion**

- [ ] Service installiert (`.\install_service.ps1`)
- [ ] Service startet automatisch nach PC-Reboot
- [ ] Server antwortet unter `http://localhost:5000`
- [ ] Energieoptionen angepasst (Laptop schläft nicht)
- [ ] Logs funktionieren (`logs\service.log` existiert)
- [ ] Cloudflared-Tunnel läuft für externe URL
- [ ] Backup/Monitoring eingerichtet

---

## 🎓 **Lernpfad**

1. **Heute**: Installation & Erste Tests
2. **Diese Woche**: Logs überwachen, Fehler debuggen
3. **Nächste Woche**: Monitoring-System einrichten
4. **Monatlich**: Service-Health überprüfen

---

## 📚 **Weitere Ressourcen**

- **Service-Management Menü**: `.\service_manager.ps1`
- **Manuelle Installation**: `.\install_service.ps1`
- **VM Backup**: `.\vm_manager.ps1`
- **Server-Code**: `server_v2.py`
- **Logs**: `logs\service.log`

---

**Stand: April 15, 2026**  
**Version: 1.0 - Production Ready**
