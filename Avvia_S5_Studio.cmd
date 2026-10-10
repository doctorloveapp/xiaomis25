@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0S5Studio-1.8.1.exe" (
  start "" "%~dp0S5Studio-1.8.1.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.8.exe" (
  start "" "%~dp0S5Studio-1.8.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.7.7.exe" (
  start "" "%~dp0S5Studio-1.7.7.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.7.6.exe" (
  start "" "%~dp0S5Studio-1.7.6.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.7.5.exe" (
  start "" "%~dp0S5Studio-1.7.5.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.7.4.exe" (
  start "" "%~dp0S5Studio-1.7.4.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.7.3.exe" (
  start "" "%~dp0S5Studio-1.7.3.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.7.2.exe" (
  start "" "%~dp0S5Studio-1.7.2.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.7.1.exe" (
  start "" "%~dp0S5Studio-1.7.1.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.7.exe" (
  start "" "%~dp0S5Studio-1.7.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.6.1.exe" (
  start "" "%~dp0S5Studio-1.6.1.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.6.exe" (
  start "" "%~dp0S5Studio-1.6.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.5.exe" (
  start "" "%~dp0S5Studio-1.5.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.4.1.exe" (
  start "" "%~dp0S5Studio-1.4.1.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.4.exe" (
  start "" "%~dp0S5Studio-1.4.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-1.3.exe" (
  start "" "%~dp0S5Studio-1.3.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-1.2.exe" (
  start "" "%~dp0S5Studio-1.2.exe"
  exit /b
)
if exist "%~dp0S5Studio-1.1.exe" (
  start "" "%~dp0S5Studio-1.1.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-1.0.exe" (
  start "" "%~dp0S5Studio-1.0.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-0.11.exe" (
  start "" "%~dp0S5Studio-0.11.exe"
  exit /b
)
if exist "%~dp0S5Studio-0.10.exe" (
  start "" "%~dp0S5Studio-0.10.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-0.9.exe" (
  start "" "%~dp0S5Studio-0.9.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-0.8.exe" (
  start "" "%~dp0S5Studio-0.8.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-0.7.exe" (
  start "" "%~dp0S5Studio-0.7.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-0.6.exe" (
  start "" "%~dp0S5Studio-0.6.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-0.5.exe" (
  start "" "%~dp0S5Studio-0.5.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-0.4.exe" (
  start "" "%~dp0S5Studio-0.4.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-0.3.exe" (
  start "" "%~dp0S5Studio-0.3.exe"
  exit /b 0
)
if exist "%~dp0S5Studio-0.2.exe" (
  start "" "%~dp0S5Studio-0.2.exe"
  exit /b 0
)
if exist "%~dp0S5Studio.exe" (
  start "" "%~dp0S5Studio.exe"
  exit /b 0
)
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 main.py
) else (
  python main.py
)
if errorlevel 1 pause
