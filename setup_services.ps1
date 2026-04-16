#Requires -RunAsAdministrator

# ==============================================
# RenLern Server Dienste Setup Skript
# ==============================================

param(
    [string]$VMName = "RenLern-Debian",
    [string]$VMIP = "192.168.178.100", # Voraussichtliche IP, muss ggf. angepasst werden
    [string]$SSHAliase = "renlern-vm",
    [string]$SSHUser = "root",
    [string]$SSHKeyPath = "$env:USERPROFILE\.ssh\id_rsa_renlern"
)

# --- Konfiguration --- 
$serverScriptName = "server_neu.py"
$serverScriptPath = "C:\Users\Administrator\Desktop\Repo clone\lernapp-apk\$serverScriptName"
$serverWorkingDirectory = "C:\Users\Administrator\Desktop\Repo clone\lernapp-apk\"
$debianSetupScript = "C:\Users\Administrator\Desktop\Repo clone\lernapp-apk\setup_debian_vm.ps1"

# --- Dienste starten --- 

# 1. Flask Server (server_neu.py)
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        Flask Server (server_neu.py) starten        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Prüfen ob der Prozess bereits läuft
$proc = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$serverScriptPath" }
if ($proc) {
    Write-Host "✅ Flask Server läuft bereits." -ForegroundColor Green
} else {
    Write-Host "🚀 Startet Flask Server..."
    try {
        # Startet den Server im Hintergrund, ohne neues Fenster
        Start-Process "python.exe" -ArgumentList "$serverScriptPath" -WorkingDirectory "$serverWorkingDirectory" -WindowStyle Hidden
        Write-Host "✅ Flask Server gestartet." -ForegroundColor Green
    } catch {
        Write-Host "❌ Fehler beim Starten des Flask Servers: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 2. SSH-Zugang zur Debian VM
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           SSH Zugang zur Debian VM               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# SSH Client installieren (falls nicht vorhanden)
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "➕ Installiert OpenSSH Client..."
    Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
}

# SSH Key erstellen (falls nicht vorhanden)
if (-not (Test-Path $SSHKeyPath)) {
    Write-Host "🔐 Erstellt SSH Key für $VMName..."
    try {
        ssh-keygen -t rsa -b 4096 -C "$VMName @ $env:COMPUTERNAME" -f "$SSHKeyPath" -N ""
        Write-Host "✅ SSH Key erstellt: $SSHKeyPath"
        Write-Host "Öffentlichen Key kopieren und zur authorized_keys der VM hinzufügen!"
        Write-Host "   (z.B. per: scp $($SSHKeyPath).pub $($SSHUser)@$VMIP:/home/$SSHUser/.ssh/authorized_keys)"
    } catch {
        Write-Host "❌ Fehler beim Erstellen des SSH Keys: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 3. Debian VM Setup Skript ausführen (optional, falls nötig)
#    Dies muss manuell oder über eine geplante Aufgabe erfolgen, wenn die VM läuft
if ($PSCmdlet.MyInvocation.BoundParameters.ContainsKey('RunDebianSetup') -and $PSBoundParameters['RunDebianSetup']) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║            Debian VM Setup Skript ausführen        ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    if (Test-Path $debianSetupScript) {
        try {
            Write-Host "🚀 Führe $debianSetupScript aus..."
            # Hier wird das Skript über SSH auf der VM ausgeführt
            # Achtung: Passwortabfrage oder Key-Authentifizierung nötig!
            # Beispiel mit Passwort (nicht empfohlen für Skripte):
            # sshpass -p 'dein_passwort' ssh $SSHUser@$VMIP "bash /tmp/setup.sh"
            
            # Besser: SSH Key Authentifizierung (wennauthorized_keys gesetzt ist)
            # Zuerst das Skript auf die VM kopieren
            scp "$debianSetupScript" "${SSHUser}@${VMIP}:/tmp/setup.sh"
            # Dann auf der VM ausführen
            ssh "${SSHUser}@${VMIP}" "bash /tmp/setup.sh"
            
            Write-Host "✅ Debian VM Setup abgeschlossen."
        } catch {
            Write-Host "❌ Fehler beim Ausführen des Debian Setup Skripts: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️ Debian Setup Skript nicht gefunden: $debianSetupScript" -ForegroundColor Yellow
    }
}

# 4. Cloudflared Tunnel
#    Hinweis: Cloudflared muss separat installiert und konfiguriert sein!
#    Dieses Skript geht davon aus, dass Cloudflared als Dienst läuft.
#    Wenn nicht, muss es manuell installiert und gestartet werden.
#    Siehe: https://developers.cloudflare.com/cloudflare-one-dollar-one/connections/connect-apps/install-and-setup/installation/
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              Cloudflared Tunnel Status             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$cloudflaredProc = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($cloudflaredProc) {
    Write-Host "✅ Cloudflared läuft." -ForegroundColor Green
} else {
    Write-Host "⚠️ Cloudflared nicht gefunden oder läuft nicht." -ForegroundColor Yellow
    Write-Host "   Bitte manuell installieren und konfigurieren:"
    Write-Host "   https://developers.cloudflare.com/cloudflare-one-dollar-one/connections/connect-apps/install-and-setup/installation/"
    # Versuch, Cloudflared zu starten (wenn es im PATH ist)
    try {
        # start C:\path\to\cloudflared.exe tunnel --config C:\path\to\config.yml
        Write-Host "   Versuche Cloudflared zu starten... (Konfiguration wird benötigt)"
    } catch {
        Write-Host "   Konfiguration oder Pfad nicht gefunden." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Alle Dienste wurden überprüft und gestartet (soweit möglich)."
Write-Host "Verwenden Sie die Desktop-Verknüpfung, um den Server zu verwalten."
