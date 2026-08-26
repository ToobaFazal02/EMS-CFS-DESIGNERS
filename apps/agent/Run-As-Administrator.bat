@echo off
REM CFS Designers — Agent (Run as Administrator)
REM Uses project venv so PySide6/pynput are available after UAC.
cd /d "%~dp0"

set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Venv missing. Run first:
  echo   python -m venv .venv
  echo   .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)

echo Launching EMS Agent as Administrator...
echo If UAC asks, click Yes. A separate window will open — this one can close.
powershell -NoProfile -Command "Start-Process -FilePath '%PY%' -ArgumentList '-m','ems_agent' -Verb RunAs -WorkingDirectory '%CD%'"
timeout /t 3 /nobreak >nul
echo Done. Look for the EMS Agent window on the taskbar.
