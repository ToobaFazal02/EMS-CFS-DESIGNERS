@echo off
title CFS Designers - prepare Agent folder for office PCs
cd /d "%~dp0"

set "DEST=%USERPROFILE%\Desktop\CFS-Agent-Install"
if exist "%DEST%" rd /s /q "%DEST%"

if exist "dist-handover\CFS-Designers-Agent\CFS-Designers-Agent.exe" (
  echo Copying standalone exe pack (no Python on employee PCs)...
  xcopy /E /I /Q /Y "dist-handover\CFS-Designers-Agent" "%DEST%" >nul
  goto add_docs
)
if exist "dist-ui2\CFS-Designers-Agent\CFS-Designers-Agent.exe" (
  echo Copying standalone exe pack (no Python on employee PCs)...
  xcopy /E /I /Q /Y "dist-ui2\CFS-Designers-Agent" "%DEST%" >nul
  goto add_docs
)
if exist "dist-fresh\CFS-Designers-Agent\CFS-Designers-Agent.exe" (
  echo Copying standalone exe pack (no Python on employee PCs)...
  xcopy /E /I /Q /Y "dist-fresh\CFS-Designers-Agent" "%DEST%" >nul
  goto add_docs
)
if exist "dist\CFS-Designers-Agent\CFS-Designers-Agent.exe" (
  echo Copying standalone exe pack (no Python on employee PCs)...
  xcopy /E /I /Q /Y "dist\CFS-Designers-Agent" "%DEST%" >nul
  goto add_docs
)

echo No exe yet. Run BUILD-EXE.bat on this PC first for a no-Python pack.
mkdir "%DEST%"
mkdir "%DEST%\ems_agent"
xcopy /E /I /Q /Y "ems_agent" "%DEST%\ems_agent" >nul
copy /Y "INSTALL-AGENT.bat" "%DEST%\" >nul
copy /Y "START-AGENT.bat" "%DEST%\" >nul
copy /Y "REMOVE-AUTOSTART.bat" "%DEST%\" >nul
copy /Y "Run-As-Administrator.bat" "%DEST%\" >nul
copy /Y "requirements.txt" "%DEST%\" >nul
copy /Y "config.production.json" "%DEST%\config.json" >nul
copy /Y "create-shortcuts.ps1" "%DEST%\" >nul
if exist "assets" xcopy /E /I /Q /Y "assets" "%DEST%\assets" >nul

:add_docs
if exist "EMPLOYEE-INSTALL.txt" copy /Y "EMPLOYEE-INSTALL.txt" "%DEST%\" >nul

:done

echo.
echo  Folder ready:
echo  %DEST%
echo.
echo  Copy this folder to each employee PC.
echo  Do NOT copy .venv or agent_data from your own PC.
echo.
pause
