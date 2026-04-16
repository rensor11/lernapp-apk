Write-Host "" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "RENLERN SERVICE - FINAL STATUS CHECK" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$allSuccess = $true

# Test 1
try {
    $r = Invoke-WebRequest -Uri "http://localhost:5000/" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Main page: HTTP 200" -ForegroundColor Green
} catch {
    Write-Host "✗ Main page failed" -ForegroundColor Red
    $allSuccess = $false
}

# Test 2
try {
    $r = Invoke-WebRequest -Uri "http://localhost:5000/portal.html" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Admin Portal: HTTP 200" -ForegroundColor Green
} catch {
    Write-Host "✗ Portal failed" -ForegroundColor Red
    $allSuccess = $false
}

# Test 3
try {
    $r = Invoke-WebRequest -Uri "http://localhost:5000/home.html" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Home Cloud: HTTP 200" -ForegroundColor Green
} catch {
    Write-Host "✗ Home failed" -ForegroundColor Red
    $allSuccess = $false
}

# Test 4
try {
    $r = Invoke-WebRequest -Uri "http://localhost:5000/lernapp.html" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Quiz App: HTTP 200" -ForegroundColor Green
} catch {
    Write-Host "✗ Quiz failed" -ForegroundColor Red
    $allSuccess = $false
}

Write-Host "" -ForegroundColor Green

if ($allSuccess) {
    Write-Host "SUCCESS: Service is operational!" -ForegroundColor Green
} else {
    Write-Host "Some endpoints not responding" -ForegroundColor Yellow
}

