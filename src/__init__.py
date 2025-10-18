"""
F1 Dual Twin System - Core Package

This package provides the core functionality for the F1 Dual Digital Twin System,
including telemetry processing, twin model management, and state persistence.
"""

from .interfaces import (
    TelemetryProcessor,
    TwinModel,
    StateManager,
    ConfigurationManager,
    TelemetryValidationError,
    StateConsistencyError,
    ConfigurationError,
    TwinModelError
)

from .base_telemetry import BaseTelemetryProcessor
from .base_twin import BaseTwinModel
from .base_state import BaseStateManager
from .utils.config import SystemConfig, get_config, set_config, load_config_file

from .system_init import (
    SystemInitializer,
    initialize_system,
    get_component,
    get_system_status,
    shutdown_system
)

from .schemas import (
    TELEMETRY_SCHEMA,
    CAR_TWIN_SCHEMA,
    FIELD_TWIN_SCHEMA,
    validate_json_schema,
    get_schema
)

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