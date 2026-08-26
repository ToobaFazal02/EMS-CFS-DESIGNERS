@echo off
REM Kill stale EMS API on port 8000, then start fresh with reload
cd /d "%~dp0"

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do (
  echo Stopping old process on port 8000 PID %%a ...
  taskkill /PID %%a /F >nul 2>&1
)

if not exist .venv\Scripts\python.exe (
  echo Create venv first: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)

echo Starting API on http://127.0.0.1:8000 ...
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
