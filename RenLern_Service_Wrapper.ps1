# RenLern Service Wrapper
$ErrorActionPreference = 'Continue'
Set-Location 'c:\Users\Administrator\Desktop\Repo clone\lernapp-apk'

$logPath = 'logs\service.log'
if (-not (Test-Path 'logs')) { New-Item -ItemType Directory -Path 'logs' -Force | Out-Null }

$msg = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Service Wrapper startet..."
Write-Host $msg
$msg | Add-Content $logPath

try {
    & py server_v2.py 2>&1 | ForEach-Object {
        $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $_"
        Write-Host $line
        $line | Add-Content $logPath
    }
} catch {
    $err = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - ERROR: $_"
    Write-Host $err -ForegroundColor Red
    $err | Add-Content $logPath
}
