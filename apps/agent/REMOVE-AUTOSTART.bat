@echo off
title Remove CFS Designers Agent shortcuts
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\CFS Designers Agent.lnk"
set "MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\CFS Designers\CFS Designers Agent.lnk"
set "DESK=%USERPROFILE%\Desktop\CFS Designers Agent.lnk"
if exist "%STARTUP%" del "%STARTUP%"
if exist "%MENU%" del "%MENU%"
if exist "%DESK%" del "%DESK%"
echo Shortcuts removed (Desktop / Start Menu / Startup).
pause
