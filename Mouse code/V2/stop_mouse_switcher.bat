@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo Stopping Windows Mouse Screen Switcher...
powershell -Command "Get-CimInstance Win32_Process -Filter \"name='pythonw.exe' and CommandLine like '%mouse_switcher.py%'\" | Remove-CimInstance" >nul 2>&1
echo Done.
ping 127.0.0.1 -n 3 >nul
exit /b
