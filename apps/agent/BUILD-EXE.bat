@echo off
setlocal
title CFS Designers - build Agent exe
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
  echo Creating build venv...
  python -m venv .venv
  if errorlevel 1 (
    echo Python required on THIS PC to build the exe. Employees will not need Python.
    pause
    exit /b 1
  )
)
.venv\Scripts\pip install -q -r requirements.txt pyinstaller
if errorlevel 1 (
  echo pip failed
  pause
  exit /b 1
)

echo Building windowed exe (a few minutes)...
.venv\Scripts\pyinstaller --noconfirm --clean cfs-agent.spec
if errorlevel 1 (
  echo Build failed
  pause
  exit /b 1
)

copy /Y config.production.json "dist\CFS-Designers-Agent\config.json" >nul
copy /Y INSTALL-AGENT.bat "dist\CFS-Designers-Agent\" >nul
copy /Y EMPLOYEE-INSTALL.txt "dist\CFS-Designers-Agent\" >nul
copy /Y create-shortcuts.ps1 "dist\CFS-Designers-Agent\" >nul
copy /Y REMOVE-AUTOSTART.bat "dist\CFS-Designers-Agent\" >nul
if exist assets xcopy /E /I /Q /Y assets "dist\CFS-Designers-Agent\assets" >nul

echo.
echo  EXE ready:
echo  %CD%\dist\CFS-Designers-Agent\
echo  Zip THAT folder and send to the office. They only run INSTALL-AGENT.bat
echo  No Python on employee PCs.
echo.
pause
