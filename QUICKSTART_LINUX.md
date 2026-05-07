#  Quick Start Guide - InspectionVision (Linux)
##  Setup on New Machine

### Step 1: Verify Python Installation
Open a terminal and type:
```bash
python3 --version
```

**Expected Output**: `Python 3.8.x` or higher

**If Python Not Found**:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-venv python3-pip

# Fedora/RHEL
sudo dnf install python3 python3-pip

# Arch
sudo pacman -S python python-pip
```

---

### Step 2: Navigate to Final_app
```bash
cd /path/to/Final_app
```
(Adjust path based on where you extracted)

---

### Step 3: Make Scripts Executable (One-Time)
```bash
chmod +x install.sh run.sh
```

---

### Step 4: Run Installation
```bash
./install.sh
```

---

## For New Users (First Time Setup)

### Step 1: Install (One-Time Setup)
```bash
chmod +x install.sh run.sh
./install.sh
# Wait for completion (~5-15 minutes)
```

### Step 2: Run the Application
```bash
./run.sh
# Wait for "Application Starting..." message
# Open browser to: http://localhost:8000
```

### Step 3: Test the System
```
1. Open the dashboard
2. Select a model (Corrosion/PPE/Inspection)
3. Upload a test image from "Test images" folder
4. Click "Analyze"
5. View results!
```

---

## Daily Usage (After Installation)

### To Start:
```bash
./run.sh
```

### To Stop:
```
Press CTRL+C in the terminal
```

---

##  Using the Dashboard

### Image Analysis
1. Click **"Image Analysis"** tab
2. Choose model: **Corrosion** | **PPE** | **Inspection**
3. Upload image (drag & drop or click)
4. Adjust confidence if needed
5. Click **"Analyze Image"**
6. View results with bounding boxes

### Video Analysis
1. Click **"Video Analysis"** tab
2. Select detection model
3. Upload video file
4. Configure settings
5. Click **"Analyze Video"**
6. Review processed output

### Live Camera Stream
1. Click **"Live Stream"** tab
2. Enter camera URL:
   ```
   rtsp://192.168.1.100:554/stream
   ```
3. Select model
4. Click **"Start Stream"**
5. View real-time detections

---

##  Important URLs

| Purpose | URL |
|---------|-----|
| **Dashboard** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

---

##  Test Images Location

```
Final_app/Test images/
├── corrosion/        (7 test images)
├── Inspection/       (27 test images)
└── PPE/             (8 test images)
```

---

## Troubleshooting

### Problem: "python3: command not found"
**Fix**: Install Python 3 using your package manager (see Step 1 above)

### Problem: "No module named venv"
**Fix**:
```bash
# Ubuntu/Debian
sudo apt install python3-venv
```

### Problem: Installation fails
**Fix**:
```bash
python3 -m pip install --upgrade pip
```
Then run `./install.sh` again

### Problem: Permission denied when running scripts
**Fix**:
```bash
chmod +x install.sh run.sh
```

### Problem: Server won't start
**Fix**: Check if model files exist in `Weights_final/` folder:
```bash
ls -la Weights_final/
```

### Problem: Port 8000 already in use
**Fix**: Either kill the existing process or edit `run.sh` to use a different port:
```bash
# Find what's using port 8000
lsof -i :8000

# Or change port in run.sh to 8080
```

---

##  Tips

-  Keep the terminal open while using the app
-  Use Chrome or Firefox for best experience
-  Test with sample images first
-  GPU (with CUDA) improves performance significantly
-  Close the app with CTRL+C before shutting down
-  If running on a remote server, use `--host 0.0.0.0` (already configured) to allow external access

---


