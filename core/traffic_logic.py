"""
Traffic signal control logic with state machine implementation.
Handles normal cycling and emergency override for ambulances.
"""

import time
import threading
from enum import Enum
from datetime import datetime

class SignalState(Enum):
    """Traffic signal states."""
    RED = "RED"
    GREEN = "GREEN"
    YELLOW = "YELLOW"

class SignalMode(Enum):
    """Operating modes for traffic control."""
    NORMAL = "NORMAL"
    EMERGENCY = "EMERGENCY"

class TrafficSignalController:
    """
    State machine for controlling 4-lane traffic signals.
    Implements dynamic timing based on vehicle count and emergency override.
    """
    
    def __init__(self, detection_system, database_manager):
        """
        Initialize traffic signal controller.
        
        Args:
            detection_system: MultiLaneDetectionSystem instance
            database_manager: DatabaseManager instance
        """
        self.detection_system = detection_system
        self.db = database_manager
        
        # Signal states for each lane
        self.lane_states = {1: SignalState.RED, 2: SignalState.RED, 
                           3: SignalState.RED, 4: SignalState.RED}
        
        # Current active lane
        self.current_lane = 1
        self.mode = SignalMode.NORMAL
        
        # Timing parameters
        self.yellow_duration = 3
        self.transition_delay = 2
        
        # Control flags
        self.running = False
        self.force_emergency_lane = None
        self.lock = threading.Lock()
        
        # Statistics
        self.cycle_count = 0
        self.emergency_count = 0
        self.total_wait_time_saved = 0
        
        print("Traffic Signal Controller initialized")
    
    def calculate_green_duration(self, vehicle_count):
        """
        Calculate green signal duration based on vehicle count.
        Implements dynamic timing algorithm.
        
        Args:
            vehicle_count: Number of vehicles detected
            
        Returns:
            Green signal duration in seconds
        """
        if vehicle_count > 15:
            return 60
        elif vehicle_count >= 5:
            return 30
        else:
            return 15
    
    def get_lane_state(self, lane_id):
        """Get current signal state for a lane."""
        with self.lock:
            return self.lane_states.get(lane_id, SignalState.RED)
    
    def get_all_states(self):
        """Get signal states for all lanes."""
        with self.lock:
            return self.lane_states.copy()
    
    def force_emergency(self, lane_id):
        """
        Manually trigger emergency mode for a specific lane.
        
        Args:
            lane_id: Lane to give priority (1-4)
        """
        with self.lock:
            self.force_emergency_lane = lane_id
            print(f"[MANUAL OVERRIDE] Emergency triggered for Lane {lane_id}")
    
    def transition_to_lane(self, from_lane, to_lane, reason="Normal Cycle"):
        """
        Transition from one lane to another with proper signal sequencing.
        
        Args:
            from_lane: Current green lane
            to_lane: Next lane to turn green
            reason: Reason for transition (logging)
        """
        print(f"\n[TRANSITION] Lane {from_lane} -> Lane {to_lane} | Reason: {reason}")
        
        # Yellow phase for current lane
        with self.lock:
            self.lane_states[from_lane] = SignalState.YELLOW
        print(f"  Lane {from_lane}: YELLOW ({self.yellow_duration}s)")
        time.sleep(self.yellow_duration)
        
        # Red phase with delay
        with self.lock:
            self.lane_states[from_lane] = SignalState.RED
        print(f"  Lane {from_lane}: RED (transition delay {self.transition_delay}s)")
        time.sleep(self.transition_delay)
        
        # Green for next lane
        with self.lock:
            self.lane_states[to_lane] = SignalState.GREEN
            self.current_lane = to_lane
        print(f"  Lane {to_lane}: GREEN")
    
    def handle_normal_cycle(self):
        """Execute normal traffic signal cycling logic."""
        lane = self.current_lane
        
        # Get vehicle count for current lane
        lane_data = self.detection_system.get_lane_data(lane)
        _, counts, ambulance = lane_data
        total_vehicles = sum(counts.values())
        
        # Check for ambulance in current lane
        if ambulance:
            print(f"[AMBULANCE DETECTED] Lane {lane} - Extending green time")
            self.mode = SignalMode.EMERGENCY
            self.emergency_count += 1
        
        # Calculate dynamic green duration
        green_duration = self.calculate_green_duration(total_vehicles)
        
        # Calculate wait time saved vs fixed 60s
        fixed_time = 60
        wait_time_saved = max(0, fixed_time - green_duration)
        self.total_wait_time_saved += wait_time_saved
        
        print(f"\n{'='*70}")
        print(f"[CYCLE {self.cycle_count + 1}] Lane {lane} - {self.mode.value} MODE")
        print(f"{'='*70}")
        print(f"  Vehicles Detected: {total_vehicles}")
        print(f"  Vehicle Breakdown: {dict(counts)}")
        print(f"  Ambulance Present: {ambulance}")
        print(f"  Green Duration: {green_duration}s")
        print(f"  Time Saved vs Fixed (60s): {wait_time_saved}s")
        print(f"{'='*70}")
        
        # Log to database
        try:
            self.db.log_traffic_cycle(
                lane_id=lane,
                vehicle_counts=counts,
                ambulance_detected=ambulance,
                green_duration=green_duration,
                signal_mode=self.mode.value
            )
        except Exception as e:
            print(f"Error logging to database: {e}")
        
        # Keep lane green for calculated duration
        time.sleep(green_duration)
        
        # Move to next lane
        next_lane = (lane % 4) + 1
        self.transition_to_lane(lane, next_lane)
        
        # Reset to normal mode
        self.mode = SignalMode.NORMAL
        self.cycle_count += 1
    
    def handle_emergency_override(self, emergency_lane):
        """
        Handle emergency mode when ambulance is detected.
        
        Args:
            emergency_lane: Lane with ambulance
        """
        current = self.current_lane
        
        if current == emergency_lane:
            # Ambulance is in current green lane, extend time
            print(f"[EMERGENCY] Ambulance in active lane {emergency_lane} - continuing")
            return
        
        print(f"\n{'*'*70}")
        print(f"[EMERGENCY OVERRIDE] Switching to Lane {emergency_lane} immediately!")
        print(f"{'*'*70}")
        self.emergency_count += 1
        
        # Immediate transition to emergency lane
        self.transition_to_lane(current, emergency_lane, reason="AMBULANCE DETECTED")
        
        # Give emergency lane extended green time
        emergency_duration = 45
        print(f"[EMERGENCY] Lane {emergency_lane} GREEN for {emergency_duration}s")
        
        # Get counts for logging
        _, counts, _ = self.detection_system.get_lane_data(emergency_lane)
        
        # Log emergency event
        try:
            self.db.log_traffic_cycle(
                lane_id=emergency_lane,
                vehicle_counts=counts,
                ambulance_detected=True,
                green_duration=emergency_duration,
                signal_mode='EMERGENCY'
            )
        except Exception as e:
            print(f"Error logging emergency event: {e}")
        
        time.sleep(emergency_duration)
        self.cycle_count += 1
        print(f"{'*'*70}\n")
    
    def check_emergency_conditions(self):
        """
        Check all lanes for emergency conditions (ambulances).
        
        Returns:
            Lane ID if emergency detected, None otherwise
        """
        # Check manual override first
        with self.lock:
            if self.force_emergency_lane:
                lane = self.force_emergency_lane
                self.force_emergency_lane = None
                return lane
        
        # Check all lanes for ambulances
        all_data = self.detection_system.get_all_lane_data()
        
        for lane_id, data in all_data.items():
            if data['ambulance']:
                return lane_id
        
        return None
    
    def run(self):
        """Main control loop for traffic signal state machine."""
        self.running = True
        
        # Initialize: Set Lane 1 to GREEN
        with self.lock:
            self.lane_states[1] = SignalState.GREEN
            self.current_lane = 1
        
        print("\n" + "="*70)
        print("[TRAFFIC CONTROLLER] System Started")
        print("="*70)
        print(f"Initial State: Lane 1 GREEN")
        print(f"Mode: {self.mode.value}")
        print("="*70 + "\n")
        
        while self.running:
            try:
                # Check for emergency conditions
                emergency_lane = self.check_emergency_conditions()
                
                if emergency_lane:
                    # Emergency mode: Prioritize ambulance lane
                    self.mode = SignalMode.EMERGENCY
                    self.handle_emergency_override(emergency_lane)
                else:
                    # Normal mode: Continue regular cycling
                    self.mode = SignalMode.NORMAL
                    self.handle_normal_cycle()
                
            except Exception as e:
                print(f"[ERROR] Traffic controller error: {e}")
                time.sleep(5)
        
        print("\n[TRAFFIC CONTROLLER] Stopped")
    
    def start(self):
        """Start the traffic controller in a separate thread."""
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        print("Traffic controller thread started")
    
    def stop(self):
        """Stop the traffic controller."""
        self.running = False
        print("Traffic controller stop requested")
    
    def get_statistics(self):
        """
        Get current system statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            'total_cycles': self.cycle_count,
            'emergency_events': self.emergency_count,
            'wait_time_saved': self.total_wait_time_saved,
            'current_lane': self.current_lane,
            'mode': self.mode.value,
            'avg_wait_saved_per_cycle': (
                self.total_wait_time_saved / self.cycle_count 
                if self.cycle_count > 0 else 0
            )
        }