@echo off
setlocal EnableExtensions
title CFS Designers - Build Manager Setup.exe
cd /d "%~dp0"

echo.
echo ============================================================
echo   Manager Setup build (fixes corrupt target after OOM)
echo   Close Chrome / Docker first. Do NOT close this window.
echo ============================================================
echo.

REM Stop leftover compilers that hold locks / eat RAM
taskkill /IM rustc.exe /F >nul 2>&1
taskkill /IM cargo.exe /F >nul 2>&1
taskkill /IM link.exe /F >nul 2>&1
taskkill /IM app.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

echo [1/4] Removing corrupt Rust build cache...
REM libapp_lib.rlib can become multi-GB garbage after OOM - must delete
if exist "src-tauri\target\release\deps\libapp_lib.rlib" del /f /q "src-tauri\target\release\deps\libapp_lib.rlib"
if exist "src-tauri\target\release\deps\app*" del /f /q "src-tauri\target\release\deps\app*"
if exist "src-tauri\target\release\app.exe" del /f /q "src-tauri\target\release\app.exe"
if exist "src-tauri\target\release\app.pdb" del /f /q "src-tauri\target\release\app.pdb"
if exist "src-tauri\target\release\app.lib" del /f /q "src-tauri\target\release\app.lib"
if exist "src-tauri\target\release\app.d" del /f /q "src-tauri\target\release\app.d"
if exist "src-tauri\target\release\.fingerprint\app-*" rd /s /q "src-tauri\target\release\.fingerprint" 2>nul
REM Incremental cache often corrupt after crash
if exist "src-tauri\target\release\incremental" rd /s /q "src-tauri\target\release\incremental"

echo [2/4] Low-RAM cargo settings...
set "CARGO_BUILD_JOBS=1"
set "CARGO_INCREMENTAL=0"

echo [3/4] Building frontend + Tauri (10-25 min)...
call npm run tauri:build
if errorlevel 1 (
  echo.
  echo BUILD FAILED. If OOM again: restart PC, close everything, run this bat again.
  pause
  exit /b 1
)

echo.
echo [4/4] Looking for Setup.exe...
set "NSIS=src-tauri\target\release\bundle\nsis"
if exist "%NSIS%" (
  dir /b "%NSIS%\*.exe"
  echo.
  echo Setup is here:
  echo   %CD%\%NSIS%\
) else (
  echo NSIS folder missing - build may have failed before bundle step.
)

echo.
echo DONE. Attach that Setup.exe to GitHub Release with Agent zip.
pause
