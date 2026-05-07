"""
Test script to debug detection box coordinates
"""
import cv2
import numpy as np
from pathlib import Path
from app.inference_multimodel import MultiModelEngine

# Initialize engine
MODEL_PATHS = {
    "corrosion": Path("Weights_final/Corrosion_best.pt"),
    "ppe": Path("Weights_final/PPE_best.pt"),
    "inspection": Path("Weights_final/Inspection_best.pt")
}

engine = MultiModelEngine(MODEL_PATHS)

# Test with a sample image
test_image_path = r"Rust_Detection_Samples\rust_input_1.JPG"

if Path(test_image_path).exists():
    print(f"Loading test image: {test_image_path}")
    image = cv2.imread(test_image_path)
    
    if image is not None:
        print(f"Image shape: {image.shape}")
        h, w = image.shape[:2]
        print(f"Image dimensions: {w}x{h}")
        
        # Run detection
        print("\nRunning detection with corrosion model...")
        detections = engine.detect_image(image, "corrosion")
        
        print(f"\nDetections found:")
        for class_name, class_dets in detections.items():
            print(f"\n{class_name}: {len(class_dets)} detections")
            for i, det in enumerate(class_dets):
                bbox = det["bbox"]
                conf = det["confidence"]
                x, y, bw, bh = bbox
                print(f"  Detection {i+1}:")
                print(f"    Confidence: {conf:.3f}")
                print(f"    BBox (x, y, w, h): {x}, {y}, {bw}, {bh}")
                print(f"    Bottom-right would be: ({x+bw}, {y+bh})")
                print(f"    As percentage of image: x={x/w*100:.1f}%, y={y/h*100:.1f}%, w={bw/w*100:.1f}%, h={bh/h*100:.1f}%")
                
                # Check if coordinates are reasonable
                if x < 0 or y < 0:
                    print(f"    ⚠️ WARNING: Negative coordinates!")
                if x + bw > w or y + bh > h:
                    print(f"    ⚠️ WARNING: Box extends beyond image boundaries!")
                if bw <= 0 or bh <= 0:
                    print(f"    ⚠️ WARNING: Invalid box dimensions!")
        
        # Draw and save annotated image
        annotated = engine.draw_detections(image, detections, "corrosion")
        output_path = "outputs/test_detection_debug.jpg"
        cv2.imwrite(output_path, annotated)
        print(f"\n✓ Annotated image saved to: {output_path}")
        print("Please check this image to see if boxes are drawn correctly.")
    else:
        print("Failed to load image!")
else:
    print(f"Test image not found: {test_image_path}")
    print("Please update the test_image_path variable with a valid image path.")
