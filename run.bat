@echo off
title JanSahayak AI
echo ===================================================
echo   Starting JanSahayak AI (Integrated Server)
echo ===================================================
echo.
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in backend\.venv.
    pause
    exit /b 1
)

if not exist "frontend\dist" (
    echo [INFO] Building frontend production bundle...
    cd frontend
    call npm run build
    cd ..
)

echo [INFO] Opening http://localhost:8000 in your browser...
start "" "http://localhost:8000"

echo [INFO] Starting FastAPI server on port 8000...
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
