"""
Core interfaces and abstract base classes for the F1 Dual Twin System.

This module defines the contracts that all components must implement to ensure
consistent behavior and enable proper dependency injection and testing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class TelemetryProcessor(ABC):
    """Abstract base class for telemetry data processing components."""
    
    @abstractmethod
    def ingest_telemetry(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming telemetry data and return normalized format.
        
        Args:
            raw_data: Raw telemetry data from source
            
        Returns:
            Normalized telemetry data in standard JSON format
            
        Raises:
            TelemetryValidationError: If data fails validation
        """
        pass
    
    @abstractmethod
    def validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        Validate telemetry data against expected schema.
        
        Args:
            data: Telemetry data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw telemetry to standardized JSON format.
        
        Args:
            raw_data: Raw telemetry data
            
        Returns:
            Normalized data in standard format
        """
        pass


class TwinModel(ABC):
    """Abstract base class for digital twin models (Car Twin and Field Twin)."""
    
    @abstractmethod
    def update_state(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Update twin model state based on new telemetry data.
        
        Args:
            telemetry_data: Normalized telemetry data
        """
        pass
    
    @abstractmethod
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current state of the twin model.
        
        Returns:
            Current state in JSON format
        """
        pass
    
    @abstractmethod
    def predict(self, horizon_seconds: int) -> Dict[str, Any]:
        """
        Generate predictions based on current state.
        
        Args:
            horizon_seconds: Prediction time horizon in seconds
            
        Returns:
            Prediction data in JSON format
        """
        pass


class StateManager(ABC):
    """Abstract base class for state management and persistence."""
    
    @abstractmethod
    def persist_state(self, state_data: Dict[str, Any]) -> None:
        """
        Persist state data to storage.
        
        Args:
            state_data: State data to persist
        """
        pass
    
    @abstractmethod
    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Load state data from storage.
        
        Returns:
            Loaded state data or None if no valid state exists
        """
        pass
    
    @abstractmethod
    def ensure_consistency(self) -> bool:
        """
        Verify state consistency across components.
        
        Returns:
            True if state is consistent, False otherwise
        """
        pass


class ConfigurationManager(ABC):
    """Abstract base class for system configuration management."""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        pass
    
    @abstractmethod
    def load_config(self, config_path: str) -> None:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
        """
        pass


# Custom exceptions for the system
class TelemetryValidationError(Exception):
    """Raised when telemetry data fails validation."""
    pass


class StateConsistencyError(Exception):
    """Raised when state consistency checks fail."""
    pass


class ConfigurationError(Exception):
    """Raised when configuration issues occur."""
    pass


class TwinModelError(Exception):
    """Raised when twin model operations fail."""
    pass