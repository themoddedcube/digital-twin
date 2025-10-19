# Continuous AI Strategy Service

## Overview

The Continuous AI Strategy Service is a background service that automatically runs Monte Carlo simulations every 2 seconds and feeds the results to a continuously running MAX model for real-time AI strategy recommendations.

## 🚀 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telemetry    │───▶│  Monte Carlo     │───▶│   MAX Model     │
│   Data Source  │    │  Simulation      │    │   (Always On)   │
│                │    │  (Every 2s)      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Strategy Queue  │    │  AI Strategy    │
                       │  (Background)    │    │  Recommendations│
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                └────────┬───────────────┘
                                         ▼
                                ┌─────────────────┐
                                │   API Endpoint  │
                                │   (Real-time)   │
                                └─────────────────┘
```

## 🎯 Key Features

### **Continuous Processing**
- **Monte Carlo simulations** run every 2 seconds automatically
- **MAX model** stays loaded and ready for instant processing
- **Background threads** handle simulation and AI processing
- **Queue-based architecture** for reliable data flow

### **Real-time AI Recommendations**
- **Always-available** AI recommendations
- **Latest race state** from continuous simulations
- **High-performance** with minimal latency
- **Automatic updates** every 2 seconds

### **Service Management**
- **Start/Stop** service via API endpoints
- **Health monitoring** and status reporting
- **Graceful shutdown** with proper cleanup
- **Error handling** and recovery

## 🔧 Usage

### **Quick Start**

```bash
# Start the API server with continuous AI service
python start_continuous_ai.py

# Or start manually
python src/twin_system/api_server.py
# Then start the continuous service
curl -X POST http://localhost:8000/api/v1/continuous-ai/start
```

### **API Endpoints**

#### **Get AI Recommendations**
```bash
# Get latest AI recommendations
curl http://localhost:8000/api/v1/continuous-ai/recommendations
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2024-03-17T14:30:45.123Z",
  "recommendations": [
    {
      "priority": "urgent",
      "category": "pit_strategy",
      "title": "URGENT: Pit Stop Required",
      "description": "Tire wear at 65% - pit stop required within 2 laps",
      "confidence": 0.95,
      "expected_benefit": "Prevent tire failure",
      "execution_lap": 27,
      "reasoning": "Tire wear exceeds safe threshold",
      "risks": ["Tire failure if delayed"],
      "alternatives": ["Extend current stint if track position critical"]
    }
  ],
  "race_state": {
    "current_lap": 25,
    "position": 3,
    "tire_wear": 0.65,
    "fuel_level": 0.45,
    "tire_compound": "medium",
    "track_temp": 28.5
  },
  "service_status": {
    "is_running": true,
    "simulation_count": 15,
    "last_simulation_time": "2024-03-17T14:30:45.123Z",
    "queue_size": 0,
    "latest_recommendations_count": 3
  }
}
```

#### **Service Status**
```bash
# Check service status
curl http://localhost:8000/api/v1/continuous-ai/status
```

#### **Service Control**
```bash
# Start service
curl -X POST http://localhost:8000/api/v1/continuous-ai/start

# Stop service
curl -X POST http://localhost:8000/api/v1/continuous-ai/stop
```

## 🧪 Testing

### **Run Tests**
```bash
# Test the continuous AI service
python test_continuous_ai.py

# Test individual components
python test_simple_integration.py
```

### **Manual Testing**
```bash
# Check service status
curl http://localhost:8000/api/v1/continuous-ai/status

# Get recommendations
curl http://localhost:8000/api/v1/continuous-ai/recommendations

# Start service
curl -X POST http://localhost:8000/api/v1/continuous-ai/start

# Stop service
curl -X POST http://localhost:8000/api/v1/continuous-ai/stop
```

## ⚙️ Configuration

### **Service Parameters**
```python
# In continuous_ai_service.py
ContinuousAIService(
    api_base_url="http://localhost:8000",      # API server URL
    max_base_url="http://localhost:8000/v1",   # MAX model URL
    simulation_interval=2.0,                   # Seconds between simulations
    max_queue_size=100                         # Max queue size
)
```

### **Environment Variables**
```bash
# Optional environment variables
export API_BASE_URL="http://localhost:8000"
export MAX_BASE_URL="http://localhost:8000/v1"
export SIMULATION_INTERVAL="2.0"
export MAX_QUEUE_SIZE="100"
```

## 🔄 How It Works

### **1. Background Simulation Loop**
- **Runs every 2 seconds** automatically
- **Calls Monte Carlo API** to get simulation results
- **Queues results** for AI processing
- **Updates race state** with latest data

### **2. AI Processing Loop**
- **Processes queued simulations** continuously
- **Feeds data to MAX model** for AI analysis
- **Generates recommendations** based on simulation results
- **Stores latest recommendations** for API access

### **3. API Integration**
- **Exposes recommendations** via REST API
- **Provides service status** and health monitoring
- **Handles service control** (start/stop)
- **Real-time data** with minimal latency

## 📊 Performance

### **Expected Performance**
- **Simulation frequency**: Every 2 seconds
- **AI processing time**: ~500ms per batch
- **API response time**: < 100ms for recommendations
- **Memory usage**: ~50MB for service
- **CPU usage**: ~10% on modern hardware

### **Scalability**
- **Queue-based processing** prevents blocking
- **Background threads** handle heavy processing
- **Efficient memory management** with queue limits
- **Error recovery** and automatic retry

## 🛠️ Development

### **Adding New Features**
1. **Modify `continuous_ai_service.py`** for core functionality
2. **Update API endpoints** in `api_server.py`
3. **Add tests** in `test_continuous_ai.py`
4. **Update documentation** as needed

### **Debugging**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check service status
service = get_continuous_ai_service()
status = service.get_service_status()
print(status)
```

### **Monitoring**
- **Service status** via `/api/v1/continuous-ai/status`
- **Simulation count** and timing
- **Queue size** and processing rate
- **Error logs** and recovery status

## 🚨 Troubleshooting

### **Common Issues**

1. **Service not starting**
   - Check MAX model is running
   - Verify API server is accessible
   - Check error logs for details

2. **No recommendations generated**
   - Ensure Monte Carlo simulations are running
   - Check MAX model connectivity
   - Verify queue is processing

3. **High memory usage**
   - Reduce `max_queue_size`
   - Check for memory leaks
   - Monitor queue processing rate

4. **Slow performance**
   - Increase `simulation_interval`
   - Check MAX model performance
   - Monitor system resources

### **Debug Commands**
```bash
# Check service status
curl http://localhost:8000/api/v1/continuous-ai/status

# Check Monte Carlo simulations
curl http://localhost:8000/api/v1/monte-carlo/simulate

# Check AI strategist
curl http://localhost:8000/api/v1/ai-strategy/recommendations

# Check system health
curl http://localhost:8000/api/v1/health
```

## 🎉 Benefits

### **For Race Engineers**
- **Real-time AI guidance** during races
- **Continuous strategy updates** every 2 seconds
- **Always-available recommendations** without manual requests
- **Latest simulation data** for decision making

### **For Developers**
- **Simple API integration** with existing systems
- **Background processing** doesn't block main application
- **Scalable architecture** with queue-based processing
- **Easy monitoring** and health checks

### **For System Performance**
- **Efficient resource usage** with background processing
- **Minimal API latency** for recommendations
- **Automatic error recovery** and retry logic
- **Graceful shutdown** and cleanup

## 📋 Summary

The Continuous AI Strategy Service provides:

✅ **Automatic Monte Carlo simulations** every 2 seconds  
✅ **Continuous MAX model processing** for AI recommendations  
✅ **Real-time API access** to latest recommendations  
✅ **Background processing** with queue-based architecture  
✅ **Service management** with start/stop/status endpoints  
✅ **High performance** with minimal latency  
✅ **Easy integration** with existing systems  

Perfect for real-time F1 strategy decisions with always-available AI guidance!
