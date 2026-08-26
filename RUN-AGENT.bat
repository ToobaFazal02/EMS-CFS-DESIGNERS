@echo off
title EMS - Agent
cd /d "D:\imp\ems-cfs-designers\apps\agent"

set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo ERROR: Agent venv missing.
  echo Run once in this folder:
  echo   python -m venv .venv
  echo   .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)

echo.
echo  Opening Agent as Administrator...
echo  UAC popup - click YES.
echo  Agent window will appear on taskbar (this window can stay or close).
echo.
powershell -NoProfile -Command "Start-Process -FilePath '%PY%' -ArgumentList '-m','ems_agent' -Verb RunAs -WorkingDirectory '%CD%'"
pause
