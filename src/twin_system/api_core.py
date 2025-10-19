"""
Core API functionality for F1 Dual Twin System.

This module contains the core API classes and functionality separated from FastAPI
to enable testing and development without external dependencies.
"""

import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
import json


class APICache:
    """In-memory cache for API responses to meet 50ms response time requirement."""
    
    def __init__(self, cache_ttl_seconds: int = 1):
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value if still valid."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check if cache entry is still valid
            if time.time() - self._cache_timestamps[key] > self.cache_ttl:
                del self._cache[key]
                del self._cache_timestamps[key]
                return None
            
            return self._cache[key].copy()
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set cached value with timestamp."""
        with self._lock:
            self._cache[key] = value.copy()
            self._cache_timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._cache_timestamps.clear()


class APIMetrics:
    """Performance metrics tracking for API endpoints."""
    
    def __init__(self):
        self.request_count = 0
        self.total_response_time = 0.0
        self.max_response_time = 0.0
        self.min_response_time = float('inf')
        self.endpoint_metrics: Dict[str, Dict[str, Any]] = {}
        self.concurrent_connections = 0
        self.max_concurrent_connections = 0
        self._lock = threading.RLock()
    
    def record_request(self, endpoint: str, response_time_ms: float) -> None:
        """Record request metrics."""
        with self._lock:
            # Global metrics
            self.request_count += 1
            self.total_response_time += response_time_ms
            self.max_response_time = max(self.max_response_time, response_time_ms)
            self.min_response_time = min(self.min_response_time, response_time_ms)
            
            # Endpoint-specific metrics
            if endpoint not in self.endpoint_metrics:
                self.endpoint_metrics[endpoint] = {
                    "count": 0,
                    "total_time": 0.0,
                    "max_time": 0.0,
                    "min_time": float('inf')
                }
            
            metrics = self.endpoint_metrics[endpoint]
            metrics["count"] += 1
            metrics["total_time"] += response_time_ms
            metrics["max_time"] = max(metrics["max_time"], response_time_ms)
            metrics["min_time"] = min(metrics["min_time"], response_time_ms)
    
    def increment_connections(self) -> None:
        """Increment concurrent connection count."""
        with self._lock:
            self.concurrent_connections += 1
            self.max_concurrent_connections = max(self.max_concurrent_connections, self.concurrent_connections)
    
    def decrement_connections(self) -> None:
        """Decrement concurrent connection count."""
        with self._lock:
            self.concurrent_connections = max(0, self.concurrent_connections - 1)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        with self._lock:
            if self.request_count == 0:
                return {"status": "no_requests"}
            
            endpoint_stats = {}
            for endpoint, metrics in self.endpoint_metrics.items():
                if metrics["count"] > 0:
                    endpoint_stats[endpoint] = {
                        "request_count": metrics["count"],
                        "avg_response_time_ms": metrics["total_time"] / metrics["count"],
                        "max_response_time_ms": metrics["max_time"],
                        "min_response_time_ms": metrics["min_time"]
                    }
            
            return {
                "total_requests": self.request_count,
                "avg_response_time_ms": self.total_response_time / self.request_count,
                "max_response_time_ms": self.max_response_time,
                "min_response_time_ms": self.min_response_time,
                "concurrent_connections": self.concurrent_connections,
                "max_concurrent_connections": self.max_concurrent_connections,
                "endpoints": endpoint_stats
            }


# Schema versioning support
SUPPORTED_SCHEMA_VERSIONS = ["1.0.0", "1.1.0"]
DEFAULT_SCHEMA_VERSION = "1.0.0"


class SchemaVersionManager:
    """Manages API schema versioning for backward compatibility."""
    
    @staticmethod
    def get_version_from_headers(headers: Dict[str, str]) -> str:
        """Extract schema version from request headers."""
        # Check Accept header for version
        accept_header = headers.get("Accept", "")
        if "version=" in accept_header:
            version = accept_header.split("version=")[1].split(";")[0].strip()
            if version in SUPPORTED_SCHEMA_VERSIONS:
                return version
        
        # Check custom header
        version = headers.get("X-Schema-Version")
        if version and version in SUPPORTED_SCHEMA_VERSIONS:
            return version
        
        return DEFAULT_SCHEMA_VERSION
    
    @staticmethod
    def get_version_from_query(query_params: Dict[str, str]) -> str:
        """Extract schema version from query parameters."""
        version = query_params.get("schema_version")
        if version and version in SUPPORTED_SCHEMA_VERSIONS:
            return version
        return DEFAULT_SCHEMA_VERSION
    
    @staticmethod
    def get_version_from_request(request) -> str:
        """Extract schema version from request (mock-compatible)."""
        # Handle mock request objects
        if hasattr(request, 'headers') and hasattr(request, 'query_params'):
            # Check headers first
            if hasattr(request.headers, 'get'):
                version = SchemaVersionManager.get_version_from_headers(request.headers)
                if version != DEFAULT_SCHEMA_VERSION:
                    return version
            
            # Check query params
            if hasattr(request.query_params, 'get'):
                return SchemaVersionManager.get_version_from_query(request.query_params)
        
        return DEFAULT_SCHEMA_VERSION
    
    @staticmethod
    def transform_response_for_version(data: Dict[str, Any], version: str) -> Dict[str, Any]:
        """Transform response data based on requested schema version."""
        if version == "1.0.0":
            return data
        elif version == "1.1.0":
            # Add enhanced metadata for v1.1.0
            if "metadata" in data:
                data["metadata"]["schema_features"] = ["enhanced_metrics", "concurrent_support"]
            return data
        else:
            return data


class ConcurrentAccessManager:
    """Manages concurrent client connections and prevents performance degradation."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.active_connections = set()
        self._lock = threading.RLock()
    
    def acquire_connection(self, client_id: str) -> bool:
        """Acquire a connection slot for a client."""
        with self._lock:
            if len(self.active_connections) >= self.max_connections:
                return False
            self.active_connections.add(client_id)
            return True
    
    def release_connection(self, client_id: str) -> None:
        """Release a connection slot."""
        with self._lock:
            self.active_connections.discard(client_id)
    
    def get_connection_count(self) -> int:
        """Get current connection count."""
        with self._lock:
            return len(self.active_connections)


class APIResponseBuilder:
    """Builds standardized API responses with versioning support."""
    
    def __init__(self, schema_manager: SchemaVersionManager):
        self.schema_manager = schema_manager
    
    def build_success_response(self, data: Dict[str, Any], schema_version: str = DEFAULT_SCHEMA_VERSION) -> Dict[str, Any]:
        """Build successful API response."""
        response = {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": schema_version,
            **data
        }
        
        return self.schema_manager.transform_response_for_version(response, schema_version)
    
    def build_error_response(self, error_message: str, status_code: int = 500, schema_version: str = DEFAULT_SCHEMA_VERSION) -> Dict[str, Any]:
        """Build error API response."""
        response = {
            "success": False,
            "error": error_message,
            "status_code": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": schema_version
        }
        
        return self.schema_manager.transform_response_for_version(response, schema_version)
    
    def build_health_response(self, components_status: Dict[str, str], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Build health check response."""
        overall_status = "healthy"
        if any(status != "healthy" for status in components_status.values()):
            overall_status = "degraded"
        
        return {
            "success": True,
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "components": components_status,
            "performance": metrics,
            "api_versioning": {
                "supported_versions": SUPPORTED_SCHEMA_VERSIONS,
                "default_version": DEFAULT_SCHEMA_VERSION
            }
        }


class APIDataProcessor:
    """Processes and validates data for API responses."""
    
    def __init__(self, cache: APICache, response_builder: APIResponseBuilder):
        self.cache = cache
        self.response_builder = response_builder
    
    def get_cached_or_fetch(self, cache_key: str, fetch_func, schema_version: str = DEFAULT_SCHEMA_VERSION) -> Dict[str, Any]:
        """Get data from cache or fetch fresh data with schema version support."""
        versioned_cache_key = f"{cache_key}:v{schema_version}"
        
        # Try cache first
        cached_data = self.cache.get(versioned_cache_key)
        if cached_data:
            return cached_data
        
        # Fetch fresh data
        try:
            fresh_data = fetch_func()
            
            # Transform for requested schema version
            transformed_data = self.response_builder.schema_manager.transform_response_for_version(fresh_data, schema_version)
            
            # Cache the result
            self.cache.set(versioned_cache_key, transformed_data)
            
            return transformed_data
            
        except Exception as e:
            return self.response_builder.build_error_response(f"Data fetch failed: {str(e)}", schema_version=schema_version)
    
    def validate_and_process_twin_data(self, twin_data: Dict[str, Any], twin_type: str, schema_version: str = DEFAULT_SCHEMA_VERSION) -> Dict[str, Any]:
        """Validate and process twin data for API response."""
        if not twin_data:
            return self.response_builder.build_error_response(
                f"No {twin_type} data available", 
                status_code=404, 
                schema_version=schema_version
            )
        
        # Build successful response
        response_data = {
            twin_type: twin_data,
            "metadata": {
                "last_update": twin_data.get("last_update_timestamp"),
                "update_source": twin_data.get("update_source", "unknown")
            }
        }
        
        if twin_type == "field_twin":
            response_data["metadata"]["competitor_count"] = len(twin_data.get("competitors", []))
        elif twin_type == "telemetry":
            response_data["metadata"]["car_count"] = len(twin_data.get("cars", []))
        
        return self.response_builder.build_success_response(response_data, schema_version)


class MockStateHandler:
    """Mock state handler for testing API functionality."""
    
    def __init__(self):
        self.car_twin_state = self._create_mock_car_twin_state()
        self.field_twin_state = self._create_mock_field_twin_state()
        self.telemetry_state = self._create_mock_telemetry_state()
        self.environment_state = self._create_mock_environment_state()
    
    def _create_mock_car_twin_state(self) -> Dict[str, Any]:
        """Create mock car twin state."""
        return {
            "car_id": "44",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_state": {
                "speed": 301.2,
                "tire_temp": [85.2, 87.1, 84.8, 86.5],
                "tire_wear": 0.42,
                "fuel_level": 0.55,
                "lap_time": 83.245
            },
            "predictions": {
                "tire_degradation_rate": 0.008,
                "fuel_consumption_rate": 2.1,
                "predicted_pit_lap": 35,
                "performance_delta": -0.3
            },
            "strategy_metrics": {
                "optimal_pit_window": [33, 37],
                "tire_life_remaining": 8,
                "fuel_laps_remaining": 26
            },
            "last_update_timestamp": datetime.now(timezone.utc).isoformat(),
            "update_source": "car_twin"
        }
    
    def _create_mock_field_twin_state(self) -> Dict[str, Any]:
        """Create mock field twin state."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "competitors": [
                {
                    "car_id": "33",
                    "team": "Red Bull",
                    "current_position": 1,
                    "gap_to_leader": 0.0,
                    "predicted_strategy": "two_stop",
                    "pit_probability": 0.15,
                    "strategic_threat_level": "high",
                    "behavioral_profile": {
                        "undercut_tendency": 0.7,
                        "aggressive_defense": 0.8,
                        "tire_management": 0.6
                    }
                }
            ],
            "strategic_opportunities": [
                {
                    "type": "undercut_window",
                    "target_car": "33",
                    "probability": 0.65,
                    "execution_lap": 28
                }
            ],
            "last_update_timestamp": datetime.now(timezone.utc).isoformat(),
            "update_source": "field_twin"
        }
    
    def _create_mock_telemetry_state(self) -> Dict[str, Any]:
        """Create mock telemetry state."""
        return {
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
            ],
            "last_update_timestamp": datetime.now(timezone.utc).isoformat(),
            "update_source": "telemetry_ingestor"
        }
    
    def _create_mock_environment_state(self) -> Dict[str, Any]:
        """Create mock environment state."""
        return {
            "track_conditions": {
                "temperature": 40.1,
                "weather": "sunny",
                "track_status": "green"
            },
            "weather": {
                "current": "sunny",
                "forecast": "stable"
            },
            "flags": {
                "yellow": False,
                "safety_car": False,
                "drs_enabled": True
            },
            "last_update_timestamp": datetime.now(timezone.utc).isoformat(),
            "update_source": "environment_monitor"
        }
    
    def get_car_twin_state(self) -> Dict[str, Any]:
        """Get car twin state."""
        return self.car_twin_state.copy()
    
    def get_field_twin_state(self) -> Dict[str, Any]:
        """Get field twin state."""
        return self.field_twin_state.copy()
    
    def get_telemetry_state(self) -> Dict[str, Any]:
        """Get telemetry state."""
        return self.telemetry_state.copy()
    
    def get_environment_state(self) -> Dict[str, Any]:
        """Get environment state."""
        return self.environment_state.copy()
    
    def get_complete_system_state(self) -> Dict[str, Any]:
        """Get complete system state."""
        return {
            "car_twin": self.get_car_twin_state(),
            "field_twin": self.get_field_twin_state(),
            "telemetry": self.get_telemetry_state(),
            "environment": self.get_environment_state(),
            "system_metadata": {
                "last_car_twin_update": time.time(),
                "last_field_twin_update": time.time(),
                "last_telemetry_update": time.time(),
                "state_handler_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }


# Factory function to create API components
def create_api_components(max_connections: int = 10, cache_ttl: int = 1) -> Dict[str, Any]:
    """Create and configure API components."""
    cache = APICache(cache_ttl_seconds=cache_ttl)
    metrics = APIMetrics()
    schema_manager = SchemaVersionManager()
    connection_manager = ConcurrentAccessManager(max_connections=max_connections)
    response_builder = APIResponseBuilder(schema_manager)
    data_processor = APIDataProcessor(cache, response_builder)
    mock_state_handler = MockStateHandler()
    
    return {
        "cache": cache,
        "metrics": metrics,
        "schema_manager": schema_manager,
        "connection_manager": connection_manager,
        "response_builder": response_builder,
        "data_processor": data_processor,
        "state_handler": mock_state_handler
    }