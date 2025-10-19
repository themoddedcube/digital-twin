# F1 Dual Twin System REST API Server

## Overview

The F1 Dual Twin System REST API Server provides high-performance, low-latency access to Car Twin, Field Twin, telemetry, and environment data. The server is designed to meet strict performance requirements with sub-50ms response times and support for concurrent client connections.

## Features Implemented

### ✅ Task 6.1: REST API Endpoints
- **FastAPI-based server** with async support
- **Core endpoints** for all twin data types:
  - `/api/v1/car-twin` - Car Twin state and predictions
  - `/api/v1/field-twin` - Field Twin competitor models and strategic analysis
  - `/api/v1/telemetry` - Current telemetry data and track conditions
  - `/api/v1/environment` - Environment state and race context
  - `/api/v1/system/complete` - Complete system state from all components
- **Performance optimization** with in-memory caching (1-second TTL)
- **Response time monitoring** with automatic performance tracking
- **Health check endpoint** (`/api/v1/health`) for system monitoring

### ✅ Task 6.2: API Versioning and Concurrent Access Support
- **Schema versioning** with backward compatibility support
  - Supported versions: 1.0.0, 1.1.0
  - Version specification via headers, query parameters, or Accept header
  - Automatic response transformation based on requested version
- **Concurrent connection management**
  - Configurable maximum connections (default: 10)
  - Connection tracking and load balancing
  - Graceful degradation under high load
- **Additional monitoring endpoints**:
  - `/api/v1/version` - API version information
  - `/api/v1/metrics` - Performance metrics and statistics
  - `/api/v1/concurrent-status` - Real-time connection status

## Architecture

### Core Components

1. **APICache**: In-memory caching with TTL for sub-50ms response times
2. **APIMetrics**: Performance tracking and monitoring
3. **SchemaVersionManager**: Backward-compatible API versioning
4. **ConcurrentAccessManager**: Connection limiting and load management
5. **APIResponseBuilder**: Standardized response formatting
6. **APIDataProcessor**: Data validation and processing pipeline

### Performance Features

- **Sub-50ms Response Times**: Achieved through in-memory caching and optimized data access
- **Concurrent Access Support**: Up to 10 simultaneous connections without performance degradation
- **Automatic Performance Monitoring**: Real-time tracking of response times and connection counts
- **Load-based Warnings**: Automatic alerts for slow responses (>50ms)

## API Endpoints

### Core Data Endpoints

#### GET /api/v1/car-twin
Returns current Car Twin state with predictions and strategy metrics.

**Response Format:**
```json
{
  "success": true,
  "timestamp": "2024-03-17T14:30:45.123Z",
  "schema_version": "1.0.0",
  "car_twin": {
    "car_id": "44",
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
    }
  },
  "metadata": {
    "last_update": "2024-03-17T14:30:44.123Z",
    "update_source": "car_twin"
  }
}
```

#### GET /api/v1/field-twin
Returns Field Twin state with competitor models and strategic opportunities.

#### GET /api/v1/telemetry
Returns current telemetry data including track conditions and car data.

#### GET /api/v1/environment
Returns environment state with track conditions, weather, and race context.

### System Endpoints

#### GET /api/v1/health
System health check with component status and performance metrics.

#### GET /api/v1/version
API version information and schema compatibility details.

#### GET /api/v1/metrics
Detailed performance metrics for all endpoints.

#### GET /api/v1/concurrent-status
Real-time concurrent connection status and load information.

## Schema Versioning

### Version Specification
Clients can specify the desired schema version using:

1. **Accept Header**: `Accept: application/json; version=1.1.0`
2. **Custom Header**: `X-Schema-Version: 1.1.0`
3. **Query Parameter**: `?schema_version=1.1.0`

### Supported Versions

- **1.0.0** (Default): Original schema format
- **1.1.0**: Enhanced metadata and concurrent access support

### Backward Compatibility
- All versions remain supported for 12 months after deprecation notice
- 6-month advance notice for version deprecation
- Automatic response transformation based on requested version

## Performance Requirements

### Response Time Requirements
- **Target**: < 50ms for all endpoints
- **Monitoring**: Automatic tracking and alerting
- **Optimization**: In-memory caching with 1-second TTL

### Concurrent Access
- **Maximum Connections**: 10 simultaneous clients (configurable)
- **Load Management**: Automatic connection limiting
- **Performance Impact**: No degradation under normal load

### Caching Strategy
- **Cache TTL**: 1 second (configurable)
- **Cache Keys**: Versioned by schema version
- **Cache Invalidation**: Automatic TTL-based expiration

## Installation and Setup

### Prerequisites
```bash
pip install -r requirements.txt
```

### Required Dependencies
- `fastapi==0.104.1`
- `uvicorn[standard]==0.24.0`
- `pydantic==2.5.0`

### Running the Server

#### Development Mode
```bash
python src/api_server.py
```

#### Production Mode
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

#### Configuration
Server configuration is loaded from `config/system_config.json`:

```json
{
  "api": {
    "host": "localhost",
    "port": 8000,
    "response_timeout_ms": 50,
    "max_concurrent_connections": 10,
    "enable_cors": true,
    "api_version": "v1"
  }
}
```

## Testing

### Running Tests
```bash
python test_api_server.py
```

### Test Coverage
- API Cache functionality
- Performance metrics tracking
- Schema versioning
- Concurrent access management
- Response building and data processing
- State handler integration

### Mock Data
The system includes comprehensive mock data for testing:
- Mock Car Twin state with realistic predictions
- Mock Field Twin with competitor models
- Mock telemetry data with F1 race simulation
- Mock environment state with track conditions

## Integration

### State Handler Integration
The API server integrates with the F1 Dual Twin System's State Handler:

```python
from dashboard import get_state_handler

state_handler = get_state_handler()
car_twin_data = state_handler.get_car_twin_state()
```

### External System Integration
External systems can consume the API using standard HTTP clients:

```python
import requests

# Get car twin data
response = requests.get("http://localhost:8000/api/v1/car-twin")
car_data = response.json()

# Specify schema version
headers = {"X-Schema-Version": "1.1.0"}
response = requests.get("http://localhost:8000/api/v1/field-twin", headers=headers)
```

## Monitoring and Observability

### Performance Metrics
- Request count and response times per endpoint
- Concurrent connection tracking
- Cache hit/miss ratios
- System health status

### Health Checks
- Component status monitoring
- Performance threshold alerting
- Automatic degradation detection

### Logging
- Request/response logging
- Performance warnings for slow responses
- Error tracking and reporting

## Error Handling

### HTTP Status Codes
- `200`: Success
- `404`: Endpoint not found
- `429`: Too many concurrent connections
- `500`: Internal server error
- `503`: Service unavailable (state handler not available)

### Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "status_code": 500,
  "timestamp": "2024-03-17T14:30:45.123Z",
  "schema_version": "1.0.0"
}
```

## Security Considerations

### CORS Configuration
- Configurable CORS settings
- Production-ready defaults
- Origin validation support

### Rate Limiting
- Connection-based limiting
- Graceful degradation under load
- Automatic connection management

## Future Enhancements

### Planned Features
- Authentication and authorization
- Rate limiting per client
- WebSocket support for real-time updates
- Compression for large responses
- Request/response caching strategies

### Performance Optimizations
- Connection pooling
- Response compression
- Advanced caching strategies
- Load balancing support

## Requirements Compliance

### Requirement 5.1: REST Endpoints
✅ **Implemented**: Complete REST API with all required endpoints for twin data access

### Requirement 5.2: Schema Versioning
✅ **Implemented**: JSON schema versioning with backward compatibility support

### Requirement 5.3: Response Time
✅ **Implemented**: Sub-50ms response times through in-memory caching

### Requirement 5.4: Concurrent Access
✅ **Implemented**: Support for 10+ concurrent connections without performance degradation

### Requirement 5.5: Backward Compatibility
✅ **Implemented**: Schema versioning maintains backward-compatible data formats

## Conclusion

The F1 Dual Twin System REST API Server successfully implements all required functionality for external system integration. The server provides high-performance, low-latency access to twin data with comprehensive versioning support and concurrent access management. The modular architecture ensures maintainability and extensibility for future enhancements.