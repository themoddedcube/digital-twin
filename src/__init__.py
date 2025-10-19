"""
F1 Race Twin Edge - Complete System Package

Organized into three main modules:
- core: Base classes, interfaces, schemas
- twin_system: Digital twin components and telemetry
- max_integration: MAX LLM and simulation components
"""

# Core infrastructure
from .core.interfaces import (
    TelemetryProcessor,
    TwinModel,
    StateManager,
    ConfigurationManager,
    TelemetryValidationError,
    StateConsistencyError,
    ConfigurationError,
    TwinModelError
)

from .core.base_telemetry import BaseTelemetryProcessor
from .core.base_twin import BaseTwinModel
from .core.base_state import BaseStateManager
from .core.schemas import (
    TELEMETRY_SCHEMA,
    CAR_TWIN_SCHEMA,
    FIELD_TWIN_SCHEMA,
    validate_json_schema,
    get_schema
)

# Twin system components
from .twin_system import (
    CarTwin,
    FieldTwin,
    TelemetryIngestor,
    TelemetrySimulator,
    StateHandler,
    SystemMonitor,
    MainOrchestrator
)

# MAX integration
from .max_integration import (
    AIStrategist,
    HPCOrchestrator
)

# Configuration
from .utils.config import SystemConfig, get_config, set_config, load_config_file

__version__ = "1.0.0"
__author__ = "F1 Dual Twin System Team"

# Package metadata
__all__ = [
    # Core interfaces
    "TelemetryProcessor",
    "TwinModel", 
    "StateManager",
    "ConfigurationManager",
    
    # Base implementations
    "BaseTelemetryProcessor",
    "BaseTwinModel",
    "BaseStateManager",
    "SystemConfig",
    
    # System initialization
    "SystemInitializer",
    "initialize_system",
    "get_component",
    "get_system_status",
    "shutdown_system",
    
    # Configuration utilities
    "get_config",
    "set_config",
    "load_config_file",
    
    # Schema utilities
    "TELEMETRY_SCHEMA",
    "CAR_TWIN_SCHEMA", 
    "FIELD_TWIN_SCHEMA",
    "validate_json_schema",
    "get_schema",
    
    # Exceptions
    "TelemetryValidationError",
    "StateConsistencyError",
    "ConfigurationError",
    "TwinModelError"
]