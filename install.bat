@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   CaptionFoundry - Installation
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Python %PYVER% detected

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

:: Get Node.js version
for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODEVER=%%i
echo [OK] Node.js %NODEVER% detected

:: Check if venv exists
if exist "venv" (
    echo [INFO] Virtual environment already exists
    set /p RECREATE="Do you want to recreate it? (y/N): "
    if /i "!RECREATE!"=="y" (
        echo [INFO] Removing existing venv...
        rmdir /s /q venv
    ) else (
        goto :install_deps
    )
)

:: Create virtual environment
echo.
echo [INFO] Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

:install_deps
:: Activate venv and install dependencies
echo.
echo [INFO] Installing Python dependencies...
call venv\Scripts\activate.bat

pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

:: Install Node.js dependencies (Electron)
echo.
echo [INFO] Installing Node.js dependencies (Electron)...
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)
echo [OK] Node.js dependencies installed

:: Create config from template if not exists
if not exist "config\settings.yaml" (
    echo.
    echo [INFO] Creating default configuration...
    copy "config\settings.yaml.template" "config\settings.yaml" >nul
    echo [OK] Configuration file created at config\settings.yaml
)

:: Create data directories
echo.
echo [INFO] Creating data directories...
if not exist "data\thumbnails" mkdir "data\thumbnails"
if not exist "data\exports" mkdir "data\exports"
if not exist "data\logs" mkdir "data\logs"
echo [OK] Data directories created

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo To start CaptionFoundry, run: start.bat
echo.
echo Configuration: config\settings.yaml
echo Database: data\captionforge.db (created on first run)
echo.

pause