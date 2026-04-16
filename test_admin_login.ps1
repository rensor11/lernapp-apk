try {
    $body = @{username='admin'; password='Admin@123'} | ConvertTo-Json
    $r = Invoke-RestMethod -Uri 'http://localhost:5000/api/login' -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 10
    Write-Host 'LOGIN_OK'
    $r | ConvertTo-Json -Compress | Write-Host
} catch {
    Write-Host 'LOGIN_ERR'
    Write-Host $_.Exception.Message
}