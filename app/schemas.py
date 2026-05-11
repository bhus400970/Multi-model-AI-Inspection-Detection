"""
schemas.py - Pydantic Data Models
Request and response schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x: int = Field(..., description="Top-left X coordinate")
    y: int = Field(..., description="Top-left Y coordinate")
    width: int = Field(..., description="Box width")
    height: int = Field(..., description="Box height")


class Detection(BaseModel):
    """Single detection instance"""
    bbox: BoundingBox
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    class_id: int = Field(..., description="Class ID (0=corrosion, 1=crack, 2=leak)")
    class_name: str = Field(..., description="Class name")


class ClassResult(BaseModel):
    """Results for a single damage class"""
    detected: bool = Field(..., description="Whether this class was detected")
    count: int = Field(..., ge=0, description="Number of detections")
    avg_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence")
    regions: List[Detection] = Field(default=[], description="List of all detected regions")
    
    # Class-specific metrics
    surface_coverage: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0, 
        description="Surface coverage % (corrosion only)"
    )
    total_length: Optional[float] = Field(
        None, 
        ge=0.0, 
        description="Total crack length normalized by image width (crack only)"
    )
    
    # Risk assessment
    risk_level: str = Field(
        ..., 
        description="Risk level: Low, Medium, High, or Critical"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "detected": True,
                "count": 3,
                "avg_confidence": 0.85,
                "regions": [
                    {
                        "bbox": {"x": 100, "y": 150, "width": 200, "height": 180},
                        "confidence": 0.87,
                        "class_id": 0,
                        "class_name": "corrosion"
                    }
                ],
                "surface_coverage": 12.5,
                "risk_level": "Medium"
            }
        }


class ImageAnalysisResponse(BaseModel):
    """Response for image analysis"""
    success: bool = Field(..., description="Whether analysis succeeded")
    message: str = Field(..., description="Status message")
    
    # Images
    annotated_image: str = Field(..., description="Base64 encoded annotated image")
    original_image: Optional[str] = Field(None, description="Base64 encoded original")
    
    # Detection results per class - now using Optional fields
    corrosion: Optional[ClassResult] = Field(None, description="Corrosion detection results") 
    crack: Optional[ClassResult] = Field(None, description="Crack detection results")
    leak: Optional[ClassResult] = Field(None, description="Leak detection results")
    
    # PPE classes
    Person: Optional[ClassResult] = Field(None, description="Person detection results")
    Gloves: Optional[ClassResult] = Field(None, description="Gloves detection results")
    Goggles: Optional[ClassResult] = Field(None, description="Goggles detection results")
    Hardhat: Optional[ClassResult] = Field(None, description="Hardhat detection results")
    Mask: Optional[ClassResult] = Field(None, description="Mask detection results")
    Safety_Vest: Optional[ClassResult] = Field(None, alias="Safety Vest", description="Safety Vest detection results")
    
    # Dynamic class results (for any model)
    class_results: Optional[Dict[str, ClassResult]] = Field(None, description="All class detection results")
    
    # Model info
    model_name: Optional[str] = Field(None, description="Model used for detection")
    
    # Overall metrics
    total_detections: int = Field(..., ge=0, description="Total detections across all classes")
    avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Average confidence across all detections")
    processing_time: float = Field(..., ge=0.0, description="Processing time in seconds")
    
    # Image info
    image_dimensions: Dict[str, int] = Field(
        ..., 
        description="Image dimensions (width, height)"
    )
    
    # Metadata
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Analysis timestamp"
    )
    
    class Config:
        populate_by_name = True
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Analysis completed successfully",
                "annotated_image": "data:image/jpeg;base64,/9j/4AAQ...",
                "original_image": "data:image/jpeg;base64,/9j/4AAQ...",
                "model_name": "corrosion",
                "class_results": {
                    "corrosion": {
                        "detected": True,
                        "count": 2,
                        "avg_confidence": 0.85,
                        "regions": [],
                        "surface_coverage": 15.3,
                        "risk_level": "Medium"
                    }
                },
                "total_detections": 2,
                "processing_time": 0.234,
                "image_dimensions": {"width": 1920, "height": 1080},
                "timestamp": "2024-01-30T10:30:00"
            }
        }


class VideoAnalysisResponse(BaseModel):
    """Response for video analysis"""
    success: bool = Field(..., description="Whether analysis succeeded")
    message: str = Field(..., description="Status message")
    
    # Video output
    video_url: str = Field(..., description="URL to download annotated video")
    
    # Detection results per class - now using Optional fields
    corrosion: Optional[ClassResult] = Field(None, description="Corrosion detection results")
    crack: Optional[ClassResult] = Field(None, description="Crack detection results")
    leak: Optional[ClassResult] = Field(None, description="Leak detection results")
    
    # PPE classes
    Person: Optional[ClassResult] = Field(None, description="Person detection results")
    Gloves: Optional[ClassResult] = Field(None, description="Gloves detection results")
    Goggles: Optional[ClassResult] = Field(None, description="Goggles detection results")
    Hardhat: Optional[ClassResult] = Field(None, description="Hardhat detection results")
    Mask: Optional[ClassResult] = Field(None, description="Mask detection results")
    Safety_Vest: Optional[ClassResult] = Field(None, alias="Safety Vest", description="Safety Vest detection results")
    
    # Dynamic class results (for any model)
    class_results: Optional[Dict[str, ClassResult]] = Field(None, description="All class detection results")
    
    # Model info
    model_name: Optional[str] = Field(None, description="Model used for detection")
    
    # Video-specific metrics
    total_detections: int = Field(..., ge=0, description="Total detections in entire video")
    processed_frames: int = Field(..., ge=0, description="Number of frames analyzed")
    frames_with_detections: Optional[Dict[str, int]] = Field(None, description="Frames with each class")
    max_detections_in_frame: int = Field(..., ge=0, description="Max detections in single frame")
    avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Average confidence across all detections")
    
    # Performance metrics
    processing_time: float = Field(..., ge=0.0, description="Total processing time")
    video_duration: float = Field(..., ge=0.0, description="Original video duration")
    fps: float = Field(..., ge=0.0, description="Video FPS")
    
    # Metadata
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Analysis timestamp"
    )
    
    class Config:
        populate_by_name = True
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Video analysis completed",
                "video_url": "/outputs/analyzed_20240130_103000.mp4",
                "model_name": "inspection",
                "class_results": {
                    "corrosion": {
                        "detected": True,
                        "count": 45,
                        "avg_confidence": 0.82,
                        "regions": [],
                        "surface_coverage": 8.5,
                        "risk_level": "Medium"
                    }
                },
                "total_detections": 57,
                "processed_frames": 150,
                "max_detections_in_frame": 8,
                "processing_time": 45.6,
                "video_duration": 30.0,
                "fps": 30,
                "timestamp": "2024-01-30T10:30:00"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    version: str = Field(..., description="Application version")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_path: Optional[str] = Field(None, description="Path to model weights")
    device: str = Field(..., description="Computation device (cuda/cpu)")

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "model_loaded": True,
                "model_path": "weights/best.pt",
                "device": "cuda:0"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = Field(default=False, description="Always false for errors")
    message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Error timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Invalid file type",
                "error_type": "ValidationError",
                "timestamp": "2024-01-30T10:30:00"
            }
        }


class StreamResponse(BaseModel):
    """Response for stream operations"""
    success: bool = Field(..., description="Whether operation succeeded")
    stream_id: Optional[str] = Field(None, description="Stream identifier")
    model: str = Field(..., description="Model name being used")
    status: str = Field(..., description="Stream status")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "stream_id": "stream_abc123",
                "model": "corrosion",
                "status": "active",
                "message": "Stream started successfully"
            }
        }


class MultiModelHealthResponse(BaseModel):
    """Health check response for multi-model API"""
    status: str = Field(..., description="Overall system status")
    version: str = Field(..., description="API version")
    models: Dict[str, bool] = Field(..., description="Model loading status")
    device: str = Field(..., description="Device being used (cpu/cuda)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Health check timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "models": {
                    "corrosion": True,
                    "ppe": True,
                    "inspection": True
                },
                "device": "cpu",
                "timestamp": "2024-01-30T10:30:00"
            }
        }
