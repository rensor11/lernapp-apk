# LernApp Server-Migration: VM -> Bare-Metal Debian

## Projektstatus (8. April 2026)

**Ziel:** LernApp-Server von einer VM auf einen alten Laptop mit Debian 12 migrieren. Alles so automatisiert, dass man nur einen USB-Stick einstecken und EIN Skript ausführen muss.

### Was ist fertig

| Datei | Beschreibung |
|-------|-------------|
| `INSTALL.sh` | **Master-Skript v2** - 15 Phasen, installiert ALLES automatisch inkl. Security-Hardening |
| `server.env` | Config-Datei: Tunnel-Token, SSH-Key, LAN-Subnet hier eintragen |
| `KURZANLEITUNG.txt` | Schritt-für-Schritt Anleitung (Deutsch) |
| `MIGRATION_GUIDE.md` | Ausführliche Migrations-Dokumentation |
| `01_setup_debian_server.sh` | Einzelskript: System-Grundsetup |
| `02_deploy_services.sh` | Einzelskript: systemd-Services |
| `03_service_manager.sh` | Einzelskript: Service-Verwaltung (start/stop/status) |
| `04_backup_vm.sh` | Einzelskript: Alte VM sichern |
| `cloudflared_config_template.yml` | Cloudflare Tunnel Config-Vorlage |
| `prepare_usb.ps1` | Windows: USB-Stick automatisch bespielen |
| `app_files/` | Alle 7 Quelldateien der App |

### INSTALL.sh v2 - 15 Phasen

1. System-Update & Pakete
2. **SSH-Härtung** (Port 8022, nur moderne Crypto, max 3 Versuche)
3. **Firewall mit Netzwerk-Zonen** (Flask nur localhost, SSH nur LAN)
4. **Kernel-Hardening** (SYN-Flood-Schutz, kein Forwarding, ASLR)
5. **fail2ban** (SSH: 3 Versuche = 2h Ban, Login: 10 Versuche = 30min)
6. **Automatische Sicherheitsupdates** (unattended-upgrades)
7. App-User mit Ressourcen-Limits
8. Python-venv + Flask/Gunicorn
9. Node.js 20 LTS
10. **Cloudflared automatisch mit Token** (kein manuelles Login!)
11. yt-dlp
12. App-Dateien kopieren
13. **systemd-Services mit Sandboxing** (NoNewPrivileges, ProtectSystem, MemoryMax)
14. Dienste starten (richtige Reihenfolge)
15. Sicherheitsaudit

### Sicherheitsarchitektur (7 Schichten)

```
Internet
  │
  ▼
[Cloudflare CDN + WAF + DDoS-Schutz]
  │  verschlüsselter Tunnel
  ▼
[FIREWALL] ── Alles blockiert außer SSH (nur LAN)
  │
  ▼
[fail2ban] ── Ban nach 3 Fehlversuchen
  │
  ▼
[cloudflared] ──► [Flask :5000 nur localhost]
 (sandboxed)       (sandboxed, nur 127.0.0.1)
                    │
                    ▼
                  [SQLite DB] (Rechte: 700)
```

### Was noch offen ist

- [ ] **Cloudflared Tunnel-Token finden** und in `server.env` eintragen
  - Token liegt irgendwo auf der VM (dc01), konnte von Webterminal aus nicht gefunden werden
  - Nächster Versuch: direkt von Schule aus auf VM zugreifen
  - Befehle zum Suchen: `ps aux | grep cloudflared`, `grep -r cloudflared /etc/systemd/`
- [ ] USB-Stick bespielen und auf Laptop testen

### Bestehende Infrastruktur

| Service | Details |
|---------|---------|
| Domain | renlern.org |
| Tunnel | "renlern" (ID: ddae2756-eb01-46d4-be69-d47bf9e5404f, Healthy) |
| Routes | renlern.org, www.renlern.org, terminal.renlern.org |
| VM | dc01 (User: renas) |
| Flask | server_neu.py, Port 5000, SQLite DB |
| Cloudflare | Renas98@msn.com |

### Chat-Verlauf Zusammenfassung

1. **Analyse:** Workspace untersucht, alle Services inventarisiert
2. **Skripte v1:** 4 Einzelskripte + Guide erstellt (im Repo)
3. **Desktop-Ordner:** Alles nach "migrations guide" auf Desktop kopiert
4. **USB-Ready:** INSTALL.sh Master-Skript, app_files kopiert, prepare_usb.ps1
5. **Security v2:** INSTALL.sh komplett neu mit 15 Phasen, Kernel-Hardening, fail2ban, Netzwerk-Segmentierung, Cloudflared Auto-Token
6. **Token-Suche:** Cloudflare Dashboard geöffnet, Tunnel gefunden (Healthy), Token auf VM nicht in üblichen Pfaden gefunden
7. **GitHub Push:** Alles committed und gepusht (17 Dateien)

### Nächste Session

Von der Schule aus direkt auf die VM zugreifen, Token finden, in server.env eintragen. Danach ist alles bereit für den USB-Stick.
