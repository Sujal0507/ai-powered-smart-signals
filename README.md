# 🚦 Intelligent Traffic Management System (ITMS)

**AI-Powered Traffic Signal Control using YOLOv8 for Vehicle Detection**

---

## 👨‍💻 Author

**Sujal Patel**  
MSc Big Data Analytics Student  
*This project demonstrates the application of computer vision and machine learning to solve real-world urban traffic challenges.*

---

## 🎯 Problem Statement

Traditional traffic signal systems operate on fixed timers, leading to several critical issues:

- **Inefficient Traffic Flow**: Signals remain green for 60 seconds even when no vehicles are present, while other lanes with heavy traffic wait unnecessarily.
- **Increased Congestion**: Static timing fails to adapt to real-time traffic conditions, causing bottlenecks during peak hours.
- **Emergency Vehicle Delays**: Ambulances and emergency vehicles get stuck in traffic, leading to potentially life-threatening delays in critical situations.
- **Wasted Time & Fuel**: Drivers spend unnecessary time at red lights, resulting in increased fuel consumption and carbon emissions.

**The Challenge**: How can we make traffic signals "intelligent" enough to adapt to real-time traffic conditions and prioritize emergency vehicles?

---

## 💡 Solution Overview

This system uses computer vision (YOLOv8) to detect vehicles in real-time across 4 traffic lanes and dynamically adjusts signal timing based on traffic density. It includes emergency vehicle (ambulance) detection for priority override.

## Features

- ✅ **Real-time Vehicle Detection** using YOLOv8
- ✅ **Dynamic Signal Timing** based on traffic density
- ✅ **Ambulance Detection** with emergency override
- ✅ **Multi-lane Processing** (4 lanes simultaneously)
- ✅ **Traffic Analytics** with database logging
- ✅ **Interactive Dashboard** built with Streamlit

## Requirements

- Python 3.8 or higher
- Windows/Linux/Mac
- Traffic video file (MP4 format)

## Installation

### 1. Clone or Download the Project

```bash
cd ai-signals-project
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics streamlit opencv-python-headless pandas sqlalchemy plotly
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

## Setup

### Get a Traffic Video

You need a traffic video file. Download from:

1. **Pexels** (Recommended): https://www.pexels.com/search/videos/traffic/
2. **Pixabay**: https://pixabay.com/videos/search/traffic/
3. **Videvo**: https://www.videvo.net/free-stock-video-footage/traffic/

**Tips:**
- Choose videos with clear vehicle visibility
- 30-60 seconds duration is ideal
- Higher resolution = better detection
- Daytime videos work best

### Place the Video

Save your traffic video as:
```
assets/traffic.mp4
```

The `assets/` folder will be created automatically, or create it manually:
```bash
mkdir assets
```

## Running the System

### Method 1: Quick Start (Recommended)

```bash
streamlit run app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

### Method 2: Using Setup Script

```bash
python run_system.py
```

This will:
- Check all dependencies
- Verify video file exists
- Launch the Streamlit dashboard

### Method 3: Test First

Run tests to verify everything is working:

```bash
python test_system.py
```

Then start the system:
```bash
streamlit run app.py
```

## Using the Dashboard

### 1. Start the System

1. Open the dashboard in your browser
2. Click **"🚀 Start System"** in the sidebar
3. Wait 15-30 seconds for initialization
4. YOLOv8 model will download automatically on first run (~6MB)

### 2. Monitor Traffic

- **Live Monitoring Tab**: View 4 video feeds with real-time detection
- **Analytics Tab**: See traffic statistics and charts
- **Logs Tab**: View detailed traffic cycle logs

### 3. Adjust Settings

- **Detection Confidence**: Adjust the slider (0.3 - 0.9)
  - Lower = More detections (may include false positives)
  - Higher = Fewer, more confident detections

### 4. Emergency Override

Use the **"🚨 Emergency Override"** buttons to manually trigger ambulance priority for any lane.

### 5. Stop the System

Click **"🛑 Stop System"** in the sidebar when done.

## How It Works

### Traffic Signal Logic

**Normal Mode:**
- Signals cycle through lanes 1 → 2 → 3 → 4 → 1
- Green duration = `Base Time (15s) + (Vehicle Count × 2s)`
- Maximum green time: 60 seconds
- Minimum green time: 15 seconds

**Emergency Mode:**
- Triggered when ambulance is detected
- Current lane immediately transitions to red (via yellow)
- Emergency lane gets green signal
- Extended green time: 45 seconds

### Vehicle Detection

- Uses YOLOv8n (nano) model for speed
- Detects: cars, buses, trucks, motorcycles
- Runs on CPU (no GPU required)
- Processes 4 video streams simultaneously

### Database

- SQLite database stores all traffic cycles
- Logs: timestamp, lane, vehicle counts, signal duration, mode
- Analytics generated from historical data

## Project Structure

```
ai-signals-project/
├── core/
│   ├── __init__.py           # Package initialization
│   ├── detector.py           # YOLOv8 vehicle detection
│   ├── traffic_logic.py      # Signal control logic
│   └── database.py           # SQLite database manager
├── assets/
│   └── traffic.mp4           # Traffic video (you provide this)
├── data/
│   └── traffic_data.db       # SQLite database (auto-created)
├── app.py                    # Main Streamlit dashboard
├── requirements.txt          # Python dependencies
├── run_system.py             # Setup and launch script
├── test_system.py            # System tests
└── README.md                 # This file
```

## Troubleshooting

### "Video file not found" Error

Make sure you have placed a video file at `assets/traffic.mp4`

### "DLL load failed" or Import Errors

Reinstall PyTorch:
```bash
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### "torch.classes" Warning

This is just a warning and can be ignored. The system will work fine.

### Slow Performance

- Use a shorter video (30-60 seconds)
- Lower the video resolution
- Reduce detection confidence threshold
- Close other applications

### No Vehicles Detected

- Check if video shows clear vehicles
- Lower the confidence threshold
- Ensure video has good lighting
- Try a different video

## Performance Tips

1. **Video Quality**: Use 720p or 1080p videos for best results
2. **Video Length**: 30-60 seconds is optimal (loops automatically)
3. **Lighting**: Daytime videos with good visibility work best
4. **Confidence**: Start with 0.5, adjust based on results
5. **CPU Usage**: System uses ~50-70% CPU on modern processors

## Known Limitations

- Ambulance detection is placeholder (standard YOLOv8 doesn't detect ambulances)
- For production ambulance detection, train a custom YOLOv8 model
- Uses same video for all 4 lanes (demo purposes)
- CPU-only (no GPU acceleration in this version)

## Future Enhancements

- [ ] Custom YOLOv8 model for ambulance detection
- [ ] Support for 4 different video sources
- [ ] GPU acceleration support
- [ ] Cloud deployment
- [ ] Mobile app integration
- [ ] Historical data visualization
- [ ] Traffic prediction using ML

## Technical Details

- **Framework**: Streamlit
- **Detection**: Ultralytics YOLOv8n
- **Database**: SQLite with SQLAlchemy
- **Visualization**: Plotly
- **Video Processing**: OpenCV
- **Threading**: Python threading for multi-lane processing

## Credits

- YOLOv8 by Ultralytics
- Streamlit for dashboard framework
- OpenCV for video processing

## License

This is an academic project for educational purposes.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the error messages in the terminal
3. Ensure all dependencies are installed correctly

---

**Happy Traffic Managing! 🚦**
