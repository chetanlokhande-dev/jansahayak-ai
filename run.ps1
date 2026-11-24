# JanSahayak AI - Integrated Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   Starting JanSahayak AI (Integrated Server)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot

if (-not (Test-Path "backend\.venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Virtual environment not found in backend\.venv" -ForegroundColor Red
    Exit 1
}

if (-not (Test-Path "frontend\dist")) {
    Write-Host "[INFO] Building frontend production bundle..." -ForegroundColor Yellow
    Set-Location frontend
    npm run build
    Set-Location $PSScriptRoot
}

Write-Host "[INFO] Opening http://localhost:8000 in your browser..." -ForegroundColor Green
Start-Process "http://localhost:8000"

Write-Host "[INFO] Starting server on port 8000..." -ForegroundColor Green
& "backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
