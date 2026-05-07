# 🐳 Quick Start Guide - InspectionVision (Docker)

## Prerequisites

### Required Software
- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
  - Windows: https://docs.docker.com/desktop/install/windows-install/
  - Mac: https://docs.docker.com/desktop/install/mac-install/
  - Linux: https://docs.docker.com/engine/install/

### Verify Docker Installation
Open terminal/command prompt and run:
```bash
docker --version
docker-compose --version
```

**Expected Output**:
- Docker version 20.x or higher
- Docker Compose version 2.x or higher

---

## 🚀 Quick Start (3 Steps)

### Step 1: Navigate to Application Directory
```bash
cd "C:\Users\464_0970\OneDrive - Yokogawa Electric Corporation\Final_app"
```
*(Adjust path based on your installation)*

### Step 2: Build and Start the Application
```bash
docker-compose up -d
```

**What this does:**
- Downloads necessary base images
- Builds the InspectionVision container
- Starts the application in the background
- Sets up networking and volumes

**First-time build**: Takes 5-10 minutes depending on internet speed

### Step 3: Access the Application
Open your browser and navigate to:
```
http://localhost:8000
```

**Dashboard:** Open `dashboard.html` or navigate to `http://localhost:8000/static/dashboard.html`

---

## 📋 Common Commands

### View Logs
```bash
# View real-time logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100
```

### Stop the Application
```bash
docker-compose stop
```

### Start the Application (after stopping)
```bash
docker-compose start
```

### Restart the Application
```bash
docker-compose restart
```

### Stop and Remove Containers
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### Check Container Status
```bash
docker-compose ps
```

### Access Container Shell (for debugging)
```bash
docker-compose exec inspectionvision bash
```

---

## 🔍 Health Check

### Check Application Status
```bash
curl http://localhost:8000/health
```

Or open in browser: `http://localhost:8000/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "models": {
    "corrosion": "loaded",
    "ppe": "loaded",
    "inspection": "loaded"
  }
}
```

---

## 📁 Data Persistence

The following directories are automatically mounted and persist data:

| Host Directory | Container Directory | Purpose |
|---------------|---------------------|---------|
| `./outputs` | `/app/outputs` | Analysis results, annotated images/videos |
| `./static/uploads` | `/app/static/uploads` | Uploaded files from web interface |

**Note:** Data in these directories persists even when containers are removed.

---

## 🎯 Using the Application

### 1. Image Analysis
- Navigate to `http://localhost:8000`
- Upload an image (JPG, PNG)
- Select model: Corrosion, PPE, or Inspection
- Click "Analyze"
- View results with bounding boxes and confidence scores

### 2. Video Analysis
- Upload a video file (MP4, AVI)
- Select detection model
- View processed video with detections

### 3. IP Camera/Stream
- Enter RTSP or HTTP stream URL
- Start live detection
- Real-time analysis with WebSocket updates

---

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the application directory:
```env
# Server Configuration
PORT=8000
HOST=0.0.0.0

# Model Configuration
CONFIDENCE_THRESHOLD=0.5
IOU_THRESHOLD=0.45

# Logging
LOG_LEVEL=INFO
```

Update `docker-compose.yml` to use the file:
```yaml
services:
  inspectionvision:
    env_file:
      - .env
```

### Resource Limits
Edit `docker-compose.yml` to adjust CPU/Memory:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'        # Maximum CPU cores
      memory: 8G       # Maximum memory
    reservations:
      cpus: '2'        # Minimum CPU cores
      memory: 4G       # Minimum memory
```

---

## 🐛 Troubleshooting

### Issue: Port 8000 Already in Use
**Solution:**
```bash
# Option 1: Change port in docker-compose.yml
ports:
  - "8080:8000"  # Access via http://localhost:8080

# Option 2: Stop conflicting service
docker ps  # Find container using port 8000
docker stop <container_id>
```

### Issue: Container Keeps Restarting
**Solution:**
```bash
# Check logs
docker-compose logs inspectionvision

# Common causes:
# 1. Missing model weights - ensure Weights_final/ directory exists
# 2. Memory issues - increase Docker memory limit
# 3. Dependencies issue - rebuild container
```

### Issue: Slow Performance
**Solution:**
1. Increase Docker Desktop resources (Settings → Resources)
2. Allocate more CPU cores and memory in `docker-compose.yml`
3. For GPU support, see "GPU Acceleration" section below

### Issue: Cannot Access Application
**Solution:**
```bash
# 1. Check container is running
docker-compose ps

# 2. Check container health
docker-compose exec inspectionvision curl http://localhost:8000/health

# 3. Verify firewall allows port 8000
# 4. Try http://127.0.0.1:8000 instead of localhost
```

---

## 🚀 Advanced Configuration

### GPU Acceleration (NVIDIA)

#### Prerequisites
- NVIDIA GPU
- NVIDIA drivers installed
- NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

#### Update docker-compose.yml
```yaml
services:
  inspectionvision:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### Verify GPU Access
```bash
docker-compose exec inspectionvision nvidia-smi
```

### Production Deployment

#### Use Production Dockerfile
Create `Dockerfile.prod`:
```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p outputs static/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main_multimodel:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Production docker-compose.yml
```yaml
version: '3.8'

services:
  inspectionvision:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: inspectionvision-prod
    ports:
      - "8000:8000"
    volumes:
      - ./outputs:/app/outputs
      - ./static/uploads:/app/static/uploads
    environment:
      - PYTHONUNBUFFERED=1
      - WORKERS=4
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Multi-Container Setup (with Nginx)

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - inspectionvision
    restart: unless-stopped

  inspectionvision:
    build: .
    expose:
      - "8000"
    volumes:
      - ./outputs:/app/outputs
      - ./static/uploads:/app/static/uploads
    restart: unless-stopped
```

---

## 📊 Monitoring

### Container Stats
```bash
# Real-time resource usage
docker stats inspectionvision

# Detailed inspection
docker inspect inspectionvision
```

### Application Logs
```bash
# Follow logs
docker-compose logs -f inspectionvision

# Filter by time
docker-compose logs --since 30m inspectionvision

# Search logs
docker-compose logs inspectionvision | grep ERROR
```

---

## 🔄 Updates and Maintenance

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Verify health
curl http://localhost:8000/health
```

### Clean Up
```bash
# Remove stopped containers
docker-compose down

# Remove images and volumes (caution: deletes data!)
docker-compose down -v --rmi all

# Prune unused Docker resources
docker system prune -a
```

---

## 📞 Support

### Check Application Logs
```bash
docker-compose logs --tail=50 inspectionvision
```

### Access Interactive Shell
```bash
docker-compose exec inspectionvision bash

# Inside container:
python -c "import torch; print(torch.__version__)"
python -c "import cv2; print(cv2.__version__)"
```

### Export Logs for Debugging
```bash
docker-compose logs > inspectionvision-logs.txt
```

---

## 🎓 Next Steps

1. ✅ **Test with sample images** - Upload images from `Test images/` directory
2. ✅ **Configure models** - Adjust confidence thresholds in application
3. ✅ **Set up IP cameras** - Add RTSP stream URLs for live monitoring
4. ✅ **Monitor performance** - Use `docker stats` and application logs
5. ✅ **Scale if needed** - Adjust resource limits and worker count

---

## 📝 Notes

- **First startup**: Takes 30-60 seconds for models to load
- **Memory requirement**: Minimum 4GB RAM, recommended 8GB+
- **Disk space**: Approximately 5GB for images and dependencies
- **Network**: Ensure port 8000 is not blocked by firewall
- **Data backup**: Regular backup of `outputs/` and `static/uploads/` recommended

---

**Docker deployment provides:**
- ✅ Consistent environment across systems
- ✅ Easy deployment and scaling
- ✅ Isolated dependencies
- ✅ Simple updates and rollbacks
- ✅ Production-ready configuration
