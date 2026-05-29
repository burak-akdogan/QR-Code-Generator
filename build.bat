@echo off
setlocal EnableDelayedExpansion
title QR Code Generator - Builder

echo.
echo  ============================================
echo    QR Code Generator  ^|  Build to .EXE
echo  ============================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not found in PATH.
    echo          Download it from: https://www.python.org/downloads/
    echo          Make sure to tick "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo  [1/3] Installing dependencies...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies. Check your internet connection.
    pause
    exit /b 1
)

echo  [2/3] Installing PyInstaller...
pip install pyinstaller -q

echo  [3/3] Building executable (this may take 1-2 minutes)...
set PYINST=%APPDATA%\..\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts\pyinstaller.exe
python -m pyinstaller ^
    --onefile ^
    --windowed ^
    --name "QR Code Generator" ^
    --collect-data customtkinter ^
    main.py

echo.
if exist "dist\QR Code Generator.exe" (
    echo  ============================================
    echo    BUILD SUCCESSFUL!
    echo    Location: dist\QR Code Generator.exe
    echo  ============================================
    echo.
    echo  You can now distribute that single .exe file.
    echo  No Python or extra installs needed on target PC.
) else (
    echo  [ERROR] Build failed. Review the output above for details.
)

echo.
pause
