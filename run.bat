@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   Internal Assessment Marks Management System - Launcher
echo ========================================================
echo.

:: 1. SEARCH FOR PYTHON
set "PY_CMD="

:: Try standard commands first
where python >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD (
    where py >nul 2>nul && set "PY_CMD=py"
)

:: Try the last known success path if others fail
if not defined PY_CMD (
    set "KNOWN_PATH=C:\Users\Dell\AppData\Local\Programs\Python\Python315\python.exe"
    if exist "!KNOWN_PATH!" (
        set "PY_CMD=!KNOWN_PATH!"
    )
)

if not defined PY_CMD (
    echo [ERROR] Python not found automatically.
    echo Please ensure Python 3.x is installed.
    pause
    exit /b
)

echo [✓] Using Python: %PY_CMD%
echo.

:: 2. VERIFY DEPENDENCIES
echo [1/2] Checking dependencies...
"%PY_CMD%" -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo [!] Note: Some dependencies might need manual installation or internet check.
)

:: 3. START APP
echo [2/2] Starting backend server (Powering up)...
echo.
echo ========================================================
echo   SERVER IS STARTING...
echo.
echo   1. Keep this window OPEN while using the app.
echo   2. Open your browser to: http://localhost:5000
echo.
echo ========================================================
echo.

cd backend
"%PY_CMD%" app.py

pause
