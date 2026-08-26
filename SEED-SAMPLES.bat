@echo off
title CFS Designers — Seed SAMPLE data
cd /d "D:\imp\ems-cfs-designers\apps\api"
echo.
echo  Seeding SAMPLE clients / projects / invoices...
echo  (Summit LGS paid 50%% + Harbour Frames unpaid)
echo.
.venv\Scripts\python.exe -m app.seed
echo.
echo  Done. Restart API (RUN-API.bat), then open Projects + Payments.
pause
