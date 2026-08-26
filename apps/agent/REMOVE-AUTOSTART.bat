@echo off
title Remove EMS Agent Autostart
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\CFS Designers Agent.lnk"
if exist "%LNK%" (
  del "%LNK%"
  echo Autostart removed.
) else (
  echo No autostart shortcut found.
)
pause
