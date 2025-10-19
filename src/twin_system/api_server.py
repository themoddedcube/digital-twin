"""
REST API server for F1 Dual Twin System external integration.

This module provides a FastAPI-based REST API server that exposes twin data
with sub-50ms response times and concurrent access support.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import uvicorn
from pydantic import BaseModel
from typing import Union

from twin_system.dashboard import get_state_handler, StateHandler
from twin_system.system_monitor import get_system_monitor
from utils.config import get_config
from core.schemas import validate_json_schema, CAR_TWIN_SCHEMA, FIELD_TWIN_SCHEMA, TELEMETRY_SCHEMA


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
    def get_version_from_request(request: Request) -> str:
        """Extract schema version from request headers or query params."""
        # Check Accept header for version
        accept_header = request.headers.get("Accept", "")
        if "version=" in accept_header:
            version = accept_header.split("version=")[1].split(";")[0].strip()
            if version in SUPPORTED_SCHEMA_VERSIONS:
                return version
        
        # Check query parameter
        version = request.query_params.get("schema_version")
        if version and version in SUPPORTED_SCHEMA_VERSIONS:
            return version
        
        # Check custom header
        version = request.headers.get("X-Schema-Version")
        if version and version in SUPPORTED_SCHEMA_VERSIONS:
            return version
        
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

# Concurrent access management
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
            api_metrics.increment_connections()
            return True
    
    def release_connection(self, client_id: str) -> None:
        """Release a connection slot."""
        with self._lock:
            self.active_connections.discard(client_id)
            api_metrics.decrement_connections()
    
    def get_connection_count(self) -> int:
        """Get current connection count."""
        with self._lock:
            return len(self.active_connections)

# Global instances
api_cache = APICache()
api_metrics = APIMetrics()
schema_manager = SchemaVersionManager()
connection_manager = ConcurrentAccessManager()
state_handler: Optional[StateHandler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global state_handler
    
    # Startup
    try:
        state_handler = get_state_handler()
        print("API Server: State handler initialized")
    except Exception as e:
        print(f"API Server: Failed to initialize state handler: {e}")
        state_handler = None
    
    yield
    
    # Shutdown
    if state_handler:
        try:
            state_handler.shutdown()
            print("API Server: State handler shutdown complete")
        except Exception as e:
            print(f"API Server: Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="F1 Dual Twin System API",
    description="REST API for accessing Car Twin, Field Twin, and telemetry data",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Middleware to track response times and enforce performance requirements."""
    start_time = time.time()
    
    # Generate client ID for connection tracking
    client_id = f"{request.client.host}:{request.client.port}:{int(time.time() * 1000)}"
    
    # Check concurrent connection limits
    max_connections = get_config("api.max_concurrent_connections", 10)
    connection_manager.max_connections = max_connections
    
    if not connection_manager.acquire_connection(client_id):
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "Too many concurrent connections",
                "max_connections": max_connections,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        endpoint = request.url.path
        api_metrics.record_request(endpoint, response_time_ms)
        
        # Get schema version for response
        schema_version = schema_manager.get_version_from_request(request)
        
        # Add performance and versioning headers
        response.headers["X-Response-Time-Ms"] = str(round(response_time_ms, 2))
        response.headers["X-Cache-Status"] = "hit" if hasattr(request.state, "cache_hit") else "miss"
        response.headers["X-Schema-Version"] = schema_version
        response.headers["X-Supported-Versions"] = ",".join(SUPPORTED_SCHEMA_VERSIONS)
        response.headers["X-Concurrent-Connections"] = str(connection_manager.get_connection_count())
        
        # Log slow responses
        if response_time_ms > 50:
            print(f"WARNING: Slow API response: {endpoint} took {response_time_ms:.2f}ms")
        
        return response
        
    finally:
        # Always release connection
        connection_manager.release_connection(client_id)


def get_cached_or_fetch(cache_key: str, fetch_func, request: Request = None) -> Dict[str, Any]:
    """Get data from cache or fetch fresh data with schema version support."""
    # Include schema version in cache key
    schema_version = DEFAULT_SCHEMA_VERSION
    if request:
        schema_version = schema_manager.get_version_from_request(request)
    
    versioned_cache_key = f"{cache_key}:v{schema_version}"
    
    # Try cache first
    cached_data = api_cache.get(versioned_cache_key)
    if cached_data:
        if request:
            request.state.cache_hit = True
        return cached_data
    
    # Fetch fresh data
    fresh_data = fetch_func()
    
    # Transform for requested schema version
    if request:
        fresh_data = schema_manager.transform_response_for_version(fresh_data, schema_version)
    
    # Cache the result
    api_cache.set(versioned_cache_key, fresh_data)
    
    return fresh_data


@app.get("/api/v1/car-twin", response_model=Dict[str, Any])
async def get_car_twin_data(request: Request):
    """
    Get current Car Twin state and predictions.
    
    Supports schema versioning via Accept header, X-Schema-Version header, or schema_version query parameter.
    
    Returns:
        Car Twin state data with predictions and strategy metrics
    """
    if not state_handler:
        raise HTTPException(status_code=503, detail="State handler not available")
    
    def fetch_car_twin():
        try:
            car_twin_state = state_handler.get_car_twin_state()
            
            if not car_twin_state:
                return {
                    "success": False,
                    "message": "No Car Twin data available",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "schema_version": "1.0.0",
                    "car_twin": None
                }
            
            # Validate schema compliance
            if not validate_json_schema(car_twin_state, CAR_TWIN_SCHEMA):
                print("WARNING: Car Twin data does not match expected schema")
            
            return {
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0",
                "car_twin": car_twin_state,
                "metadata": {
                    "last_update": car_twin_state.get("last_update_timestamp"),
                    "update_source": car_twin_state.get("update_source", "unknown")
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0"
            }
    
    return get_cached_or_fetch("car_twin", fetch_car_twin, request)


@app.get("/api/v1/field-twin", response_model=Dict[str, Any])
async def get_field_twin_data(request: Request):
    """
    Get current Field Twin state with competitor models and strategic analysis.
    
    Supports schema versioning via Accept header, X-Schema-Version header, or schema_version query parameter.
    
    Returns:
        Field Twin state data with competitor predictions and opportunities
    """
    if not state_handler:
        raise HTTPException(status_code=503, detail="State handler not available")
    
    def fetch_field_twin():
        try:
            field_twin_state = state_handler.get_field_twin_state()
            
            if not field_twin_state:
                return {
                    "success": False,
                    "message": "No Field Twin data available",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "schema_version": "1.0.0",
                    "field_twin": None
                }
            
            # Validate schema compliance
            if not validate_json_schema(field_twin_state, FIELD_TWIN_SCHEMA):
                print("WARNING: Field Twin data does not match expected schema")
            
            return {
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0",
                "field_twin": field_twin_state,
                "metadata": {
                    "last_update": field_twin_state.get("last_update_timestamp"),
                    "update_source": field_twin_state.get("update_source", "unknown"),
                    "competitor_count": len(field_twin_state.get("competitors", []))
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0"
            }
    
    return get_cached_or_fetch("field_twin", fetch_field_twin, request)


@app.get("/api/v1/telemetry", response_model=Dict[str, Any])
async def get_telemetry_data(request: Request):
    """
    Get current telemetry data including raw and processed information.
    
    Supports schema versioning via Accept header, X-Schema-Version header, or schema_version query parameter.
    
    Returns:
        Current telemetry state with track conditions and car data
    """
    if not state_handler:
        raise HTTPException(status_code=503, detail="State handler not available")
    
    def fetch_telemetry():
        try:
            telemetry_state = state_handler.get_telemetry_state()
            
            if not telemetry_state:
                return {
                    "success": False,
                    "message": "No telemetry data available",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "schema_version": "1.0.0",
                    "telemetry": None
                }
            
            # Validate schema compliance
            if not validate_json_schema(telemetry_state, TELEMETRY_SCHEMA):
                print("WARNING: Telemetry data does not match expected schema")
            
            return {
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0",
                "telemetry": telemetry_state,
                "metadata": {
                    "last_update": telemetry_state.get("last_update_timestamp"),
                    "update_source": telemetry_state.get("update_source", "unknown"),
                    "car_count": len(telemetry_state.get("cars", []))
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0"
            }
    
    return get_cached_or_fetch("telemetry", fetch_telemetry, request)


@app.get("/api/v1/environment", response_model=Dict[str, Any])
async def get_environment_data(request: Request):
    """
    Get current environment data including track conditions and race state.
    
    Supports schema versioning via Accept header, X-Schema-Version header, or schema_version query parameter.
    
    Returns:
        Environment state with track conditions, weather, and race context
    """
    if not state_handler:
        raise HTTPException(status_code=503, detail="State handler not available")
    
    def fetch_environment():
        try:
            environment_state = state_handler.get_environment_state()
            telemetry_state = state_handler.get_telemetry_state()
            
            # Combine environment and race context data
            combined_environment = {
                "track_conditions": environment_state.get("track_conditions", {}),
                "race_context": {
                    "current_lap": telemetry_state.get("lap", 0),
                    "session_type": telemetry_state.get("session_type", "unknown"),
                    "track_status": environment_state.get("track_status", "green")
                },
                "weather": environment_state.get("weather", {}),
                "flags": environment_state.get("flags", {})
            }
            
            return {
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0",
                "environment": combined_environment,
                "metadata": {
                    "last_update": environment_state.get("last_update_timestamp"),
                    "update_source": environment_state.get("update_source", "unknown")
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0"
            }
    
    return get_cached_or_fetch("environment", fetch_environment, request)


@app.get("/api/v1/health", response_model=Dict[str, Any])
async def health_check():
    """
    System health check endpoint for monitoring.
    
    Returns:
        System health status and performance metrics
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "components": {
                "state_handler": "healthy" if state_handler else "unavailable",
                "api_cache": "healthy",
                "metrics_collector": "healthy"
            },
            "performance": api_metrics.get_metrics(),
            "system_info": {
                "cache_entries": len(api_cache._cache),
                "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0,
                "concurrent_connections": connection_manager.get_connection_count(),
                "max_concurrent_connections": connection_manager.max_connections
            },
            "api_versioning": {
                "supported_versions": SUPPORTED_SCHEMA_VERSIONS,
                "default_version": DEFAULT_SCHEMA_VERSION
            }
        }
        
        # Check component health
        if state_handler:
            try:
                # Test state handler responsiveness
                state_handler.get_complete_system_state()
                health_status["components"]["state_handler"] = "healthy"
            except Exception as e:
                health_status["components"]["state_handler"] = f"error: {str(e)}"
                health_status["status"] = "degraded"
        else:
            health_status["status"] = "degraded"
        
        # Add system monitor health data
        try:
            system_monitor = get_system_monitor()
            if system_monitor:
                monitor_health = system_monitor.get_system_health_report()
                health_status["system_monitor"] = {
                    "overall_health": monitor_health.get("overall_health"),
                    "health_score": monitor_health.get("health_score"),
                    "component_health": monitor_health.get("component_health"),
                    "active_alerts": len(monitor_health.get("active_alerts", []))
                }
                
                # Update overall status based on system monitor
                if monitor_health.get("overall_health") in ["critical", "degraded"]:
                    health_status["status"] = monitor_health.get("overall_health")
                elif monitor_health.get("overall_health") == "warning" and health_status["status"] == "healthy":
                    health_status["status"] = "warning"
        except Exception as e:
            health_status["system_monitor_error"] = str(e)
        
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }


@app.get("/api/v1/system/complete", response_model=Dict[str, Any])
async def get_complete_system_state(request: Request):
    """
    Get complete system state from all components.
    
    Supports schema versioning via Accept header, X-Schema-Version header, or schema_version query parameter.
    
    Returns:
        Complete system state including all twin data and metadata
    """
    if not state_handler:
        raise HTTPException(status_code=503, detail="State handler not available")
    
    def fetch_complete_state():
        try:
            complete_state = state_handler.get_complete_system_state()
            
            return {
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0",
                "system_state": complete_state,
                "metadata": {
                    "components": ["car_twin", "field_twin", "telemetry", "environment"],
                    "data_freshness": {
                        "car_twin": complete_state.get("system_metadata", {}).get("last_car_twin_update"),
                        "field_twin": complete_state.get("system_metadata", {}).get("last_field_twin_update"),
                        "telemetry": complete_state.get("system_metadata", {}).get("last_telemetry_update")
                    }
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0"
            }
    
    return get_cached_or_fetch("complete_state", fetch_complete_state, request)


@app.post("/api/v1/cache/clear")
async def clear_cache():
    """
    Clear API cache (for development and testing).
    
    Returns:
        Cache clear confirmation
    """
    api_cache.clear()
    return {
        "success": True,
        "message": "API cache cleared",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/v1/metrics", response_model=Dict[str, Any])
async def get_api_metrics():
    """
    Get API performance metrics.
    
    Returns:
        Detailed performance metrics for all endpoints
    """
    return {
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": api_metrics.get_metrics(),
        "cache_stats": {
            "entries": len(api_cache._cache),
            "ttl_seconds": api_cache.cache_ttl
        },
        "concurrent_access": {
            "active_connections": connection_manager.get_connection_count(),
            "max_connections": connection_manager.max_connections
        }
    }


@app.get("/api/v1/version", response_model=Dict[str, Any])
async def get_api_version_info():
    """
    Get API version information and supported schema versions.
    
    Returns:
        API version details and backward compatibility information
    """
    return {
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_version": "1.0.0",
        "schema_versioning": {
            "supported_versions": SUPPORTED_SCHEMA_VERSIONS,
            "default_version": DEFAULT_SCHEMA_VERSION,
            "version_headers": [
                "Accept: application/json; version=1.0.0",
                "X-Schema-Version: 1.0.0"
            ],
            "version_query_param": "schema_version=1.0.0"
        },
        "backward_compatibility": {
            "1.0.0": "Original schema format",
            "1.1.0": "Enhanced metadata and concurrent access support"
        },
        "deprecation_policy": {
            "notice_period_months": 6,
            "support_period_months": 12
        }
    }


@app.get("/api/v1/system/performance", response_model=Dict[str, Any])
async def get_system_performance():
    """
    Get detailed system performance metrics and monitoring data.
    
    Returns:
        Comprehensive performance and monitoring report
    """
    try:
        system_monitor = get_system_monitor()
        if not system_monitor:
            return {
                "success": False,
                "error": "System monitor not available",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Get comprehensive reports
        health_report = system_monitor.get_system_health_report()
        performance_report = system_monitor.get_performance_report()
        
        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_report": health_report,
            "performance_report": performance_report,
            "api_performance": api_metrics.get_metrics(),
            "system_status": {
                "monitoring_enabled": system_monitor.monitoring_enabled,
                "monitoring_running": system_monitor.running,
                "monitored_components": list(system_monitor.monitored_components.keys())
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.get("/api/v1/concurrent-status", response_model=Dict[str, Any])
async def get_concurrent_status():
    """
    Get current concurrent access status and connection information.
    
    Returns:
        Concurrent connection status and performance impact
    """
    connection_count = connection_manager.get_connection_count()
    max_connections = connection_manager.max_connections
    
    # Calculate load percentage
    load_percentage = (connection_count / max_connections) * 100 if max_connections > 0 else 0
    
    # Determine status based on load
    if load_percentage < 50:
        status = "optimal"
    elif load_percentage < 80:
        status = "moderate"
    elif load_percentage < 95:
        status = "high"
    else:
        status = "critical"
    
    return {
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "concurrent_access": {
            "status": status,
            "active_connections": connection_count,
            "max_connections": max_connections,
            "load_percentage": round(load_percentage, 1),
            "available_slots": max_connections - connection_count
        },
        "performance_impact": {
            "expected_response_time_ms": min(50, 25 + (load_percentage * 0.3)),
            "degradation_risk": "low" if load_percentage < 80 else "medium" if load_percentage < 95 else "high"
        },
        "recommendations": {
            "optimal_load": "< 50% for best performance",
            "max_recommended": "< 80% to avoid degradation",
            "scale_threshold": "> 90% consider scaling"
        }
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "available_endpoints": [
                "/api/v1/car-twin",
                "/api/v1/field-twin", 
                "/api/v1/telemetry",
                "/api/v1/environment",
                "/api/v1/health",
                "/api/v1/system/complete",
                "/api/v1/version",
                "/api/v1/metrics",
                "/api/v1/concurrent-status"
            ],
            "schema_versioning": {
                "supported_versions": SUPPORTED_SCHEMA_VERSIONS,
                "default_version": DEFAULT_SCHEMA_VERSION
            }
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Set startup time for uptime calculation
    app.state.start_time = time.time()
    return app


def run_server(host: str = None, port: int = None, reload: bool = False):
    """
    Run the API server with specified configuration.
    
    Args:
        host: Server host (defaults to config)
        port: Server port (defaults to config)
        reload: Enable auto-reload for development
    """
    # Get configuration
    api_config = get_config("api", {})
    server_host = host or api_config.get("host", "localhost")
    server_port = port or api_config.get("port", 8000)
    
    print(f"Starting F1 Dual Twin API Server on {server_host}:{server_port}")
    
    # Configure uvicorn
    uvicorn.run(
        "api_server:app",
        host=server_host,
        port=server_port,
        reload=reload,
        access_log=True,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)