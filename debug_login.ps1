try {
    $body = '{"username":"admin","password":"Admin@123"}'
    $r = Invoke-WebRequest -Uri 'http://localhost:5000/api/login' -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 10
    Write-Host 'OK'
    Write-Host $r.StatusCode
    Write-Host $r.Content
} catch {
    Write-Host 'ERR'
    if ($_.Exception.Response) {
        $resp = $_.Exception.Response
        Write-Host $resp.StatusCode.Value__
        $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
        Write-Host $reader.ReadToEnd()
    } else {
        Write-Host $_.Exception.Message
    }
}