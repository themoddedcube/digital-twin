#!/usr/bin/env python3
"""
Test Main Orchestrator with Live Telemetry.

This test demonstrates the complete F1 Dual Twin System
running with live telemetry through the main orchestrator.
"""

import sys
import time
import json
import threading
import socket
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_udp_telemetry_stream():
    """Create a continuous UDP telemetry stream."""
    def send_telemetry():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lap = 25
        
        try:
            for i in range(20):  # Send 20 updates
                telemetry_data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "lap": lap + (i // 4),  # Advance lap every 4 updates
                    "session_type": "race",
                    "track_conditions": {
                        "temperature": 32.0 + (i * 0.5),
                        "weather": "sunny",
                        "track_status": "green"
                    },
                    "cars": [
                        {
                            "car_id": "44",
                            "team": "Mercedes",
                            "driver": "Hamilton",
                            "position": 3,
                            "speed": 290.0 + (i * 1.5),
                            "tire": {
                                "compound": "medium",
                                "age": 15 + i,
                                "wear_level": 0.4 + (i * 0.02)
                            },
                            "fuel_level": 0.7 - (i * 0.02),
                            "lap_time": 83.5 - (i * 0.1),
                            "sector_times": [28.2, 31.1, 24.2]
                        },
                        {
                            "car_id": "1", 
                            "team": "Red Bull",
                            "driver": "Verstappen",
                            "position": 1,
                            "speed": 295.0 + (i * 1.2),
                            "tire": {
                                "compound": "soft",
                                "age": 12 + i,
                                "wear_level": 0.35 + (i * 0.015)
                            },
                            "fuel_level": 0.65 - (i * 0.018),
                            "lap_time": 82.8 - (i * 0.08),
                            "sector_times": [27.8, 30.5, 24.5]
                        },
                        {
                            "car_id": "16",
                            "team": "Ferrari", 
                            "driver": "Leclerc",
                            "position": 2,
                            "speed": 292.0 + (i * 1.3),
                            "tire": {
                                "compound": "hard",
                                "age": 18 + i,
                                "wear_level": 0.3 + (i * 0.01)
                            },
                            "fuel_level": 0.75 - (i * 0.025),
                            "lap_time": 83.2 - (i * 0.09),
                            "sector_times": [28.0, 30.8, 24.4]
                        }
                    ]
                }
                
                # Send UDP packet
                data = json.dumps(telemetry_data).encode('utf-8')
                sock.sendto(data, ('localhost', 20777))
                
                if i % 4 == 0:  # Log every 4th update
                    print(f"   📡 Streaming lap {telemetry_data['lap']}: Hamilton {telemetry_data['cars'][0]['speed']:.1f} km/h")
                
                time.sleep(1.5)  # Send every 1.5 seconds
                
        except Exception as e:
            print(f"   ❌ UDP stream error: {e}")
        finally:
            sock.close()
    
    return threading.Thread(target=send_telemetry, daemon=True)


def test_orchestrator_with_live_telemetry():
    """Test the main orchestrator with live telemetry."""
    print("🏁 F1 DUAL TWIN SYSTEM - ORCHESTRATOR + LIVE TELEMETRY TEST")
    print("=" * 70)
    
    try:
        # Import orchestrator
        from main_orchestrator import MainOrchestrator
        from utils.config import load_config
        
        print("1️⃣ Configuring system for live telemetry...")
        
        # Load and modify config for live mode
        load_config("config/sys