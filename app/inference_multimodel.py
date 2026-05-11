"""
inference_multimodel.py - Multi-Model Detection Engine
Supports multiple YOLO models for different detection tasks:
- Corrosion: corrosion, crack, leak detection
- PPE: helmet, vest, goggles, gloves, no-helmet, no-vest detection
- Inspection: defect, damage, anomaly detection
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration per model type
MODEL_CONFIGS = {
    "corrosion": {
        "CONF_THRESHOLD": 0.05,  
        "IOU_THRESHOLD": 0.30,
        "IMG_SIZE": 960,
        "CLASS_NAMES": ["corrosion"],
        "CLASS_CONF_THRESHOLDS": {0: 0.05},  # Match CONF_THRESHOLD
        "COLORS": {
            "corrosion": (0, 0, 255)       # Red
        }
    },
    "ppe": {
        "CONF_THRESHOLD": 0.05,
        "IOU_THRESHOLD": 0.30,
        "IMG_SIZE": 640,
        "CLASS_NAMES": ["Person", "Gloves", "Goggles", "Hardhat", "Mask", "Safety Vest"],
        "CLASS_CONF_THRESHOLDS": {0: 0.05, 1: 0.05, 2: 0.05, 3: 0.05, 4: 0.05, 5: 0.05},
        "COLORS": {
            "Person": (255, 128, 0),       # Orange
            "Gloves": (0, 200, 100),       # Green
            "Goggles": (255, 200, 0),      # Gold
            "Hardhat": (0, 255, 255),      # Yellow
            "Mask": (255, 0, 255),         # Magenta
            "Safety Vest": (0, 255, 200)   # Cyan
        }
    },
    "inspection": {
        "CONF_THRESHOLD": 0.001,  # Very low for crack/leak
        "IOU_THRESHOLD": 0.25,
        "IMG_SIZE": 768,
        "CLASS_NAMES": ["corrosion", "crack", "leak"],
        "CLASS_CONF_THRESHOLDS": {0: 0.05, 1: 0.006, 2: 0.005},  # Increased crack threshold to reduce false positives
        "COLORS": {
            "corrosion": (0, 0, 255),      # Red
            "crack": (0, 165, 255),        # Orange
            "leak": (255, 0, 255)          # Magenta
        }
    }
}

# Common config - relaxed filters for better detection
COMMON_CONFIG = {
     "MIN_BOX_AREA":       100,    # was 4 — filters out pixel-noise detections
    "MAX_BOX_AREA_RATIO": 0.85,   # was 0.99 — ignores near-full-frame boxes (usually FP)
    "MIN_ASPECT_RATIO":   0.04,   # was 0.005 — still allows thin cracks, rejects 1px slivers
    "MAX_ASPECT_RATIO":   50.0,   # was 200 — 50:1 is already very elongated for a real crack
    "DEVICE": "cpu",
}


class MultiModelEngine:
    """
    Multi-Model Detection Engine
    Manages multiple YOLO models for different detection tasks
    """
    
    def __init__(self, model_paths: Dict[str, str]):
        """
        Initialize with dictionary of model paths
        
        Args:
            model_paths: Dict mapping model names to weight file paths
                        e.g., {"corrosion": "path/to/corrosion.pt", "ppe": "path/to/ppe.pt"}
        """
        self.model_paths = model_paths
        self.models = {}
        self.device = COMMON_CONFIG["DEVICE"]
        
        # Load all models
        for model_name, model_path in model_paths.items():
            try:
                self._load_model(model_name, model_path)
            except Exception as e:
                logger.error(f"Failed to load {model_name} model: {e}")
                self.models[model_name] = None
    
    def _load_model(self, model_name: str, model_path: str): 
        """Load a single YOLO model"""
        try:
            path = Path(model_path)
            if not path.exists():
                logger.warning(f"Model not found at {model_path}. {model_name} will use mock mode.")
                self.models[model_name] = None
                return
            
            from ultralytics import YOLO
            
            logger.info(f"Loading {model_name} model from {model_path}")
            model = YOLO(str(model_path))
            model.to(self.device)
            
            self.models[model_name] = model
            
            # Update class names from model if available
            if hasattr(model, 'names'):
                actual_classes = list(model.names.values())
                if model_name in MODEL_CONFIGS:
                    MODEL_CONFIGS[model_name]["CLASS_NAMES"] = actual_classes
                    # Generate colors for any new class names
                    existing_colors = MODEL_CONFIGS[model_name].get("COLORS", {})
                    color_palette = [
                        (255, 128, 0), (0, 255, 128), (128, 0, 255), (255, 255, 0),
                        (0, 255, 255), (255, 0, 255), (128, 255, 0), (0, 128, 255),
                        (255, 0, 128), (0, 255, 0), (255, 128, 128), (128, 128, 255)
                    ]
                    for i, cls in enumerate(actual_classes):
                        if cls not in existing_colors:
                            existing_colors[cls] = color_palette[i % len(color_palette)]
                    MODEL_CONFIGS[model_name]["COLORS"] = existing_colors
                    # Update class-specific thresholds
                    class_thresholds = MODEL_CONFIGS[model_name].get("CLASS_CONF_THRESHOLDS", {})
                    base_threshold = MODEL_CONFIGS[model_name].get("CONF_THRESHOLD", 0.15)
                    for i in range(len(actual_classes)):
                        if i not in class_thresholds:
                            class_thresholds[i] = base_threshold
                    MODEL_CONFIGS[model_name]["CLASS_CONF_THRESHOLDS"] = class_thresholds
                logger.info(f"✓ {model_name} model loaded, classes: {actual_classes}")
            
        except Exception as e:
            logger.error(f"Error loading {model_name} model: {e}", exc_info=True)
            self.models[model_name] = None
    
    def is_model_loaded(self, model_name: str) -> bool:
        """Check if a model is loaded"""
        return model_name in self.models and self.models[model_name] is not None
    
    def get_class_names(self, model_name: str) -> List[str]:
        """Get class names for a model"""
        if model_name in MODEL_CONFIGS:
            return MODEL_CONFIGS[model_name]["CLASS_NAMES"]
        return []
    
    def get_config(self, model_name: str) -> dict:
        """Get configuration for a model"""
        return MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["corrosion"])
    
    def detect_image(self, image: np.ndarray, model_name: str) -> Dict[str, List[Dict]]:
        """
        Run detection on an image with specified model
        
        Args:
            image: Input image (BGR format)
            model_name: Name of the model to use
            
        Returns:
            Dictionary mapping class names to list of detections
        """
        config = self.get_config(model_name) # Get model-specific config
        class_names = config["CLASS_NAMES"] 
        
        # Initialize empty detections
        detections = {name: [] for name in class_names}
        
        # Check if model is loaded
        if not self.is_model_loaded(model_name):
            logger.warning(f"{model_name} model not loaded, using mock detection")
            return self._mock_detect(image, model_name)
        
        model = self.models[model_name]
        
        # Run inference
        results = model(
            image,
            imgsz=config["IMG_SIZE"],
            conf=config["CONF_THRESHOLD"],
            iou=config["IOU_THRESHOLD"],
            device=self.device,
            verbose=False
        )[0]
        
        if results.boxes is None:
            return detections
        
        h, w = image.shape[:2]
        logger.info(f"  Raw detections: {len(results.boxes)} boxes")
        
        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            # Get class name first for logging
            if cls < len(class_names):
                class_name = class_names[cls]
            else:
                class_name = f"class_{cls}"
            
            # Class-wise confidence threshold
            class_thresholds = config.get("CLASS_CONF_THRESHOLDS", {})
            threshold = class_thresholds.get(cls, config["CONF_THRESHOLD"])
            if conf < threshold:
                logger.debug(f"  Skipped {class_name} (conf {conf:.2f} < {threshold})")
                continue
            
            # Get bbox
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            bw = x2 - x1
            bh = y2 - y1
            area = bw * bh
            
            # Area filtering
            if area < COMMON_CONFIG["MIN_BOX_AREA"]:
                logger.debug(f"  Skipped {class_name} (area {area:.0f} < {COMMON_CONFIG['MIN_BOX_AREA']})")
                continue
            if area > COMMON_CONFIG["MAX_BOX_AREA_RATIO"] * (w * h):
                logger.debug(f"  Skipped {class_name} (area ratio too large)")
                continue
            
            # Aspect ratio filtering
            aspect = max(bw, bh) / (min(bw, bh) + 1e-6)
            if aspect < COMMON_CONFIG["MIN_ASPECT_RATIO"] or aspect > COMMON_CONFIG["MAX_ASPECT_RATIO"]:
                logger.debug(f"  Skipped {class_name} (aspect {aspect:.2f} out of range)")
                continue
            
            detections[class_name].append({
                "bbox": [int(x1), int(y1), int(bw), int(bh)],
                "confidence": conf,
                "class_id": cls,
                "class_name": class_name
            })
            logger.info(f"  Detected: {class_name} (conf: {conf:.2f})")
        
        return detections
    
    def _mock_detect(self, image: np.ndarray, model_name: str) -> Dict[str, List[Dict]]:
        """Generate mock detections for testing"""
        config = self.get_config(model_name)
        class_names = config["CLASS_NAMES"]
        height, width = image.shape[:2]
        
        detections = {name: [] for name in class_names}
        
        # Generate random detections for the first class
        if class_names:
            num_dets = np.random.randint(1, 4)
            for i in range(num_dets):
                x = np.random.randint(0, max(1, width - 200))
                y = np.random.randint(0, max(1, height - 200))
                w = np.random.randint(50, min(200, width - x))
                h = np.random.randint(50, min(200, height - y))
                conf = np.random.uniform(0.5, 0.95)
                
                detections[class_names[0]].append({
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "confidence": float(conf),
                    "class_id": 0,
                    "class_name": class_names[0]
                })
        
        return detections
    
    def calculate_metrics(self, detections: Dict[str, List[Dict]], 
                         image_shape: Tuple, model_name: str) -> Dict:
        """Calculate class-specific metrics"""
        from app.schemas import ClassResult, Detection, BoundingBox
        
        config = self.get_config(model_name)
        class_names = config["CLASS_NAMES"]
        height, width = image_shape[:2]
        
        results = {}
        
        for class_name in class_names:
            class_dets = detections.get(class_name, [])
            
            detected = len(class_dets) > 0
            count = len(class_dets)
            avg_conf = np.mean([d["confidence"] for d in class_dets]) if class_dets else 0.0
            
            # Calculate class-specific metrics
            surface_coverage = None
            total_length = None
            
            if class_name == "corrosion":
                surface_coverage = self._calc_coverage(class_dets, width, height)
            elif class_name == "crack":
                total_length = self._calc_length(class_dets, width)
            
            # Calculate risk level
            risk = self._calc_risk(class_name, count, surface_coverage, total_length, model_name)
            
            # Convert to Detection objects
            det_objects = [
                Detection(
                    bbox=BoundingBox(
                        x=int(d["bbox"][0]),
                        y=int(d["bbox"][1]),
                        width=int(d["bbox"][2]),
                        height=int(d["bbox"][3])
                    ),
                    confidence=d["confidence"],
                    class_id=d["class_id"],
                    class_name=d["class_name"]
                )
                for d in class_dets
            ]
            
            results[class_name] = ClassResult(
                detected=detected,
                count=count,
                avg_confidence=float(avg_conf),
                regions=det_objects,
                surface_coverage=surface_coverage,
                total_length=total_length,
                risk_level=risk
            )
        
        return results
    
    def _calc_coverage(self, detections: List[Dict], width: int, height: int) -> float:
        """Calculate surface coverage using binary mask"""
        if not detections:
            return 0.0
        
        mask = np.zeros((height, width), dtype=np.uint8)
        
        for det in detections:
            x, y, w, h = [int(v) for v in det["bbox"]]
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = min(w, width - x)
            h = min(h, height - y)
            mask[y:y+h, x:x+w] = 1
        
        covered = np.sum(mask)
        total = width * height
        return (covered / total) * 100.0
    
    def _calc_length(self, detections: List[Dict], width: int) -> float:
        """Calculate crack length (normalized)"""
        if not detections:
            return 0.0
        
        total_length = sum(np.sqrt(d["bbox"][2]**2 + d["bbox"][3]**2) for d in detections)
        return total_length / width
    
    def _calc_risk(self, class_name: str, count: int, 
                   coverage: Optional[float], length: Optional[float],
                   model_name: str) -> str:
        """Calculate risk level based on model and class"""
        
        # Corrosion model risks (single class: corrosion)
        if model_name == "corrosion":
            cov = coverage or 0
            if cov >= 70 or count >= 5:
                return "Critical"
            elif cov >= 40 or count >= 3:
                return "High"
            elif cov >= 20 or count >= 2:
                return "Medium"
            elif count >= 1:
                return "Low"
            return "None"
        
        # PPE model risks - all are positive detections
        elif model_name == "ppe":
            # Person detection doesn't have risk
            if class_name == "Person":
                return "Info"
            # PPE equipment detections are good (compliance)
            if count >= 1:
                return "Compliant"
            return "Missing"
        
        # Inspection model risks (corrosion, crack, leak)
        elif model_name == "inspection":
            if class_name == "corrosion":
                cov = coverage or 0
                if cov >= 70 or count >= 5:
                    return "Critical"
                elif cov >= 40 or count >= 3:
                    return "High"
                elif cov >= 20 or count >= 2:
                    return "Medium"
                return "Low"
            
            elif class_name == "crack":
                len_val = length or 0
                if len_val >= 1.5 or count >= 5:
                    return "Critical"
                elif len_val >= 1.0 or count >= 3:
                    return "High"
                elif len_val >= 0.5 or count >= 2:
                    return "Medium"
                return "Low"
            
            elif class_name == "leak":
                if count >= 5:
                    return "Critical"
                elif count >= 3:
                    return "High"
                elif count >= 2:
                    return "Medium"
                return "Low"
        
        return "Low"
    
    def draw_detections(self, image: np.ndarray, 
                       detections: Dict[str, List[Dict]],
                       model_name: str) -> np.ndarray:
        """Draw bounding boxes on image"""
        annotated = image.copy()
        
        config = self.get_config(model_name)
        colors = config.get("COLORS", {})
        default_color = (0, 255, 0)  # Green
        
        for class_name, class_dets in detections.items():
            color = colors.get(class_name, default_color)
            
            for det in class_dets:
                x, y, w, h = det["bbox"]
                conf = det["confidence"]
                
                # Draw box
                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 3)
                
                # Draw label
                label = f"{class_name}: {conf:.2f}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                
                (text_w, text_h), baseline = cv2.getTextSize(
                    label, font, font_scale, thickness
                )
                
                # Background
                cv2.rectangle(
                    annotated,
                    (x, y - text_h - 10),
                    (x + text_w + 10, y),
                    color,
                    -1
                )
                
                # Text
                cv2.putText(
                    annotated,
                    label,
                    (x + 5, y - 5),
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness
                )
        
        return annotated
    
    def detect_video(self, video_path: str, output_path: str, 
                    model_name: str) -> Dict:
        """
        Process video with specified model
        
        Args:
            video_path: Input video path
            output_path: Output video path
            model_name: Model to use for detection
            
        Returns:
            Dictionary with video analysis results
        """
        # Ensure paths are strings for OpenCV
        video_path_str = str(video_path)
        output_path_str = str(output_path)
        
        cap = cv2.VideoCapture(video_path_str)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path_str}")
        
        config = self.get_config(model_name)
        class_names = config["CLASS_NAMES"]
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        # Use mp4v codec (universally available; FFmpeg re-encodes to H.264 later)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path_str, fourcc, fps, (width, height))
        
        if not out.isOpened():
            # Fallback to XVID if mp4v unavailable
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            output_path_str_avi = output_path_str.replace('.mp4', '.avi')
            out = cv2.VideoWriter(output_path_str_avi, fourcc, fps, (width, height))
        
        if not out.isOpened():
            logger.error(f"Failed to create video writer: {output_path_str}")
            cap.release()
            raise RuntimeError(f"Failed to create video writer: {output_path_str}")
        
        # Stats tracking
        frame_count = 0
        total_detections = 0
        max_detections = 0
        all_confidences = []
        frames_with_class = {name: 0 for name in class_names}
        class_total_counts = {name: 0 for name in class_names}
        
        # Process every Nth frame for speed, but keep last detections for smooth drawing
        process_every = max(1, int(fps / 10))  # ~10 FPS processing for smoother tracking
        last_detections = {}  # Cache last detections for smooth box drawing
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            if frame_count % process_every == 0:
                # Detect on key frames
                detections = self.detect_image(frame, model_name)
                last_detections = detections  # Cache for subsequent frames
                
                # Track stats
                frame_total = 0
                for class_name, class_dets in detections.items():
                    if class_dets:
                        frames_with_class[class_name] += 1
                        class_total_counts[class_name] += len(class_dets)
                        frame_total += len(class_dets)
                        for det in class_dets:
                            all_confidences.append(det["confidence"])
                
                total_detections += frame_total
                max_detections = max(max_detections, frame_total)
            
            # Always draw using last known detections for stable boxes
            annotated = self.draw_detections(frame, last_detections, model_name)
            out.write(annotated)
        
        cap.release()
        out.release()
        
        processed_frames = frame_count // process_every
        avg_confidence = np.mean(all_confidences) if all_confidences else 0.0
        
        result = {
            "total_detections": total_detections,
            "processed_frames": processed_frames,
            "max_detections": max_detections,
            "avg_confidence": float(avg_confidence),
            "duration": duration,
            "fps": fps
        }
        
        # Add per-class frame counts
        for class_name in class_names:
            result[f"frames_with_{class_name}"] = frames_with_class[class_name]
        
        # Add class results
        for class_name in class_names:
            count = class_total_counts[class_name]
            result[class_name] = {
                "detected": count > 0,
                "count": count,
                "avg_confidence": 0.0,
                "regions": [],
                "risk_level": self._calc_risk(class_name, count, None, None, model_name)
            }
        
        return result
