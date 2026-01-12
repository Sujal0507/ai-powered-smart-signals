from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

Base = declarative_base()

class TrafficLog(Base):
    """
    SQLAlchemy model for traffic logs.
    """
    __tablename__ = 'traffic_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    lane_id = Column(Integer)
    vehicle_counts = Column(JSON) # Store counts as JSON: {'car': 5, ...}
    ambulance_detected = Column(Boolean)
    green_duration = Column(Float)
    signal_mode = Column(String) # 'NORMAL' or 'EMERGENCY'

    def __repr__(self):
        return f"<TrafficLog(lane={self.lane_id}, time={self.timestamp})>"

class DatabaseManager:
    """
    Manages SQLite database interactions.
    """
    def __init__(self, db_path='data/traffic.db'):
        """
        Initialize database connection.
        Args:
            db_path: Path to sqlite database file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def log_traffic_cycle(self, lane_id, vehicle_counts, ambulance_detected, green_duration, signal_mode):
        """
        Log a completed signal cycle.
        """
        session = self.Session()
        try:
            log = TrafficLog(
                lane_id=lane_id,
                vehicle_counts=vehicle_counts,
                ambulance_detected=ambulance_detected,
                green_duration=green_duration,
                signal_mode=signal_mode
            )
            session.add(log)
            session.commit()
        except Exception as e:
            print(f"Error logging to DB: {e}")
            session.rollback()
        finally:
            session.close()

    def get_recent_logs(self, limit=50):
        """
        Get recent traffic logs as a pandas DataFrame.
        """
        import pandas as pd
        session = self.Session()
        try:
            logs = session.query(TrafficLog).order_by(TrafficLog.timestamp.desc()).limit(limit).all()
            if not logs:
                return pd.DataFrame()
                
            data = []
            for log in logs:
                # Calculate total vehicles
                total = sum(log.vehicle_counts.values()) if log.vehicle_counts else 0
                data.append({
                    'timestamp': log.timestamp,
                    'lane_id': log.lane_id,
                    'total_vehicles': total,
                    'ambulance': log.ambulance_detected,
                    'green_duration': log.green_duration,
                    'mode': log.signal_mode
                })
            return pd.DataFrame(data)
        finally:
            session.close()

    def get_today_stats(self):
        """
        Get statistics for the current day.
        Returns:
            dict containing total_cycles, etc.
        """
        session = self.Session()
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            
            logs = session.query(TrafficLog).filter(TrafficLog.timestamp >= start_of_day).all()
            
            total_cycles = len(logs)
            emergency_events = sum(1 for l in logs if l.signal_mode == 'EMERGENCY')
            
            # Calculate total vehicles
            total_vehicles = sum(sum(l.vehicle_counts.values()) if l.vehicle_counts else 0 for l in logs)
            
            # This logic assumes we save the "wait_time_saved" in the DB or calculate it here.
            # The current schema doesn't have 'wait_time_saved'. 
            # We can calculate it roughly: max(0, 60 - green_duration)
            wait_time_saved = sum(max(0, 60 - l.green_duration) for l in logs) if logs else 0
            
            return {
                'total_cycles': total_cycles,
                'total_vehicles': total_vehicles,
                'emergency_events': emergency_events,
                'wait_time_saved': wait_time_saved
            }
        finally:
            session.close()

    def get_lane_stats(self):
        """
        Get aggregated stats per lane for analytics.
        """
        import pandas as pd
        session = self.Session()
        try:
            # Query all time or last 24h
            limit_time = datetime.now() - timedelta(hours=24)
            logs = session.query(TrafficLog).filter(TrafficLog.timestamp >= limit_time).all()
            
            if not logs:
                return pd.DataFrame()
            
            data = []
            for log in logs:
                total = sum(log.vehicle_counts.values()) if log.vehicle_counts else 0
                data.append({
                    'lane_id': log.lane_id,
                    'total_vehicles': total,
                    'green_duration': log.green_duration,
                    'ambulance': 1 if log.ambulance_detected else 0
                })
            
            df = pd.DataFrame(data)
            
            # Group by lane
            stats = df.groupby('lane_id').agg({
                'total_vehicles': ['sum', 'mean'],
                'lane_id': 'count', # count of cycles
                'ambulance': 'sum',
                'green_duration': 'mean'
            }).reset_index()
            
            # Flatten columns
            stats.columns = ['lane_id', 'total_vehicles', 'avg_vehicles', 'total_cycles', 'emergency_events', 'avg_green_time']
            return stats
            
        finally:
            session.close()
    
    def get_lane_analytics(self, hours=24):
        """
        Get aggregated stats per lane for analytics (alias for get_lane_stats).
        
        Args:
            hours: Number of hours to look back (default: 24)
        """
        return self.get_lane_stats()
            
    def close(self):
        self.engine.dispose()
