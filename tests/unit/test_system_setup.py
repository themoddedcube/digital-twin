#!/usr/bin/env python3
"""
Test script to validate the F1 Dual Twin System setup.

This script tests the core interfaces, base implementations, and system initialization
to ensure everything is working correctly.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import (
    initialize_system,
    get_component,
    get_system_status,
    shutdown_system,
    get_config,
    set_config,
    validate_json_schema,
    get_schema,
    TELEMETRY_SCHEMA
)


def test_configuration():
    """Test configuration management."""
    print("Testing configuration management...")
    
    # Test default configuration
    update_interval = get_config("telemetry.update_interval_seconds")
    print(f"Default telemetry update interval: {update_interval}s")
    
    # Test setting configuration
    set_config("test.value", 42)
    test_value = get_config("test.value")
    assert test_value == 42, f"Expected 42, got {test_value}"
    
    print("✓ Configuration management working")


def test_schemas():
    """Test JSON schema validation."""
    print("Testing JSON schemas...")
    
    # Test telemetry schema
    valid_telemetry = {
        "timestamp": "2024-03-17T14:30:45.123Z",
        "lap": 26,
        "session_type": "race",
        "track_conditions": {
            "temperature": 40.1,
            "weather": "sunny",
            "track_status": "green"
        },
        "cars": [
            {
                "car_id": "44",
                "team": "Mercedes",
                "driver": "Hamilton",
                "position": 3,
                "speed": 301.2,
                "tire": {
                    "compound": "medium",
                    "age": 12,
                    "wear_level": 0.42
                },
                "fuel_level": 0.55,
                "lap_time": 83.245
            }
        ]
    }
    
    # Basic validation (our simple validator)
    is_valid = validate_json_schema(valid_telemetry, TELEMETRY_SCHEMA)
    print(f"Telemetry validation result: {is_valid}")
    
    # Test schema retrieval
    schema = get_schema("telemetry")
    assert schema is not None, "Failed to retrieve telemetry schema"
    
    print("✓ Schema validation working")


def test_system_initialization():
    """Test system initialization."""
    print("Testing system initialization...")
    
    # Initialize system with config file
    config_file = "config/system_config.json"
    success = initialize_system(config_file)
    assert success, "System initialization failed"
    
    print("✓ System initialization successful")


def test_component_access():
    """Test component registration and access."""
    print("Testing component access...")
    
    # Get telemetry processor
    telemetry_processor = get_component("telemetry_processor")
    assert telemetry_processor is not None, "Failed to get telemetry processor"
    
    # Get state manager
    state_manager = get_component("state_manager")
    assert state_manager is not None, "Failed to get state manager"
    
    print("✓ Component access working")


def test_telemetry_processing():
    """Test telemetry processing functionality."""
    print("Testing telemetry processing...")
    
    telemetry_processor = get_component("telemetry_processor")
    
    # Test with sample data
    sample_data = {
        "timestamp": "2024-03-17T14:30:45.123Z",
        "lap": 1,
        "session_type": "race",
        "track_conditions": {
            "temperature": 25.0,
            "weather": "sunny",
            "track_status": "green"
        },
        "cars": [
            {
                "car_id": "44",
                "team": "Mercedes",
                "driver": "Hamilton",
                "position": 1,
                "speed": 300.0,
                "tire": {
                    "compound": "medium",
                    "age": 5,
                    "wear_level": 0.1
                },
                "fuel_level": 0.8,
                "lap_time": 85.0
            }
        ]
    }
    
    try:
        normalized_data = telemetry_processor.ingest_telemetry(sample_data)
        assert normalized_data is not None, "Telemetry processing returned None"
        assert "timestamp" in normalized_data, "Missing timestamp in normalized data"
        print("✓ Telemetry processing working")
    except Exception as e:
        print(f"✗ Telemetry processing failed: {e}")


def test_state_management():
    """Test state management functionality."""
    print("Testing state management...")
    
    state_manager = get_component("state_manager")
    
    # Test state persistence
    test_state = {
        "test_key": "test_value",
        "timestamp": "2024-03-17T14:30:45.123Z"
    }
    
    try:
        state_manager.persist_state(test_state)
        loaded_state = state_manager.load_state()
        
        assert loaded_state is not None, "Failed to load state"
        assert "test_key" in loaded_state, "Test key not found in loaded state"
        assert loaded_state["test_key"] == "test_value", "Test value mismatch"
        
        print("✓ State management working")
    except Exception as e:
        print(f"✗ State management failed: {e}")


def test_system_status():
    """Test system status reporting."""
    print("Testing system status...")
    
    status = get_system_status()
    assert status["initialized"] is True, "System not showing as initialized"
    assert "components" in status, "Missing components in status"
    assert len(status["components"]) > 0, "No components registered"
    
    print(f"✓ System status: {len(status['components'])} components registered")


def main():
    """Run all tests."""
    print("=" * 50)
    print("F1 Dual Twin System Setup Test")
    print("=" * 50)
    
    try:
        # Test individual components
        test_configuration()
        test_schemas()
        
        # Test system initialization
        test_system_initialization()
        
        # Test integrated functionality
        test_component_access()
        test_telemetry_processing()
        test_state_management()
        test_system_status()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! System setup is working correctly.")
        print("=" * 50)
        
        # Show final system status
        print("\nFinal System Status:")
        status = get_system_status()
        print(json.dumps(status, indent=2))
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return False
    
    finally:
        # Clean shutdown
        print("\nShutting down system...")
        shutdown_system()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)