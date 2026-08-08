@echo off
title CamShow - 1-Click Installer & Setup
echo ====================================================
echo        CamShow Virtual Camera Setup & Installer
echo ====================================================
echo.

:: 1. Check Python Installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/3] Installing Python Dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Failed installing dependencies via pip. Trying user mode...
    python -m pip install --user -r requirements.txt
)

echo.
echo [2/3] Building CamShow.exe Executable...
python build_exe.py

echo.
echo [3/3] Setup Complete!
echo.
echo Launching CamShow.exe...
if exist "dist\CamShow.exe" (
    start "" "dist\CamShow.exe"
) else (
    python main.py
)

pause
