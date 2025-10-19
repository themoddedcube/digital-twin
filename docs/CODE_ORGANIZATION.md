# Source Code Organization

Clean, modular organization of the F1 Race Twin Edge system.

## 📁 Directory Structure

```
src/
├── core/                  # Core infrastructure
│   ├── interfaces.py      # Abstract base classes
│   ├── base_twin.py       # BaseTwinModel implementation
│   ├── base_telemetry.py  # BaseTelemetryProcessor
│   ├── base_state.py      # BaseStateManager
│   └── schemas.py         # JSON schema validation
│
├── twin_system/           # Digital Twin System (Team: Abi)
│   ├── twin_model.py      # CarTwin - vehicle state modeling
│   ├── field_twin.py      # FieldTwin - competitor analysis
│   ├── telemetry_feed.py  # Telemetry ingestion & simulation
│   ├── dashboard.py       # StateHandler (deprecated - external team)
│   ├── system_monitor.py  # Health monitoring
│   ├── system_recovery.py # Error recovery
│   ├── system_init.py     # System initialization
│   ├── main_orchestrator.py # Main orchestration loop
│   ├── api_server.py      # REST API server
│   └── api_core.py        # API utilities
│
├── max_integration/       # MAX/Modular Integration (Team: Alan)
│   ├── ai_strategist.py   # MAX LLM integration
│   ├── hpc_orchestrator.py # HPC compute orchestration
│   └── simulate_strategy.mojo # Mojo simulation kernel
│
├── utils/                 # Shared utilities
│   ├── config.py          # Configuration management
│   └── visual_utils.py    # Visualization helpers
│
└── compat_layer.py        # Compatibility bridge between systems
```

## 🎯 Module Responsibilities

### Core (`core/`)
**Purpose:** Foundation classes and interfaces

- **interfaces.py** - Abstract base classes for all components
- **base_*.py** - Default implementations
- **schemas.py** - Data validation and schema definitions

**Used by:** All other modules

---

### Twin System (`twin_system/`)
**Purpose:** Real-time digital twin modeling and telemetry

**Owner:** Abi (Telemetry & Digital Twin Developer)

**Key Components:**
- **CarTwin** - Maintains real-time car state
- **FieldTwin** - Models competitor behavior
- **TelemetryIngestor** - Processes live/simulated telemetry
- **StateHandler** - State persistence (being moved to dashboard team)

**Data Flow:**
```
Telemetry → TelemetryIngestor → CarTwin/FieldTwin → StateHandler
```

---

### MAX Integration (`max_integration/`)
**Purpose:** AI-powered strategy recommendations and HPC simulation

**Owner:** Alan (Systems Architect / HPC Lead)

**Key Components:**
- **AIStrategist** - MAX LLM integration for strategy recommendations
- **HPCOrchestrator** - Manages hybrid edge/cloud compute
- **simulate_strategy.mojo** - High-performance Mojo simulation kernel

**Data Flow:**
```
Twin State → Mojo Simulation → MAX LLM → AI Recommendations
```

---

### Utils (`utils/`)
**Purpose:** Shared configuration and utilities

**Key Components:**
- **config.py** - Centralized configuration management
- **visual_utils.py** - Dashboard visualization helpers

---

## 🔗 Integration Points

### How the Modules Connect

1. **Telemetry Input**
   ```python
   from twin_system import TelemetryIngestor
   ingestor = TelemetryIngestor()
   ```

2. **Digital Twin Updates**
   ```python
   from twin_system import CarTwin, FieldTwin
   car_twin = CarTwin(car_id="44")
   field_twin = FieldTwin()
   ```

3. **MAX AI Strategy**
   ```python
   from max_integration import AIStrategist
   strategist = AIStrategist()
   recommendations = await strategist.generate_recommendations(data)
   ```

4. **HPC Orchestration**
   ```python
   from max_integration import HPCOrchestrator
   orchestrator = HPCOrchestrator()
   ```

---

## 🔧 Using the Compatibility Layer

For backward compatibility with demo/test scripts:

```python
from compat_layer import (
    DigitalTwin,      # Maps to CarTwin
    FieldTwin,        # Direct import
    TelemetryGenerator, # Maps to TelemetrySimulator
    TelemetryStreamer  # Maps to TelemetryIngestor
)
```

---

## 📦 Import Examples

### From Root Level
```python
import sys
sys.path.insert(0, 'src')

# Using organized modules
from twin_system import CarTwin, FieldTwin
from max_integration import AIStrategist
from core import TELEMETRY_SCHEMA
```

### From Within src/
```python
# Within twin_system files
from .twin_model import CarTwin
from ..core.interfaces import TwinModel
from ..max_integration import AIStrategist

# Within max_integration files
from .ai_strategist import AIStrategist
from ..twin_system.field_twin import FieldTwin
from ..core.schemas import CAR_TWIN_SCHEMA
```

---

## ⚡ Quick Reference

| Component | Import Path | Purpose |
|-----------|------------|---------|
| CarTwin | `twin_system.twin_model` | Car state modeling |
| FieldTwin | `twin_system.field_twin` | Competitor analysis |
| TelemetryIngestor | `twin_system.telemetry_feed` | Telemetry processing |
| AIStrategist | `max_integration.ai_strategist` | AI recommendations |
| HPCOrchestrator | `max_integration.hpc_orchestrator` | HPC management |
| Mojo Kernel | `max_integration/simulate_strategy.mojo` | GPU simulation |

---

## 🚀 Getting Started

1. **For Telemetry/Twin Work:**
   Focus on `twin_system/` module

2. **For MAX/Simulation Work:**
   Focus on `max_integration/` module

3. **For Infrastructure:**
   Modify `core/` module

4. **For Testing:**
   Use `compat_layer.py` for backward compatibility

---

## 📝 Adding New Components

### Add to Twin System
Create file in `twin_system/` and add to `twin_system/__init__.py`

### Add to MAX Integration
Create file in `max_integration/` and add to `max_integration/__init__.py`

### Add Core Infrastructure
Create file in `core/` and add to `core/__init__.py`

---

**Clean, organized, and ready for team collaboration!** 🏎️

