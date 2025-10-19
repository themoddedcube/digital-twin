"""
Simple Monte Carlo Handler for F1 Race Strategy

This module provides a straightforward interface to Monte Carlo simulation
for pit strategy optimization, with Mojo kernel integration via MAX Engine.
"""

import time
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from max_integration.mojo_simulation import get_mojo_handler, MojoSimulationHandler


@dataclass
class MonteCarloResult:
    """Simple Monte Carlo simulation result"""
    pit_lap: int
    final_position: int
    total_time: float
    success_probability: float
    tire_life_remaining: int
    fuel_laps_remaining: int


class MonteCarloHandler:
    """
    Simple Monte Carlo handler for pit strategy simulation.
    
    This provides a straightforward interface to run Monte Carlo simulations
    for F1 race strategy optimization.
    """
    
    def __init__(self):
        """Initialize the Monte Carlo handler."""
        self.simulation_count = 1000
        self.last_simulation_time = None
        self.simulation_history = []
        self.mojo_handler = get_mojo_handler()
        
    def run_simulation(
        self, 
        race_state: Dict[str, Any], 
        pit_window_start: int = None, 
        pit_window_end: int = None
    ) -> List[MonteCarloResult]:
        """
        Run Monte Carlo simulation for pit strategy optimization using Mojo kernel.
        
        Args:
            race_state: Current race state data
            pit_window_start: Start of pit window (defaults to current lap + 1)
            pit_window_end: End of pit window (defaults to current lap + 10)
            
        Returns:
            List of simulation results for different pit strategies
        """
        start_time = time.time()
        
        # Set default pit window
        current_lap = race_state.get("current_lap", 0)
        if pit_window_start is None:
            pit_window_start = current_lap + 1
        if pit_window_end is None:
            pit_window_end = current_lap + 10
        
        try:
            # Try to use Mojo kernel via MAX Engine
            mojo_results = self.mojo_handler.run_simulation(
                race_state, pit_window_start, pit_window_end
            )
            
            # Convert Mojo results to MonteCarloResult format
            results = []
            for mojo_result in mojo_results:
                result = MonteCarloResult(
                    pit_lap=mojo_result.pit_lap,
                    final_position=mojo_result.final_position,
                    total_time=mojo_result.total_time,
                    success_probability=mojo_result.success_probability,
                    tire_life_remaining=mojo_result.tire_life_remaining,
                    fuel_laps_remaining=mojo_result.fuel_laps_remaining
                )
                results.append(result)
            
            # Sort by total time (best first)
            results.sort(key=lambda x: x.total_time)
            
            # Store in history
            self.last_simulation_time = time.time() - start_time
            self.simulation_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "race_state": race_state,
                "results_count": len(results),
                "processing_time_ms": self.last_simulation_time * 1000,
                "best_strategy": results[0] if results else None,
                "mojo_used": True
            })
            
            # Keep only last 50 simulations
            if len(self.simulation_history) > 50:
                self.simulation_history.pop(0)
            
            return results
            
        except Exception as e:
            print(f"Mojo simulation failed, falling back to Python: {e}")
            # Fallback to Python implementation
            return self._run_python_simulation(race_state, pit_window_start, pit_window_end)
    
    def _run_python_simulation(
        self, 
        race_state: Dict[str, Any], 
        pit_window_start: int, 
        pit_window_end: int
    ) -> List[MonteCarloResult]:
        """Fallback Python simulation when Mojo is not available."""
        
        start_time = time.time()
        
        # Extract race parameters
        tire_wear = race_state.get("tire_wear", 0.5)
        fuel_level = race_state.get("fuel_level", 0.5)
        tire_compound = race_state.get("tire_compound", "medium")
        track_temp = race_state.get("track_temp", 25.0)
        position = race_state.get("position", 1)
        
        # Run simulations for each pit lap in the window
        results = []
        
        for pit_lap in range(pit_window_start, pit_window_end + 1):
            result = self._simulate_pit_strategy(
                race_state, pit_lap, tire_compound, track_temp
            )
            results.append(result)
        
        # Sort by total time (best first)
        results.sort(key=lambda x: x.total_time)
        
        # Store in history
        self.last_simulation_time = time.time() - start_time
        self.simulation_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "race_state": race_state,
            "results_count": len(results),
            "processing_time_ms": self.last_simulation_time * 1000,
            "best_strategy": results[0] if results else None,
            "mojo_used": False
        })
        
        # Keep only last 50 simulations
        if len(self.simulation_history) > 50:
            self.simulation_history.pop(0)
        
        return results
    
    def _simulate_pit_strategy(
        self, 
        race_state: Dict[str, Any], 
        pit_lap: int, 
        tire_compound: str, 
        track_temp: float
    ) -> MonteCarloResult:
        """Simulate a specific pit strategy."""
        
        # Base parameters
        base_lap_time = self._get_base_lap_time(tire_compound)
        tire_wear = race_state.get("tire_wear", 0.5)
        fuel_level = race_state.get("fuel_level", 0.5)
        current_lap = race_state.get("current_lap", 0)
        position = race_state.get("position", 1)
        
        # Run Monte Carlo simulations
        successful_simulations = 0
        total_time_sum = 0.0
        final_positions = []
        
        for _ in range(self.simulation_count):
            simulation_time, success = self._run_single_simulation(
                current_lap, pit_lap, tire_wear, fuel_level, 
                base_lap_time, track_temp, tire_compound
            )
            
            if success:
                successful_simulations += 1
                total_time_sum += simulation_time
                # Use actual position data, not random changes
                final_positions.append(position)
        
        # Calculate results
        success_probability = successful_simulations / self.simulation_count
        avg_time = total_time_sum / max(successful_simulations, 1)
        avg_position = sum(final_positions) / len(final_positions) if final_positions else position
        
        # Calculate remaining resources
        tire_life_remaining = max(0, int((1.0 - tire_wear) / 0.05))
        fuel_laps_remaining = max(0, int(fuel_level / 0.02))
        
        return MonteCarloResult(
            pit_lap=pit_lap,
            final_position=int(avg_position),
            total_time=avg_time,
            success_probability=success_probability,
            tire_life_remaining=tire_life_remaining,
            fuel_laps_remaining=fuel_laps_remaining
        )
    
    def _run_single_simulation(
        self, 
        current_lap: int, 
        pit_lap: int, 
        tire_wear: float, 
        fuel_level: float,
        base_lap_time: float, 
        track_temp: float, 
        tire_compound: str
    ) -> tuple[float, bool]:
        """Run a single Monte Carlo simulation using Mojo kernel."""
        
        try:
            # Try to use Mojo kernel if available
            return self._run_mojo_simulation(
                current_lap, pit_lap, tire_wear, fuel_level,
                base_lap_time, track_temp, tire_compound
            )
        except Exception as e:
            print(f"Mojo simulation failed, falling back to Python: {e}")
            # Fallback to Python implementation
            return self._run_python_simulation(
                current_lap, pit_lap, tire_wear, fuel_level,
                base_lap_time, track_temp, tire_compound
            )
    
    def _run_mojo_simulation(
        self, 
        current_lap: int, 
        pit_lap: int, 
        tire_wear: float, 
        fuel_level: float,
        base_lap_time: float, 
        track_temp: float, 
        tire_compound: str
    ) -> tuple[float, bool]:
        """Run simulation using Mojo kernel via MAX Engine."""
        
        # Import Mojo simulation functions
        try:
            from mojo import simulate_strategy
        except ImportError:
            raise Exception("Mojo simulation module not available")
        
        # Prepare data for Mojo kernel using real data
        race_state = {
            "lap": current_lap,
            "position": 1,  # This will be updated by the simulation
            "tire_wear": tire_wear,
            "fuel_level": fuel_level,
            "tire_compound": tire_compound,
            "track_temp": track_temp,
            "gap_ahead": 0.0,  # These would come from real telemetry
            "gap_behind": 0.0
        }
        
        # Call Mojo simulation kernel
        result = simulate_strategy.run_strategy_simulation(
            race_state, pit_lap, pit_lap + 1  # Single pit lap simulation
        )
        
        if result and len(result) > 0:
            sim_result = result[0]  # Get first (and only) result
            return sim_result.total_time, sim_result.success_probability > 0.5
        else:
            return 0.0, False
    
    def _run_python_simulation(
        self, 
        current_lap: int, 
        pit_lap: int, 
        tire_wear: float, 
        fuel_level: float,
        base_lap_time: float, 
        track_temp: float, 
        tire_compound: str
    ) -> tuple[float, bool]:
        """Fallback Python simulation implementation."""
        
        simulation_time = 0.0
        current_tire_wear = tire_wear
        current_fuel = fuel_level
        
        # Simulate laps from current to pit
        for lap in range(current_lap, pit_lap):
            # Calculate lap time with degradation
            tire_penalty = current_tire_wear * 3.0  # Max 3 second penalty
            fuel_penalty = (1.0 - current_fuel) * 2.0  # Max 2 second penalty
            temp_factor = 1.0 + (track_temp - 25.0) * 0.001
            random_variance = (random.random() - 0.5) * 0.5  # ±0.25s variance
            
            lap_time = (base_lap_time + tire_penalty + fuel_penalty + random_variance) * temp_factor
            simulation_time += lap_time
            
            # Update tire wear
            wear_rate = self._get_wear_rate(tire_compound) + (random.random() - 0.5) * 0.02
            current_tire_wear += wear_rate
            
            # Update fuel level
            fuel_consumption = 0.02 + (random.random() - 0.5) * 0.005
            current_fuel -= fuel_consumption
            
            # Check for failure
            if current_tire_wear > 1.0 or current_fuel < 0.0:
                return 0.0, False
        
        # Add pit stop time
        simulation_time += 22.0  # 22 second pit stop
        current_tire_wear = 0.0  # Fresh tires
        current_fuel = 1.0  # Full fuel
        
        # Simulate remaining race
        remaining_laps = 50 - pit_lap
        for lap in range(remaining_laps):
            fuel_penalty = (1.0 - current_fuel) * 2.0
            temp_factor = 1.0 + (track_temp - 25.0) * 0.001
            random_variance = (random.random() - 0.5) * 0.5
            
            lap_time = (base_lap_time + fuel_penalty + random_variance) * temp_factor
            simulation_time += lap_time
            
            fuel_consumption = 0.02 + (random.random() - 0.5) * 0.005
            current_fuel -= fuel_consumption
            
            if current_fuel < 0.0:
                return 0.0, False
        
        return simulation_time, True
    
    def _get_base_lap_time(self, tire_compound: str) -> float:
        """Get base lap time for tire compound."""
        compound_times = {
            "soft": 89.0,
            "medium": 90.0,
            "hard": 91.0
        }
        return compound_times.get(tire_compound, 90.0)
    
    def _get_wear_rate(self, tire_compound: str) -> float:
        """Get tire wear rate for compound."""
        wear_rates = {
            "soft": 0.08,
            "medium": 0.05,
            "hard": 0.03
        }
        return wear_rates.get(tire_compound, 0.05)
    
    def get_best_strategy(self, results: List[MonteCarloResult]) -> Optional[MonteCarloResult]:
        """Get the best strategy from simulation results."""
        if not results:
            return None
        
        # Find strategy with best combination of time and success probability
        best_score = float('inf')
        best_result = None
        
        for result in results:
            # Score combines time and success probability (lower is better)
            time_score = result.total_time
            success_penalty = (1.0 - result.success_probability) * 50.0
            score = time_score + success_penalty
            
            if score < best_score:
                best_score = score
                best_result = result
        
        return best_result
    
    def get_simulation_stats(self) -> Dict[str, Any]:
        """Get simulation statistics."""
        return {
            "total_simulations": len(self.simulation_history),
            "last_simulation_time_ms": self.last_simulation_time * 1000 if self.last_simulation_time else 0,
            "simulation_count_per_run": self.simulation_count,
            "last_simulation": self.simulation_history[-1] if self.simulation_history else None
        }


# Global instance
_monte_carlo_handler: Optional[MonteCarloHandler] = None


def get_monte_carlo_handler() -> MonteCarloHandler:
    """Get the global Monte Carlo handler instance."""
    global _monte_carlo_handler
    if _monte_carlo_handler is None:
        _monte_carlo_handler = MonteCarloHandler()
    return _monte_carlo_handler
