#!/bin/bash
echo "============================================================"
echo "  InspectionVision Multi-Model Detection System"
echo "  Starting Application..."
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run './install.sh' first to set up the environment."
    echo ""
    exit 1
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate
echo ""

# Check if model weights exist
if [ ! -f "Weights_final/Corrosion_best.pt" ]; then
    echo "[WARNING] Corrosion model not found at: Weights_final/Corrosion_best.pt"
fi
if [ ! -f "Weights_final/PPE_best.pt" ]; then
    echo "[WARNING] PPE model not found at: Weights_final/PPE_best.pt"
fi
if [ ! -f "Weights_final/Inspection_best.pt" ]; then
    echo "[WARNING] Inspection model not found at: Weights_final/Inspection_best.pt"
fi
echo ""

# Create necessary directories if they don't exist
mkdir -p static/uploads
mkdir -p outputs
echo "[INFO] Directory structure verified."
echo ""

# Start the application
echo "[INFO] Starting FastAPI server..."
echo ""
echo "============================================================"
echo "  Application Starting..."
echo "  Access the dashboard at: http://localhost:8000"
echo "  API Documentation at: http://localhost:8000/docs"
echo "  Press CTRL+C to stop the server"
echo "============================================================"
echo ""

python -m uvicorn app.main_multimodel:app --host 0.0.0.0 --port 8000 --reload

# Check if the application exited with an error
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Application exited with errors!"
    echo "Please check the error messages above."
    echo ""
    exit 1
fi
