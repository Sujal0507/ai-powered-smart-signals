"""
Quick start script for Intelligent Traffic Management System.
Handles setup verification and system launch.
"""

import os
import sys
import subprocess

def print_header():
    """Print welcome header."""
    print("=" * 70)
    print("  INTELLIGENT TRAFFIC MANAGEMENT SYSTEM (ITMS)")
    print("  MSc Major Project - AI-Powered Traffic Control")
    print("=" * 70)
    print()

def check_python_version():
    """Check if Python version is compatible."""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ✗ Python 3.8+ required (you have {version.major}.{version.minor})")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if all required packages are installed."""
    print("\n✓ Checking dependencies...")
    
    required = [
        'streamlit',
        'ultralytics',
        'cv2',
        'pandas',
        'sqlalchemy',
        'plotly'
    ]
    
    missing = []
    for package in required:
        try:
            if package == 'cv2':
                __import__('cv2')
            else:
                __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n  ⚠ Missing packages: {', '.join(missing)}")
        print("  Run: pip install -r requirements.txt")
        return False
    
    return True

def check_directories():
    """Ensure required directories exist."""
    print("\n✓ Checking directories...")
    
    directories = ['core', 'assets', 'data']
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"  Creating {directory}/")
            os.makedirs(directory, exist_ok=True)
        else:
            print(f"  ✓ {directory}/")
    
    return True

def check_video_file():
    """Check if video file exists."""
    print("\n✓ Checking video file...")
    
    video_path = 'assets/traffic.mp4'
    if os.path.exists(video_path):
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        print(f"  ✓ Video found ({size_mb:.2f} MB)")
        return True
    else:
        print(f"  ⚠ Video not found: {video_path}")
        print("\n  Please add a traffic video file:")
        print("  1. Download from: https://www.pexels.com/search/videos/traffic/")
        print("  2. Save as: assets/traffic.mp4")
        print("  3. Run this script again")
        return False

def check_core_files():
    """Check if core module files exist."""
    print("\n✓ Checking core files...")
    
    core_files = [
        'core/__init__.py',
        'core/detector.py',
        'core/traffic_logic.py',
        'core/database.py'
    ]
    
    all_exist = True
    for file in core_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (missing)")
            all_exist = False
    
    if not all_exist:
        print("\n  ⚠ Some core files are missing!")
        print("  Please ensure all project files are in place.")
        return False
    
    return True

def launch_streamlit():
    """Launch the Streamlit application."""
    print("\n" + "=" * 70)
    print("  LAUNCHING APPLICATION")
    print("=" * 70)
    print("\n  Starting Streamlit server...")
    print("  Dashboard will open in your browser automatically")
    print("  Press Ctrl+C to stop the server\n")
    print("=" * 70 + "\n")
    
    try:
        subprocess.run(['streamlit', 'run', 'app.py'])
    except KeyboardInterrupt:
        print("\n\n✓ System stopped successfully")
    except Exception as e:
        print(f"\n✗ Error launching Streamlit: {e}")
        return False
    
    return True

def main():
    """Main execution function."""
    print_header()
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Core Files", check_core_files),
        ("Video File", check_video_file)
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("  ✓ ALL CHECKS PASSED")
        print("=" * 70)
        
        # Launch application
        launch_streamlit()
    else:
        print("  ✗ SETUP INCOMPLETE")
        print("=" * 70)
        print("\n  Please fix the issues above and try again.")
        print("\n  Quick Setup:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Add video file: assets/traffic.mp4")
        print("  3. Run this script again: python run_system.py")
        sys.exit(1)

if __name__ == "__main__":
    main()