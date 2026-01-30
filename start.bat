@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   CaptionFoundry - Starting Desktop App
echo ========================================
echo.

:: Check if venv exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

:: Check if node_modules exists
if not exist "node_modules" (
    echo [ERROR] Node.js dependencies not installed
    echo Please run install.bat first
    pause
    exit /b 1
)

:: Check if config exists
if not exist "config\settings.yaml" (
    echo [WARNING] Configuration file not found
    echo Copying template...
    copy "config\settings.yaml.template" "config\settings.yaml" >nul
)

echo [INFO] Starting CaptionFoundry...
echo.

:: Start the Electron app (which will spawn the Python backend)
call npm start

pause