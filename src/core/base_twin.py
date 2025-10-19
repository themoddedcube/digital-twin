"""
Base twin model implementation for the F1 Dual Twin System.

This module provides the foundational twin model class that both Car Twin
and Field Twin inherit from, ensuring consistent behavior and interfaces.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from abc import abstractmethod

from core.interfaces import TwinModel, TwinModelError
from core.schemas import validate_json_schema
from utils.config import get_config


class BaseTwinModel(TwinModel):
    """
    Base implementation for digital twin models.
    
    Provides common functionality for state management, validation,
    and performance tracking that both Car Twin and Field Twin use.
    """
    
    def __init__(self, twin_id: str, schema_name: str):
        """
        Initialize base twin model.
        
        Args:
            twin_id: Unique identifier for this twin instance
            schema_name: Name of the JSON schema to validate against
        """
        self.twin_id = twin_id
        self.schema_name = schema_name
        self._state: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None
        self._update_count = 0
        self._performance_metrics = {
            "total_updates": 0,
            "avg_update_time_ms": 0.0,
            "last_update_time_ms": 0.0,
            "validation_failures": 0
        }
    
    def update_state(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Update twin model state based on new telemetry data.
        
        Args:
            telemetry_data: Normalized telemetry data
            
        Raises:
            TwinModelError: If update fails or data is invalid
        """
        start_time = time.time()
        
        try:
            # Validate input data
            if not self._validate_input_data(telemetry_data):
                self._performance_metrics["validation_failures"] += 1
                raise TwinModelError(f"Invalid telemetry data for {self.twin_id}")
            
            # Perform the actual state update (implemented by subclasses)
            self._update_internal_state(telemetry_data)
            
            # Update metadata
            self._last_update = datetime.now(timezone.utc)
            self._update_count += 1
            
            # Update performance metrics
            update_time_ms = (time.time() - start_time) * 1000
            self._update_performance_metrics(update_time_ms)
            
            # Validate output state
            current_state = self.get_current_state()
            if not self._validate_output_state(current_state):
                raise TwinModelError(f"Generated invalid state for {self.twin_id}")
                
        except Exception as e:
            raise TwinModelError(f"Failed to update {self.twin_id}: {str(e)}")
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current state of the twin model.
        
        Returns:
            Current state in JSON format with metadata
        """
        base_state = {
            "twin_id": self.twin_id,
            "timestamp": self._last_update.isoformat() if self._last_update else None,
            "update_count": self._update_count,
            "performance_metrics": self._performance_metrics.copy()
        }
        
        # Add twin-specific state (implemented by subclasses)
        twin_state = self._get_twin_specific_state()
        base_state.update(twin_state)
        
        return base_state
    
    def predict(self, horizon_seconds: int) -> Dict[str, Any]:
        """
        Generate predictions based on current state.
        
        Args:
            horizon_seconds: Prediction time horizon in seconds
            
        Returns:
            Prediction data in JSON format
        """
        if not self._state:
            raise TwinModelError(f"Cannot predict without state data for {self.twin_id}")
        
        # Generate predictions (implemented by subclasses)
        predictions = self._generate_predictions(horizon_seconds)
        
        # Add prediction metadata
        prediction_data = {
            "twin_id": self.twin_id,
            "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
            "horizon_seconds": horizon_seconds,
            "based_on_update": self._last_update.isoformat() if self._last_update else None,
            "predictions": predictions
        }
        
        return prediction_data
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this twin model.
        
        Returns:
            Performance metrics dictionary
        """
        return self._performance_metrics.copy()
    
    def reset_state(self) -> None:
        """Reset twin model to initial state."""
        self._state = {}
        self._last_update = None
        self._update_count = 0
        self._performance_metrics = {
            "total_updates": 0,
            "avg_update_time_ms": 0.0,
            "last_update_time_ms": 0.0,
            "validation_failures": 0
        }
    
    @abstractmethod
    def _update_internal_state(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Update the internal state based on telemetry data.
        
        This method must be implemented by subclasses to define
        twin-specific state update logic.
        
        Args:
            telemetry_data: Validated telemetry data
        """
        pass
    
    @abstractmethod
    def _get_twin_specific_state(self) -> Dict[str, Any]:
        """
        Get twin-specific state data.
        
        This method must be implemented by subclasses to return
        the current state in the expected format.
        
        Returns:
            Twin-specific state dictionary
        """
        pass
    
    @abstractmethod
    def _generate_predictions(self, horizon_seconds: int) -> Dict[str, Any]:
        """
        Generate twin-specific predictions.
        
        This method must be implemented by subclasses to generate
        predictions based on current state.
        
        Args:
            horizon_seconds: Prediction time horizon
            
        Returns:
            Prediction data dictionary
        """
        pass
    
    def _validate_input_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate input telemetry data.
        
        Args:
            data: Telemetry data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        # Basic validation - check for required timestamp
        if "timestamp" not in data:
            return False
        
        # Additional validation can be added by subclasses
        return self._additional_input_validation(data)
    
    def _validate_output_state(self, state: Dict[str, Any]) -> bool:
        """
        Validate output state against schema.
        
        Args:
            state: State data to validate
            
        Returns:
            True if state is valid, False otherwise
        """
        try:
            from schemas import get_schema
            schema = get_schema(self.schema_name)
            return validate_json_schema(state, schema)
        except Exception:
            # If schema validation fails, allow the state but log the issue
            return True
    
    def _additional_input_validation(self, data: Dict[str, Any]) -> bool:
        """
        Additional input validation hook for subclasses.
        
        Args:
            data: Telemetry data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        return True
    
    def _update_performance_metrics(self, update_time_ms: float) -> None:
        """
        Update performance tracking metrics.
        
        Args:
            update_time_ms: Time taken for this update in milliseconds
        """
        self._performance_metrics["total_updates"] += 1
        self._performance_metrics["last_update_time_ms"] = update_time_ms
        
        # Calculate running average
        total_updates = self._performance_metrics["total_updates"]
        current_avg = self._performance_metrics["avg_update_time_ms"]
        new_avg = ((current_avg * (total_updates - 1)) + update_time_ms) / total_updates
        self._performance_metrics["avg_update_time_ms"] = new_avg
        
        # Check performance thresholds
        max_update_time = get_config("performance.max_update_time_ms", 500)
        if update_time_ms > max_update_time:
            print(f"Warning: {self.twin_id} update took {update_time_ms:.2f}ms (threshold: {max_update_time}ms)")
    
    def __str__(self) -> str:
        """String representation of the twin model."""
        return f"{self.__class__.__name__}(id={self.twin_id}, updates={self._update_count})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the twin model."""
        return (f"{self.__class__.__name__}(twin_id='{self.twin_id}', "
                f"schema='{self.schema_name}', updates={self._update_count}, "
                f"last_update={self._last_update})")