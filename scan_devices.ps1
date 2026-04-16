# Netzwerk-Scan - Ultra SIMPLE
Write-Host "`nStarte Netzwerk-Scan..."
Write-Host "================================`n"

# Finde lokale IP
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"})[0].IPAddress

if ($null -eq $localIP) {
    Write-Host "FEHLER: Keine lokale IP gefunden"
    exit
}

Write-Host "Lokale IP: $localIP"
$net = ($localIP -split '\.')[0..2] -join '.'
Write-Host "Scanne: $net.0/24`n"

$ports = @(80, 8080, 8000, 8888, 3000, 5000, 9000)
$found = @()

for ($i = 1; $i -le 254; $i++) {
    $ip = "$net.$i"
    Write-Host -NoNewline "[$i/254] Checking $ip... "
    
    foreach ($port in $ports) {
        $tcp = New-Object System.Net.Sockets.TcpClient
        try {
            $result = $tcp.BeginConnect($ip, $port, $null, $null)
            $result.AsyncWaitHandle.WaitOne(200) | Out-Null
            
            if ($tcp.Connected) {
                Write-Host "[FOUND: $ip`:$port]" -ForegroundColor Green
                $found += "$ip`:$port"
            }
        }
        catch {
        }
        finally {
            $tcp.Close()
        }
    }
    Write-Host ""
}

Write-Host "`n================================"
Write-Host "RESULTS:"
Write-Host "================================"

if ($found.Count -eq 0) {
    Write-Host "No devices found"
} else {
    Write-Host "Found $($found.Count) device(s):`n" -ForegroundColor Green
    foreach ($dev in $found) {
        Write-Host "  $dev" -ForegroundColor Cyan
    }
}

Write-Host ""

