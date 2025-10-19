"""
Car Twin model implementation for the F1 Dual Twin System.

This module implements the Car Twin digital model that maintains real-time
state tracking for our racing car based on telemetry data inputs.
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from core.base_twin import BaseTwinModel
from core.interfaces import TwinModelError
from utils.config import get_config
from core.schemas import validate_json_schema, CAR_TWIN_SCHEMA
import json


class CarTwin(BaseTwinModel):
    """
    Car Twin digital model for real-time car state tracking.
    
    Maintains high-fidelity state representation including speed, tire metrics,
    fuel levels, and lap times with sub-200ms update latency requirements.
    """
    
    def __init__(self, car_id: str):
        """
        Initialize Car Twin model.
        
        Args:
            car_id: Unique identifier for the car (e.g., "44" for Hamilton)
        """
        super().__init__(twin_id=car_id, schema_name="car_twin")
        self.car_id = car_id
        
        # Initialize core state tracking
        self._current_state = {
            "speed": 0.0,
            "tire_temp": [0.0, 0.0, 0.0, 0.0],  # [FL, FR, RL, RR]
            "tire_wear": 0.0,
            "fuel_level": 1.0,
            "lap_time": 0.0
        }
        
        # Historical data for calculations
        self._lap_history: List[Dict[str, Any]] = []
        self._tire_history: List[Dict[str, Any]] = []
        self._fuel_history: List[Dict[str, Any]] = []
        
        # Performance tracking
        self._sector_times: List[float] = [0.0, 0.0, 0.0]
        self._best_lap_time: Optional[float] = None
        self._current_lap: int = 0
        
        # Configuration
        self._max_history_length = get_config("car_twin.max_history_length", 50)
        self._update_latency_threshold_ms = get_config("car_twin.update_latency_threshold_ms", 200)
    
    def _update_internal_state(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Update internal car state based on telemetry data.
        
        Args:
            telemetry_data: Validated telemetry data
            
        Raises:
            TwinModelError: If car data not found or invalid
        """
        # Find our car's data in the telemetry
        car_data = self._extract_car_data(telemetry_data)
        if not car_data:
            raise TwinModelError(f"No telemetry data found for car {self.car_id}")
        
        # Update core state metrics
        self._update_speed(car_data)
        self._update_tire_metrics(car_data)
        self._update_fuel_level(car_data)
        self._update_lap_timing(car_data, telemetry_data)
        
        # Update historical data for trend analysis
        self._update_historical_data(car_data, telemetry_data)
        
        # Store complete state
        self._state = {
            "car_id": self.car_id,
            "current_state": self._current_state.copy(),
            "lap": self._current_lap,
            "sector_times": self._sector_times.copy(),
            "best_lap_time": self._best_lap_time
        }
    
    def _get_twin_specific_state(self) -> Dict[str, Any]:
        """
        Get Car Twin specific state data in the expected JSON schema format.
        
        Returns:
            Car Twin state matching the CAR_TWIN_SCHEMA format
        """
        # Get current predictions and strategy metrics
        predictions = self._generate_predictions(300)  # 5-minute horizon
        strategy_metrics = self.get_strategy_metrics()
        
        return {
            "car_id": self.car_id,
            "current_state": self._current_state.copy(),
            "predictions": predictions,
            "strategy_metrics": strategy_metrics
        }
    
    def _generate_predictions(self, horizon_seconds: int) -> Dict[str, Any]:
        """
        Generate predictions based on current state and historical data.
        
        Args:
            horizon_seconds: Prediction time horizon
            
        Returns:
            Prediction data including tire degradation, fuel consumption, and pit strategy
        """
        predictions = {
            "tire_degradation_rate": self._predict_tire_degradation(),
            "fuel_consumption_rate": self._predict_fuel_consumption(),
            "predicted_pit_lap": self._predict_optimal_pit_lap(),
            "performance_delta": self._calculate_performance_delta()
        }
        
        return predictions
    
    def _extract_car_data(self, telemetry_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract our car's data from telemetry.
        
        Args:
            telemetry_data: Complete telemetry data
            
        Returns:
            Our car's data or None if not found
        """
        cars = telemetry_data.get("cars", [])
        for car in cars:
            if car.get("car_id") == self.car_id:
                return car
        return None
    
    def _update_speed(self, car_data: Dict[str, Any]) -> None:
        """
        Update speed tracking.
        
        Args:
            car_data: Car-specific telemetry data
        """
        speed = car_data.get("speed", 0.0)
        if isinstance(speed, (int, float)) and speed >= 0:
            self._current_state["speed"] = float(speed)
    
    def _update_tire_metrics(self, car_data: Dict[str, Any]) -> None:
        """
        Update tire temperature and wear tracking.
        
        Args:
            car_data: Car-specific telemetry data
        """
        tire_data = car_data.get("tire", {})
        
        # Update tire wear
        wear_level = tire_data.get("wear_level", 0.0)
        if isinstance(wear_level, (int, float)) and 0 <= wear_level <= 1:
            self._current_state["tire_wear"] = float(wear_level)
        
        # Estimate tire temperatures (not in basic telemetry, so calculate from wear/speed)
        # This is a simplified estimation - real implementation would use actual sensors
        base_temp = 80.0  # Base tire temperature
        speed_factor = self._current_state["speed"] / 300.0  # Normalize speed
        wear_factor = self._current_state["tire_wear"] * 20.0  # Wear increases temp
        
        estimated_temp = base_temp + (speed_factor * 30.0) + wear_factor
        self._current_state["tire_temp"] = [estimated_temp] * 4  # Same for all tires for now
    
    def _update_fuel_level(self, car_data: Dict[str, Any]) -> None:
        """
        Update fuel level tracking.
        
        Args:
            car_data: Car-specific telemetry data
        """
        fuel_level = car_data.get("fuel_level", 1.0)
        if isinstance(fuel_level, (int, float)) and 0 <= fuel_level <= 1:
            self._current_state["fuel_level"] = float(fuel_level)
    
    def _update_lap_timing(self, car_data: Dict[str, Any], telemetry_data: Dict[str, Any]) -> None:
        """
        Update lap timing and sector data.
        
        Args:
            car_data: Car-specific telemetry data
            telemetry_data: Complete telemetry data for lap context
        """
        # Update current lap number
        current_lap = telemetry_data.get("lap", 1)
        if isinstance(current_lap, int) and current_lap > 0:
            self._current_lap = current_lap
        
        # Update lap time
        lap_time = car_data.get("lap_time", 0.0)
        if isinstance(lap_time, (int, float)) and lap_time > 0:
            self._current_state["lap_time"] = float(lap_time)
            
            # Track best lap time
            if self._best_lap_time is None or lap_time < self._best_lap_time:
                self._best_lap_time = lap_time
        
        # Update sector times if available
        sector_times = car_data.get("sector_times", [])
        if isinstance(sector_times, list) and len(sector_times) == 3:
            self._sector_times = [float(t) for t in sector_times if isinstance(t, (int, float))]
    
    def _update_historical_data(self, car_data: Dict[str, Any], telemetry_data: Dict[str, Any]) -> None:
        """
        Update historical data for trend analysis.
        
        Args:
            car_data: Car-specific telemetry data
            telemetry_data: Complete telemetry data
        """
        timestamp = telemetry_data.get("timestamp", datetime.now(timezone.utc).isoformat())
        
        # Add lap data
        if self._current_state["lap_time"] > 0:
            lap_entry = {
                "timestamp": timestamp,
                "lap": self._current_lap,
                "lap_time": self._current_state["lap_time"],
                "sector_times": self._sector_times.copy(),
                "speed": self._current_state["speed"]
            }
            self._lap_history.append(lap_entry)
        
        # Add tire data
        tire_entry = {
            "timestamp": timestamp,
            "lap": self._current_lap,
            "wear_level": self._current_state["tire_wear"],
            "tire_temp": self._current_state["tire_temp"].copy(),
            "compound": car_data.get("tire", {}).get("compound", "unknown")
        }
        self._tire_history.append(tire_entry)
        
        # Add fuel data
        fuel_entry = {
            "timestamp": timestamp,
            "lap": self._current_lap,
            "fuel_level": self._current_state["fuel_level"]
        }
        self._fuel_history.append(fuel_entry)
        
        # Trim history to prevent memory issues
        self._trim_historical_data()
    
    def _trim_historical_data(self) -> None:
        """Trim historical data to maintain memory limits."""
        if len(self._lap_history) > self._max_history_length:
            self._lap_history = self._lap_history[-self._max_history_length:]
        
        if len(self._tire_history) > self._max_history_length:
            self._tire_history = self._tire_history[-self._max_history_length:]
        
        if len(self._fuel_history) > self._max_history_length:
            self._fuel_history = self._fuel_history[-self._max_history_length:]
    
    def _additional_input_validation(self, data: Dict[str, Any]) -> bool:
        """
        Additional validation for Car Twin telemetry data.
        
        Args:
            data: Telemetry data to validate
            
        Returns:
            True if data is valid for Car Twin processing
        """
        # Check for cars array
        if "cars" not in data or not isinstance(data["cars"], list):
            return False
        
        # Check if our car is in the data
        car_data = self._extract_car_data(data)
        if not car_data:
            return False
        
        # Validate required car fields
        required_fields = ["speed", "tire", "fuel_level", "lap_time"]
        for field in required_fields:
            if field not in car_data:
                return False
        
        return True
    
    def get_lap_history(self, last_n_laps: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get historical lap data.
        
        Args:
            last_n_laps: Number of recent laps to return (None for all)
            
        Returns:
            List of lap data entries
        """
        if last_n_laps is None:
            return self._lap_history.copy()
        return self._lap_history[-last_n_laps:] if last_n_laps > 0 else []
    
    def get_tire_history(self, last_n_entries: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get historical tire data.
        
        Args:
            last_n_entries: Number of recent entries to return (None for all)
            
        Returns:
            List of tire data entries
        """
        if last_n_entries is None:
            return self._tire_history.copy()
        return self._tire_history[-last_n_entries:] if last_n_entries > 0 else []
    
    def get_fuel_history(self, last_n_entries: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get historical fuel data.
        
        Args:
            last_n_entries: Number of recent entries to return (None for all)
            
        Returns:
            List of fuel data entries
        """
        if last_n_entries is None:
            return self._fuel_history.copy()
        return self._fuel_history[-last_n_entries:] if last_n_entries > 0 else []
    
    def _predict_tire_degradation(self) -> float:
        """
        Predict tire degradation rate based on wear patterns and track conditions.
        
        Returns:
            Predicted tire degradation rate per lap (0.0 to 0.1)
        """
        if len(self._tire_history) < 2:
            # Default degradation rate for new tires
            return 0.008
        
        # Calculate degradation rate from recent tire data
        recent_data = self._tire_history[-10:]  # Last 10 data points
        if len(recent_data) < 2:
            return 0.008
        
        # Calculate wear progression
        wear_deltas = []
        for i in range(1, len(recent_data)):
            prev_wear = recent_data[i-1]["wear_level"]
            curr_wear = recent_data[i]["wear_level"]
            lap_diff = recent_data[i]["lap"] - recent_data[i-1]["lap"]
            
            if lap_diff > 0:
                wear_delta = (curr_wear - prev_wear) / lap_diff
                wear_deltas.append(wear_delta)
        
        if not wear_deltas:
            return 0.008
        
        # Average degradation rate with temperature adjustment
        base_degradation = sum(wear_deltas) / len(wear_deltas)
        
        # Adjust for tire temperature (higher temp = faster degradation)
        avg_temp = sum(self._current_state["tire_temp"]) / 4
        temp_factor = 1.0 + ((avg_temp - 85.0) / 100.0)  # 85°C is optimal
        
        # Adjust for track conditions (simplified)
        track_factor = 1.0  # Would be based on track surface, weather, etc.
        
        predicted_rate = base_degradation * temp_factor * track_factor
        
        # Clamp to reasonable bounds
        return max(0.001, min(0.05, predicted_rate))
    
    def _predict_fuel_consumption(self) -> float:
        """
        Predict fuel consumption rate based on recent usage patterns.
        
        Returns:
            Predicted fuel consumption rate per lap (kg/lap)
        """
        if len(self._fuel_history) < 2:
            # Default consumption rate
            return 2.1
        
        # Calculate consumption from recent fuel data
        recent_data = self._fuel_history[-10:]  # Last 10 data points
        if len(recent_data) < 2:
            return 2.1
        
        # Calculate fuel usage progression
        consumption_rates = []
        for i in range(1, len(recent_data)):
            prev_fuel = recent_data[i-1]["fuel_level"]
            curr_fuel = recent_data[i]["fuel_level"]
            lap_diff = recent_data[i]["lap"] - recent_data[i-1]["lap"]
            
            if lap_diff > 0 and prev_fuel > curr_fuel:
                # Convert fuel level percentage to actual consumption
                fuel_used = (prev_fuel - curr_fuel) * 110  # Assume 110kg max fuel
                consumption_per_lap = fuel_used / lap_diff
                consumption_rates.append(consumption_per_lap)
        
        if not consumption_rates:
            return 2.1
        
        # Average consumption with driving style adjustment
        base_consumption = sum(consumption_rates) / len(consumption_rates)
        
        # Adjust for current speed/driving style
        speed_factor = 1.0 + ((self._current_state["speed"] - 250.0) / 500.0)
        
        predicted_rate = base_consumption * speed_factor
        
        # Clamp to reasonable bounds (1.5 to 4.0 kg/lap)
        return max(1.5, min(4.0, predicted_rate))
    
    def _predict_optimal_pit_lap(self) -> int:
        """
        Predict optimal pit stop lap based on tire degradation and fuel levels.
        
        Returns:
            Predicted optimal pit lap number
        """
        if self._current_lap == 0:
            return 25  # Default mid-race pit
        
        # Get current predictions
        tire_degradation_rate = self._predict_tire_degradation()
        fuel_consumption_rate = self._predict_fuel_consumption()
        
        # Calculate tire life remaining
        current_wear = self._current_state["tire_wear"]
        max_wear_threshold = 0.85  # 85% wear is critical
        
        if tire_degradation_rate > 0:
            tire_laps_remaining = (max_wear_threshold - current_wear) / tire_degradation_rate
        else:
            tire_laps_remaining = 50  # Conservative estimate
        
        # Calculate fuel laps remaining
        current_fuel = self._current_state["fuel_level"]
        if fuel_consumption_rate > 0:
            fuel_kg_remaining = current_fuel * 110  # Convert to kg
            fuel_laps_remaining = fuel_kg_remaining / fuel_consumption_rate
        else:
            fuel_laps_remaining = 50  # Conservative estimate
        
        # Pit when the limiting factor (tire or fuel) reaches critical level
        limiting_laps = min(tire_laps_remaining, fuel_laps_remaining)
        
        # Add safety margin and current lap
        safety_margin = 2  # Pit 2 laps before critical
        predicted_pit_lap = self._current_lap + max(1, int(limiting_laps - safety_margin))
        
        # Ensure reasonable bounds (don't pit too early or too late)
        race_length = get_config("race.total_laps", 70)
        return max(self._current_lap + 1, min(race_length - 5, predicted_pit_lap))
    
    def _calculate_performance_delta(self) -> float:
        """
        Calculate performance delta compared to optimal lap time.
        
        Returns:
            Performance delta in seconds (negative = faster than optimal)
        """
        if not self._best_lap_time or self._current_state["lap_time"] <= 0:
            return 0.0
        
        # Use best lap as reference for optimal performance
        optimal_time = self._best_lap_time
        current_time = self._current_state["lap_time"]
        
        # Adjust optimal time for current tire wear
        tire_wear = self._current_state["tire_wear"]
        wear_penalty = tire_wear * 2.0  # 2 seconds penalty at 100% wear
        
        # Adjust optimal time for fuel load
        fuel_level = self._current_state["fuel_level"]
        fuel_penalty = fuel_level * 0.5  # 0.5 seconds penalty at full fuel
        
        adjusted_optimal = optimal_time + wear_penalty + fuel_penalty
        
        # Calculate delta
        delta = current_time - adjusted_optimal
        
        # Clamp to reasonable bounds
        return max(-5.0, min(10.0, delta))
    
    def get_strategy_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy metrics for pit window analysis.
        
        Returns:
            Strategy metrics including pit windows and remaining capacity
        """
        tire_degradation_rate = self._predict_tire_degradation()
        fuel_consumption_rate = self._predict_fuel_consumption()
        predicted_pit_lap = self._predict_optimal_pit_lap()
        
        # Calculate tire life remaining
        current_wear = self._current_state["tire_wear"]
        max_wear_threshold = 0.85
        
        if tire_degradation_rate > 0:
            tire_laps_remaining = int((max_wear_threshold - current_wear) / tire_degradation_rate)
        else:
            tire_laps_remaining = 50
        
        # Calculate fuel laps remaining
        current_fuel = self._current_state["fuel_level"]
        if fuel_consumption_rate > 0:
            fuel_kg_remaining = current_fuel * 110
            fuel_laps_remaining = int(fuel_kg_remaining / fuel_consumption_rate)
        else:
            fuel_laps_remaining = 50
        
        # Calculate optimal pit window (3-lap window around predicted lap)
        pit_window_start = max(self._current_lap + 1, predicted_pit_lap - 1)
        pit_window_end = predicted_pit_lap + 2
        
        return {
            "optimal_pit_window": [pit_window_start, pit_window_end],
            "tire_life_remaining": max(0, tire_laps_remaining),
            "fuel_laps_remaining": max(0, fuel_laps_remaining),
            "predicted_pit_lap": predicted_pit_lap,
            "tire_degradation_rate": tire_degradation_rate,
            "fuel_consumption_rate": fuel_consumption_rate,
            "performance_delta": self._calculate_performance_delta()
        }
    
    def get_current_performance_summary(self) -> Dict[str, Any]:
        """
        Get current performance summary for quick analysis.
        
        Returns:
            Performance summary data
        """
        return {
            "car_id": self.car_id,
            "current_lap": self._current_lap,
            "current_speed": self._current_state["speed"],
            "tire_wear": self._current_state["tire_wear"],
            "fuel_level": self._current_state["fuel_level"],
            "last_lap_time": self._current_state["lap_time"],
            "best_lap_time": self._best_lap_time,
            "avg_tire_temp": sum(self._current_state["tire_temp"]) / 4,
            "total_laps_recorded": len(self._lap_history)
        }
    
    def to_json(self, include_metadata: bool = True) -> str:
        """
        Serialize Car Twin state to JSON string.
        
        Args:
            include_metadata: Whether to include versioning and metadata
            
        Returns:
            JSON string representation of the Car Twin state
        """
        state_data = self.get_current_state()
        
        if include_metadata:
            # Add versioning and metadata
            json_output = {
                "schema_version": "1.0.0",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "twin_type": "car_twin",
                "data": state_data
            }
        else:
            json_output = state_data
        
        return json.dumps(json_output, indent=2, ensure_ascii=False)
    
    def to_dict(self, validate_schema: bool = True) -> Dict[str, Any]:
        """
        Get Car Twin state as dictionary in schema-compliant format.
        
        Args:
            validate_schema: Whether to validate against CAR_TWIN_SCHEMA
            
        Returns:
            Dictionary representation of Car Twin state
            
        Raises:
            TwinModelError: If schema validation fails
        """
        state_data = self.get_current_state()
        
        if validate_schema:
            if not validate_json_schema(state_data, CAR_TWIN_SCHEMA):
                raise TwinModelError(f"Car Twin state does not match expected schema for {self.car_id}")
        
        return state_data
    
    def export_to_file(self, file_path: str, include_metadata: bool = True) -> None:
        """
        Export Car Twin state to JSON file.
        
        Args:
            file_path: Path to output JSON file
            include_metadata: Whether to include versioning and metadata
        """
        json_data = self.to_json(include_metadata=include_metadata)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
        except Exception as e:
            raise TwinModelError(f"Failed to export Car Twin data to {file_path}: {str(e)}")
    
    def get_api_response_format(self) -> Dict[str, Any]:
        """
        Get Car Twin data in API response format with proper versioning.
        
        Returns:
            API-ready dictionary with metadata and versioning
        """
        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0.0",
            "car_twin": self.to_dict(validate_schema=True),
            "metadata": {
                "update_count": self._update_count,
                "last_update": self._last_update.isoformat() if self._last_update else None,
                "performance_metrics": self.get_performance_metrics(),
                "data_quality": {
                    "lap_data_points": len(self._lap_history),
                    "tire_data_points": len(self._tire_history),
                    "fuel_data_points": len(self._fuel_history)
                }
            }
        }