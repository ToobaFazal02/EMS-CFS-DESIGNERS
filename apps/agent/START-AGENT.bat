@echo off
REM CFS Designers — start Windows Agent
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Create venv first: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)
echo Starting Agent...
.venv\Scripts\python.exe -m ems_agent
pause
