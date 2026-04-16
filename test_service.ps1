$location = 'c:\Users\Administrator\Desktop\Repo clone\lernapp-apk'
Set-Location $location

Write-Host "Starting RenLernServer Task..." -ForegroundColor Cyan
Get-ScheduledTask -TaskName 'RenLernServer' | Start-ScheduledTask -ErrorAction SilentlyContinue
Start-Sleep -Seconds 6

Write-Host "Testing Server Connection..." -ForegroundColor Cyan
$success = $false

for ($i = 1; $i -le 4; $i++) {
    try {
        $response = Invoke-WebRequest -Uri 'http://localhost:5000/api/ping' -TimeoutSec 2 -ErrorAction Stop
        Write-Host "SUCCESS - Server is responding!" -ForegroundColor Green
        $success = $true
        break
    } catch {
        if ($i -lt 4) {
            $elapsed = $i * 5
            Write-Host "Waiting... ($elapsed seconds elapsed)" -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    }
}

if ($success) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SERVICE SUCCESSFULLY INSTALLED!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Server is now running as Windows Service:" -ForegroundColor Cyan
    Write-Host "  - Task: RenLernServer" -ForegroundColor Cyan
    Write-Host "  - User: SYSTEM" -ForegroundColor Cyan
    Write-Host "  - Starts: At Windows Startup" -ForegroundColor Cyan
    Write-Host "  - Auto-Restart: Enabled on crash" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Access at:" -ForegroundColor Green
    Write-Host "  - Local: http://localhost:5000" -ForegroundColor Green
    Write-Host "  - Admin Portal: http://localhost:5000/portal.html" -ForegroundColor Green
    Write-Host "  - Cloud Storage: http://localhost:5000/home.html" -ForegroundColor Green
    Write-Host "  - External: https://renlern.org" -ForegroundColor Green
    Write-Host "========================================"
} else {
    Write-Host "ERROR - Server not responding" -ForegroundColor Red
    Write-Host "Checking logs..." -ForegroundColor Yellow
    if (Test-Path 'logs\service.log') {
        Get-Content 'logs\service.log' -Tail 10
    }
}
