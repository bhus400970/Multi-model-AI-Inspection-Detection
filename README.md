#  InspectionVision - AI-Powered Multi-Model Detection System

A FastAPI-based multi-model detection system supporting Corrosion Detection, PPE (Personal Protective Equipment) Detection, and General Inspection Detection with real-time IP camera streaming capabilities.

##  Table of Contents
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
  - [Docker Installation (Recommended)](#docker-installation-recommended)
  - [Manual Installation](#manual-installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Model Information](#model-information)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

##  Features

-  **Multi-Model Detection**: Simultaneous support for three specialized detection models
  - **Corrosion Detection**: Identify rust and corrosion in infrastructure
  - **PPE Detection**: Verify proper use of safety equipment (helmets, vests, gloves, etc.)
  - **Inspection Detection**: General-purpose object detection for facility inspections

-  **Multiple Input Sources**:
  - Image upload and analysis
  - Video file processing
  - Real-time IP camera/RTSP streams
  - WebSocket support for live streaming

-  **Advanced Features**:
  - Confidence threshold adjustment
  - Annotated output with bounding boxes
  - Real-time detection metrics
  - Health monitoring endpoints
  - Persistent storage for results

-  **Web Interface**:
  - Interactive dashboard
  - Live stream visualization
  - Model selection
  - Result download

---

##  System Requirements

### For Docker Deployment (Recommended)
- **OS**: Windows 10/11, macOS 10.15+, or Linux
- **Docker**: Docker Desktop 20.x+ or Docker Engine 20.x+
- **Docker Compose**: Version 2.x+
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Disk Space**: 10GB free space
- **CPU**: Multi-core processor (4+ cores recommended)

### For Manual Installation
- **Python**: 3.8, 3.9, 3.10, or 3.11
- **RAM**: Minimum 4GB, Recommended 8GB+
- **GPU**: Optional (NVIDIA GPU with CUDA for faster inference)
- **Disk Space**: 10GB free space

---

##  Installation Methods

### Docker Installation (Recommended)

Docker provides the easiest and most reliable way to deploy InspectionVision with all dependencies pre-configured.

#### Step 1: Install Docker

**Windows:**
1. Download [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Run installer and follow setup wizard
3. Restart computer if prompted
4. Verify installation:
   ```powershell
   docker --version
   docker-compose --version
   ```

**macOS:**
1. Download [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
2. Drag Docker.app to Applications
3. Launch Docker Desktop
4. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

**Linux (Ubuntu/Debian):**
```bash
# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Add user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker-compose --version
```

#### Step 2: Clone or Download Project

```bash
# Option 1: Clone with Git
git clone <repository-url>
cd Final_app

# Option 2: Extract downloaded ZIP file
# Navigate to the extracted folder
cd Final_app
```

#### Step 3: Build and Run with Docker

```bash
# Build and start the application
docker-compose up -d

# Wait for build to complete (5-10 minutes first time)
# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Step 4: Access Application

Open your browser and navigate to:
- **Application**: http://localhost:8000
- **Dashboard**: http://localhost:8000/static/dashboard.html
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### Step 5: Stop Application

```bash
# Stop containers
docker-compose stop

# Stop and remove containers
docker-compose down
```

---

### Manual Installation

If you prefer to run without Docker or need to modify the code:

#### Step 1: Install Python

Ensure Python 3.8+ is installed:
```bash
python --version
```

Download from https://www.python.org/downloads/ if needed.

#### Step 2: Navigate to Project Directory

```bash
cd Final_app
```

#### Step 3: Install Dependencies

**Windows:**
```cmd
# Run the install script
install.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Linux/macOS:**
```bash
# Run the install script
chmod +x install.sh
./install.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 4: Run Application

**Windows:**
```cmd
run.bat
```

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

**Or manually:**
```bash
# Activate virtual environment first
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

uvicorn app.main_multimodel:app --host 0.0.0.0 --port 8000 --reload
```

---

##  Project Structure

```
Final_app/
│
├── app/                          # Application source code
│   ├── main_multimodel.py        # FastAPI application entry point
│   ├── inference_multimodel.py   # Multi-model inference engine
│   ├── schemas.py                # Pydantic models for API
│   └── storage.py                # File storage management
│
├── Weights_final/                # Pre-trained model weights
│   ├── Corrosion_best.pt         # Corrosion detection model
│   ├── Inspection_best.pt        # Inspection detection model
│   └── PPE_best.pt               # PPE detection model
│
├── static/                       # Static web files
│   ├── dashboard.html            # Web dashboard interface
│   └── uploads/                  # User uploaded files
│
├── outputs/                      # Processed results
│   ├── images/                   # Annotated images
│   └── videos/                   # Processed videos
│
├── Test images/                  # Sample test images
│   ├── corrosion/
│   ├── Inspection/
│   └── PPE/
│
├── Test videos/                  # Sample test videos
│   ├── Corrosion/
│   ├── Inspection/
│   └── PPE/
│
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Docker orchestration config
├── .dockerignore                 # Docker build exclusions
├── requirements.txt              # Python dependencies
├── install.bat                   # Windows installation script
├── install.sh                    # Linux/Mac installation script
├── run.bat                       # Windows run script
├── run.sh                        # Linux/Mac run script
├── README.md                     # This file
├── QUICKSTART.md                 # Quick start guide (native)
├── QUICKSTART_LINUX.md           # Linux-specific quick start
└── QUICKSTART_DOCKER.md          # Docker deployment guide
```

---

##  Usage

### Web Interface

1. **Access Dashboard**
   - Open http://localhost:8000/static/dashboard.html
   - Or open `dashboard.html` in your browser

2. **Image Analysis**
   - Click "Upload Image"
   - Select an image file (JPG, PNG, BMP)
   - Choose detection model (Corrosion, PPE, or Inspection)
   - Click "Analyze"
   - View results with bounding boxes and confidence scores
   - Download annotated image

3. **Video Analysis**
   - Click "Upload Video"
   - Select a video file (MP4, AVI, MOV)
   - Choose detection model
   - Wait for processing
   - Download processed video

4. **Live Stream (IP Camera)**
   - Enter RTSP URL (e.g., `rtsp://username:password@camera-ip:554/stream`)
   - Or HTTP stream URL
   - Select detection model
   - Click "Start Stream"
   - View real-time detections
   - Click "Stop Stream" to end

### API Usage

#### Image Analysis
```bash
curl -X POST "http://localhost:8000/analyze-image/corrosion" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/image.jpg"
```

#### Video Analysis
```bash
curl -X POST "http://localhost:8000/analyze-video/ppe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/video.mp4"
```

#### Health Check
```bash
curl http://localhost:8000/health
```

### Python Client Example

```python
import requests

# Analyze image
with open('test.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/analyze-image/corrosion',
        files=files
    )
    result = response.json()
    print(f"Detected {result['detections_count']} objects")
    print(f"Confidence scores: {result['confidence_scores']}")

# Check health
health = requests.get('http://localhost:8000/health').json()
print(f"Status: {health['status']}")
```

---

##  API Documentation

### Interactive API Documentation

Once the application is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint, redirects to docs |
| `/health` | GET | Health check and model status |
| `/analyze-image/{model}` | POST | Analyze uploaded image |
| `/analyze-video/{model}` | POST | Process video file |
| `/stream/start` | POST | Start IP camera stream |
| `/stream/stop/{stream_id}` | POST | Stop active stream |
| `/stream/{stream_id}` | WebSocket | WebSocket for live stream |

### Model Parameter

Available models for `{model}` parameter:
- `corrosion` - Corrosion detection
- `ppe` - PPE detection
- `inspection` - General inspection

---

##  Model Information

### Corrosion Detection Model
- **Purpose**: Detect rust, corrosion, and material degradation
- **Use Cases**: Infrastructure inspection, pipeline monitoring, equipment maintenance
- **Classes**: Corrosion, rust, degradation

### PPE Detection Model
- **Purpose**: Verify proper use of personal protective equipment
- **Use Cases**: Construction site safety, manufacturing safety compliance
- **Classes**: Helmet, safety vest, gloves, goggles, boots

### Inspection Detection Model
- **Purpose**: General-purpose object detection for facility inspections
- **Use Cases**: Equipment monitoring, facility inspection, anomaly detection
- **Classes**: Various equipment and facility components

All models are based on **YOLOv8** architecture and optimized for real-time inference.

---

##  Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000

# Model Configuration
CONFIDENCE_THRESHOLD=0.5
IOU_THRESHOLD=0.45
MODEL_INPUT_SIZE=640

# Logging
LOG_LEVEL=INFO

# Storage
MAX_UPLOAD_SIZE=100MB
OUTPUT_DIRECTORY=./outputs
```

### Docker Configuration

Edit `docker-compose.yml` to customize:

```yaml
services:
  inspectionvision:
    environment:
      - CONFIDENCE_THRESHOLD=0.6  # Adjust confidence threshold
    ports:
      - "8080:8000"  # Change external port
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

---

##  Troubleshooting

### Docker Issues

**Problem**: Build fails with DNS resolution errors
```bash
# Error: "Temporary failure resolving 'deb.debian.org'"

# Solution 1: Check Docker Desktop DNS settings
# Docker Desktop → Settings → Resources → Network → DNS Server
# Use: 8.8.8.8 (Google DNS) or 1.1.1.1 (Cloudflare DNS)

# Solution 2: Retry build (sometimes temporary network issue)
docker-compose build --no-cache

# Solution 3: Check your internet connection and firewall
# Ensure Docker can access the internet

# Solution 4: Use a VPN or different network if corporate firewall blocks
```

**Problem**: Container fails to start
```bash
# Check logs
docker-compose logs inspectionvision

# Common issues:
# 1. Port already in use - change port in docker-compose.yml
# 2. Insufficient memory - increase Docker memory limit
# 3. Missing model files - ensure Weights_final/ directory exists
```

**Problem**: Cannot access application
```bash
# Verify container is running
docker-compose ps

# Check if port is accessible
curl http://localhost:8000/health

# Check firewall settings
# Try http://127.0.0.1:8000 instead
```

**Problem**: Slow performance
- Increase Docker Desktop memory allocation (Settings → Resources)
- Reduce video resolution for processing
- Use GPU acceleration (see QUICKSTART_DOCKER.md)

### Manual Installation Issues

**Problem**: Module import errors
```bash
# Ensure virtual environment is activated
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Problem**: CUDA/GPU not detected
```bash
# Check PyTorch CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Common Errors

| Error | Solution |
|-------|----------|
| `Port 8000 already in use` | Change port or stop conflicting service |
| `Model file not found` | Ensure `Weights_final/` directory contains .pt files |
| `Out of memory` | Reduce batch size or increase system RAM |
| `CUDA out of memory` | Reduce input image size or use CPU mode |
| `Connection refused` | Check if application is running: `docker-compose ps` |

---

##  Performance Optimization

### Docker Optimization
- Allocate sufficient resources (CPU: 4+ cores, RAM: 8GB+)
- Use GPU acceleration for NVIDIA GPUs
- Enable BuildKit for faster builds: `export DOCKER_BUILDKIT=1`

### Application Optimization
- Adjust confidence thresholds to reduce false positives
- Reduce input image/video resolution for faster processing
- Use appropriate model for specific use case
- Enable batch processing for multiple images

---

##  Security Considerations

- Change default ports in production
- Implement authentication for API endpoints
- Use HTTPS in production (configure reverse proxy)
- Limit upload file sizes
- Sanitize file inputs
- Run container as non-root user in production
- Regularly update dependencies for security patches

---

##  Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


---

##  Support

For issues and questions:
- Check existing documentation (QUICKSTART.md, QUICKSTART_DOCKER.md)
- Review troubleshooting section above
- Check application logs: `docker-compose logs -f`
- Contact: [Your contact information]

---

##  Additional Resources

- **Docker Documentation**: https://docs.docker.com/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **YOLOv8 Documentation**: https://docs.ultralytics.com/
- **OpenCV Documentation**: https://docs.opencv.org/

---

##  Version History

- **v1.0.0** - Initial multi-model support
  - Corrosion detection model
  - PPE detection model
  - Inspection detection model
  - Docker deployment support
  - Real-time IP camera streaming
  - Web dashboard interface


