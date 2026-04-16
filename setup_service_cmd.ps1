# Remove old task
Write-Host 'Removing old task...' -ForegroundColor Yellow
Get-ScheduledTask 'RenLernServer' -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false -Force -ErrorAction SilentlyContinue

# Create new task with CMD script instead of PowerShell
Write-Host 'Creating new Scheduled Task with CMD script...' -ForegroundColor Cyan

$trigger = New-ScheduledTaskTrigger -AtStartup
$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/c `"c:\Users\Administrator\Desktop\Repo clone\lernapp-apk\RenLern_Service_Starter.cmd`""
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit 0
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName 'RenLernServer' -Trigger $trigger -Action $action -Settings $settings -Principal $principal -Force | Out-Null

Write-Host 'Task created successfully!' -ForegroundColor Green
Write-Host 'Starting task...' -ForegroundColor Cyan
Get-ScheduledTask 'RenLernServer' | Start-ScheduledTask
Start-Sleep -Seconds 6

Write-Host 'Testing server...' -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:5000/' -TimeoutSec 2 -ErrorAction Stop
    Write-Host 'SUCCESS - Server is running! Status: 200' -ForegroundColor Green
} catch {
    Write-Host 'Server not responding (may still be starting)' -ForegroundColor Yellow
    Start-Sleep -Seconds 8
    try {
        $response = Invoke-WebRequest -Uri 'http://localhost:5000/' -TimeoutSec 2 -ErrorAction Stop
        Write-Host 'SUCCESS - Server is now running! Status: 200' -ForegroundColor Green
    } catch {
        Write-Host 'Server still not responding' -ForegroundColor Red
        Write-Host 'Checking logs...' -ForegroundColor Yellow
        if (Test-Path 'c:\Users\Administrator\Desktop\Repo clone\lernapp-apk\logs\service.log') {
            Write-Host '--- Log Contents ---' -ForegroundColor Cyan
            Get-Content 'c:\Users\Administrator\Desktop\Repo clone\lernapp-apk\logs\service.log'
        } else {
            Write-Host 'No log file found' -ForegroundColor Red
        }
    }
}
