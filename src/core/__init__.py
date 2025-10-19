"""
Core Infrastructure Module

Base classes, interfaces, and schemas for the F1 Dual Twin System.
"""

from core.interfaces import (
    TelemetryProcessor,
    TwinModel,
    StateManager,
    ConfigurationManager,
    TelemetryValidationError,
    StateConsistencyError,
    ConfigurationError,
    TwinModelError
)

from core.base_telemetry import BaseTelemetryProcessor
from core.base_twin import BaseTwinModel
from core.base_state import BaseStateManager
from core.schemas import (
    TELEMETRY_SCHEMA,
    CAR_TWIN_SCHEMA,
    FIELD_TWIN_SCHEMA,
    validate_json_schema,
    get_schema
)

__all__ = [
    # Interfaces
    'TelemetryProcessor',
    'TwinModel',
    'StateManager',
    'ConfigurationManager',
    
    # Base classes
    'BaseTelemetryProcessor',
    'BaseTwinModel',
    'BaseStateManager',
    
    # Schemas
    'TELEMETRY_SCHEMA',
    'CAR_TWIN_SCHEMA',
    'FIELD_TWIN_SCHEMA',
    'validate_json_schema',
    'get_schema',
    
    # Exceptions
    'TelemetryValidationError',
    'StateConsistencyError',
    'ConfigurationError',
    'TwinModelError'
]

