try {
    $r = Invoke-RestMethod -Uri 'http://localhost:5000/api/admin/user-category-stats?user_id=1' -Headers @{ 'X-Admin-User' = 'admin' } -Method GET -TimeoutSec 10
    Write-Host 'STATS_OK'
    $r | ConvertTo-Json -Compress | Write-Host
} catch {
    Write-Host 'STATS_ERR'
    if ($_.Exception.Response) {
        $resp = $_.Exception.Response
        Write-Host $resp.StatusCode.Value__
        $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
        Write-Host $reader.ReadToEnd()
    } else {
        Write-Host $_.Exception.Message
    }
}