@echo off
title EMS - Kill port 8000 + start API
cd /d "D:\imp\ems-cfs-designers\apps\api"

echo Killing anything on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do taskkill /F /PID %%a >nul 2>&1

REM Orphan uvicorn / multiprocessing children from --reload
wmic process where "CommandLine like '%%uvicorn%%app.main%%'" call terminate >nul 2>&1
wmic process where "CommandLine like '%%multiprocessing.spawn%%'" call terminate >nul 2>&1

timeout /t 2 /nobreak >nul

echo.
echo  Starting clean API (no reload)...
echo  Check: http://127.0.0.1:8000/api/v1/health
echo  Must show: report_version phase5-complete
echo.
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
