@echo off
setlocal
title CFS Designers Agent - Install
cd /d "%~dp0"

echo ============================================
echo   CFS Designers - Agent Setup
echo ============================================
echo.

set "ICON=%CD%\assets\cfs-agent.ico"
if not exist "%ICON%" set "ICON=%CD%\CFS-Designers-Agent.exe"
if not exist "%ICON%" set "ICON=%CD%\assets\cfs-logo.png"

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\CFS Designers"
set "DESKTOP=%USERPROFILE%\Desktop"
if not exist "%STARTMENU%" mkdir "%STARTMENU%"

set "LNK_STARTUP=%STARTUP%\CFS Designers Agent.lnk"
set "LNK_MENU=%STARTMENU%\CFS Designers Agent.lnk"
set "LNK_DESK=%DESKTOP%\CFS Designers Agent.lnk"

if exist "%CD%\CFS-Designers-Agent.exe" goto exe_install
if exist "%CD%\dist\CFS-Designers-Agent\CFS-Designers-Agent.exe" (
  echo Move the whole CFS-Designers-Agent folder, not only this bat.
  pause
  exit /b 1
)

echo This pack has no .exe. Trying Python setup...
if not exist .venv\Scripts\python.exe (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Python not found. Ask the office for CFS-Designers-Agent.exe pack.
    pause
    exit /b 1
  )
  .venv\Scripts\pip install -r requirements.txt
  if errorlevel 1 (
    echo Package install failed.
    pause
    exit /b 1
  )
)
set "TARGET=%CD%\.venv\Scripts\pythonw.exe"
if not exist "%TARGET%" set "TARGET=%CD%\.venv\Scripts\python.exe"
set "ARGS=-m ems_agent"
goto make_links

:exe_install
echo Found CFS-Designers-Agent.exe - no Python needed.
set "TARGET=%CD%\CFS-Designers-Agent.exe"
set "ARGS=NONE"
if not exist "%CD%\config.json" if exist "%CD%\config.production.json" copy /Y "%CD%\config.production.json" "%CD%\config.json" >nul

:make_links
echo Creating Desktop, Start Menu, and Startup shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create-shortcuts.ps1" -Python "%TARGET%" -WorkDir "%CD%" -Icon "%ICON%" -StartupLink "%LNK_STARTUP%" -MenuLink "%LNK_MENU%" -DesktopLink "%LNK_DESK%" -Arguments "%ARGS%"
if errorlevel 1 (
  echo Shortcut creation failed.
  pause
  exit /b 1
)

echo.
echo  Done. No extra black window.
echo  - Desktop:     CFS Designers Agent
echo  - Start Menu:  CFS Designers
echo  - Autostart:   ON
echo.
echo  Launch agent now?
choice /C YN /M "Start agent"
if errorlevel 2 goto end
if errorlevel 1 start "" "%TARGET%" %ARGS:NONE=%

:end
echo.
pause
