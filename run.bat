@echo off
echo ============================================================
echo   InspectionVision Multi-Model Detection System
echo   Starting Application...
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run 'install.bat' first to set up the environment.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Check if model weights exist
if not exist "Weights_final\Corrosion_best.pt" (
    echo [WARNING] Corrosion model not found at: Weights_final\Corrosion_best.pt
)
if not exist "Weights_final\PPE_best.pt" (
    echo [WARNING] PPE model not found at: Weights_final\PPE_best.pt
)
if not exist "Weights_final\Inspection_best.pt" (
    echo [WARNING] Inspection model not found at: Weights_final\Inspection_best.pt
)
echo.

REM Create necessary directories if they don't exist
if not exist "static\uploads" mkdir static\uploads
if not exist "outputs" mkdir outputs
echo [INFO] Directory structure verified.
echo.

REM Start the application
echo [INFO] Starting FastAPI server...
echo.
echo ============================================================
echo   Application Starting...
echo   Access the dashboard at: http://localhost:8000
echo   API Documentation at: http://localhost:8000/docs
echo   Press CTRL+C to stop the server
echo ============================================================
echo.

python -m uvicorn app.main_multimodel:app --host 0.0.0.0 --port 8000 --reload

REM Check if the application exited with an error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with errors!
    echo Please check the error messages above.
    echo.
    pause
    exit /b 1
)
