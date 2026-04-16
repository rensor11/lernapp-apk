# Docker + Home Assistant Installation Script
$ErrorActionPreference = "SilentlyContinue"

Write-Host "==========================================" 
Write-Host "DOCKER INSTALLATION & HOME ASSISTANT SETUP"
Write-Host "==========================================="
Write-Host ""

# Check Docker
Write-Host "[1] Checking Docker Installation..." -ForegroundColor Yellow
$dockerExists = Get-Command docker -ErrorAction SilentlyContinue

if ($dockerExists) {
    Write-Host "[OK] Docker is installed" -ForegroundColor Green
    docker --version
} else {
    Write-Host "[FAIL] Docker not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "PLEASE INSTALL DOCKER MANUALLY:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1 - Chocolatey:" -ForegroundColor Cyan
    Write-Host "  choco install docker-desktop -y"
    Write-Host ""
    Write-Host "Option 2 - WinGet:" -ForegroundColor Cyan
    Write-Host "  winget install Docker.DockerDesktop"
    Write-Host ""
    Write-Host "Option 3 - Manual Download:" -ForegroundColor Cyan
    Write-Host "  https://www.docker.com/products/docker-desktop"
    Write-Host ""
    Write-Host "After install: Start Docker Desktop app and run this script again"
    Write-Host ""
    exit 1
}

# Check Docker Daemon
Write-Host ""
Write-Host "[2] Checking Docker Daemon..." -ForegroundColor Yellow
$dockerInfo = docker info 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Docker Daemon is running" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Docker Daemon is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop app and try again"
    exit 1
}

# Check Home Assistant Image
Write-Host ""
Write-Host "[3] Checking Home Assistant Image..." -ForegroundColor Yellow
$haExists = docker images | Select-String "homeassistant/home-assistant"

if ($haExists) {
    Write-Host "[OK] Home Assistant image exists" -ForegroundColor Green
} else {
    Write-Host "[INFO] Downloading Home Assistant image (5-10 min)..." -ForegroundColor Yellow
    docker pull homeassistant/home-assistant:latest
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Home Assistant image downloaded" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Error downloading image" -ForegroundColor Red
        exit 1
    }
}

# Start Home Assistant Container
Write-Host ""
Write-Host "[4] Starting Home Assistant Container..." -ForegroundColor Yellow

# Stop existing container
docker stop homeassistant -q 2>$null
docker rm homeassistant -q 2>$null

# Create config directory
$containerDir = "C:\homeassistant_config"
New-Item -Path $containerDir -ItemType Directory -Force | Out-Null

Write-Host "Running Docker command..."
docker run -d `
  --name homeassistant `
  -p 8123:8123 `
  -e TZ=Europe/Berlin `
  -v ${containerDir}:/config `
  homeassistant/home-assistant:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Container started" -ForegroundColor Green
    Write-Host ""
    Write-Host "[INFO] Waiting 30 seconds for Home Assistant to boot..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    Write-Host ""
    Write-Host "[SUCCESS] Home Assistant is now running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Open browser: http://localhost:8123" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Create account"
    Write-Host "  2. Add Fritz!Box integration"
    Write-Host "  3. Generate API token"
    Write-Host ""
} else {
    Write-Host "[FAIL] Error starting container" -ForegroundColor Red
    docker logs homeassistant
    exit 1
}
