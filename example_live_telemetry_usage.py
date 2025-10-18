#!/usr/bin/env python3
"""
Example usage of Live Telemetry in F1 Dual Twin System.

This example shows how to:
1. Configure live telemetry sources
2. Switch between simulator and live modes
3. Handle telemetry data in real-time
4. Integrate with the twin models
"""

import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def example_websocket_telemetry():
    """Example of using WebSocket live telemetry."""
    print("=== WebSocket Live Telemetry Example ===")
    
    from telemetry_feed import TelemetryIngestor
    from utils.config import load_config
    
    # Load configuration
    load_config("config/system_config.json")
    
    # Create ingestor
    ingestor = TelemetryIngestor()
    
    # Switch to WebSocket mode
    print("Switching to WebSocket live telemetry...")
    success = ingestor.switch_to_live_mode(
        source_type="websocket",
        websocket_url="ws://your-f1-server:8080/telemetry",
        timeout=5.0,
        max_reconnect_attempts=3
    )
    
    if success:
        print("✓ Connected to WebSocket telemetry source")
        
        # Start ingestion
        ingestor.start_ingestion()
        
        # Let it run for a few seconds
        time.sleep(10)
        
        # Check status
        status = ingestor.get_data_source_status()
        print(f"Status: {json.dumps(status, indent=2)}")
        
        # Stop ingestion
        ingestor.stop_ingestion()
        
    else:
        print("✗ Failed to connect to WebSocket source (expected - no server running)")
        print("   Automatically fell back to simulator mode")


def example_udp_telemetry():
    """Example of using UDP live telemetry."""
    print("\n=== UDP Live Telemetry Example ===")
    
    from telemetry_feed import TelemetryIngestor
    
    # Create ingestor
    ingestor = TelemetryIngestor()
    
    # Switch to UDP mode
    print("Switching to UDP live telemetry...")
    success = ingestor.switch_to_live_mode(
        source_type="udp",
        host="localhost",
        port=20777,
        timeout=1.0
    )
    
    if success:
        print("✓ UDP telemetry client listening on localhost:20777")
        print("  (Send JSON telemetry data to this UDP port)")
        
        # Start ingestion
        ingestor.start_ingestion()
        
        # Let it run briefly
        time.sleep(3)
        
        # Stop ingestion
        ingestor.stop_ingestion()
        
    else:
        print("✗ Failed to set up UDP telemetry client")


def example_full_integration():
    """Example of full integration with twin models."""
    print("\n=== Full Integration Example ===")
    
    from telemetry_feed import TelemetryIngestor
    from twin_model import CarTwin
    from field_twin import FieldTwin
    from dashboard import StateHandler
    
    # Create components
    ingestor = TelemetryIngestor()
    car_twin = CarTwin("44")  # Hamilton's car
    field_twin = FieldTwin()
    state_handler = StateHandler(storage_path="shared")
    
    print("1. Starting with simulator mode...")
    
    # Start ingestion
    ingestor.start_ingestion()
    
    # Process a few updates
    for i in range(3):
        time.sleep(1)
        
        # Get latest telemetry
        telemetry_data = ingestor._get_telemetry_data()
        
        if telemetry_data:
            print(f"   Update {i+1}: Lap {telemetry_data['lap']}, {len(telemetry_data['cars'])} cars")
            
            # Update twin models
            car_twin.update_state(telemetry_data)
            field_twin.update_state(telemetry_data)
            
            # Update state handler
            state_handler.update_car_twin_state(car_twin.get_current_state())
            state_handler.update_field_twin_state(field_twin.get_current_state())
            state_handler.update_telemetry_state(telemetry_data)
    
    # Stop ingestion
    ingestor.stop_ingestion()
    
    # Show final states
    print("\n2. Final twin states:")
    car_state = car_twin.get_current_state()
    field_state = field_twin.get_current_state()
    
    print(f"   Car Twin - Speed: {car_state['current_state']['speed']:.1f} km/h")
    print(f"   Car Twin - Fuel: {car_state['current_state']['fuel_level']:.1%}")
    print(f"   Car Twin - Predicted Pit Lap: {car_state['predictions']['predicted_pit_lap']}")
    print(f"   Field Twin - Competitors: {len(field_state['competitors'])}")
    print(f"   Field Twin - Opportunities: {len(field_state['strategic_opportunities'])}")


def example_configuration_options():
    """Show different configuration options."""
    print("\n=== Configuration Options ===")
    
    # WebSocket configuration
    websocket_config = {
        "telemetry": {
            "use_simulator": False,
            "live_source_type": "websocket",
            "update_interval_seconds": 1,  # Faster updates for live data
            "max_failures_before_fallback": 3,
            "live_source": {
                "websocket_url": "ws://f1-telemetry-server:8080/live",
                "timeout": 10.0,
                "max_reconnect_attempts": 10,
                "reconnect_delay": 1.0
            }
        }
    }
    
    # UDP configuration
    udp_config = {
        "telemetry": {
            "use_simulator": False,
            "live_source_type": "udp",
            "update_interval_seconds": 0.1,  # Very fast for UDP
            "max_failures_before_fallback": 10,
            "live_source": {
                "host": "0.0.0.0",  # Listen on all interfaces
                "port": 20777,      # F1 game default port
                "timeout": 0.5
            }
        }
    }
    
    print("WebSocket Configuration:")
    print(json.dumps(websocket_config, indent=2))
    
    print("\nUDP Configuration:")
    print(json.dumps(udp_config, indent=2))
    
    print("\nUsage Notes:")
    print("- WebSocket: Good for HTTP-based telemetry APIs")
    print("- UDP: Good for F1 game telemetry or high-frequency data")
    print("- Set use_simulator=false to enable live mode")
    print("- Automatic fallback ensures system reliability")
    print("- All data is normalized to the same schema")


if __name__ == "__main__":
    print("F1 Dual Twin System - Live Telemetry Usage Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_websocket_telemetry()
        example_udp_telemetry()
        example_full_integration()
        example_configuration_options()
        
        print("\n" + "=" * 60)
        print("🏁 Live Telemetry Integration Complete!")
        print("\nNext Steps:")
        print("1. Configure your telemetry source in config/system_config.json")
        print("2. Set use_simulator=false to enable live mode")
        print("3. Start the main orchestrator: python src/main_orchestrator.py")
        print("4. The system will automatically handle live data and fallback")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()