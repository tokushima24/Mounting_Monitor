@echo off
REM ============================================
REM Swine Monitor - Windows Build Script (uv)
REM ============================================
REM Usage: scripts\build_windows.bat (from project root)
REM ============================================

echo.
echo ========================================
echo   Swine Monitor Build Script (uv)
echo ========================================
echo.

REM Change to project root
cd /d "%~dp0\.."
echo Working directory: %CD%

REM Check uv installation
echo [0/5] Checking uv installation...
uv --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] uv is not installed or not in PATH
    echo.
    echo Please install uv using one of these methods:
    echo.
    echo Method 1 (PowerShell - Recommended):
    echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 ^| iex"
    echo.
    echo Method 2 (pip):
    echo   pip install uv
    echo.
    echo Method 3 (pipx):
    echo   pipx install uv
    echo.
    echo See BUILD_GUIDE.md for detailed instructions.
    echo.
    pause
    exit /b 1
)

uv --version
echo uv detected successfully.

REM Create/sync virtual environment
echo [1/5] Creating/syncing virtual environment with uv...
if not exist ".venv" (
    echo Creating new virtual environment...
    uv venv
)

REM Sync dependencies
echo [2/5] Installing dependencies...
uv pip install -r requirements.txt

REM Install PyInstaller
echo [3/5] Installing PyInstaller...
uv pip install pyinstaller

REM Clean previous builds
if exist "dist\SwineMonitor" rmdir /s /q "dist\SwineMonitor"
if exist "build" rmdir /s /q "build"

REM Build executable using uv run
echo [4/5] Building executable...
uv run pyinstaller scripts\build.spec --clean

REM Create distribution folder
echo [5/5] Creating distribution package...
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
