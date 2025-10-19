#!/usr/bin/env python3
"""
Test script for F1 Dual Twin API Server functionality.

This script tests the API server components without requiring external dependencies.
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_api_cache():
    """Test API cache functionality."""
    print("Testing API Cache...")
    
    # Import after path setup
    from api_core import APICache
    
    cache = APICache(cache_ttl_seconds=1)
    
    # Test set and get
    test_data = {"test": "data", "timestamp": datetime.now(timezone.utc).isoformat()}
    cache.set("test_key", test_data)
    
    retrieved = cache.get("test_key")
    assert retrieved == test_data, "Cache get/set failed"
    
    # Test TTL expiration
    import time
    time.sleep(1.1)  # Wait for TTL to expire
    expired = cache.get("test_key")
    assert expired is None, "Cache TTL not working"
    
    print("✓ API Cache tests passed")


def test_api_metrics():
    """Test API metrics functionality."""
    print("Testing API Metrics...")
    
    from api_core import APIMetrics
    
    metrics = APIMetrics()
    
    # Test recording requests
    metrics.record_request("/api/v1/car-twin", 25.5)
    metrics.record_request("/api/v1/field-twin", 30.2)
    metrics.record_request("/api/v1/car-twin", 22.1)
    
    # Test connection tracking
    metrics.increment_connections()
    metrics.increment_connections()
    assert metrics.concurrent_connections == 2, "Connection tracking failed"
    
    metrics.decrement_connections()
    assert metrics.concurrent_connections == 1, "Connection decrement failed"
    
    # Test metrics retrieval
    result = metrics.get_metrics()
    assert result["total_requests"] == 3, "Request count incorrect"
    assert "/api/v1/car-twin" in result["endpoints"], "Endpoint metrics missing"
    assert result["endpoints"]["/api/v1/car-twin"]["request_count"] == 2, "Endpoint count incorrect"
    
    print("✓ API Metrics tests passed")


def test_schema_version_manager():
    """Test schema versioning functionality."""
    print("Testing Schema Version Manager...")
    
    from api_core import SchemaVersionManager
    
    # Mock request object
    class MockRequest:
        def __init__(self, headers=None, query_params=None):
            self.headers = headers or {}
            self.query_params = query_params or {}
    
    manager = SchemaVersionManager()
    
    # Test default version
    request = MockRequest()
    version = manager.get_version_from_request(request)
    assert version == "1.0.0", "Default version incorrect"
    
    # Test header version
    request = MockRequest(headers={"X-Schema-Version": "1.1.0"})
    version = manager.get_version_from_request(request)
    assert version == "1.1.0", "Header version parsing failed"
    
    # Test query parameter version
    request = MockRequest(query_params={"schema_version": "1.1.0"})
    version = manager.get_version_from_request(request)
    assert version == "1.1.0", "Query param version parsing failed"
    
    # Test response transformation
    test_data = {"metadata": {"test": "data"}}
    transformed = manager.transform_response_for_version(test_data, "1.1.0")
    assert "schema_features" in transformed["metadata"], "Version transformation failed"
    
    print("✓ Schema Version Manager tests passed")


def test_concurrent_access_manager():
    """Test concurrent access management."""
    print("Testing Concurrent Access Manager...")
    
    from api_core import ConcurrentAccessManager
    
    manager = ConcurrentAccessManager(max_connections=2)
    
    # Test connection acquisition
    assert manager.acquire_connection("client1"), "First connection failed"
    assert manager.acquire_connection("client2"), "Second connection failed"
    assert not manager.acquire_connection("client3"), "Third connection should fail"
    
    # Test connection release
    manager.release_connection("client1")
    assert manager.acquire_connection("client3"), "Connection after release failed"
    
    assert manager.get_connection_count() == 2, "Connection count incorrect"
    
    print("✓ Concurrent Access Manager tests passed")


def test_api_endpoints_structure():
    """Test API endpoint structure without FastAPI dependencies."""
    print("Testing API Endpoint Structure...")
    
    # Test that we can import the module structure
    try:
        import api_core
        
        # Check that key classes exist
        assert hasattr(api_core, 'APICache'), "APICache class missing"
        assert hasattr(api_core, 'APIMetrics'), "APIMetrics class missing"
        assert hasattr(api_core, 'SchemaVersionManager'), "SchemaVersionManager class missing"
        assert hasattr(api_core, 'ConcurrentAccessManager'), "ConcurrentAccessManager class missing"
        
        # Check constants
        assert hasattr(api_core, 'SUPPORTED_SCHEMA_VERSIONS'), "Schema versions missing"
        assert hasattr(api_core, 'DEFAULT_SCHEMA_VERSION'), "Default version missing"
        
        print("✓ API Endpoint Structure tests passed")
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    
    return True


def test_integration_with_state_handler():
    """Test integration with state handler (mock)."""
    print("Testing State Handler Integration...")
    
    from api_core import MockStateHandler, create_api_components
    
    # Test mock state handler
    mock_handler = MockStateHandler()
    
    # Test all state retrieval methods
    car_twin = mock_handler.get_car_twin_state()
    assert car_twin["car_id"] == "44", "Car twin state invalid"
    
    field_twin = mock_handler.get_field_twin_state()
    assert len(field_twin["competitors"]) > 0, "Field twin state invalid"
    
    telemetry = mock_handler.get_telemetry_state()
    assert telemetry["lap"] > 0, "Telemetry state invalid"
    
    environment = mock_handler.get_environment_state()
    assert "track_conditions" in environment, "Environment state invalid"
    
    complete_state = mock_handler.get_complete_system_state()
    assert all(key in complete_state for key in ["car_twin", "field_twin", "telemetry", "environment"]), "Complete state invalid"
    
    # Test API components integration
    components = create_api_components()
    assert "state_handler" in components, "State handler not in components"
    assert "data_processor" in components, "Data processor not in components"
    
    print("✓ State Handler Integration tests passed")


def test_api_response_builder():
    """Test API response builder functionality."""
    print("Testing API Response Builder...")
    
    from api_core import APIResponseBuilder, SchemaVersionManager
    
    schema_manager = SchemaVersionManager()
    builder = APIResponseBuilder(schema_manager)
    
    # Test success response
    test_data = {"test": "data"}
    success_response = builder.build_success_response(test_data)
    assert success_response["success"] is True, "Success response invalid"
    assert "timestamp" in success_response, "Timestamp missing"
    assert "schema_version" in success_response, "Schema version missing"
    
    # Test error response
    error_response = builder.build_error_response("Test error", 404)
    assert error_response["success"] is False, "Error response invalid"
    assert error_response["status_code"] == 404, "Status code incorrect"
    
    # Test health response
    components_status = {"state_handler": "healthy", "cache": "healthy"}
    metrics = {"requests": 100}
    health_response = builder.build_health_response(components_status, metrics)
    assert health_response["status"] == "healthy", "Health status incorrect"
    assert "api_versioning" in health_response, "API versioning info missing"
    
    print("✓ API Response Builder tests passed")


def test_api_data_processor():
    """Test API data processor functionality."""
    print("Testing API Data Processor...")
    
    from api_core import create_api_components
    
    components = create_api_components()
    data_processor = components["data_processor"]
    
    # Test cached fetch
    def mock_fetch():
        return {"data": "test", "timestamp": datetime.now(timezone.utc).isoformat()}
    
    # First call should fetch
    result1 = data_processor.get_cached_or_fetch("test_key", mock_fetch)
    assert "data" in result1, "Data fetch failed"
    
    # Second call should use cache
    result2 = data_processor.get_cached_or_fetch("test_key", mock_fetch)
    assert result1 == result2, "Cache not working"
    
    # Test twin data validation
    mock_twin_data = {"car_id": "44", "timestamp": datetime.now(timezone.utc).isoformat()}
    processed = data_processor.validate_and_process_twin_data(mock_twin_data, "car_twin")
    assert processed["success"] is True, "Twin data processing failed"
    assert "car_twin" in processed, "Twin data missing from response"
    
    print("✓ API Data Processor tests passed")


def create_sample_api_response():
    """Create sample API responses for testing."""
    print("Creating Sample API Responses...")
    
    # Create shared directory if it doesn't exist
    shared_dir = Path("shared")
    shared_dir.mkdir(exist_ok=True)
    
    # Sample telemetry state
    sample_telemetry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
                "lap_time": 83.245,
                "sector_times": [28.1, 31.2, 23.9]
            }
        ]
    }
    
    # Write sample data
    with open(shared_dir / "telemetry_state.json", "w") as f:
        json.dump(sample_telemetry, f, indent=2)
    
    print("✓ Sample API responses created")


def main():
    """Run all tests."""
    print("F1 Dual Twin API Server Tests")
    print("=" * 40)
    
    try:
        test_api_cache()
        test_api_metrics()
        test_schema_version_manager()
        test_concurrent_access_manager()
        
        if test_api_endpoints_structure():
            test_integration_with_state_handler()
            test_api_response_builder()
            test_api_data_processor()
            create_sample_api_response()
        
        print("\n" + "=" * 40)
        print("✓ All API Server tests passed!")
        print("\nAPI Server Features Implemented:")
        print("- In-memory caching with TTL")
        print("- Performance metrics tracking")
        print("- Schema versioning support")
        print("- Concurrent connection management")
        print("- REST endpoint structure")
        print("- State handler integration")
        print("- Error handling and health checks")
        
        print("\nTo run the server:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run server: python src/api_server.py")
        print("3. Access endpoints at http://localhost:8000/api/v1/")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)