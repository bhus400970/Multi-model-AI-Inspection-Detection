#  Quick Start Guide - InspectionVision
##  Setup on New Machine

### Step 1: Verify Python Installation
Open Command Prompt and type:
```cmd
python --version
```

**Expected Output**: `Python 3.8.x` or higher

**If Python Not Found**:
1. Download from: https://www.python.org/downloads/
2. Check "Add Python to PATH" during installation
3. Install Python
4. Restart Command Prompt

---

### Step 2: Navigate to Final_app
```cmd
cd C:\InspectionVision\Final_app
```
(Adjust path based on where you extracted)

---

### Step 3: Run Installation
Double-click `install.bat` OR run:
```cmd
install.bat
```

## For New Users (First Time Setup)

### Step 1: Install (One-Time Setup)
```
1. Double-click: install.bat
2. Wait for completion (~5-15 minutes)
3. Close the window when done
```

### Step 2: Run the Application
```
1. Double-click: run.bat
2. Wait for "Application Starting..." message
3. Open browser to: http://localhost:8000
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
```
run.bat
```

### To Stop:
```
Press CTRL+C in the terminal window
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

### Problem: "Python is not recognized"
**Fix**: Install Python from python.org

### Problem: Installation fails
**Fix**: 
```cmd
python -m pip install --upgrade pip
```
Then run `install.bat` again

### Problem: Server won't start
**Fix**: Check if model files exist in `Weights_final/` folder

### Problem: Port 8000 already in use
**Fix**: Change port in `run.bat`:
```
--port 8080
```

---

##  Tips

-  Keep the terminal window open while using the app
-  Use Chrome or Firefox for best experience
-  Test with sample images first
-  GPU improves performance significantly
-  Close the app with CTRL+C before shutting down

---


