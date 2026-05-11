"""
main.py - FastAPI Application Entry Point
Multi-Model Detection System with IP Camera & Live Stream Support
Supports: Corrosion, PPE, and Inspection detection models
"""
import uvicorn
import asyncio
import uuid 
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging
from datetime import datetime
from time import time
from typing import Dict, Optional
from pydantic import BaseModel
import subprocess

from app.inference_multimodel import MultiModelEngine
from app.schemas import ImageAnalysisResponse, VideoAnalysisResponse, StreamResponse, MultiModelHealthResponse
from app.storage import StorageManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="InspectionVision Multi-Model Dashboard",
    description="AI-Powered Multi-Model Detection System with IP Camera Support",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model weights paths (relative to project root)
MODEL_PATHS = {
    "corrosion": Path("Weights_final/Corrosion_best.pt"),
    "ppe": Path("Weights_final/PPE_best.pt"),
    "inspection": Path("Weights_final/Inspection_best.pt")
}

# Initialize components
try:
    engine = MultiModelEngine(MODEL_PATHS)
    storage = StorageManager()
    logger.info("✓ Multi-model detection engine initialized successfully")
except Exception as e:
    logger.error(f"✗ Failed to initialize detection engine: {e}")
    engine = None
    storage = StorageManager()

# Active stream connections
active_streams: Dict[str, dict] = {}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/outputs/{filename}")
async def serve_video(filename: str, request: Request):
    """Serve video files with Range request support for browser playback"""
    import mimetypes
    import os
    video_path = Path("outputs") / Path(filename).name  # sanitize path
    if not video_path.exists() or not video_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    file_size = video_path.stat().st_size
    content_type = mimetypes.guess_type(str(video_path))[0] or "video/mp4"

    range_header = request.headers.get("range")
    if range_header:
        # Parse Range header: bytes=start-end
        range_spec = range_header.strip().split("=")[-1]
        range_parts = range_spec.split("-")
        start = int(range_parts[0]) if range_parts[0] else 0
        end = int(range_parts[1]) if range_parts[1] else file_size - 1
        end = min(end, file_size - 1)
        content_length = end - start + 1

        def iter_range():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk = f.read(min(8192, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            iter_range(),
            status_code=206,
            media_type=content_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            },
        )
    else:
        return FileResponse(
            path=str(video_path),
            media_type=content_type,
            headers={"Accept-Ranges": "bytes"},
        )


class StreamRequest(BaseModel):
    stream_url: str


@app.get("/")
async def root():
    """Serve main dashboard HTML page"""
    return FileResponse("static/dashboard.html")


@app.get("/dashboard.html")
async def dashboard():
    """Serve dashboard HTML page"""
    return FileResponse("static/dashboard.html")


@app.get("/legacy")
async def legacy():
    """Serve legacy single-model HTML page"""
    return FileResponse("static/index.html")


@app.get("/health", response_model=MultiModelHealthResponse)
async def health_check():
    """Health check endpoint"""
    models_status = {}
    if engine:
        for model_name in MODEL_PATHS.keys():
            models_status[model_name] = engine.is_model_loaded(model_name)
    
    return MultiModelHealthResponse(
        status="healthy",
        version="1.0.0",
        models=models_status,
        device=engine.device if engine else "unknown"
    )


# ===========================================
# CORROSION MODEL ENDPOINTS
# ===========================================
@app.post("/api/detect/corrosion/image", response_model=ImageAnalysisResponse)
async def detect_corrosion_image(file: UploadFile = File(...)):
    """Analyze image for corrosion, crack, and leak detection"""
    return await process_image(file, "corrosion")


@app.post("/api/detect/corrosion/video", response_model=VideoAnalysisResponse)
async def detect_corrosion_video(file: UploadFile = File(...)):
    """Analyze video for corrosion, crack, and leak detection"""
    return await process_video(file, "corrosion")


# ===========================================
# PPE MODEL ENDPOINTS
# ===========================================
@app.post("/api/detect/ppe/image", response_model=ImageAnalysisResponse)
async def detect_ppe_image(file: UploadFile = File(...)):
    """Analyze image for PPE detection (helmet, vest, goggles, etc.)"""
    return await process_image(file, "ppe")


@app.post("/api/detect/ppe/video", response_model=VideoAnalysisResponse)
async def detect_ppe_video(file: UploadFile = File(...)):
    """Analyze video for PPE detection"""
    return await process_video(file, "ppe")


# ===========================================
# INSPECTION MODEL ENDPOINTS
# ===========================================
@app.post("/api/detect/inspection/image", response_model=ImageAnalysisResponse)
async def detect_inspection_image(file: UploadFile = File(...)):
    """Analyze image for general inspection (defects, damage, anomaly)"""
    return await process_image(file, "inspection")


@app.post("/api/detect/inspection/video", response_model=VideoAnalysisResponse)
async def detect_inspection_video(file: UploadFile = File(...)):
    """Analyze video for general inspection"""
    return await process_video(file, "inspection")


# ===========================================
# STREAMING ENDPOINTS
# ===========================================
@app.post("/api/stream/{model_name}")
async def start_stream(model_name: str, request: StreamRequest):
    """Start an IP camera stream for the specified model"""
    if model_name not in MODEL_PATHS:
        raise HTTPException(status_code=400, detail=f"Invalid model: {model_name}")
    
    stream_id = str(uuid.uuid4())
    
    try:
        # Test connection to stream
        cap = cv2.VideoCapture(request.stream_url)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Failed to connect to stream URL")
        
        # Store stream info
        active_streams[stream_id] = {
            "url": request.stream_url,
            "model": model_name,
            "cap": cap,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Started stream {stream_id} for {model_name} from {request.stream_url}")
        
        return StreamResponse(
            success=True,
            stream_id=stream_id,
            model=model_name,
            status="connected"
        )
        
    except Exception as e:
        logger.error(f"Failed to start stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stream/{model_name}/frame")
async def get_stream_frame(model_name: str, stream_id: str):
    """Get a processed frame from an active stream"""
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    stream_info = active_streams[stream_id]
    
    if not stream_info["active"]:
        raise HTTPException(status_code=400, detail="Stream is not active")
    
    try:
        cap = stream_info["cap"]
        ret, frame = cap.read()
        
        if not ret:
            # Try to reconnect
            cap.release()
            cap = cv2.VideoCapture(stream_info["url"])
            active_streams[stream_id]["cap"] = cap
            ret, frame = cap.read()
            
            if not ret:
                raise HTTPException(status_code=500, detail="Failed to read frame")
        
        # Process frame with model
        if engine:
            detections = engine.detect_image(frame, model_name)
            class_results = engine.calculate_metrics(detections, frame.shape, model_name)
            annotated_frame = engine.draw_detections(frame, detections, model_name)
            
            # Convert to base64
            frame_b64 = storage.image_to_base64(annotated_frame)
            
            total_detections = sum(result.count for result in class_results.values())
            
            return {
                "success": True,
                "frame": frame_b64,
                "detections": detections,
                "total_detections": total_detections,
                **{k: v.dict() for k, v in class_results.items()}
            }
        else:
            frame_b64 = storage.image_to_base64(frame)
            return {
                "success": True,
                "frame": frame_b64,
                "detections": {},
                "total_detections": 0
            }
            
    except Exception as e:
        logger.error(f"Error getting stream frame: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/stream/{stream_id}")
async def stop_stream(stream_id: str):
    """Stop an active stream"""
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    try:
        stream_info = active_streams[stream_id]
        stream_info["active"] = False
        if stream_info["cap"]:
            stream_info["cap"].release()
        del active_streams[stream_id]
        
        logger.info(f"Stopped stream {stream_id}")
        return {"success": True, "message": "Stream stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/stream/{model_name}")
async def websocket_stream(websocket: WebSocket, model_name: str):
    """WebSocket endpoint for real-time camera streaming with detection"""
    await websocket.accept()
    
    if model_name not in MODEL_PATHS:
        await websocket.close(code=1008, reason=f"Invalid model: {model_name}")
        return
    
    stream_id = str(uuid.uuid4())
    cap = None
    
    try:
        # Wait for stream URL from client
        data = await websocket.receive_json()
        stream_url = data.get("stream_url")
        
        if not stream_url:
            await websocket.send_json({"error": "No stream URL provided"})
            return
        
        # Connect to stream
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            await websocket.send_json({"error": "Failed to connect to stream"})
            return
        
        await websocket.send_json({"status": "connected", "stream_id": stream_id})
        
        # Stream processing loop
        while True:
            ret, frame = cap.read()
            if not ret:
                await websocket.send_json({"error": "Failed to read frame"})
                break
            
            # Process frame
            if engine:
                detections = engine.detect_image(frame, model_name)
                class_results = engine.calculate_metrics(detections, frame.shape, model_name)
                annotated_frame = engine.draw_detections(frame, detections, model_name)
                frame_b64 = storage.image_to_base64(annotated_frame)
                
                total_detections = sum(result.count for result in class_results.values())
                
                await websocket.send_json({
                    "frame": frame_b64,
                    "total_detections": total_detections,
                    "detections": {k: v.dict() for k, v in class_results.items()}
                })
            else:
                frame_b64 = storage.image_to_base64(frame)
                await websocket.send_json({"frame": frame_b64, "total_detections": 0})
            
            # Small delay to prevent overwhelming the connection
            await asyncio.sleep(0.033)  # ~30 FPS
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for stream {stream_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if cap:
            cap.release()


# ===========================================
# SHARED PROCESSING FUNCTIONS
# ===========================================
async def process_image(file: UploadFile, model_name: str) -> ImageAnalysisResponse:
    """Process image with specified model"""
    start_time = time()
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Detection engine not available")
    
    try:
        # Validate file type
        allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Validate file size (50MB)
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        if size > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Max: 50MB")
        
        logger.info(f"Processing image with {model_name} model: {file.filename} ({size/1024:.1f}KB)")
        
        # Read image
        contents = await file.read()
        image = storage.read_image_from_bytes(contents)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid or corrupted image")
        
        height, width = image.shape[:2]
        
        # Run detection with specified model
        detections = engine.detect_image(image, model_name)
        
        # Calculate metrics
        class_results = engine.calculate_metrics(detections, image.shape, model_name)
        
        # Draw detections
        annotated_image = engine.draw_detections(image, detections, model_name)
        
        # Convert to base64
        annotated_b64 = storage.image_to_base64(annotated_image)
        original_b64 = storage.image_to_base64(image)
        
        # Calculate totals
        total_detections = sum(result.count for result in class_results.values())
        avg_confidence = 0.0
        if total_detections > 0:
            all_confs = []
            for result in class_results.values():
                for region in result.regions:
                    all_confs.append(region.confidence)
            avg_confidence = sum(all_confs) / len(all_confs) if all_confs else 0.0
        
        processing_time = time() - start_time
        logger.info(f"✓ Processed with {model_name} in {processing_time:.2f}s, {total_detections} detections")
        
        # Build response with class_results dict for flexibility
        response_data = {
            "success": True,
            "message": f"Analysis with {model_name} completed successfully",
            "annotated_image": annotated_b64,
            "original_image": original_b64,
            "model_name": model_name,
            "class_results": class_results,
            "total_detections": total_detections,
            "avg_confidence": avg_confidence,
            "processing_time": processing_time,
            "image_dimensions": {"width": width, "height": height},
            "timestamp": datetime.now().isoformat()
        }
        
        # Also add individual class fields for schema compatibility
        for class_name, result in class_results.items():
            # Replace spaces with underscores for field names
            field_name = class_name.replace(" ", "_")
            response_data[field_name] = result
        
        return ImageAnalysisResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error processing image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def process_video(file: UploadFile, model_name: str) -> VideoAnalysisResponse:
    """Process video with specified model"""
    start_time = time()
    temp_path = None

    if engine is None:
        raise HTTPException(status_code=503, detail="Detection engine not available")

    try:
        # Validate file type
        allowed_types = {"video/mp4", "video/avi", "video/quicktime", "video/x-msvideo"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )

        # Validate file size (500MB)
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        if size > 500 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Max: 500MB")

        logger.info(f"Processing video with {model_name} model: {file.filename} ({size/(1024*1024):.1f}MB)")

        # Save temp file
        temp_path = storage.save_temp_file(file.file)

        # Generate output path
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        output_name = f"{model_name}_annotated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        temp_output_path = output_dir / f"temp_{output_name}"
        final_output_path = output_dir / output_name

        # Process video - ensure paths are strings
        result = engine.detect_video(str(temp_path), str(temp_output_path), model_name)

        # Convert to H.264
        # Try to get ffmpeg via imageio_ffmpeg if available, otherwise fallback to 'ffmpeg' on PATH
        import importlib
        ffmpeg_exe = "ffmpeg"
        try:
            if importlib.util.find_spec("imageio_ffmpeg") is not None:
                imageio_ffmpeg = importlib.import_module("imageio_ffmpeg")
                try:
                    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                except Exception:
                    ffmpeg_exe = "ffmpeg"
        except Exception:
            ffmpeg_exe = "ffmpeg"

        ffmpeg_cmd = [
            ffmpeg_exe,
            "-y",
            "-i", str(temp_output_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",   # improves streaming
            str(final_output_path)
        ]

        ffmpeg_result = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if ffmpeg_result.returncode != 0:
            logger.warning(f"FFmpeg conversion failed: {ffmpeg_result.stderr}")
            # Fallback: if the temporary annotated file exists, serve it instead of failing
            try:
                if Path(temp_output_path).exists():
                    logger.info("Using temporary annotated video as fallback due to FFmpeg failure.")
                    final_output_path = temp_output_path
                else:
                    raise RuntimeError(f"FFmpeg failed and temporary file not found: {ffmpeg_result.stderr}")
            except Exception as e:
                raise RuntimeError(str(e))

        # Build class_results dict from result data
        class_results = {}
        frames_with_detections = {}
        class_names = engine.get_class_names(model_name)

        for class_name in class_names:
            if class_name in result:
                from app.schemas import ClassResult
                class_data = result[class_name]
                class_results[class_name] = ClassResult(
                    detected=class_data.get("detected", False),
                    count=class_data.get("count", 0),
                    avg_confidence=class_data.get("avg_confidence", 0.0),
                    regions=[],
                    risk_level=class_data.get("risk_level", "Low")
                )
            # Get frames with this class
            frame_key = f"frames_with_{class_name}"
            if frame_key in result:
                frames_with_detections[class_name] = result[frame_key]

        # Build response
        processing_time = time() - start_time
        response_data = {
            "success": True,
            "message": f"Video analysis with {model_name} completed",
            # Serve final output via the mounted /outputs static route
            "video_url": f"/outputs/{final_output_path.name}",
            "model_name": model_name,
            "class_results": class_results,
            "frames_with_detections": frames_with_detections,
            "total_detections": result["total_detections"],
            "processed_frames": result["processed_frames"],
            "max_detections_in_frame": result["max_detections"],
            "avg_confidence": result.get("avg_confidence", 0.0),
            "processing_time": processing_time,
            "video_duration": result["duration"],
            "fps": result["fps"],
            "timestamp": datetime.now().isoformat()
        }

        # Add individual class fields for schema compatibility
        for class_name, class_result in class_results.items():
            field_name = class_name.replace(" ", "_")
            response_data[field_name] = class_result

        return VideoAnalysisResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error processing video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink()
        # Remove temporary annotated video only if it's different from the final output
        try:
            if temp_output_path and Path(temp_output_path).exists() and temp_output_path != final_output_path:
                Path(temp_output_path).unlink()
        except Exception:
            pass


# ===========================================
# MODEL INFO ENDPOINTS
# ===========================================
@app.get("/api/models")
async def get_models_info():
    """Get information about all loaded models"""
    if engine is None:
        return {"loaded": False, "message": "Engine not initialized"}
    
    models_info = {}
    for model_name in MODEL_PATHS.keys():
        models_info[model_name] = {
            "loaded": engine.is_model_loaded(model_name),
            "path": MODEL_PATHS[model_name],
            "classes": engine.get_class_names(model_name)
        }
    
    return {
        "loaded": True,
        "device": engine.device,
        "models": models_info
    }


@app.get("/api/model/{model_name}/info")
async def get_model_info(model_name: str):
    """Get information about a specific model"""
    if model_name not in MODEL_PATHS:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    if engine is None:
        return {"loaded": False}
    
    return {
        "loaded": engine.is_model_loaded(model_name),
        "model_path": MODEL_PATHS[model_name],
        "device": engine.device,
        "classes": engine.get_class_names(model_name)
    }


# ===========================================
# LEGACY ENDPOINTS (backward compatibility) # Legacy endpoints are backward-compatible API routes
#  that map old request paths to the new multi-model pipeline without requiring 
# clients to change their code. In your system, they default to the corrosion model and 
# internally call the new unified processing functions.
# ===========================================
@app.post("/infer/image", response_model=ImageAnalysisResponse)
async def legacy_infer_image(file: UploadFile = File(...)):
    """Legacy alias - uses corrosion model"""
    return await process_image(file, "corrosion")


@app.post("/infer/video", response_model=VideoAnalysisResponse)
async def legacy_infer_video(file: UploadFile = File(...)):
    """Legacy alias - uses corrosion model"""
    return await process_video(file, "corrosion")


@app.post("/api/detect/image", response_model=ImageAnalysisResponse)
async def legacy_detect_image(file: UploadFile = File(...)):
    """Legacy alias - uses corrosion model"""
    return await process_image(file, "corrosion")


@app.post("/api/detect/video", response_model=VideoAnalysisResponse)
async def legacy_detect_video(file: UploadFile = File(...)):
    """Legacy alias - uses corrosion model"""
    return await process_video(file, "corrosion")


if __name__ == "__main__":
    print("=" * 60)
    print(" Starting InspectionVision Multi-Model Dashboard v4.0")
    print("=" * 60)
    print(f" Server: http://0.0.0.0:8000")
    print(f" Dashboard: http://0.0.0.0:8000/")
    print(f" API Docs: http://0.0.0.0:8000/docs")
    print(f" Health: http://0.0.0.0:8000/health")
    print("=" * 60)
    print(" Models:")
    for name, path in MODEL_PATHS.items():
        print(f"   - {name}: {path}")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
