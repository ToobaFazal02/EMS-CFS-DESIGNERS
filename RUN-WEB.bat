@echo off
title EMS - Web (port 5173)
cd /d "D:\imp\ems-cfs-designers\apps\web"

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5174 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo.
echo  Web running: http://127.0.0.1:5173
echo  Login there. Leave this window OPEN.
echo.
call npm run dev -- --host 127.0.0.1 --port 5173
pause
