"""Quick test to verify detector initialization."""
import sys
print("Testing detector initialization...")

try:
    from core.detector import VehicleDetector
    print("[OK] Imported VehicleDetector")
    
    print("Initializing detector...")
    detector = VehicleDetector(confidence=0.5)
    print("[OK] Detector initialized successfully!")
    print(f"Model loaded: YOLOv8")
    print(f"Confidence threshold: {detector.confidence}")
    print("\n[SUCCESS] All tests passed!")
    
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
