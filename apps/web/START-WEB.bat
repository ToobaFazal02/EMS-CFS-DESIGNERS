@echo off
REM CFS Designers — start Web (port 5173)
cd /d "%~dp0"
echo Starting Web on http://127.0.0.1:5173 ...
call npm run dev -- --host 127.0.0.1 --port 5173
pause
