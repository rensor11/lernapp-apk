# LernApp Server-Migration: Anleitung & Empfehlung
## Stand: April 2026

---

## Empfehlung: Bare-Metal Debian (KEIN VM auf dem Laptop)

**Ich empfehle dir, Debian direkt auf den Laptop zu installieren (Bare-Metal), KEINE VM.**

### Begründung:

| Kriterium | Bare-Metal Debian | VM auf dem Laptop |
|-----------|-------------------|-------------------|
| **Performance** | 100% der Hardware | 70-80% (Overhead durch Hypervisor) |
| **RAM** | Alles für Dienste | Host-OS frisst 1-2 GB weg |
| **Komplexität** | Einfach: 1 OS, fertig | Doppelt: Host-OS + Gast-OS verwalten |
| **Autostart** | systemd startet alles beim Boot | VM muss erst selbst starten |
| **Stabilität** | Direkte Hardware-Zugriffe | Zusätzliche Fehlerquelle |
| **Stromverbrauch** | Minimal | Höher durch Host-OS |

**Ein alter Laptop als Server** profitiert maximal von Bare-Metal, weil:
- RAM ist begrenzt → kein Overhead für einen Host
- CPU ist schwächer → jeder Zyklus zählt
- Der Laptop hat schon eine eingebaute USV (Akku!)
- Debian 12 läuft stabil auf fast jeder Hardware

### Wann DOCH eine VM Sinn macht:
- Wenn du auf dem Laptop AUCH noch andere Dinge machen willst (z.B. Desktop)
- Wenn du Snapshots für schnelle Rollbacks brauchst
- Wenn du mehrere isolierte Umgebungen brauchst

---

## Migrations-Ablauf (Schritt für Schritt)

### Phase 1: Alte VM sichern
```bash
# Auf der alten VM ausfuehren:
bash 04_backup_vm.sh
# -> Erstellt /tmp/lernapp_migration_DATUM.tar.gz
```

### Phase 2: Laptop vorbereiten
1. **Debian 12 (Bookworm) ISO herunterladen:**
   - https://www.debian.org/download
   - Empfohlen: `debian-12-amd64-netinst.iso`

2. **USB-Stick erstellen:**
   - Windows: [Rufus](https://rufus.ie) oder [balenaEtcher](https://etcher.balena.io)
   - Linux: `dd if=debian-12-amd64-netinst.iso of=/dev/sdX bs=4M status=progress`

3. **Installation:**
   - Vom USB booten (BIOS: F12/F2/Del beim Start)
   - Minimal-Installation wählen (kein Desktop!)
   - Partitionierung: Gesamte Platte, eine Partition reicht
   - Bei Software-Auswahl: NUR "SSH-Server" und "Standard-Systemwerkzeuge"

### Phase 3: Server einrichten
```bash
# Als root auf dem neuen Laptop:

# 1. Setup-Skript ausfuehren:
bash 01_setup_debian_server.sh

# 2. Backup vom alten Server kopieren:
scp -P 8022 user@alter_server:/tmp/lernapp_migration_*.tar.gz /tmp/

# 3. Backup entpacken:
cd /tmp && tar -xzf lernapp_migration_*.tar.gz

# 4. Dateien an richtige Stellen kopieren:
cp -r /tmp/lernapp_migration_*/app_files/* /opt/lernapp/
cp -r /tmp/lernapp_migration_*/cloudflared_config /home/lernapp/.cloudflared

# 5. Dienste deployen:
bash 02_deploy_services.sh

# 6. Status pruefen:
bash 03_service_manager.sh status
```

### Phase 4: Cloudflared-Tunnel umleiten
```bash
# Tunnel auf neuen Server zeigen lassen:
# Option A: Token-basiert (empfohlen)
cloudflared service install <DEIN_TUNNEL_TOKEN>

# Option B: Config-Datei
# /home/lernapp/.cloudflared/config.yml wurde aus dem Backup kopiert
# -> Nur starten und pruefen, ob der Tunnel verbindet
systemctl restart cloudflared-tunnel
journalctl -u cloudflared-tunnel -f
```

### Phase 5: Testen
```bash
# Lokal testen:
curl http://localhost:5000/api/health

# Extern testen:
curl https://renlern.org/api/health

# SSH testen:
ssh -p 8022 lernapp@IP_DES_LAPTOPS
```

---

## Dienste-Übersicht

| Dienst | systemd-Name | Port | Autostart |
|--------|-------------|------|-----------|
| SSH | `sshd` | 8022 | Ja |
| Flask (LernApp) | `lernapp-flask` | 5000 | Ja |
| Cloudflared | `cloudflared-tunnel` | - (Tunnel) | Ja |
| Node.js (optional) | `lernapp-node` | 3000 | Nein |

## Nützliche Befehle

```bash
# Alle Dienste auf einen Blick:
bash 03_service_manager.sh status

# Einzelnen Dienst neustarten:
systemctl restart lernapp-flask

# Logs live verfolgen:
journalctl -u lernapp-flask -f

# Alle Dienste starten/stoppen:
bash 03_service_manager.sh start
bash 03_service_manager.sh stop
```

---

## Datei-Übersicht (migration/ Ordner)

| Datei | Zweck | Wo ausführen |
|-------|-------|--------------|
| `01_setup_debian_server.sh` | System + alle Tools installieren | Neuer Laptop |
| `02_deploy_services.sh` | systemd-Dienste einrichten | Neuer Laptop |
| `03_service_manager.sh` | Dienste steuern (start/stop/status) | Neuer Laptop |
| `04_backup_vm.sh` | Alte VM komplett sichern | Alte VM |
| `MIGRATION_GUIDE.md` | Diese Anleitung | Zum Lesen |
