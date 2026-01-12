"""
Vehicle detection system using YOLOv8.
Handles multiple video streams for traffic signal control.
"""

import cv2
import threading
import time
import numpy as np
import torch

# Fix for PyTorch 2.6 weights_only=True default
# Monkey-patch ultralytics to use weights_only=False for trusted YOLOv8 models
try:
    import ultralytics.nn.tasks as tasks
    original_torch_safe_load = tasks.torch_safe_load
    
    def patched_torch_safe_load(file, *args, **kwargs):
        """Patched version that uses weights_only=False for YOLOv8 models."""
        try:
            # Try to load with weights_only=False (safe for trusted ultralytics models)
            return torch.load(file, map_location='cpu', weights_only=False), file
        except Exception:
            # Fallback to original function
            return original_torch_safe_load(file, *args, **kwargs)
    
    tasks.torch_safe_load = patched_torch_safe_load
    print("Applied PyTorch 2.6 compatibility patch for YOLOv8")
except Exception as e:
    print(f"Warning: Could not apply PyTorch 2.6 patch: {e}")

from ultralytics import YOLO

class VehicleDetector:
    """
    YOLOv8-based vehicle detector.
    Identifies vehicles and ambulances in video frames.
    """
    def __init__(self, model_path='yolov8n.pt', confidence=0.5):
        """
        Initialize detection model.
        
        Args:
            model_path: Path to YOLOv8 model weights
            confidence: Detection confidence threshold
        """
        self.model = YOLO(model_path)
        self.confidence = confidence
        
        # COCO Class IDs for vehicles
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        
        # Mapping for display
        self.class_names = {
            2: 'car',
            3: 'motorcycle',
            5: 'bus',
            7: 'truck'
        }
        
        print(f"VehicleDetector initialized with {model_path}")

    def detect(self, frame):
        """
        Run detection on a single frame.
        
        Args:
            frame: OpenCV image array
            
        Returns:
            annotated_frame: Frame with bounding boxes
            counts: Dictionary of vehicle counts
            ambulance_detected: Boolean indicating ambulance presence
        """
        if frame is None:
            return None, {}, False
            
        results = self.model(frame, conf=self.confidence, verbose=False)[0]
        
        counts = {'car': 0, 'bus': 0, 'truck': 0, 'motorcycle': 0}
        ambulance_detected = False
        
        # Process detections
        for box in results.boxes:
            cls_id = int(box.cls[0])
            
            # Count vehicles
            if cls_id in self.vehicle_classes:
                name = self.class_names.get(cls_id, 'vehicle')
                counts[name] = counts.get(name, 0) + 1
            
            # Check for ambulance (Custom logic or specific class)
            # Standard YOLOv8 COCO doesn't have ambulance, but we can 
            # simulate it or if we had a custom model we'd check for that class.
            # For this MVP, we might simulate ambulance if a specific visual marker is seen
            # or if we were using a custom trained model.
            # Here we will assume if the model detects 'truck' with high confidence 
            # and it's white/red (mock logic) OR just if we had an ambulance class.
            # Since user asked for placeholder:
            if hasattr(self.model.names, 'get'):
                class_name = self.model.names.get(cls_id)
                if class_name == 'ambulance':
                    ambulance_detected = True
        
        annotated_frame = results.plot()
        return annotated_frame, counts, ambulance_detected

    def update_confidence(self, new_conf):
        self.confidence = new_conf


class LaneVideoProcessor(threading.Thread):
    """
    Background thread to process video for a single lane.
    """
    def __init__(self, lane_id, video_source, detector):
        super().__init__()
        self.lane_id = lane_id
        self.video_source = video_source
        self.detector = detector
        self.running = False
        self.latest_frame = None
        self.latest_counts = {'car': 0, 'bus': 0, 'truck': 0, 'motorcycle': 0}
        self.is_ambulance = False
        self.lock = threading.Lock()
        self.daemon = True

    def run(self):
        """Main loop for video processing."""
        self.running = True
        cap = cv2.VideoCapture(self.video_source)
        
        print(f"Started processor for Lane {self.lane_id}")
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
                continue
                
            # Resize for performance (optional, but good for CPU)
            frame = cv2.resize(frame, (640, 360))
            
            # Detect
            annotated_frame, counts, ambulance = self.detector.detect(frame)
            
            # Update state
            with self.lock:
                self.latest_frame = annotated_frame
                self.latest_counts = counts
                self.is_ambulance = ambulance
            
            # Simulate real-time (skip some sleep if needed for speed, or add to reduce load)
            time.sleep(0.03) 
            
        cap.release()
        print(f"Stopped processor for Lane {self.lane_id}")

    def get_data(self):
        with self.lock:
            # Return copy or current reference. 
            # If frame is large, might be better to return only when needed or encode it.
            return self.latest_frame, self.latest_counts.copy(), self.is_ambulance

    def stop(self):
        self.running = False


class MultiLaneDetectionSystem:
    """
    Manages detection for 4 lanes using threading.
    """
    def __init__(self, video_paths, confidence=0.5):
        """
        Args:
            video_paths: List of 4 video paths (one per lane)
            confidence: Initial confidence threshold
        """
        self.detector = VehicleDetector(confidence=confidence)
        self.processors = []
        
        for i, path in enumerate(video_paths, 1):
            if i > 4: break
            processor = LaneVideoProcessor(i, path, self.detector)
            self.processors.append(processor)

    def start(self):
        for p in self.processors:
            if not p.is_alive():
                p.start()

    def stop(self):
        for p in self.processors:
            p.stop()
        for p in self.processors:
            p.join(timeout=1.0)

    def get_lane_data(self, lane_id):
        """
        Get latest data for a specific lane.
        lane_id: 1-4
        """
        if 1 <= lane_id <= len(self.processors):
            return self.processors[lane_id-1].get_data()
        return None, {}, False

    def get_all_lane_data(self):
        data = {}
        for p in self.processors:
            frame, counts, ambulance = p.get_data()
            total = sum(counts.values())
            data[p.lane_id] = {
                'frame': frame,
                'counts': counts,
                'ambulance': ambulance,
                'total': total
            }
        return data

    def update_confidence(self, confidence):
        self.detector.update_confidence(confidence)
