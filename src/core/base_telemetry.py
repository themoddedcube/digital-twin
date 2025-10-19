"""
Base telemetry processor implementation for the F1 Dual Twin System.

This module provides the foundational telemetry processing functionality
that handles data ingestion, validation, and normalization.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.interfaces import TelemetryProcessor, TelemetryValidationError
from core.schemas import validate_json_schema, get_schema
from utils.config import get_config


class BaseTelemetryProcessor(TelemetryProcessor):
    """
    Base implementation for telemetry data processing.
    
    Handles common telemetry operations including validation, normalization,
    and error handling with fallback mechanisms.
    """
    
    def __init__(self):
        """Initialize base telemetry processor."""
        self._last_valid_data: Optional[Dict[str, Any]] = None
        self._processing_stats = {
            "total_processed": 0,
            "validation_failures": 0,
            "normalization_failures": 0,
            "fallback_uses": 0,
            "avg_processing_time_ms": 0.0
        }
        
        # Load configuration
        self.processing_timeout_ms = get_config("telemetry.processing_timeout_ms", 250)
        self.validation_enabled = get_config("telemetry.validation_enabled", True)
        self.fallback_enabled = get_config("telemetry.fallback_to_last_valid", True)
        self.output_file = get_config("telemetry.output_file", "shared/telemetry_state.json")
    
    def ingest_telemetry(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming telemetry data and return normalized format.
        
        Args:
            raw_data: Raw telemetry data from source
            
        Returns:
            Normalized telemetry data in standard JSON format
            
        Raises:
            TelemetryValidationError: If data fails validation and no fallback available
        """
        start_time = time.time()
        
        try:
            # Validate input data if enabled
            if self.validation_enabled and not self.validate_schema(raw_data):
                self._processing_stats["validation_failures"] += 1
                if self.fallback_enabled and self._last_valid_data:
                    self._processing_stats["fallback_uses"] += 1
                    return self._create_fallback_data()
                else:
                    raise TelemetryValidationError("Invalid telemetry data and no fallback available")
            
            # Normalize the data
            normalized_data = self.normalize_data(raw_data)
            
            # Validate normalized data
            if self.validation_enabled and not self._validate_normalized_data(normalized_data):
                self._processing_stats["normalization_failures"] += 1
                if self.fallback_enabled and self._last_valid_data:
                    self._processing_stats["fallback_uses"] += 1
                    return self._create_fallback_data()
                else:
                    raise TelemetryValidationError("Normalization produced invalid data")
            
            # Store as last valid data
            self._last_valid_data = normalized_data.copy()
            
            # Update processing statistics
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_processing_stats(processing_time_ms)
            
            # Check processing time threshold
            if processing_time_ms > self.processing_timeout_ms:
                print(f"Warning: Telemetry processing took {processing_time_ms:.2f}ms "
                      f"(threshold: {self.processing_timeout_ms}ms)")
            
            # Write to output file
            self._write_output_file(normalized_data)
            
            return normalized_data
            
        except Exception as e:
            if isinstance(e, TelemetryValidationError):
                raise
            else:
                raise TelemetryValidationError(f"Telemetry processing failed: {str(e)}")
    
    def validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        Validate telemetry data against expected schema.
        
        Args:
            data: Telemetry data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Basic structure validation
            if not isinstance(data, dict):
                return False
            
            # Check for minimum required fields
            required_fields = ["timestamp", "cars"]
            for field in required_fields:
                if field not in data:
                    return False
            
            # Validate timestamp format
            if not self._validate_timestamp(data["timestamp"]):
                return False
            
            # Validate cars data
            if not isinstance(data["cars"], list) or len(data["cars"]) == 0:
                return False
            
            # Additional validation can be implemented by subclasses
            return self._additional_validation(data)
            
        except Exception:
            return False
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw telemetry to standardized JSON format.
        
        Args:
            raw_data: Raw telemetry data
            
        Returns:
            Normalized data in standard format
        """
        try:
            # Create base normalized structure
            normalized = {
                "timestamp": self._normalize_timestamp(raw_data.get("timestamp")),
                "lap": raw_data.get("lap", 0),
                "session_type": raw_data.get("session_type", "unknown"),
                "track_conditions": self._normalize_track_conditions(raw_data.get("track_conditions", {})),
                "cars": self._normalize_cars_data(raw_data.get("cars", []))
            }
            
            return normalized
            
        except Exception as e:
            raise TelemetryValidationError(f"Data normalization failed: {str(e)}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get telemetry processing statistics.
        
        Returns:
            Processing statistics dictionary
        """
        return self._processing_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self._processing_stats = {
            "total_processed": 0,
            "validation_failures": 0,
            "normalization_failures": 0,
            "fallback_uses": 0,
            "avg_processing_time_ms": 0.0
        }
    
    def _validate_normalized_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate normalized data against telemetry schema.
        
        Args:
            data: Normalized telemetry data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            schema = get_schema("telemetry")
            return validate_json_schema(data, schema)
        except Exception:
            return False
    
    def _create_fallback_data(self) -> Dict[str, Any]:
        """
        Create fallback data based on last valid data.
        
        Returns:
            Fallback telemetry data
        """
        if not self._last_valid_data:
            raise TelemetryValidationError("No fallback data available")
        
        fallback_data = self._last_valid_data.copy()
        
        # Update timestamp to current time
        fallback_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Mark as fallback data
        fallback_data["_fallback"] = True
        fallback_data["_fallback_reason"] = "Using last valid data due to processing failure"
        
        return fallback_data
    
    def _normalize_timestamp(self, timestamp: Any) -> str:
        """
        Normalize timestamp to ISO 8601 format.
        
        Args:
            timestamp: Timestamp in various formats
            
        Returns:
            ISO 8601 formatted timestamp string
        """
        if isinstance(timestamp, str):
            # Assume it's already in correct format
            return timestamp
        elif isinstance(timestamp, (int, float)):
            # Assume Unix timestamp
            return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
        else:
            # Use current time as fallback
            return datetime.now(timezone.utc).isoformat()
    
    def _normalize_track_conditions(self, track_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize track conditions data.
        
        Args:
            track_data: Raw track conditions data
            
        Returns:
            Normalized track conditions
        """
        return {
            "temperature": float(track_data.get("temperature", 25.0)),
            "weather": str(track_data.get("weather", "sunny")),
            "track_status": str(track_data.get("track_status", "green"))
        }
    
    def _normalize_cars_data(self, cars_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize cars data array.
        
        Args:
            cars_data: Raw cars data array
            
        Returns:
            Normalized cars data array
        """
        normalized_cars = []
        
        for car_data in cars_data:
            if not isinstance(car_data, dict):
                continue
            
            normalized_car = {
                "car_id": str(car_data.get("car_id", "unknown")),
                "team": str(car_data.get("team", "unknown")),
                "driver": str(car_data.get("driver", "unknown")),
                "position": int(car_data.get("position", 20)),
                "speed": float(car_data.get("speed", 0.0)),
                "tire": self._normalize_tire_data(car_data.get("tire", {})),
                "fuel_level": float(car_data.get("fuel_level", 0.0)),
                "lap_time": float(car_data.get("lap_time", 120.0))
            }
            
            # Add optional sector times if available
            if "sector_times" in car_data:
                normalized_car["sector_times"] = [
                    float(t) for t in car_data["sector_times"][:3]
                ]
            
            normalized_cars.append(normalized_car)
        
        return normalized_cars
    
    def _normalize_tire_data(self, tire_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize tire data.
        
        Args:
            tire_data: Raw tire data
            
        Returns:
            Normalized tire data
        """
        return {
            "compound": str(tire_data.get("compound", "medium")),
            "age": int(tire_data.get("age", 0)),
            "wear_level": float(tire_data.get("wear_level", 0.0))
        }
    
    def _validate_timestamp(self, timestamp: Any) -> bool:
        """
        Validate timestamp format.
        
        Args:
            timestamp: Timestamp to validate
            
        Returns:
            True if timestamp is valid, False otherwise
        """
        try:
            if isinstance(timestamp, str):
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return True
            elif isinstance(timestamp, (int, float)):
                return timestamp > 0
            return False
        except Exception:
            return False
    
    def _additional_validation(self, data: Dict[str, Any]) -> bool:
        """
        Additional validation hook for subclasses.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        return True
    
    def _update_processing_stats(self, processing_time_ms: float) -> None:
        """
        Update processing statistics.
        
        Args:
            processing_time_ms: Processing time in milliseconds
        """
        self._processing_stats["total_processed"] += 1
        
        # Calculate running average
        total = self._processing_stats["total_processed"]
        current_avg = self._processing_stats["avg_processing_time_ms"]
        new_avg = ((current_avg * (total - 1)) + processing_time_ms) / total
        self._processing_stats["avg_processing_time_ms"] = new_avg
    
    def _write_output_file(self, data: Dict[str, Any]) -> None:
        """
        Write telemetry data to output file.
        
        Args:
            data: Telemetry data to write
        """
        try:
            output_path = Path(self.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to write telemetry output file: {e}")