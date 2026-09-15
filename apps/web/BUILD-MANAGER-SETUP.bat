@echo off
setlocal EnableExtensions
title CFS Manager Setup Build
cd /d "%~dp0"

echo ============================================================
echo   Building Manager Setup.exe (15-30 min)
echo   Do NOT close. Close Chrome/Docker first.
echo ============================================================
echo.

REM Kill lingering processes
taskkill /IM rustc.exe /F >nul 2>&1
taskkill /IM cargo.exe /F >nul 2>&1
taskkill /IM link.exe /F >nul 2>&1
taskkill /IM app.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

echo [1/4] Wiping old target...
if exist "src-tauri\target" rd /s /q "src-tauri\target"

echo [2/4] Frontend...
call npm run build
if errorlevel 1 (
  echo FRONTEND FAILED
  pause
  exit /b 1
)

echo [3/4] Rust compile...
cd src-tauri
set "CARGO_BUILD_JOBS=1"
set "CARGO_INCREMENTAL=0"
cargo build --release
if errorlevel 1 (
  echo CARGO FAILED
  cd ..
  pause
  exit /b 1
)
cd ..

echo [4/4] Bundle NSIS Setup...
call npx tauri build --bundles nsis
if errorlevel 1 (
  echo BUNDLE FAILED
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   SUCCESS - Setup.exe:
dir /b "src-tauri\target\release\bundle\nsis\*.exe"
echo   Full path:
echo   %CD%\src-tauri\target\release\bundle\nsis\
echo ============================================================
pause
