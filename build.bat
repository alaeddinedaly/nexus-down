@echo off
REM NexusDown Build Script
REM This script builds the executable using PyInstaller

echo ========================================
echo NexusDown Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller is not installed!
    echo Installing PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Check if Pillow is installed (for icon creation)
pip show pillow >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing Pillow for icon creation...
    pip install pillow
)

REM Create icon if it doesn't exist
if not exist "icon.ico" (
    echo [INFO] Creating application icon...
    python create_icon.py
    if %errorlevel% neq 0 (
        echo [WARNING] Failed to create icon, continuing without it...
    )
)

REM Clean previous builds
echo [INFO] Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "__pycache__" rmdir /s /q __pycache__

REM Build the executable
echo [INFO] Building executable...
echo.
pyinstaller --clean NexusDown.spec

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\NexusDown.exe
echo.
echo You can now:
echo 1. Run dist\NexusDown.exe directly
echo 2. Create an installer using Inno Setup (see installer.iss)
echo.
pause