@echo off
cd /d "%~dp0apps\api"
echo Clearing SAMPLE / AUDIT demo data (keeps admin + staff logins)...
call .venv\Scripts\python.exe -m app.clear_samples
echo.
pause
