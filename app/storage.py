"""
storage.py - Storage Management
Handles file uploads, conversions, and cleanup
"""
import cv2
import numpy as np
import base64
import tempfile
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages file storage and conversions"""
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.output_dir = Path("outputs")
        
        # Ensure directories exist
        self.upload_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def read_image_from_bytes(self, file_bytes: bytes) -> Optional[np.ndarray]:
        """
        Read image from bytes
        
        Args:
            file_bytes: Image file content as bytes
        
        Returns:
            Image as numpy array (BGR) or None if invalid
        """
        try:
            # Decode image
            nparr = np.frombuffer(file_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Failed to decode image")
                return None
            
            logger.info(f"Image loaded: {image.shape}")
            return image
            
        except Exception as e:
            logger.error(f"Error reading image: {e}")
            return None
    
    def image_to_base64(self, image: np.ndarray, format: str = "jpg") -> str:
        """
        Convert image to base64 data URI
        
        Args:
            image: Image as numpy array (BGR)
            format: Output format ("jpg" or "png")
        
        Returns:
            Base64 encoded data URI string
        """
        try:
            # Encode image
            if format == "jpg":
                success, buffer = cv2.imencode(
                    '.jpg', 
                    image, 
                    [cv2.IMWRITE_JPEG_QUALITY, 95]
                )
                mime_type = "image/jpeg"
            elif format == "png":
                success, buffer = cv2.imencode('.png', image)
                mime_type = "image/png"
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            if not success:
                raise Exception("Failed to encode image")
            
            # Convert to base64
            b64_bytes = base64.b64encode(buffer)
            b64_string = b64_bytes.decode('utf-8')
            
            # Return as data URI
            return f"data:{mime_type};base64,{b64_string}"
            
        except Exception as e:
            logger.error(f"Error converting to base64: {e}")
            raise
    
    def base64_to_image(self, b64_string: str) -> Optional[np.ndarray]:
        """
        Convert base64 string to image
        
        Args:
            b64_string: Base64 encoded string (with or without data URI prefix)
        
        Returns:
            Image as numpy array or None
        """
        try:
            # Remove data URI prefix if present
            if "base64," in b64_string:
                b64_string = b64_string.split("base64,")[1]
            
            # Decode base64
            img_bytes = base64.b64decode(b64_string)
            nparr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return image
            
        except Exception as e:
            logger.error(f"Error decoding base64: {e}")
            return None
    
    def save_temp_file(self, file_obj: BinaryIO, suffix: str = ".mp4") -> Path:
        """
        Save uploaded file to temporary location
        
        Args:
            file_obj: File object
            suffix: File extension
        
        Returns:
            Path to saved file
        """
        try:
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                dir=self.upload_dir
            )
            
            # Write content
            file_obj.seek(0)
            temp_file.write(file_obj.read())
            temp_file.close()
            
            temp_path = Path(temp_file.name)
            logger.info(f"Saved temp file: {temp_path}")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Error saving temp file: {e}")
            raise
    
    def save_image(self, image: np.ndarray, prefix: str = "result") -> Path:
        """
        Save image to output directory
        
        Args:
            image: Image as numpy array
            prefix: Filename prefix
        
        Returns:
            Path to saved file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.jpg"
            filepath = self.output_dir / filename
            
            cv2.imwrite(str(filepath), image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            logger.info(f"Saved image: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            raise
    
    def cleanup_file(self, filepath: Path):
        """
        Delete a file
        
        Args:
            filepath: Path to file
        """
        try:
            if filepath.exists():
                filepath.unlink()
                logger.debug(f"Deleted: {filepath}")
        except Exception as e:
            logger.error(f"Error deleting {filepath}: {e}")
    
    def get_file_size(self, filepath: Path) -> int:
        """
        Get file size in bytes
        
        Args:
            filepath: Path to file
        
        Returns:
            File size in bytes
        """
        try:
            return filepath.stat().st_size
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return 0
    
    def validate_image_size(self, file_size: int, max_size: int = 50 * 1024 * 1024) -> bool:
        """
        Validate image file size
        
        Args:
            file_size: File size in bytes
            max_size: Maximum allowed size (default 50MB)
        
        Returns:
            True if valid, False otherwise
        """
        return file_size <= max_size
    
    def validate_video_size(self, file_size: int, max_size: int = 500 * 1024 * 1024) -> bool:
        """
        Validate video file size
        
        Args:
            file_size: File size in bytes
            max_size: Maximum allowed size (default 500MB)
        
        Returns:
            True if valid, False otherwise
        """
        return file_size <= max_size
    
    def cleanup_old_files(self, directory: Path = None, max_age_hours: int = 24):
        """
        Clean up old files in directory
        
        Args:
            directory: Directory to clean (default: upload_dir)
            max_age_hours: Maximum file age in hours
        """
        if directory is None:
            directory = self.upload_dir
        
        try:
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            deleted_count = 0
            for file_path in directory.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    
                    if file_age > max_age_seconds:
                        self.cleanup_file(file_path)
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old files from {directory}")
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def list_output_files(self) -> list:
        """
        List all files in output directory
        
        Returns:
            List of file paths
        """
        try:
            return list(self.output_dir.glob("*"))
        except Exception as e:
            logger.error(f"Error listing output files: {e}")
            return []
    
    def get_output_url(self, filename: str) -> str:
        """
        Get URL for output file
        
        Args:
            filename: Output filename
        
        Returns:
            URL path
        """
        return f"/outputs/{filename}"
