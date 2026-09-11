@echo off
setlocal EnableExtensions
title CFS Designers Agent - Install
cd /d "%~dp0"

echo ================================================================================
echo   CFS Designers - Agent Setup
echo ================================================================================
echo.

REM WinRAR / 7-Zip "Open inside archive" only extracts this .bat to a temp folder.
REM The real CFS-Designers-Agent.exe is missing there - always EXTRACT the zip first.
echo %CD% | find /I "Rar$" >nul && goto need_extract
echo %CD% | find /I "\Temp\" >nul
if errorlevel 1 goto check_exe
if not exist "%CD%\CFS-Designers-Agent.exe" if not exist "%CD%\_internal" goto need_extract

:check_exe
if exist "%CD%\CFS-Designers-Agent.exe" goto exe_install
if exist "%CD%\dist\CFS-Designers-Agent\CFS-Designers-Agent.exe" (
  echo Move the whole CFS-Designers-Agent folder, not only this bat.
  pause
  exit /b 1
)

echo.
echo  ERROR: CFS-Designers-Agent.exe not found in this folder.
echo.
echo  Fix:
echo    1. Close this window.
echo    2. Right-click CFS-Agent-Install.zip - Extract All...
echo       (Do NOT double-click INSTALL-AGENT.bat inside WinRAR.)
echo    3. Open the extracted CFS-Agent-Install folder.
echo    4. Double-click INSTALL-AGENT.bat there.
echo.
pause
exit /b 1

:need_extract
echo.
echo  ERROR: You opened INSTALL-AGENT.bat from inside WinRAR / a temp folder.
echo  That does not include CFS-Designers-Agent.exe - install cannot work this way.
echo.
echo  Correct steps:
echo    1. Click No / Cancel on any WinRAR "put files back into archive" prompt.
echo    2. Right-click CFS-Agent-Install.zip - Extract All...
echo    3. Open the new CFS-Agent-Install folder on disk.
echo    4. Double-click INSTALL-AGENT.bat
echo.
pause
exit /b 1

:exe_install
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

echo Found CFS-Designers-Agent.exe - no Python needed.
set "TARGET=%CD%\CFS-Designers-Agent.exe"
set "ARGS=NONE"
if not exist "%CD%\config.json" if exist "%CD%\config.production.json" copy /Y "%CD%\config.production.json" "%CD%\config.json" >nul

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
if errorlevel 1 start "" "%TARGET%"

:end
echo.
pause
