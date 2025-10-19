"""
HPC Orchestrator for the F1 Dual Twin System.

This module orchestrates the Field Twin component and manages integration
with external HPC simulation systems for strategic analysis.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

from field_twin import FieldTwin
from interfaces import TwinModelError
from utils.config import get_config


class HPCOrchestrator:
    """
    Orchestrates Field Twin operations and HPC simulation integration.
    
    Manages the Field Twin lifecycle, coordinates with external simulation systems,
    and provides high-level strategic analysis capabilities.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize HPC Orchestrator.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.field_twin = FieldTwin()
        self.config_path = config_path
        
        # Simulation integration settings
        self.hpc_enabled = get_config("hpc.enabled", False)
        self.simulation_endpoint = get_config("hpc.simulation_endpoint", "http://localhost:8080")
        self.max_concurrent_simulations = get_config("hpc.max_concurrent", 3)
        
        # Performance tracking
        self.update_count = 0
        self.last_update_time = None
        self.performance_metrics = {
            "total_updates": 0,
            "avg_update_time_ms": 0.0,
            "simulation_requests": 0,
            "simulation_successes": 0
        }
        
        # State persistence
        self.state_file = Path("shared/field_twin_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Load previous state if available
        self._load_previous_state()
    
    def update_field_twin(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Update Field Twin with new telemetry data.
        
        Args:
            telemetry_data: Normalized telemetry data
            
        Raises:
            TwinModelError: If update fails
        """
        start_time = time.time()
        
        try:
            # Update Field Twin state
            self.field_twin.update_state(telemetry_data)
            
            # Update performance metrics
            update_time_ms = (time.time() - start_time) * 1000
            self._update_performance_metrics(update_time_ms)
            
            # Persist state
            self._persist_state()
            
            # Check for simulation triggers
            self._check_simulation_triggers()
            
            self.update_count += 1
            self.last_update_time = datetime.now(timezone.utc)
            
        except Exception as e:
            raise TwinModelError(f"Failed to update Field Twin: {str(e)}")
    
    def get_field_twin_state(self) -> Dict[str, Any]:
        """
        Get current Field Twin state.
        
        Returns:
            Field Twin state dictionary
        """
        return self.field_twin.get_current_state()
    
    def get_strategic_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive strategic analysis.
        
        Returns:
            Strategic analysis including opportunities, threats, and recommendations
        """
        field_state = self.field_twin.get_current_state()
        
        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "competitor_summary": self._generate_competitor_summary(),
            "strategic_opportunities": field_state.get("strategic_opportunities", []),
            "threat_assessment": self._assess_threats(),
            "strategic_recommendations": self._generate_recommendations(),
            "race_situation": self._analyze_race_situation(),
            "performance_metrics": self.performance_metrics.copy()
        }
        
        return analysis
    
    def predict_competitor_behavior(self, car_id: str, horizon_seconds: int) -> Dict[str, Any]:
        """
        Predict specific competitor behavior.
        
        Args:
            car_id: Target competitor car ID
            horizon_seconds: Prediction time horizon
            
        Returns:
            Competitor behavior predictions
        """
        competitor = self.field_twin.get_competitor(car_id)
        if not competitor:
            raise ValueError(f"Competitor {car_id} not found")
        
        predictions = self.field_twin.predict(horizon_seconds)
        competitor_pred = predictions.get("predictions", {}).get("competitor_predictions", {}).get(car_id, {})
        
        return {
            "car_id": car_id,
            "prediction_horizon": horizon_seconds,
            "behavioral_predictions": competitor_pred,
            "strategic_context": {
                "current_threat_level": competitor.strategic_threat_level,
                "pit_probability": competitor.pit_probability,
                "behavioral_profile": competitor.behavioral_profile
            },
            "confidence_factors": self._calculate_prediction_confidence(competitor)
        }
    
    def trigger_strategic_simulation(self, scenario: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger HPC strategic simulation.
        
        Args:
            scenario: Simulation scenario type
            parameters: Simulation parameters
            
        Returns:
            Simulation results or status
        """
        if not self.hpc_enabled:
            return {"status": "disabled", "message": "HPC simulation not enabled"}
        
        simulation_request = {
            "scenario": scenario,
            "parameters": parameters,
            "field_twin_state": self.field_twin.get_current_state(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": f"sim_{int(time.time())}"
        }
        
        try:
            # In a real implementation, this would make HTTP requests to HPC system
            result = self._mock_simulation_request(simulation_request)
            
            self.performance_metrics["simulation_requests"] += 1
            if result.get("status") == "success":
                self.performance_metrics["simulation_successes"] += 1
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Simulation failed: {str(e)}",
                "request_id": simulation_request["request_id"]
            }
    
    def _generate_competitor_summary(self) -> Dict[str, Any]:
        """Generate summary of competitor states."""
        competitors = self.field_twin.competitors
        
        summary = {
            "total_competitors": len(competitors),
            "threat_levels": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "pit_probabilities": [],
            "strategic_patterns": {},
            "active_strategies": {}
        }
        
        for competitor in competitors.values():
            # Count threat levels
            threat_level = competitor.strategic_threat_level
            summary["threat_levels"][threat_level] += 1
            
            # Collect pit probabilities
            summary["pit_probabilities"].append({
                "car_id": competitor.car_id,
                "probability": competitor.pit_probability
            })
            
            # Analyze strategic patterns
            strategy = competitor.predicted_strategy
            if strategy not in summary["active_strategies"]:
                summary["active_strategies"][strategy] = 0
            summary["active_strategies"][strategy] += 1
            
            # Behavioral patterns
            for behavior, value in competitor.behavioral_profile.items():
                if behavior not in summary["strategic_patterns"]:
                    summary["strategic_patterns"][behavior] = []
                summary["strategic_patterns"][behavior].append(value)
        
        # Calculate averages for behavioral patterns
        for behavior, values in summary["strategic_patterns"].items():
            summary["strategic_patterns"][behavior] = {
                "average": sum(values) / len(values) if values else 0.0,
                "min": min(values) if values else 0.0,
                "max": max(values) if values else 0.0
            }
        
        return summary
    
    def _assess_threats(self) -> Dict[str, Any]:
        """Assess strategic threats from competitors."""
        threats = {
            "immediate_threats": [],
            "emerging_threats": [],
            "strategic_risks": [],
            "overall_risk_level": "low"
        }
        
        high_threat_count = 0
        
        for competitor in self.field_twin.competitors.values():
            threat_data = {
                "car_id": competitor.car_id,
                "team": competitor.team,
                "threat_level": competitor.strategic_threat_level,
                "pit_probability": competitor.pit_probability,
                "position": competitor.current_position
            }
            
            if competitor.strategic_threat_level == "critical":
                threats["immediate_threats"].append(threat_data)
                high_threat_count += 2
            elif competitor.strategic_threat_level == "high":
                threats["immediate_threats"].append(threat_data)
                high_threat_count += 1
            elif competitor.strategic_threat_level == "medium" and competitor.pit_probability > 0.6:
                threats["emerging_threats"].append(threat_data)
            
            # Strategic risks
            if (competitor.behavioral_profile["undercut_tendency"] > 0.7 and 
                competitor.pit_probability > 0.4):
                threats["strategic_risks"].append({
                    "type": "undercut_risk",
                    "car_id": competitor.car_id,
                    "probability": competitor.pit_probability * competitor.behavioral_profile["undercut_tendency"]
                })
        
        # Determine overall risk level
        if high_threat_count >= 3:
            threats["overall_risk_level"] = "critical"
        elif high_threat_count >= 2:
            threats["overall_risk_level"] = "high"
        elif high_threat_count >= 1 or len(threats["emerging_threats"]) > 2:
            threats["overall_risk_level"] = "medium"
        
        return threats
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate strategic recommendations."""
        recommendations = []
        
        # Analyze opportunities
        opportunities = self.field_twin.get_strategic_opportunities()
        for opp in opportunities[:3]:  # Top 3 opportunities
            if opp["probability"] > 0.6:
                recommendations.append({
                    "type": "opportunity",
                    "priority": "high" if opp["probability"] > 0.8 else "medium",
                    "action": f"Consider {opp['type']} against {opp['target_car']}",
                    "timing": f"Execute on lap {opp['execution_lap']}",
                    "success_probability": opp["probability"],
                    "reasoning": opp.get("reasoning", "Strategic opportunity detected")
                })
        
        # Analyze threats and defensive recommendations
        threats = self._assess_threats()
        if threats["overall_risk_level"] in ["high", "critical"]:
            recommendations.append({
                "type": "defensive",
                "priority": "high",
                "action": "Prepare defensive strategy",
                "timing": "Immediate",
                "reasoning": f"Multiple threats detected ({len(threats['immediate_threats'])} immediate)"
            })
        
        # Pit strategy recommendations
        field_state = self.field_twin.get_current_state()
        race_context = field_state.get("race_context", {})
        current_lap = race_context.get("current_lap", 0)
        
        high_pit_prob_competitors = [
            comp for comp in self.field_twin.competitors.values()
            if comp.pit_probability > 0.7
        ]
        
        if len(high_pit_prob_competitors) >= 2:
            recommendations.append({
                "type": "strategic",
                "priority": "medium",
                "action": "Monitor pit window closely",
                "timing": f"Next 3-5 laps (laps {current_lap + 1}-{current_lap + 5})",
                "reasoning": f"{len(high_pit_prob_competitors)} competitors likely to pit soon"
            })
        
        return recommendations
    
    def _analyze_race_situation(self) -> Dict[str, Any]:
        """Analyze overall race situation."""
        field_state = self.field_twin.get_current_state()
        race_context = field_state.get("race_context", {})
        
        situation = {
            "race_phase": self._determine_race_phase(race_context),
            "strategic_complexity": self._assess_strategic_complexity(),
            "key_factors": self._identify_key_factors(),
            "race_dynamics": self._analyze_race_dynamics()
        }
        
        return situation
    
    def _determine_race_phase(self, race_context: Dict[str, Any]) -> str:
        """Determine current race phase."""
        current_lap = race_context.get("current_lap", 0)
        total_laps = race_context.get("total_laps", 50)
        
        progress = current_lap / total_laps if total_laps > 0 else 0
        
        if progress < 0.3:
            return "opening"
        elif progress < 0.7:
            return "middle"
        else:
            return "closing"
    
    def _assess_strategic_complexity(self) -> str:
        """Assess strategic complexity of current situation."""
        opportunities = len(self.field_twin.get_strategic_opportunities())
        threats = len([c for c in self.field_twin.competitors.values() 
                      if c.strategic_threat_level in ["high", "critical"]])
        
        complexity_score = opportunities + threats * 2
        
        if complexity_score >= 8:
            return "very_high"
        elif complexity_score >= 5:
            return "high"
        elif complexity_score >= 3:
            return "medium"
        else:
            return "low"
    
    def _identify_key_factors(self) -> List[str]:
        """Identify key factors affecting strategy."""
        factors = []
        
        # Track status
        field_state = self.field_twin.get_current_state()
        race_context = field_state.get("race_context", {})
        track_status = race_context.get("track_status", "green")
        
        if track_status != "green":
            factors.append(f"track_status_{track_status}")
        
        # Pit window activity
        high_pit_prob = sum(1 for c in self.field_twin.competitors.values() if c.pit_probability > 0.6)
        if high_pit_prob >= 3:
            factors.append("active_pit_window")
        
        # Strategic threats
        high_threats = sum(1 for c in self.field_twin.competitors.values() 
                          if c.strategic_threat_level in ["high", "critical"])
        if high_threats >= 2:
            factors.append("multiple_strategic_threats")
        
        # Tire strategy diversity
        strategies = set(c.predicted_strategy for c in self.field_twin.competitors.values())
        if len(strategies) >= 3:
            factors.append("diverse_tire_strategies")
        
        return factors
    
    def _analyze_race_dynamics(self) -> Dict[str, Any]:
        """Analyze race dynamics and trends."""
        return {
            "position_volatility": self._calculate_position_volatility(),
            "strategic_activity": self._measure_strategic_activity(),
            "competitive_pressure": self._assess_competitive_pressure()
        }
    
    def _calculate_position_volatility(self) -> float:
        """Calculate position volatility metric."""
        # Simplified calculation - in reality would use historical position data
        position_changes = 0
        for competitor in self.field_twin.competitors.values():
            if len(competitor.position_history) >= 2:
                recent_positions = list(competitor.position_history)[-5:]
                for i in range(1, len(recent_positions)):
                    if recent_positions[i]["position"] != recent_positions[i-1]["position"]:
                        position_changes += 1
        
        return min(1.0, position_changes / (len(self.field_twin.competitors) * 2))
    
    def _measure_strategic_activity(self) -> float:
        """Measure strategic activity level."""
        recent_pit_stops = sum(1 for c in self.field_twin.competitors.values() 
                              if len(c.pit_stops) > 0 and 
                              (datetime.now(timezone.utc) - c.pit_stops[-1]["timestamp"]).seconds < 300)
        
        high_pit_prob = sum(1 for c in self.field_twin.competitors.values() if c.pit_probability > 0.5)
        
        activity_score = (recent_pit_stops * 0.3) + (high_pit_prob * 0.1)
        return min(1.0, activity_score)
    
    def _assess_competitive_pressure(self) -> float:
        """Assess competitive pressure level."""
        close_competitors = sum(1 for c in self.field_twin.competitors.values() 
                               if abs(c.gap_to_leader - self.field_twin.our_gap_to_leader) < 10.0)
        
        threat_level_scores = {"low": 0.1, "medium": 0.3, "high": 0.6, "critical": 1.0}
        threat_pressure = sum(threat_level_scores.get(c.strategic_threat_level, 0) 
                             for c in self.field_twin.competitors.values())
        
        pressure_score = (close_competitors * 0.1) + (threat_pressure * 0.1)
        return min(1.0, pressure_score)
    
    def _calculate_prediction_confidence(self, competitor) -> Dict[str, float]:
        """Calculate prediction confidence factors."""
        return {
            "data_quality": min(1.0, len(competitor.lap_times_history) / 10.0),
            "behavioral_consistency": competitor.behavioral_profile["tire_management"],
            "historical_accuracy": 0.8,  # Would be calculated from past predictions
            "situational_stability": 1.0 - competitor.pit_probability
        }
    
    def _check_simulation_triggers(self) -> None:
        """Check if conditions warrant triggering HPC simulation."""
        if not self.hpc_enabled:
            return
        
        # Check for high-priority strategic opportunities
        opportunities = self.field_twin.get_strategic_opportunities()
        high_value_opportunities = [opp for opp in opportunities if opp["probability"] > 0.8]
        
        if len(high_value_opportunities) > 0:
            self.trigger_strategic_simulation("opportunity_analysis", {
                "opportunities": high_value_opportunities,
                "trigger_reason": "high_probability_opportunities"
            })
        
        # Check for critical threats
        critical_threats = [c for c in self.field_twin.competitors.values() 
                           if c.strategic_threat_level == "critical"]
        
        if len(critical_threats) >= 2:
            self.trigger_strategic_simulation("threat_response", {
                "threats": [c.car_id for c in critical_threats],
                "trigger_reason": "multiple_critical_threats"
            })
    
    def _mock_simulation_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Mock HPC simulation request for testing."""
        # Simulate processing time
        time.sleep(0.1)
        
        return {
            "status": "success",
            "request_id": request["request_id"],
            "simulation_results": {
                "scenario": request["scenario"],
                "confidence": 0.85,
                "recommendations": ["Mock recommendation 1", "Mock recommendation 2"],
                "execution_time_ms": 100
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _persist_state(self) -> None:
        """Persist Field Twin state to file."""
        try:
            state_data = {
                "field_twin_state": self.field_twin.get_current_state(),
                "orchestrator_metrics": self.performance_metrics,
                "last_update": self.last_update_time.isoformat() if self.last_update_time else None,
                "update_count": self.update_count
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Warning: Failed to persist Field Twin state: {e}")
    
    def _load_previous_state(self) -> None:
        """Load previous Field Twin state if available."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                
                # Restore orchestrator metrics
                self.performance_metrics.update(state_data.get("orchestrator_metrics", {}))
                self.update_count = state_data.get("update_count", 0)
                
                print(f"Loaded previous Field Twin state with {self.update_count} updates")
                
        except Exception as e:
            print(f"Warning: Failed to load previous state: {e}")
    
    def _update_performance_metrics(self, update_time_ms: float) -> None:
        """Update performance metrics."""
        self.performance_metrics["total_updates"] += 1
        
        # Calculate running average
        total = self.performance_metrics["total_updates"]
        current_avg = self.performance_metrics["avg_update_time_ms"]
        new_avg = ((current_avg * (total - 1)) + update_time_ms) / total
        self.performance_metrics["avg_update_time_ms"] = new_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics."""
        return {
            **self.performance_metrics,
            "field_twin_metrics": self.field_twin.get_performance_metrics(),
            "competitor_count": self.field_twin.get_competitor_count(),
            "last_update": self.last_update_time.isoformat() if self.last_update_time else None
        }