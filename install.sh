#!/bin/bash
echo "============================================================"
echo "  InspectionVision Multi-Model Detection System"
echo "  Installation Script"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed or not in PATH!"
    echo "Please install Python 3.8 or higher."
    echo ""
    exit 1
fi

echo "[INFO] Python found:"
python3 --version
echo ""

# Check Python version (requires Python 3.8+)
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "[INFO] Detected Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[STEP 1/4] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment!"
        exit 1
    fi
    echo "[SUCCESS] Virtual environment created."
else
    echo "[INFO] Virtual environment already exists."
fi
echo ""

# Activate virtual environment
echo "[STEP 2/4] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment!"
    exit 1
fi
echo "[SUCCESS] Virtual environment activated."
echo ""

# Upgrade pip
echo "[STEP 3/4] Upgrading pip..."
python -m pip install --upgrade pip
echo ""

# Install requirements
echo "[STEP 4/4] Installing dependencies from requirements.txt..."
echo "This may take several minutes depending on your internet connection..."
echo ""
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to install some dependencies!"
    echo "Please check the error messages above and try again."
    exit 1
fi
echo ""

echo "============================================================"
echo "  Installation Complete!"
echo "============================================================"
echo ""
echo "To run the application:"
echo "  1. Run './run.sh' from this folder, OR"
echo "  2. Manually activate the environment and run:"
echo "     - source venv/bin/activate"
echo "     - python -m uvicorn app.main_multimodel:app --host 0.0.0.0 --port 8000"
echo ""
echo "The application will be available at: http://localhost:8000"
echo ""
