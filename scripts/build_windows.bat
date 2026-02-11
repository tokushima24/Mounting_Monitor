@echo off
REM ============================================
REM Swine Monitor - Windows Build Script
REM ============================================
REM Usage: scripts\build_windows.bat (from project root)
REM ============================================

echo.
echo ========================================
echo   Swine Monitor Build Script
echo ========================================
echo.

REM Change to project root
cd /d "%~dp0\.."
echo Working directory: %CD%

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check pip packages
echo [1/4] Checking dependencies...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Install project dependencies
echo [2/4] Installing project dependencies...
pip install -r requirements.txt

REM Clean previous builds
if exist "dist\SwineMonitor" rmdir /s /q "dist\SwineMonitor"
if exist "build" rmdir /s /q "build"

REM Build executable
echo [3/4] Building executable...
pyinstaller scripts\build.spec --clean

REM Create distribution folder
echo [4/4] Creating distribution package...
if not exist "dist\SwineMonitor" (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

REM Copy additional files
copy config.yaml.template dist\SwineMonitor\config.yaml
copy .env.template dist\SwineMonitor\.env

REM Create data directories
mkdir dist\SwineMonitor\data 2>nul
mkdir dist\SwineMonitor\data\images 2>nul
mkdir dist\SwineMonitor\models 2>nul
mkdir dist\SwineMonitor\logs 2>nul

REM Copy model if exists
if exist "models\yolo11s.pt" (
    copy models\yolo11s.pt dist\SwineMonitor\models\
    echo   - YOLO model copied
) else (
    echo   - Warning: No YOLO model found
)

if exist "models\yolo_best.pt" (
    copy models\yolo_best.pt dist\SwineMonitor\models\
    echo   - YOLO model copied
) else (
    echo   - Warning: No YOLO model found
)

REM Copy README
copy docs\SETUP_WINDOWS.md dist\SwineMonitor\README.txt 2>nul

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo Distribution folder: dist\SwineMonitor
echo.
echo Next steps:
echo   1. Copy your YOLO model to: dist\SwineMonitor\models\
echo   2. Edit dist\SwineMonitor\config.yaml
echo   3. Edit dist\SwineMonitor\.env
echo   4. Run dist\SwineMonitor\SwineMonitor.exe
echo.
pause
