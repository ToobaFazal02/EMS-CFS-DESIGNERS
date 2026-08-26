@echo off
title EMS Agent — Install + Autostart
cd /d "%~dp0"

echo ============================================
echo   CFS Designers — Agent Setup
echo ============================================
echo.

if not exist .venv\Scripts\python.exe (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Python not found. Install Python 3.11+ first.
    pause
    exit /b 1
  )
  .venv\Scripts\pip install -r requirements.txt
)

set "PY=%CD%\.venv\Scripts\pythonw.exe"
if not exist "%PY%" set "PY=%CD%\.venv\Scripts\python.exe"

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "LNK=%STARTUP%\CFS Designers Agent.lnk"

echo Creating Startup shortcut so agent opens after Windows login...
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%LNK%'); $s.TargetPath = '%PY%'; $s.Arguments = '-m ems_agent'; $s.WorkingDirectory = '%CD%'; $s.WindowStyle = 1; $s.Description = 'CFS Designers Agent'; $s.Save()"

echo.
echo  Done.
echo  - Autostart: ON (this Windows user)
echo  - Shortcut:  %LNK%
echo.
echo  Launch agent now?
choice /C YN /M "Start agent"
if errorlevel 2 goto end
if errorlevel 1 start "" "%PY%" -m ems_agent

:end
echo.
pause
