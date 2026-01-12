"""
Intelligent Traffic Management System (ITMS) - Streamlit Dashboard
MSc Major Project: AI-Powered Traffic Control with YOLOv8
"""

import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import os
import sys

# Import custom modules
from core.detector import MultiLaneDetectionSystem
from core.traffic_logic import TrafficSignalController, SignalState
from core.database import DatabaseManager

# Page configuration
st.set_page_config(
    page_title="Intelligent Traffic Management System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .signal-red {
        color: #ff4444;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .signal-green {
        color: #44ff44;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .signal-yellow {
        color: #ffaa00;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'system_initialized' not in st.session_state:
    st.session_state.system_initialized = False
    st.session_state.detection_system = None
    st.session_state.controller = None
    st.session_state.db_manager = None
    st.session_state.confidence = 0.5
    st.session_state.uploaded_videos = {}  # Store uploaded video paths

def save_uploaded_file(uploaded_file, lane_id):
    """Save uploaded video file to assets folder."""
    try:
        os.makedirs('assets/uploaded', exist_ok=True)
        file_path = f'assets/uploaded/lane_{lane_id}.mp4'
        
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path
    except Exception as e:
        st.error(f"Error saving video for Lane {lane_id}: {e}")
        return None

def initialize_system():
    """Initialize the traffic management system."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        os.makedirs('assets', exist_ok=True)
        
        # Initialize database
        db_manager = DatabaseManager('data/traffic_data.db')
        
        # Get video paths from uploaded files or use default
        video_paths = []
        
        # Check if user uploaded videos
        if st.session_state.uploaded_videos:
            for i in range(1, 5):
                if i in st.session_state.uploaded_videos:
                    video_paths.append(st.session_state.uploaded_videos[i])
                else:
                    st.error(f"⚠️ Video for Lane {i} not uploaded!")
                    return False
        else:
            # Fallback to single video file
            video_path = 'assets/traffic.mp4'
            if not os.path.exists(video_path):
                st.error(f"⚠️ No videos uploaded and default video not found!")
                st.info("📹 Please upload videos for all 4 lanes or place a default video at 'assets/traffic.mp4'")
                return False
            video_paths = [video_path] * 4
        
        # Initialize detection system
        st.info("🔄 Initializing YOLOv8 detection system...")
        detection_system = MultiLaneDetectionSystem(
            video_paths=video_paths,
            confidence=st.session_state.confidence
        )
        
        # Initialize traffic controller
        st.info("🚦 Initializing traffic signal controller...")
        controller = TrafficSignalController(detection_system, db_manager)
        
        # Start systems
        st.info("▶️ Starting video processors...")
        detection_system.start()
        time.sleep(2)  # Give time for threads to start
        
        st.info("▶️ Starting traffic controller...")
        controller.start()
        
        # Store in session state
        st.session_state.detection_system = detection_system
        st.session_state.controller = controller
        st.session_state.db_manager = db_manager
        st.session_state.system_initialized = True
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error initializing system: {e}")
        import traceback
        st.code(traceback.format_exc())
        return False

def get_signal_color_class(state):
    """Get CSS class for signal state."""
    if state == SignalState.RED:
        return "signal-red"
    elif state == SignalState.GREEN:
        return "signal-green"
    elif state == SignalState.YELLOW:
        return "signal-yellow"
    return ""

def render_video_feed(lane_id, frame, signal_state, vehicle_count, ambulance):
    """Render a single video feed with overlays."""
    if frame is None:
        st.warning(f"Lane {lane_id}: Waiting for video feed...")
        return
    
    # Add signal status overlay
    signal_color = {
        SignalState.RED: (0, 0, 255),
        SignalState.GREEN: (0, 255, 0),
        SignalState.YELLOW: (0, 255, 255)
    }
    
    overlay_frame = frame.copy()
    color = signal_color.get(signal_state, (255, 255, 255))
    
    # Signal status box
    cv2.rectangle(overlay_frame, (10, 10), (200, 80), (0, 0, 0), -1)
    cv2.rectangle(overlay_frame, (10, 10), (200, 80), color, 3)
    cv2.putText(overlay_frame, f"Lane {lane_id}: {signal_state.value}", 
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(overlay_frame, f"Vehicles: {vehicle_count}", 
                (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Ambulance warning
    if ambulance:
        cv2.rectangle(overlay_frame, (10, 90), (200, 130), (0, 0, 255), -1)
        cv2.putText(overlay_frame, "AMBULANCE!", 
                    (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Convert BGR to RGB for Streamlit
    rgb_frame = cv2.cvtColor(overlay_frame, cv2.COLOR_BGR2RGB)
    st.image(rgb_frame, use_column_width=True)

def create_traffic_density_chart(lane_data):
    """Create bar chart for traffic density across lanes."""
    lanes = list(lane_data.keys())
    vehicles = [data['total'] for data in lane_data.values()]
    colors = ['red' if data['ambulance'] else 'lightblue' 
              for data in lane_data.values()]
    
    fig = go.Figure(data=[
        go.Bar(
            x=[f"Lane {l}" for l in lanes],
            y=vehicles,
            marker_color=colors,
            text=vehicles,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Real-Time Traffic Density",
        xaxis_title="Lane",
        yaxis_title="Vehicle Count",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )
    
    return fig

def create_analytics_chart(db_manager):
    """Create analytics visualization."""
    try:
        df = db_manager.get_lane_analytics(hours=24)
        
        if df.empty:
            return None
        
        fig = px.bar(
            df,
            x='lane_id',
            y='total_vehicles',
            title='24-Hour Traffic Volume by Lane',
            labels={'lane_id': 'Lane', 'total_vehicles': 'Total Vehicles'},
            color='avg_green_time',
            color_continuous_scale='Viridis',
            text='total_vehicles'
        )
        
        fig.update_traces(textposition='outside')
        fig.update_layout(height=400)
        return fig
        
    except Exception as e:
        st.error(f"Error creating analytics chart: {e}")
        return None

def main():
    """Main application function."""
    
    # Header
    st.markdown('<p class="main-header">🚦 Intelligent Traffic Management System</p>', 
                unsafe_allow_html=True)
    st.markdown("**AI-Powered Traffic Control | MSc Major Project**")
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Control Panel")
        
        # Model confidence slider
        confidence = st.slider(
            "Detection Confidence",
            min_value=0.3,
            max_value=0.9,
            value=st.session_state.confidence,
            step=0.05,
            help="Adjust YOLOv8 detection confidence threshold"
        )
        
        st.session_state.confidence = confidence
        
        st.divider()
        
        # Video Upload Section
        if not st.session_state.system_initialized:
            st.subheader("📹 Upload Lane Videos")
            st.caption("Upload 4 different videos (one per lane)")
            
            uploaded_count = 0
            for i in range(1, 5):
                uploaded_file = st.file_uploader(
                    f"Lane {i} Video",
                    type=['mp4', 'avi', 'mov'],
                    key=f"video_upload_{i}",
                    help=f"Upload traffic video for Lane {i}"
                )
                
                if uploaded_file is not None:
                    # Save the uploaded file
                    file_path = save_uploaded_file(uploaded_file, i)
                    if file_path:
                        st.session_state.uploaded_videos[i] = file_path
                        uploaded_count += 1
                        st.success(f"✅ Lane {i} uploaded")
            
            if uploaded_count > 0:
                st.info(f"📊 {uploaded_count}/4 videos uploaded")
            else:
                st.info("💡 Or use default video at assets/traffic.mp4")
            
            st.divider()
        
        # System controls
        st.subheader("System Control")
        
        if not st.session_state.system_initialized:
            if st.button("🚀 Start System", type="primary"):
                with st.spinner("Initializing ITMS..."):
                    if initialize_system():
                        st.success("✅ System initialized!")
                        time.sleep(2)
                        st.rerun()
        else:
            st.success("✅ System Running")
            
            # Update confidence
            if st.session_state.detection_system:
                st.session_state.detection_system.update_confidence(confidence)
            
            if st.button("🛑 Stop System", type="secondary"):
                if st.session_state.controller:
                    st.session_state.controller.stop()
                if st.session_state.detection_system:
                    st.session_state.detection_system.stop()
                st.session_state.system_initialized = False
                st.success("System stopped")
                time.sleep(1)
                st.rerun()
        
        st.divider()
        
        # Emergency override buttons
        st.subheader("🚨 Emergency Override")
        st.caption("Manually trigger ambulance priority")
        
        cols = st.columns(2)
        for i in range(1, 5):
            col = cols[(i-1) % 2]
            if col.button(f"Lane {i}", key=f"emergency_{i}"):
                if st.session_state.controller:
                    st.session_state.controller.force_emergency(i)
                    st.success(f"🚑 Emergency triggered for Lane {i}")
        
        st.divider()
        
        # Statistics
        if st.session_state.controller:
            st.subheader("📊 System Statistics")
            stats = st.session_state.controller.get_statistics()
            
            st.metric("Total Cycles", stats['total_cycles'])
            st.metric("Emergency Events", stats['emergency_events'])
            st.metric("Wait Time Saved", f"{stats['wait_time_saved']:.0f}s")
            st.metric("Avg Saved/Cycle", f"{stats['avg_wait_saved_per_cycle']:.1f}s")
            st.metric("Current Mode", stats['mode'])
    
    # Main content
    if not st.session_state.system_initialized:
        st.info("👈 Click '🚀 Start System' in the sidebar to begin")
        
        # Show system requirements
        with st.expander("📋 System Requirements & Setup"):
            st.markdown("""
            ### Before Starting:
            
            **Requirements:**
            1. Python 3.8 or higher
            2. Video file at `assets/traffic.mp4`
            3. All dependencies installed: `pip install -r requirements.txt`
            
            **First Run:**
            - YOLOv8 model will download automatically (~6MB)
            - Takes 15-30 seconds to initialize
            - Internet connection required for first-time setup
            
            **Features:**
            - ✅ Real-time vehicle detection using YOLOv8
            - ✅ Dynamic signal timing based on traffic density
            - ✅ Ambulance detection and emergency override
            - ✅ Traffic analytics and data logging
            - ✅ Multi-threaded processing for 4 lanes
            
            **Get Started:**
            1. Place traffic video at: `assets/traffic.mp4`
            2. Click "Start System" in sidebar
            3. Wait for initialization
            4. Monitor live traffic feeds!
            """)
        
        # Show video sources
        with st.expander("📹 Where to Get Traffic Videos"):
            st.markdown("""
            ### Free Traffic Video Sources:
            
            1. **Pexels** (Recommended)
               - https://www.pexels.com/search/videos/traffic/
               - High quality, free to use
               
            2. **Pixabay**
               - https://pixabay.com/videos/search/traffic/
               - No attribution required
               
            3. **Videvo**
               - https://www.videvo.net/free-stock-video-footage/traffic/
               - Mix of free and premium
            
            4. **YouTube** (with permission)
               - Search for "traffic footage"
               - Use yt-dlp: `yt-dlp "VIDEO_URL" -o assets/traffic.mp4`
            
            **Tips:**
            - Choose videos with clear vehicle visibility
            - 30-60 seconds is ideal (video loops automatically)
            - Higher resolution = better detection
            - Daytime videos work best
            """)
        
        return
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🎥 Live Monitoring", "📈 Analytics", "📋 Logs"])
    
    with tab1:
        # Live monitoring view
        detection_system = st.session_state.detection_system
        controller = st.session_state.controller
        
        if detection_system and controller:
            # Get all lane data
            lane_data = detection_system.get_all_lane_data()
            signal_states = controller.get_all_states()
            
            # Create 2x2 grid for video feeds
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Lane 1")
                data = lane_data.get(1, {})
                render_video_feed(
                    1, 
                    data.get('frame'), 
                    signal_states.get(1, SignalState.RED),
                    data.get('total', 0),
                    data.get('ambulance', False)
                )
                
                st.subheader("Lane 3")
                data = lane_data.get(3, {})
                render_video_feed(
                    3,
                    data.get('frame'),
                    signal_states.get(3, SignalState.RED),
                    data.get('total', 0),
                    data.get('ambulance', False)
                )
            
            with col2:
                st.subheader("Lane 2")
                data = lane_data.get(2, {})
                render_video_feed(
                    2,
                    data.get('frame'),
                    signal_states.get(2, SignalState.RED),
                    data.get('total', 0),
                    data.get('ambulance', False)
                )
                
                st.subheader("Lane 4")
                data = lane_data.get(4, {})
                render_video_feed(
                    4,
                    data.get('frame'),
                    signal_states.get(4, SignalState.RED),
                    data.get('total', 0),
                    data.get('ambulance', False)
                )
            
            # Traffic density chart
            st.divider()
            st.plotly_chart(
                create_traffic_density_chart(lane_data),
                use_container_width=True
            )
    
    with tab2:
        # Analytics view
        st.header("Traffic Analytics Dashboard")
        
        if st.session_state.db_manager:
            db = st.session_state.db_manager
            
            # Today's statistics
            today_stats = db.get_today_stats()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🚗 Total Vehicles Today", today_stats['total_vehicles'])
            col2.metric("🔄 Total Cycles", today_stats['total_cycles'])
            col3.metric("🚑 Emergency Events", today_stats['emergency_events'])
            
            st.divider()
            
            # Analytics chart
            chart = create_analytics_chart(db)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("📊 Run the system for a while to generate analytics data")
            
            # Lane-wise breakdown
            st.subheader("Lane-wise Performance (24 Hours)")
            df = db.get_lane_analytics(hours=24)
            
            if not df.empty:
                # Format the dataframe
                df_display = df.copy()
                df_display.columns = ['Lane', 'Total Vehicles', 'Avg Vehicles', 
                                     'Total Cycles', 'Emergency Events', 'Avg Green Time']
                df_display['Avg Green Time'] = df_display['Avg Green Time'].round(1).astype(str) + 's'
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("📊 No data available yet. Run the system to collect analytics.")
        
    with tab3:
        # Logs view
        st.header("Recent Traffic Logs")
        
        if st.session_state.db_manager:
            db = st.session_state.db_manager
            
            # Refresh button
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("🔄 Refresh Logs"):
                    st.rerun()
            with col2:
                log_limit = st.selectbox("Show", [25, 50, 100], index=1)
            
            # Recent logs
            logs_df = db.get_recent_logs(limit=log_limit)
            
            if not logs_df.empty:
                # Format the dataframe
                logs_display = logs_df.copy()
                logs_display['timestamp'] = pd.to_datetime(logs_display['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                logs_display['green_duration'] = logs_display['green_duration'].round(1).astype(str) + 's'
                logs_display.columns = ['Timestamp', 'Lane', 'Vehicles', 'Ambulance', 'Green Duration', 'Mode']
                
                st.dataframe(
                    logs_display,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("📋 No logs available yet. Start the system to begin logging.")
    
    # Auto-refresh (update every second)
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    # Add pandas import for logs tab
    import pandas as pd
    main()