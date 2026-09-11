@echo off
setlocal EnableExtensions
title CFS Designers - Rebuild Manager with Official Icon
cd /d "%~dp0"
echo.
echo ============================================================
echo   CFS Designers Manager - Icon Rebuild
echo   This compiles a fresh app.exe with the official monogram.
echo   Takes 5-15 minutes. Do NOT close this window.
echo ============================================================
echo.

REM Confirm icons exist
if not exist "src-tauri\icons\icon.ico" (
  echo ERROR: src-tauri\icons\icon.ico not found. Run from apps\web folder.
  pause & exit /b 1
)

REM Kill running Manager
taskkill /IM app.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

REM Force full fresh build — set target dir locally so Cursor sandbox cache is ignored
set "CARGO_TARGET_DIR=%~dp0src-tauri\target"
set "CARGO_INCREMENTAL=0"

echo [1/3] Building frontend (npm run build)...
call npm run build
if errorlevel 1 ( echo FRONTEND BUILD FAILED & pause & exit /b 1 )

echo.
echo [2/3] Compiling Rust binary with new icon (this takes a few minutes)...
cd src-tauri
cargo build --release
if errorlevel 1 ( echo CARGO BUILD FAILED & pause & exit /b 1 )
cd ..

echo.
echo [3/3] Installing new app.exe...
set "INSTALL_DIR=%LOCALAPPDATA%\CFS Designers"
set "SRC_EXE=%~dp0src-tauri\target\release\app.exe"
set "DEST_EXE=%INSTALL_DIR%\app.exe"

if not exist "%SRC_EXE%" (
  echo ERROR: Build output not found at %SRC_EXE%
  pause & exit /b 1
)

REM Copy new exe over installed one
copy /Y "%SRC_EXE%" "%DEST_EXE%"
if errorlevel 1 ( echo COPY FAILED - is app.exe open? & pause & exit /b 1 )

REM Update desktop shortcut icon
set "ICO=%INSTALL_DIR%\app-icon.ico"
copy /Y "src-tauri\icons\icon.ico" "%ICO%" >nul

REM Clear Windows icon cache
taskkill /F /IM explorer.exe >nul 2>&1
timeout /t 2 /nobreak >nul
del /f /q "%LOCALAPPDATA%\IconCache.db" >nul 2>&1
del /f /q "%LOCALAPPDATA%\Microsoft\Windows\Explorer\iconcache*" >nul 2>&1
start explorer.exe

echo.
echo ============================================================
echo   DONE! New app.exe installed with official monogram icon.
echo.
echo   Now do this (takes 10 seconds):
echo     1. Right-click CFS Designers in taskbar >> Unpin
echo     2. Open CFS Designers from Start Menu
echo     3. Right-click it in taskbar >> Pin to taskbar
echo ============================================================
echo.
echo Launching CFS Designers Manager...
start "" "%DEST_EXE%"
pause
