$report = @()

function Add-Report { param($name, $status, $detail) $report += [PSCustomObject]@{Component=$name;Status=$status;Detail=$detail} }

# Flask server local check
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:5000' -UseBasicParsing -TimeoutSec 10
    Add-Report 'Flask local' 'OK' "Status $($response.StatusCode)"
} catch {
    Add-Report 'Flask local' 'ERROR' $_.Exception.Message
}

# cloudflared service check
try {
    $svc = Get-Service -Name Cloudflared -ErrorAction Stop
    Add-Report 'Cloudflared service' ($svc.Status.ToString()) "DisplayName: $($svc.DisplayName)"
} catch {
    Add-Report 'Cloudflared service' 'NOT FOUND' $_.Exception.Message
}

# public domain check
try {
    $response = Invoke-WebRequest -Uri 'https://renlern.org' -UseBasicParsing -TimeoutSec 10
    Add-Report 'Public domain' 'OK' "Status $($response.StatusCode)"
} catch {
    Add-Report 'Public domain' 'ERROR' $_.Exception.Message
}

$report | Format-Table -AutoSize

if ($report.Status -contains 'ERROR' -or $report.Status -contains 'NOT FOUND') {
    exit 1
} else {
    exit 0
}
