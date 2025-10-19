# Live Telemetry Integration for F1 Dual Twin System

## Overview

The F1 Dual Twin System now supports **live telemetry ingestion** from real data sources while maintaining full backward compatibility with the existing simulator. The system can seamlessly switch between simulated and live data sources with automatic fallback for maximum reliability.

## ✅ **Implementation Complete**

### **Key Features Implemented:**

1. **🔌 Multiple Data Sources**
   - **WebSocket Client**: For HTTP-based telemetry APIs
   - **UDP Client**: For F1 game telemetry or high-frequency data streams
   - **Simulator**: Original realistic F1 data generation (fallback)

2. **🔄 Seamless Mode Switching**
   - Configuration-driven source selection
   - Runtime switching between live and simulated modes
   - Automatic fallback on live source failures

3. **🛡️ Fault Tolerance**
   - Connection retry logic with exponential backoff
   - Automatic reconnection for dropped connections
   - Graceful degradation to simulator mode
   - Configurable failure thresholds

4. **📊 Data Normalization**
   - All live sources normalized to standard `telemetry_state.json` schema
   - Downstream twin models remain fully compatible
   - No changes required to existing Car Twin or Field Twin logic

5. **⚙️ Configuration Management**
   - Easy toggle: `use_simulator=true/false`
   - Source-specific configuration options
   - Runtime reconfiguration support

## 🚀 **Usage**

### **Quick Start - Enable Live Telemetry**

1. **Update Configuration** (`config/system_config.json`):
```json
{
  "telemetry": {
    "use_simulator": false,
    "live_source_type": "websocket",
    "live_source": {
      "websocket_url": "ws://your-telemetry-server:8080/telemetry"
    }
  }
}
```

2. **Start the System**:
```bash
python src/main_orchestrator.py
```

The system will automatically:
- ✅ Connect to your live telemetry source
- ✅ Process and normalize incoming data
- ✅ Update Car Twin and Field Twin models
- ✅ Fall back to simulator if live source fails

### **WebSocket Configuration**
```json
{
  "telemetry": {
    "use_simulator": false,
    "live_source_type": "websocket",
    "live_source": {
      "websocket_url": "ws://f1-api.example.com:8080/live",
      "timeout": 10.0,
      "max_reconnect_attempts": 10,
      "reconnect_delay": 2.0
    }
  }
}
```

### **UDP Configuration (F1 Game)**
```json
{
  "telemetry": {
    "use_simulator": false,
    "live_source_type": "udp",
    "update_interval_seconds": 0.1,
    "live_source": {
      "host": "0.0.0.0",
      "port": 20777,
      "timeout": 1.0
    }
  }
}
```

## 🔧 **API Reference**

### **TelemetryIngestor Class**

#### **New Methods:**
```python
# Switch to live mode
success = ingestor.switch_to_live_mode("websocket", websocket_url="ws://...")

# Switch to simulator mode  
ingestor.switch_to_simulator_mode()

# Get current status
status = ingestor.get_data_source_status()
# Returns: {"mode": "live", "connected": True, "data_failures": 0, ...}
```

#### **Configuration Options:**
```python
{
  "use_simulator": False,              # Enable live mode
  "live_source_type": "websocket",     # "websocket" or "udp"
  "max_failures_before_fallback": 5,   # Auto-fallback threshold
  "update_interval_seconds": 1,        # Data polling frequency
  "live_source": {
    # WebSocket options
    "websocket_url": "ws://...",
    "timeout": 5.0,
    "max_reconnect_attempts": 5,
    "reconnect_delay": 2.0,
    
    # UDP options  
    "host": "localhost",
    "port": 20777,
    "timeout": 1.0
  }
}
```

## 📡 **Data Source Integration**

### **WebSocket Integration**
Perfect for REST API-based telemetry services:
```javascript
// Example WebSocket server sending F1 data
const data = {
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
      "lap_time": 83.245,
      "sector_times": [28.1, 31.2, 23.9]
    }
  ]
};

websocket.send(JSON.stringify(data));
```

### **UDP Integration**
Perfect for F1 game telemetry or high-frequency data:
```python
import socket
import json

# Send UDP telemetry data
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(json.dumps(telemetry_data).encode(), ('localhost', 20777))
```

## 🧪 **Testing**

### **Run Test Suite:**
```bash
python test_live_telemetry.py
```

### **Run Usage Examples:**
```bash
python example_live_telemetry_usage.py
```

### **Test Results:**
```
✓ Seamless switching between simulator and live modes
✓ WebSocket and UDP telemetry client support  
✓ Automatic fallback on live source failures
✓ Data normalization to standard schema
✓ Fault tolerance and reconnection logic
✓ Configuration-driven source selection
```

## 🔄 **Integration with Existing System**

### **Zero Breaking Changes**
- ✅ All existing twin models work unchanged
- ✅ Same `telemetry_state.json` schema maintained
- ✅ API endpoints return identical data structure
- ✅ Performance requirements still met (< 250ms processing)

### **Enhanced Orchestrator Integration**
The main orchestrator automatically:
- Detects live vs simulated mode
- Handles connection failures gracefully  
- Logs data source status and performance
- Applies performance optimizations

## 🚨 **Production Considerations**

### **Reliability**
- **Automatic Fallback**: System never stops working
- **Connection Monitoring**: Real-time status tracking
- **Error Recovery**: Automatic reconnection with backoff
- **Performance Monitoring**: Latency and failure tracking

### **Security**
- **WebSocket**: Supports WSS (secure WebSocket) connections
- **UDP**: Local network or VPN recommended
- **Authentication**: Extend clients for API key/token support

### **Scalability**
- **Multiple Sources**: Easy to add new telemetry source types
- **Load Balancing**: Can connect to multiple WebSocket endpoints
- **High Frequency**: UDP supports sub-100ms update rates

## 🎯 **Next Steps**

1. **Configure Your Data Source**: Update `config/system_config.json`
2. **Test Connection**: Run `test_live_telemetry.py`
3. **Deploy**: Set `use_simulator=false` and start the system
4. **Monitor**: Check logs and `/api/v1/health` endpoint
5. **Optimize**: Tune update intervals and failure thresholds

## 📞 **Support**

The live telemetry system is fully integrated and production-ready. All existing F1 Dual Twin System features continue to work seamlessly with live data sources.

**Key Benefits:**
- 🏎️ **Real Race Data**: Connect to actual F1 telemetry sources
- 🔄 **Zero Downtime**: Automatic fallback ensures continuous operation  
- ⚡ **High Performance**: Maintains < 250ms processing requirements
- 🛠️ **Easy Configuration**: Simple JSON configuration changes
- 🧪 **Fully Tested**: Comprehensive test suite validates all functionality

The F1 Dual Twin System is now ready for live race deployment! 🏁