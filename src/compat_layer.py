"""
Compatibility Layer for F1 Race Twin Edge System

This module provides compatibility between the original dual-twin system
and the demo/MAX integration system.
"""

# Re-export original system with compatible names
from twin_system.twin_model import CarTwin as DigitalTwin
from twin_system.field_twin import FieldTwin  
from twin_system.telemetry_feed import TelemetrySimulator as TelemetryGenerator, TelemetryIngestor as TelemetryStreamer

# Dashboard is handled by separate team - not importing
RaceDashboard = None  # Placeholder for external dashboard integration

# Create sample race state function for compatibility
def create_sample_race_state():
    """Create sample race state for testing"""
    from datetime import datetime
    from core.base_telemetry import TelemetryData
    
    # Return sample telemetry data
    return TelemetryData(
        timestamp=datetime.now().isoformat(),
        lap=22,
        session_type="race",
        track_conditions={
            "temperature": 28.0,
            "weather": "sunny", 
            "track_status": "green"
        },
        cars=[]
    )


__all__ = [
    'DigitalTwin',
    'FieldTwin',
    'TelemetryGenerator',
    'TelemetryStreamer',
    'RaceDashboard',
    'create_sample_race_state'
]

