@echo off
setlocal EnableExtensions
title CFS Designers - Build Manager Setup (OOM-safe)
cd /d "%~dp0"

echo.
echo ============================================================
echo   Manager Setup.exe — low-RAM build
echo   CLOSE Chrome, Docker, Cursor heavy tabs first.
echo   Do NOT close this window (15-30 min).
echo ============================================================
echo.

taskkill /IM rustc.exe /F >nul 2>&1
taskkill /IM cargo.exe /F >nul 2>&1
taskkill /IM link.exe /F >nul 2>&1
taskkill /IM app.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

echo [1/5] Wiping Rust target (kills corrupt 4GB rlib)...
if exist "src-tauri\target" rd /s /q "src-tauri\target"

echo [2/5] Low-RAM env...
set "CARGO_BUILD_JOBS=1"
set "CARGO_INCREMENTAL=0"
set "CARGO_TERM_PROGRESS_WHEN=always"

echo [3/5] Frontend build...
call npm run build
if errorlevel 1 (
  echo FRONTEND FAILED
  pause
  exit /b 1
)

echo [4/5] Cargo release (lib then bin) — watch for OOM...
cd src-tauri
cargo build --release -j 1
if errorlevel 1 (
  echo CARGO FAILED
  cd ..
  pause
  exit /b 1
)

REM Fail fast if rlib is absurdly huge again (corrupt)
for %%F in ("target\release\deps\libapp_lib.rlib") do (
  if %%~zF GTR 200000000 (
    echo ERROR: libapp_lib.rlib is %%~zF bytes — corrupt again. Restart PC and retry.
    cd ..
    pause
    exit /b 1
  )
  echo OK rlib size=%%~zF bytes
)
cd ..

echo [5/5] Bundle NSIS Setup only (no MSI)...
call npx tauri build --bundles nsis
if errorlevel 1 (
  echo BUNDLE FAILED
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   SUCCESS — Setup.exe:
dir /b "src-tauri\target\release\bundle\nsis\*.exe"
echo   Full path:
echo   %CD%\src-tauri\target\release\bundle\nsis\
echo ============================================================
pause
