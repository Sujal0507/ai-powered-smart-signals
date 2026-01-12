"""
Test script for ITMS components.
Verifies that all modules are working correctly.
"""

import sys
import os


def print_status(msg, success):
    symbol = "[OK]" if success else "[FAIL]"
    print(f"  {symbol} {msg}")

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        from core.database import DatabaseManager, TrafficLog
        print_status("Database module", True)
    except Exception as e:
        print_status(f"Database module: {e}", False)
        return False
    
    try:
        from core.detector import VehicleDetector, MultiLaneDetectionSystem
        print_status("Detector module", True)
    except Exception as e:
        print_status(f"Detector module: {e}", False)
        return False
    
    try:
        from core.traffic_logic import TrafficSignalController, SignalState
        print_status("Traffic logic module", True)
    except Exception as e:
        print_status(f"Traffic logic module: {e}", False)
        return False
    
    return True

def test_database():
    """Test database operations."""
    print("\nTesting database...")
    
    try:
        from core.database import DatabaseManager
        
        # Create test database
        db = DatabaseManager('data/test_traffic.db')
        
        # Test logging
        test_counts = {'car': 5, 'bus': 2, 'truck': 1}
        db.log_traffic_cycle(1, test_counts, False, 30.0, 'NORMAL')
        
        # Test retrieval
        stats = db.get_today_stats()
        
        print_status("Database operations successful", True)
        print(f"    - Logged test cycle")
        print(f"    - Retrieved stats: {stats}")
        
        # Cleanup
        db.close()
        if os.path.exists('data/test_traffic.db'):
            os.remove('data/test_traffic.db')
        
        return True
        
    except Exception as e:
        print_status(f"Database test failed: {e}", False)
        return False

def test_detector_initialization():
    """Test detector initialization."""
    print("\nTesting detector initialization...")
    
    try:
        from core.detector import VehicleDetector
        
        detector = VehicleDetector(confidence=0.5)
        print_status("Detector initialized", True)
        print(f"    - Model: YOLOv8n")
        print(f"    - Confidence: {detector.confidence}")
        
        return True
        
    except Exception as e:
        print_status(f"Detector initialization failed: {e}", False)
        return False

def test_traffic_controller():
    """Test traffic controller initialization."""
    print("\nTesting traffic controller...")
    
    try:
        from core.traffic_logic import TrafficSignalController, SignalState
        
        # Create mock objects
        class MockDetector:
            def get_lane_data(self, lane_id):
                return None, {'car': 5}, False
            
            def get_all_lane_data(self):
                return {i: {'frame': None, 'counts': {}, 'ambulance': False, 'total': 0} 
                       for i in range(1, 5)}
        
        class MockDB:
            def log_traffic_cycle(self, *args, **kwargs):
                pass
        
        controller = TrafficSignalController(MockDetector(), MockDB())
        
        print_status("Traffic controller initialized", True)
        print(f"    - Current lane: {controller.current_lane}")
        print(f"    - Mode: {controller.mode.value}")
        
        # Test timing calculation
        durations = {
            20: controller.calculate_green_duration(20),
            10: controller.calculate_green_duration(10),
            3: controller.calculate_green_duration(3)
        }
        
        print(f"    - Timing algorithm:")
        for count, duration in durations.items():
            print(f"      {count} vehicles -> {duration}s green")
        
        return True
        
    except Exception as e:
        print_status(f"Traffic controller test failed: {e}", False)
        return False

def test_video_file():
    """Test if video file exists."""
    print("\nChecking video file...")
    
    video_path = 'assets/traffic.mp4'
    if os.path.exists(video_path):
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        print_status(f"Video file found ({size_mb:.2f} MB)", True)
        return True
    else:
        print_status(f"Video file not found: {video_path}", False)
        print("    System will not start without video file")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("  ITMS SYSTEM TEST")
    print("=" * 70)
    print()
    
    tests = [
        ("Module Imports", test_imports),
        ("Database Operations", test_database),
        ("Detector Initialization", test_detector_initialization),
        ("Traffic Controller", test_traffic_controller),
        ("Video File", test_video_file)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status}: {name}")
    
    print("\n" + "=" * 70)
    print(f"  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("  Status: [OK] ALL TESTS PASSED - System ready!")
    else:
        print("  Status: [FAIL] Some tests failed - Check errors above")
    
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)