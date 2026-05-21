$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root "escrow_platform"
$FrontendDir = Join-Path $Root "frontend"
$BackendUrl = "http://127.0.0.1:8000/api/health/"
$FrontendUrl = "http://127.0.0.1:5173/"

Write-Host "Starting GigWay fullstack dev environment..."
Write-Host ""

if (-not (Test-Path (Join-Path $BackendDir "manage.py"))) {
    throw "Backend not found at $BackendDir."
}

if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
    throw "Frontend not found at $FrontendDir."
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found on PATH."
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js was not found on PATH."
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $FrontendDir
    try {
        & npm.cmd install
    }
    finally {
        Pop-Location
    }
}

$Port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($Port8000) {
    throw "Port 8000 is already in use. Run stop-dev.cmd first, then try again."
}

$Port5173 = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
if ($Port5173) {
    throw "Port 5173 is already in use. Run stop-dev.cmd first, then try again."
}

Write-Host "Starting backend at http://127.0.0.1:8000/"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k python manage.py runserver 127.0.0.1:8000 --noreload" -WorkingDirectory $BackendDir -WindowStyle Normal

Write-Host "Starting frontend at http://127.0.0.1:5173/"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k npm.cmd run dev -- --host 127.0.0.1" -WorkingDirectory $FrontendDir -WindowStyle Normal

Write-Host ""
Write-Host "Give both windows a few seconds to finish starting."
Write-Host "Frontend: $FrontendUrl"
Write-Host "Backend health: $BackendUrl"
Write-Host ""
Write-Host "Close the two server windows to stop the dev environment."
