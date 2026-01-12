"""
Core module for Intelligent Traffic Management System.
Contains detection, traffic logic, and database components.
"""

from .detector import VehicleDetector, MultiLaneDetectionSystem, LaneVideoProcessor
from .traffic_logic import TrafficSignalController, SignalState, SignalMode
from .database import DatabaseManager, TrafficLog

__all__ = [
    'VehicleDetector',
    'LaneVideoProcessor',
    'MultiLaneDetectionSystem',
    'TrafficSignalController',
    'SignalState',
    'SignalMode',
    'DatabaseManager',
    'TrafficLog'
]

__version__ = '1.0.0'
__author__ = 'MSc Student - AI/Computer Science'
__description__ = 'Intelligent Traffic Management System with YOLOv8'