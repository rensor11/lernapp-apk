#Requires -RunAsAdministrator

# RenLern Server Dienste Setup Skript

param(
    [string]$VMName = "RenLern-Debian",
    [string]$VMIP = "192.168.178.100",
    [string]$SSHAliase = "renlern-vm",
    [string]$SSHUser = "root",
    [string]$SSHKeyPath = "$env:USERPROFILE\.ssh\id_rsa_renlern"
)

$serverScriptName = "server_neu.py"
$serverScriptPath = "C:\Users\Administrator\Desktop\Repo clone\lernapp-apk\$serverScriptName"
$serverWorkingDirectory = "C:\Users\Administrator\Desktop\Repo clone\lernapp-apk\"
$debianSetupScript = "C:\Users\Administrator\Desktop\Repo clone\lernapp-apk\setup_debian_vm.ps1"

Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        Flask Server (server_neu.py) starten        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$proc = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*server_neu.py*" }
if ($proc) {
    Write-Host "✅ Flask Server laeuft bereits." -ForegroundColor Green
} else {
    Write-Host "🚀 Startet Flask Server..."
    try {
        Start-Process "python.exe" -ArgumentList "$serverScriptPath" -WorkingDirectory "$serverWorkingDirectory" -WindowStyle Hidden
        Start-Sleep -Seconds 2
        Write-Host "✅ Flask Server gestartet." -ForegroundColor Green
    } catch {
        Write-Host "❌ Fehler beim Starten des Flask Servers: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           SSH Zugang zur Debian VM                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan

if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "➕ Installiert OpenSSH Client..."
    try {
        Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0 | Out-Null
        Write-Host "✅ OpenSSH Client installiert." -ForegroundColor Green
    } catch {
        Write-Host "⚠️ OpenSSH Client Installation hatte Fehler." -ForegroundColor Yellow
    }
}

if (-not (Test-Path $SSHKeyPath)) {
    Write-Host "🔐 Erstellt SSH Key fuer $VMName..."
    try {
        $comment = "$VMName at $env:COMPUTERNAME"
        ssh-keygen -t rsa -b 4096 -C $comment -f "$SSHKeyPath" -N ""
        Write-Host "✅ SSH Key erstellt: $SSHKeyPath" -ForegroundColor Green
        Write-Host "Öffentlichen Key zur VM hinzufuegen mit:"
        Write-Host "   scp $($SSHKeyPath).pub ${SSHUser}@${VMIP}:/root/.ssh/authorized_keys" -ForegroundColor Yellow
    } catch {
        Write-Host "❌ Fehler beim Erstellen des SSH Keys: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              Cloudflared Tunnel Status             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$cloudflaredProc = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($cloudflaredProc) {
    Write-Host "✅ Cloudflared laeuft." -ForegroundColor Green
} else {
    Write-Host "⚠️ Cloudflared nicht gefunden oder laeuft nicht." -ForegroundColor Yellow
    Write-Host "   Prüfe ob Cloudflared installiert ist:" -ForegroundColor Cyan
    Write-Host "   https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          ✅ Dienste-Setup abgeschlossen!           ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Server Details:" -ForegroundColor Cyan
Write-Host "  Flask:     http://localhost:5000" -ForegroundColor White
Write-Host "  Portal:    http://localhost:5000/" -ForegroundColor White
Write-Host "  Home:      http://localhost:5000/home" -ForegroundColor White
Write-Host "  Lernapp:   http://localhost:5000/lernapp" -ForegroundColor White
Write-Host ""
