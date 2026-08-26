@echo off
echo ============================================
echo   EMS - Start API + Web (2 windows only)
echo   Agent: double-click RUN-AGENT.bat yourself
echo ============================================
start "EMS API" cmd /k "D:\imp\ems-cfs-designers\RUN-API.bat"
timeout /t 4 /nobreak >nul
start "EMS Web" cmd /k "D:\imp\ems-cfs-designers\RUN-WEB.bat"
echo.
echo  WEB (manager):  http://127.0.0.1:5173
echo  AGENT (employee PC): double-click RUN-AGENT.bat
echo.
pause
