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
from max_integration.monte_carlo_handler import get_monte_carlo_handler
from max_integration.ai_strategist import AIStrategist
from max_integration.continuous_ai_service import get_continuous_ai_service


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
monte_carlo_handler = get_monte_carlo_handler()
ai_strategist: Optional[AIStrategist] = None


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
    
    # Initialize AI strategist separately (non-blocking)
    try:
        # Add timeout to prevent hanging
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("AI strategist initialization timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)  # 5 second timeout
        
        ai_strategist = AIStrategist()
        signal.alarm(0)  # Cancel timeout
        print("API Server: AI strategist initialized")
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        print(f"API Server: AI strategist initialization failed (will use fallback): {e}")
        ai_strategist = None
    
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


@app.get("/api/v1/monte-carlo/simulate", response_model=Dict[str, Any])
async def run_monte_carlo_simulation(request: Request):
    """
    Run Monte Carlo simulation for pit strategy optimization.
    
    Query Parameters:
        pit_window_start: Start of pit window (optional)
        pit_window_end: End of pit window (optional)
    
    Returns:
        Monte Carlo simulation results with best strategy
    """
    if not state_handler:
        raise HTTPException(status_code=503, detail="State handler not available")
    
    def fetch_simulation():
        try:
            # Get current telemetry data
            telemetry_data = state_handler.get_telemetry_state()
            if not telemetry_data:
                return {
                    "success": False,
                    "message": "No telemetry data available for simulation",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Build race state from telemetry
            car_data = telemetry_data.get("cars", [{}])[0] if telemetry_data.get("cars") else {}
            race_state = {
                "current_lap": telemetry_data.get("lap", 0),
                "tire_wear": car_data.get("tire_wear", 0.5),
                "fuel_level": car_data.get("fuel_level", 0.5),
                "tire_compound": car_data.get("tire_compound", "medium"),
                "track_temp": telemetry_data.get("track_temperature", 25.0),
                "position": car_data.get("position", 1)
            }
            
            # Get pit window from query parameters
            pit_window_start = request.query_params.get("pit_window_start")
            pit_window_end = request.query_params.get("pit_window_end")
            
            if pit_window_start:
                pit_window_start = int(pit_window_start)
            if pit_window_end:
                pit_window_end = int(pit_window_end)
            
            # Run Monte Carlo simulation
            results = monte_carlo_handler.run_simulation(
                race_state, pit_window_start, pit_window_end
            )
            
            # Get best strategy
            best_strategy = monte_carlo_handler.get_best_strategy(results)
            
            # Convert results to dict format
            results_dict = []
            for result in results:
                results_dict.append({
                    "pit_lap": result.pit_lap,
                    "final_position": result.final_position,
                    "total_time": result.total_time,
                    "success_probability": result.success_probability,
                    "tire_life_remaining": result.tire_life_remaining,
                    "fuel_laps_remaining": result.fuel_laps_remaining
                })
            
            best_strategy_dict = None
            if best_strategy:
                best_strategy_dict = {
                    "pit_lap": best_strategy.pit_lap,
                    "final_position": best_strategy.final_position,
                    "total_time": best_strategy.total_time,
                    "success_probability": best_strategy.success_probability,
                    "tire_life_remaining": best_strategy.tire_life_remaining,
                    "fuel_laps_remaining": best_strategy.fuel_laps_remaining
                }
            
            return {
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "race_state": race_state,
                "simulation_results": results_dict,
                "best_strategy": best_strategy_dict,
                "simulation_stats": monte_carlo_handler.get_simulation_stats(),
                "metadata": {
                    "total_strategies": len(results),
                    "pit_window": {
                        "start": pit_window_start or race_state["current_lap"] + 1,
                        "end": pit_window_end or race_state["current_lap"] + 10
                    }
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    return get_cached_or_fetch("monte_carlo_simulation", fetch_simulation, request)


@app.get("/api/v1/ai-strategy/recommendations", response_model=Dict[str, Any])
async def get_ai_strategy_recommendations(request: Request):
    """
    Get AI strategy recommendations based on Monte Carlo simulation results.
    
    Returns:
        AI-generated strategy recommendations or fallback recommendations
    """
    if not state_handler:
        raise HTTPException(status_code=503, detail="State handler not available")
    
    def fetch_recommendations():
        try:
            # Get current system state
            car_twin_data = state_handler.get_car_twin_state()
            field_twin_data = state_handler.get_field_twin_state()
            telemetry_data = state_handler.get_telemetry_state()
            
            # Run Monte Carlo simulation first
            car_data = telemetry_data.get("cars", [{}])[0] if telemetry_data.get("cars") else {}
            race_state = {
                "current_lap": telemetry_data.get("lap", 0),
                "tire_wear": car_data.get("tire_wear", 0.5),
                "fuel_level": car_data.get("fuel_level", 0.5),
                "tire_compound": car_data.get("tire_compound", "medium"),
                "track_temp": telemetry_data.get("track_temperature", 25.0),
                "position": car_data.get("position", 1)
            }
            
            # Run simulation
            simulation_results = monte_carlo_handler.run_simulation(race_state)
            best_strategy = monte_carlo_handler.get_best_strategy(simulation_results)
            
            # Prepare data for AI strategist
            strategy_data = {
                "car_twin": car_twin_data,
                "field_twin": field_twin_data,
                "simulation_results": [
                    {
                        "pit_lap": result.pit_lap,
                        "final_position": result.final_position,
                        "total_time": result.total_time,
                        "success_probability": result.success_probability
                    }
                    for result in simulation_results
                ],
                "race_context": {
                    "lap": race_state["current_lap"],
                    "session_type": telemetry_data.get("session_type", "race")
                }
            }
            
            # Generate AI recommendations (synchronous for now)
            if ai_strategist:
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    recommendations = loop.run_until_complete(
                        ai_strategist.generate_recommendations(strategy_data)
                    )
                except Exception as e:
                    print(f"AI strategist failed, using fallback: {e}")
                    recommendations = _generate_fallback_recommendations(simulation_results, race_state)
            else:
                # Generate fallback recommendations when AI strategist is not available
                recommendations = _generate_fallback_recommendations(simulation_results, race_state)
            
            return {
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "recommendations": recommendations,
                "simulation_context": {
                    "best_strategy": {
                        "pit_lap": best_strategy.pit_lap,
                        "final_position": best_strategy.final_position,
                        "total_time": best_strategy.total_time,
                        "success_probability": best_strategy.success_probability
                    } if best_strategy else None,
                    "total_strategies": len(simulation_results),
                    "race_state": race_state
                },
                "metadata": {
                    "ai_strategist_available": ai_strategist is not None,
                    "recommendation_source": "ai_strategist" if ai_strategist else "fallback",
                    "monte_carlo_stats": monte_carlo_handler.get_simulation_stats()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    return get_cached_or_fetch("ai_strategy_recommendations", fetch_recommendations, request)


def _generate_fallback_recommendations(simulation_results, race_state):
    """Generate fallback recommendations when AI strategist is not available."""
    recommendations = []
    
    if not simulation_results:
        return [{
            "priority": "urgent",
            "category": "general",
            "title": "No Simulation Data Available",
            "description": "Unable to generate recommendations - no simulation data available",
            "confidence": 0.0,
            "expected_benefit": "Manual strategy required",
            "execution_lap": None,
            "reasoning": "No simulation data to analyze",
            "risks": ["No AI guidance available"],
            "alternatives": ["Manual strategy decisions"]
        }]
    
    # Get best strategy from simulation results
    best_strategy = min(simulation_results, key=lambda x: x.total_time if hasattr(x, 'total_time') else x.get("total_time", float('inf')))
    
    # Generate basic recommendations based on simulation results
    recommendations.append({
        "priority": "moderate",
        "category": "pit_strategy",
        "title": f"Recommended Pit Strategy",
        "description": f"Pit on lap {best_strategy.pit_lap if hasattr(best_strategy, 'pit_lap') else best_strategy.get('pit_lap', 'Unknown')} for optimal result",
        "confidence": best_strategy.success_probability if hasattr(best_strategy, 'success_probability') else best_strategy.get("success_probability", 0.8),
        "expected_benefit": f"Position {best_strategy.final_position if hasattr(best_strategy, 'final_position') else best_strategy.get('final_position', 'Unknown')}",
        "execution_lap": best_strategy.pit_lap if hasattr(best_strategy, 'pit_lap') else best_strategy.get("pit_lap"),
        "reasoning": f"Simulation shows this is the optimal strategy with {(best_strategy.success_probability if hasattr(best_strategy, 'success_probability') else best_strategy.get('success_probability', 0.8)):.1%} success probability",
        "risks": ["Strategy may not account for race dynamics"],
        "alternatives": ["Alternative pit windows available"]
    })
    
    # Add tire management recommendation
    tire_wear = race_state.get("tire_wear", 0.5)
    if tire_wear > 0.7:
        recommendations.append({
            "priority": "urgent",
            "category": "tire_management",
            "title": "High Tire Wear Alert",
            "description": f"Tire wear at {tire_wear:.1%} - monitor closely for pit window",
            "confidence": 0.9,
            "expected_benefit": "Prevent tire failure",
            "execution_lap": race_state.get("current_lap", 0) + 1,
            "reasoning": "Tire wear approaching critical level",
            "risks": ["Tire failure if delayed"],
            "alternatives": ["Extend stint if track position critical"]
        })
    
    # Add fuel management recommendation
    fuel_level = race_state.get("fuel_level", 0.5)
    if fuel_level < 0.3:
        recommendations.append({
            "priority": "urgent",
            "category": "fuel_saving",
            "title": "Low Fuel Alert",
            "description": f"Fuel level at {fuel_level:.1%} - consider fuel saving mode",
            "confidence": 0.85,
            "expected_benefit": "Complete race distance",
            "execution_lap": race_state.get("current_lap", 0),
            "reasoning": "Fuel level critically low",
            "risks": ["Running out of fuel"],
            "alternatives": ["Pit for fuel if necessary"]
        })
    
    return recommendations


@app.get("/api/v1/monte-carlo/stats", response_model=Dict[str, Any])
async def get_monte_carlo_stats():
    """
    Get Monte Carlo simulation statistics.
    
    Returns:
        Simulation statistics and performance metrics
    """
    try:
        stats = monte_carlo_handler.get_simulation_stats()
        
        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monte_carlo_stats": stats,
            "handler_info": {
                "simulation_count_per_run": monte_carlo_handler.simulation_count,
                "last_simulation_time": monte_carlo_handler.last_simulation_time
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.get("/api/v1/continuous-ai/recommendations", response_model=Dict[str, Any])
async def get_continuous_ai_recommendations(request: Request):
    """
    Get AI strategy recommendations from the continuously running service.
    
    This endpoint returns recommendations generated by the background service
    that runs Monte Carlo simulations every 2 seconds and feeds them to MAX.
    """
    try:
        continuous_ai_service = get_continuous_ai_service()
        
        # Get latest recommendations
        recommendations = continuous_ai_service.get_latest_recommendations()
        race_state = continuous_ai_service.get_latest_race_state()
        service_status = continuous_ai_service.get_service_status()
        
        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recommendations": recommendations,
            "race_state": race_state,
            "service_status": service_status,
            "metadata": {
                "source": "continuous_ai_service",
                "simulation_count": service_status.get("simulation_count", 0),
                "last_update": service_status.get("last_simulation_time"),
                "queue_size": service_status.get("queue_size", 0)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.get("/api/v1/continuous-ai/status", response_model=Dict[str, Any])
async def get_continuous_ai_status():
    """
    Get the status of the continuous AI service.
    
    Returns information about the background service including
    simulation count, queue size, and service health.
    """
    try:
        continuous_ai_service = get_continuous_ai_service()
        service_status = continuous_ai_service.get_service_status()
        
        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_status": service_status,
            "health": "healthy" if service_status.get("is_running", False) else "stopped"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.post("/api/v1/continuous-ai/start", response_model=Dict[str, Any])
async def start_continuous_ai_service():
    """
    Start the continuous AI service.
    
    This will begin the background service that runs Monte Carlo simulations
    every 2 seconds and feeds them to the MAX model.
    """
    try:
        continuous_ai_service = get_continuous_ai_service()
        await continuous_ai_service.start()
        
        return {
            "success": True,
            "message": "Continuous AI service started",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.post("/api/v1/continuous-ai/stop", response_model=Dict[str, Any])
async def stop_continuous_ai_service():
    """
    Stop the continuous AI service.
    
    This will stop the background service and free up resources.
    """
    try:
        continuous_ai_service = get_continuous_ai_service()
        await continuous_ai_service.stop()
        
        return {
            "success": True,
            "message": "Continuous AI service stopped",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
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
                "/api/v1/concurrent-status",
                "/api/v1/monte-carlo/simulate",
                "/api/v1/monte-carlo/stats",
                "/api/v1/ai-strategy/recommendations"
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
        "twin_system.api_server:app",
        host=server_host,
        port=server_port,
        reload=reload,
        access_log=True,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)