@echo off
echo ============================================================
echo   InspectionVision Multi-Model Detection System
echo   Installation Script
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher from python.org
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found:
python --version
echo.

REM Check Python version (requires Python 3.8+)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Detected Python version: %PYTHON_VERSION%
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [STEP 1/4] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
) else (
    echo [INFO] Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo [STEP 2/4] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated.
echo.

REM Upgrade pip
echo [STEP 3/4] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo [STEP 4/4] Installing dependencies from requirements.txt...
echo This may take several minutes depending on your internet connection...
echo.
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install some dependencies!
    echo Please check the error messages above and try again.
    pause
    exit /b 1
)
echo.

echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo To run the application:
echo   1. Run 'run.bat' from this folder, OR
echo   2. Manually activate the environment and run:
echo      - venv\Scripts\activate
echo      - python -m uvicorn app.main_multimodel:app --host 0.0.0.0 --port 8000
echo.
echo The application will be available at: http://localhost:8000
echo.
pause
