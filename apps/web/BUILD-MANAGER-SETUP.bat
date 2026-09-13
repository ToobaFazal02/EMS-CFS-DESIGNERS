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

echo [3/4] Rust (slow step, no progress bar)...
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

REM Check rlib size - corrupt if over 200MB
for %%F in ("target\release\deps\libapp_lib.rlib") do (
  set /a size_mb=%%~zF/1048576
  if %%~zF GTR 200000000 (
    echo ERROR: rlib corrupt (%%~zF bytes). Restart PC.
    cd ..
    pause
    exit /b 1
  )
  echo rlib OK: %%~zF bytes
)
cd ..

echo [4/4] NSIS bundle...
call npx tauri build --bundles nsis
if errorlevel 1 (
  echo BUNDLE FAILED
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   SUCCESS - Setup here:
dir /b "src-tauri\target\release\bundle\nsis\*.exe"
echo   %CD%\src-tauri\target\release\bundle\nsis\
echo ============================================================
pause
