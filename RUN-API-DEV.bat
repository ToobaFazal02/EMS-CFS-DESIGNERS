@echo off
title EMS - API DEV (auto-reload)
cd /d "D:\imp\ems-cfs-designers\apps\api"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
echo DEV mode with --reload. For client demo use RUN-API.bat instead.
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
