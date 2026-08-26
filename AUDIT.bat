@echo off
title CFS Designers — Functional audit
cd /d "D:\imp\ems-cfs-designers\apps\api"
echo.
echo  Running automated API audit (login, samples, gates, reports)...
echo.
.venv\Scripts\python.exe -m app.audit
echo.
pause
