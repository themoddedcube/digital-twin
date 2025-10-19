"""
Field Twin implementation for competitor modeling and strategic analysis.

This module implements the Field Twin component that tracks competitor behavior,
analyzes strategic patterns, and identifies opportunities for strategic advantage.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, deque

from base_twin import BaseTwinModel
from interfaces import TwinModelError
from utils.config import get_config


class CompetitorModel:
    """
    Individual competitor behavior model.
    
    Tracks state, strategy patterns, and behavioral tendencies for a single competitor.
    """
    
    def __init__(self, car_id: str, team: str, driver: str):
        """
        Initialize competitor model.
        
        Args:
            car_id: Unique car identifier
            team: Team name
            driver: Driver name
        """
        self.car_id = car_id
        self.team = team
        self.driver = driver
        
        # Current state
        self.current_position = 0
        self.gap_to_leader = 0.0
        self.speed = 0.0
        self.tire_compound = "medium"
        self.tire_age = 0
        self.tire_wear = 0.0
        self.fuel_level = 1.0
        self.last_lap_time = 0.0
        
        # Pit history and strategy tracking
        self.pit_stops: List[Dict[str, Any]] = []
        self.strategy_pattern = "unknown"
        self.predicted_strategy = "two_stop"
        
        # Behavioral profile
        self.behavioral_profile = {
            "undercut_tendency": 0.5,
            "aggressive_defense": 0.5,
            "tire_management": 0.5
        }
        
        # Historical data for pattern analysis
        self.lap_times_history = deque(maxlen=20)  # Last 20 laps
        self.position_history = deque(maxlen=50)   # Last 50 position updates
        self.tire_strategy_history: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.performance_baseline = 0.0
        self.degradation_rate = 0.008
        self.fuel_consumption_rate = 2.1
        
        # Strategic analysis
        self.pit_probability = 0.0
        self.strategic_threat_level = "medium"
        self.last_update = datetime.now(timezone.utc)
    
    def update_state(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Update competitor state from telemetry data.
        
        Args:
            telemetry_data: Telemetry data for this competitor
        """
        # Update basic state
        self.current_position = telemetry_data.get("position", self.current_position)
        self.speed = telemetry_data.get("speed", self.speed)
        self.last_lap_time = telemetry_data.get("lap_time", self.last_lap_time)
        
        # Update tire information
        tire_data = telemetry_data.get("tire", {})
        self.tire_compound = tire_data.get("compound", self.tire_compound)
        self.tire_age = tire_data.get("age", self.tire_age)
        self.tire_wear = tire_data.get("wear_level", self.tire_wear)
        
        # Update fuel level
        self.fuel_level = telemetry_data.get("fuel_level", self.fuel_level)
        
        # Track historical data
        if self.last_lap_time > 0:
            self.lap_times_history.append({
                "lap_time": self.last_lap_time,
                "tire_age": self.tire_age,
                "tire_compound": self.tire_compound,
                "timestamp": datetime.now(timezone.utc)
            })
        
        self.position_history.append({
            "position": self.current_position,
            "timestamp": datetime.now(timezone.utc)
        })
        
        # Detect pit stops
        self._detect_pit_stop(telemetry_data)
        
        # Update behavioral analysis
        self._update_behavioral_profile()
        
        self.last_update = datetime.now(timezone.utc)
    
    def _detect_pit_stop(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Detect if competitor has made a pit stop.
        
        Args:
            telemetry_data: Current telemetry data
        """
        # Check for tire age reset (indicates pit stop)
        tire_data = telemetry_data.get("tire", {})
        new_tire_age = tire_data.get("age", self.tire_age)
        
        if new_tire_age < self.tire_age and self.tire_age > 5:
            # Pit stop detected
            pit_stop = {
                "lap": telemetry_data.get("lap", 0),
                "timestamp": datetime.now(timezone.utc),
                "old_tire_compound": self.tire_compound,
                "new_tire_compound": tire_data.get("compound", "medium"),
                "old_tire_age": self.tire_age,
                "position_before": self.current_position,
                "position_after": telemetry_data.get("position", self.current_position)
            }
            
            self.pit_stops.append(pit_stop)
            
            # Analyze pit stop strategy
            self._analyze_pit_strategy(pit_stop)
    
    def _analyze_pit_strategy(self, pit_stop: Dict[str, Any]) -> None:
        """
        Analyze pit stop for strategic patterns.
        
        Args:
            pit_stop: Pit stop data
        """
        # Determine if this was an undercut or overcut attempt
        position_change = pit_stop["position_after"] - pit_stop["position_before"]
        
        if position_change < 0:  # Gained positions
            strategy_type = "undercut"
            self.behavioral_profile["undercut_tendency"] = min(1.0, 
                self.behavioral_profile["undercut_tendency"] + 0.1)
        elif position_change > 2:  # Lost significant positions
            strategy_type = "overcut"
        else:
            strategy_type = "standard"
        
        # Update strategy pattern
        self.tire_strategy_history.append({
            "pit_stop": pit_stop,
            "strategy_type": strategy_type,
            "tire_compound_choice": pit_stop["new_tire_compound"]
        })
        
        # Update predicted strategy based on pit count
        pit_count = len(self.pit_stops)
        if pit_count == 0:
            self.predicted_strategy = "two_stop"
        elif pit_count == 1:
            # Analyze timing to predict if one-stop or two-stop
            lap = pit_stop["lap"]
            if lap > 35:  # Late pit suggests one-stop
                self.predicted_strategy = "one_stop"
            else:
                self.predicted_strategy = "two_stop"
        elif pit_count == 2:
            self.predicted_strategy = "three_stop"
        else:
            self.predicted_strategy = "unknown"
    
    def _update_behavioral_profile(self) -> None:
        """Update behavioral profile based on recent actions."""
        if len(self.lap_times_history) < 5:
            return
        
        # Analyze tire management from lap time consistency
        recent_times = [entry["lap_time"] for entry in list(self.lap_times_history)[-10:]]
        if len(recent_times) >= 5:
            time_variance = max(recent_times) - min(recent_times)
            # Lower variance indicates better tire management
            tire_mgmt_score = max(0.0, 1.0 - (time_variance / 5.0))
            self.behavioral_profile["tire_management"] = (
                self.behavioral_profile["tire_management"] * 0.8 + tire_mgmt_score * 0.2
            )
        
        # Analyze defensive behavior from position changes
        if len(self.position_history) >= 10:
            position_changes = []
            positions = list(self.position_history)[-10:]
            for i in range(1, len(positions)):
                change = positions[i]["position"] - positions[i-1]["position"]
                position_changes.append(abs(change))
            
            avg_position_change = sum(position_changes) / len(position_changes)
            # Higher position volatility suggests more aggressive racing
            aggression_score = min(1.0, avg_position_change / 2.0)
            self.behavioral_profile["aggressive_defense"] = (
                self.behavioral_profile["aggressive_defense"] * 0.9 + aggression_score * 0.1
            )
    
    def calculate_pit_probability(self, current_lap: int, total_laps: int) -> float:
        """
        Calculate probability of pitting in next 5 laps.
        
        Args:
            current_lap: Current race lap
            total_laps: Total race laps
            
        Returns:
            Pit probability (0.0 to 1.0)
        """
        # Base probability on tire age and wear
        tire_factor = min(1.0, (self.tire_age / 25.0) + (self.tire_wear * 0.5))
        
        # Strategy-based probability
        strategy_factor = 0.0
        if self.predicted_strategy == "two_stop" and len(self.pit_stops) == 0:
            # First pit window for two-stop
            if 15 <= current_lap <= 25:
                strategy_factor = 0.7
            elif 26 <= current_lap <= 35:
                strategy_factor = 0.4
        elif self.predicted_strategy == "two_stop" and len(self.pit_stops) == 1:
            # Second pit window for two-stop
            if 35 <= current_lap <= 45:
                strategy_factor = 0.8
        elif self.predicted_strategy == "one_stop" and len(self.pit_stops) == 0:
            # Single pit window
            if 25 <= current_lap <= 40:
                strategy_factor = 0.6
        
        # Fuel factor
        fuel_factor = max(0.0, 1.0 - (self.fuel_level / 0.3))  # High probability if fuel < 30%
        
        # Combine factors
        probability = min(1.0, tire_factor * 0.4 + strategy_factor * 0.4 + fuel_factor * 0.2)
        
        self.pit_probability = probability
        return probability
    
    def assess_strategic_threat(self, our_position: int, our_gap: float) -> str:
        """
        Assess strategic threat level to our car.
        
        Args:
            our_position: Our current position
            our_gap: Our gap to this competitor (negative if behind)
            
        Returns:
            Threat level: "low", "medium", "high", "critical"
        """
        # Position-based threat
        position_diff = abs(self.current_position - our_position)
        
        if position_diff > 3:
            threat = "low"
        elif position_diff > 1:
            threat = "medium"
        else:
            # Close positions - analyze gap and strategy
            if abs(our_gap) < 5.0:  # Within 5 seconds
                if self.pit_probability > 0.6:
                    threat = "high"  # Likely to pit and affect our strategy
                elif self.behavioral_profile["undercut_tendency"] > 0.7:
                    threat = "high"  # Aggressive strategic behavior
                else:
                    threat = "medium"
            elif abs(our_gap) < 15.0:  # Within pit window
                threat = "medium"
            else:
                threat = "low"
        
        # Upgrade threat if competitor is on fresher tires
        if self.tire_age < 5 and threat in ["low", "medium"]:
            threat = "medium" if threat == "low" else "high"
        
        self.strategic_threat_level = threat
        return threat
    
    def get_state_dict(self) -> Dict[str, Any]:
        """
        Get competitor state as dictionary.
        
        Returns:
            Competitor state dictionary
        """
        return {
            "car_id": self.car_id,
            "team": self.team,
            "driver": self.driver,
            "current_position": self.current_position,
            "gap_to_leader": self.gap_to_leader,
            "predicted_strategy": self.predicted_strategy,
            "pit_probability": self.pit_probability,
            "strategic_threat_level": self.strategic_threat_level,
            "behavioral_profile": self.behavioral_profile.copy(),
            "current_state": {
                "speed": self.speed,
                "tire_compound": self.tire_compound,
                "tire_age": self.tire_age,
                "tire_wear": self.tire_wear,
                "fuel_level": self.fuel_level,
                "last_lap_time": self.last_lap_time
            },
            "pit_stops_count": len(self.pit_stops),
            "performance_metrics": {
                "degradation_rate": self.degradation_rate,
                "fuel_consumption_rate": self.fuel_consumption_rate,
                "performance_baseline": self.performance_baseline
            }
        }


class FieldTwin(BaseTwinModel):
    """
    Field Twin implementation for competitor modeling and strategic analysis.
    
    Manages multiple competitor models and provides strategic opportunity detection.
    """
    
    def __init__(self, twin_id: str = "field_twin"):
        """
        Initialize Field Twin.
        
        Args:
            twin_id: Unique identifier for this twin instance
        """
        super().__init__(twin_id, "field_twin")
        
        # Competitor models
        self.competitors: Dict[str, CompetitorModel] = {}
        
        # Race context
        self.current_lap = 0
        self.total_laps = 50  # Default, updated from telemetry
        self.session_type = "race"
        self.track_status = "green"
        
        # Strategic analysis
        self.strategic_opportunities: List[Dict[str, Any]] = []
        self.race_events: List[Dict[str, Any]] = []
        
        # Our car reference (for strategic analysis)
        self.our_car_id = get_config("car.our_car_id", "44")
        self.our_position = 1
        self.our_gap_to_leader = 0.0
        
        # Performance tracking
        self.last_opportunity_scan = datetime.now(timezone.utc)
        self.opportunity_scan_interval = timedelta(seconds=15)  # Scan every 15 seconds
    
    def _update_internal_state(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Update Field Twin state based on telemetry data.
        
        Args:
            telemetry_data: Normalized telemetry data
        """
        # Update internal state dictionary for base class
        self._state.update({
            "telemetry_data": telemetry_data,
            "last_update": datetime.now(timezone.utc).isoformat()
        })
        
        # Update race context
        self.current_lap = telemetry_data.get("lap", self.current_lap)
        self.session_type = telemetry_data.get("session_type", self.session_type)
        
        track_conditions = telemetry_data.get("track_conditions", {})
        self.track_status = track_conditions.get("track_status", self.track_status)
        
        # Process car data
        cars_data = telemetry_data.get("cars", [])
        
        # Find our car and update reference
        for car_data in cars_data:
            car_id = car_data.get("car_id")
            if car_id == self.our_car_id:
                self.our_position = car_data.get("position", self.our_position)
                # Calculate gap to leader
                leader_cars = [car for car in cars_data if car.get("position") == 1]
                if leader_cars:
                    leader_time = leader_cars[0].get("lap_time", 0)
                    our_time = car_data.get("lap_time", leader_time)
                    self.our_gap_to_leader = our_time - leader_time
                else:
                    self.our_gap_to_leader = 0.0
        
        # Update competitor models
        for car_data in cars_data:
            car_id = car_data.get("car_id")
            if car_id and car_id != self.our_car_id:
                self._update_competitor(car_data)
        
        # Detect race events
        self._detect_race_events(telemetry_data)
        
        # Update strategic opportunities
        if (datetime.now(timezone.utc) - self.last_opportunity_scan) > self.opportunity_scan_interval:
            self._scan_strategic_opportunities()
            self.last_opportunity_scan = datetime.now(timezone.utc)
    
    def _update_competitor(self, car_data: Dict[str, Any]) -> None:
        """
        Update or create competitor model.
        
        Args:
            car_data: Telemetry data for a competitor car
        """
        car_id = car_data.get("car_id")
        
        # Create competitor model if it doesn't exist
        if car_id not in self.competitors:
            self.competitors[car_id] = CompetitorModel(
                car_id=car_id,
                team=car_data.get("team", "Unknown"),
                driver=car_data.get("driver", "Unknown")
            )
        
        # Update competitor state
        competitor = self.competitors[car_id]
        competitor.update_state(car_data)
        
        # Calculate gap to leader
        if car_data.get("position") == 1:
            competitor.gap_to_leader = 0.0
        else:
            # Simplified gap calculation - in reality would use timing data
            position_diff = car_data.get("position", 1) - 1
            competitor.gap_to_leader = position_diff * 1.5  # Rough estimate
        
        # Update pit probability and threat assessment
        competitor.calculate_pit_probability(self.current_lap, self.total_laps)
        competitor.assess_strategic_threat(self.our_position, 
                                         competitor.gap_to_leader - self.our_gap_to_leader)
    
    def _detect_race_events(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Detect significant race events that affect strategy.
        
        Args:
            telemetry_data: Current telemetry data
        """
        track_conditions = telemetry_data.get("track_conditions", {})
        current_status = track_conditions.get("track_status", "green")
        
        # Detect track status changes
        if current_status != self.track_status:
            event = {
                "type": "track_status_change",
                "timestamp": datetime.now(timezone.utc),
                "lap": self.current_lap,
                "old_status": self.track_status,
                "new_status": current_status
            }
            self.race_events.append(event)
            
            # Safety car events trigger re-simulation
            if current_status in ["safety_car", "virtual_safety_car"]:
                self._trigger_resimulation("safety_car", event)
        
        # Detect pit stops (already handled in competitor models)
        for competitor in self.competitors.values():
            if len(competitor.pit_stops) > 0:
                last_pit = competitor.pit_stops[-1]
                # Check if this is a new pit stop (within last update cycle)
                if (datetime.now(timezone.utc) - last_pit["timestamp"]).seconds < 10:
                    event = {
                        "type": "competitor_pit_stop",
                        "timestamp": last_pit["timestamp"],
                        "lap": last_pit["lap"],
                        "car_id": competitor.car_id,
                        "pit_data": last_pit
                    }
                    self.race_events.append(event)
                    self._trigger_resimulation("pit_stop", event)
    
    def _trigger_resimulation(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Trigger re-simulation for significant race events.
        
        Args:
            event_type: Type of event that triggered re-simulation
            event_data: Event data
        """
        # Log the re-simulation trigger
        resim_event = {
            "type": "resimulation_triggered",
            "timestamp": datetime.now(timezone.utc),
            "trigger_event": event_type,
            "event_data": event_data,
            "lap": self.current_lap,
            "strategic_impact": self._assess_event_strategic_impact(event_type, event_data)
        }
        self.race_events.append(resim_event)
        
        # Update strategic opportunities based on the event
        self._update_opportunities_for_event(event_type, event_data)
        
        # In a full implementation, this would trigger the HPC simulation system
        print(f"Re-simulation triggered by {event_type} at lap {self.current_lap}")
    
    def _assess_event_strategic_impact(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """
        Assess the strategic impact of a race event.
        
        Args:
            event_type: Type of race event
            event_data: Event data
            
        Returns:
            Impact level: "low", "medium", "high", "critical"
        """
        if event_type == "safety_car":
            # Safety car always has high impact
            return "critical"
        
        elif event_type == "pit_stop":
            car_id = event_data.get("car_id")
            if car_id in self.competitors:
                competitor = self.competitors[car_id]
                if competitor.strategic_threat_level in ["high", "critical"]:
                    return "high"
                elif competitor.strategic_threat_level == "medium":
                    return "medium"
            return "low"
        
        elif event_type == "track_status_change":
            new_status = event_data.get("new_status", "green")
            if new_status in ["safety_car", "virtual_safety_car", "red"]:
                return "critical"
            elif new_status == "yellow":
                return "medium"
            return "low"
        
        return "medium"
    
    def _update_opportunities_for_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Update strategic opportunities based on race events.
        
        Args:
            event_type: Type of race event
            event_data: Event data
        """
        if event_type == "safety_car":
            # Safety car creates pit window opportunities
            safety_car_opportunity = {
                "type": "safety_car_opportunity",
                "target_car": "field",
                "probability": 0.9,
                "execution_lap": self.current_lap,
                "reasoning": "Safety car pit window - free pit stop opportunity"
            }
            self.strategic_opportunities.insert(0, safety_car_opportunity)
        
        elif event_type == "pit_stop":
            car_id = event_data.get("car_id")
            if car_id in self.competitors:
                competitor = self.competitors[car_id]
                
                # Create undercut response opportunity
                if competitor.strategic_threat_level in ["medium", "high", "critical"]:
                    response_opportunity = {
                        "type": "pit_response",
                        "target_car": car_id,
                        "probability": 0.7,
                        "execution_lap": self.current_lap + 1,
                        "reasoning": f"Response to {car_id} pit stop - maintain track position"
                    }
                    self.strategic_opportunities.insert(0, response_opportunity)
        
        # Remove outdated opportunities
        current_lap = self.current_lap
        self.strategic_opportunities = [
            opp for opp in self.strategic_opportunities
            if opp["execution_lap"] >= current_lap
        ]
    
    def handle_safety_car_deployment(self) -> Dict[str, Any]:
        """
        Handle safety car deployment and update strategic analysis.
        
        Returns:
            Safety car strategic analysis
        """
        analysis = {
            "deployment_lap": self.current_lap,
            "strategic_implications": [],
            "pit_window_analysis": {},
            "position_shuffle_prediction": {},
            "recommended_actions": []
        }
        
        # Analyze pit window implications
        competitors_on_old_tires = []
        competitors_on_fresh_tires = []
        
        for competitor in self.competitors.values():
            if competitor.tire_age > 15:
                competitors_on_old_tires.append(competitor.car_id)
            elif competitor.tire_age < 5:
                competitors_on_fresh_tires.append(competitor.car_id)
        
        analysis["pit_window_analysis"] = {
            "free_pit_stop_available": True,
            "competitors_likely_to_pit": competitors_on_old_tires,
            "competitors_likely_to_stay": competitors_on_fresh_tires,
            "strategic_advantage": "high" if len(competitors_on_old_tires) > 3 else "medium"
        }
        
        # Strategic implications
        if len(competitors_on_old_tires) > len(competitors_on_fresh_tires):
            analysis["strategic_implications"].append("Majority will pit - consider staying out for track position")
        else:
            analysis["strategic_implications"].append("Minority will pit - good opportunity for fresh tires")
        
        # Recommended actions
        analysis["recommended_actions"] = [
            "Evaluate tire condition vs field",
            "Consider fuel level for extended stint",
            "Prepare for restart positioning"
        ]
        
        return analysis
    
    def handle_competitor_pit_stop(self, car_id: str, pit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle competitor pit stop and analyze strategic implications.
        
        Args:
            car_id: Competitor car ID
            pit_data: Pit stop data
            
        Returns:
            Strategic analysis of the pit stop
        """
        if car_id not in self.competitors:
            return {"error": "Competitor not found"}
        
        competitor = self.competitors[car_id]
        
        analysis = {
            "car_id": car_id,
            "pit_lap": pit_data.get("lap", self.current_lap),
            "strategic_type": "unknown",
            "implications": [],
            "response_options": [],
            "threat_level_change": "none"
        }
        
        # Determine strategic type
        old_tire_age = pit_data.get("old_tire_age", 0)
        position_before = pit_data.get("position_before", competitor.current_position)
        position_after = pit_data.get("position_after", competitor.current_position)
        
        if old_tire_age < 10:
            analysis["strategic_type"] = "early_aggressive"
            analysis["implications"].append("Aggressive undercut attempt")
        elif old_tire_age > 20:
            analysis["strategic_type"] = "forced_degradation"
            analysis["implications"].append("Forced by tire degradation")
        else:
            analysis["strategic_type"] = "strategic_window"
            analysis["implications"].append("Planned strategic pit stop")
        
        # Analyze position change
        position_change = position_after - position_before
        if position_change < -1:
            analysis["implications"].append("Significant position gain - successful undercut")
            analysis["threat_level_change"] = "increased"
        elif position_change > 2:
            analysis["implications"].append("Position loss - poor pit timing or execution")
            analysis["threat_level_change"] = "decreased"
        
        # Generate response options
        if competitor.strategic_threat_level in ["medium", "high", "critical"]:
            if analysis["strategic_type"] == "early_aggressive":
                analysis["response_options"] = [
                    "Immediate counter-pit to cover undercut",
                    "Extend stint for overcut opportunity",
                    "Monitor tire degradation closely"
                ]
            else:
                analysis["response_options"] = [
                    "Continue current strategy",
                    "Adjust pit window timing",
                    "Prepare for restart battle"
                ]
        
        return analysis
    
    def detect_strategic_opportunities_from_events(self) -> List[Dict[str, Any]]:
        """
        Detect new strategic opportunities from recent race events.
        
        Returns:
            List of event-driven opportunities
        """
        opportunities = []
        
        # Analyze recent events for opportunities
        recent_events = [event for event in self.race_events 
                        if (datetime.now(timezone.utc) - event["timestamp"]).seconds < 60]
        
        for event in recent_events:
            if event["type"] == "competitor_pit_stop":
                car_id = event["event_data"].get("car_id")
                if car_id in self.competitors:
                    competitor = self.competitors[car_id]
                    
                    # Track position opportunity
                    opportunities.append({
                        "type": "track_position_gain",
                        "target_car": car_id,
                        "probability": 0.8,
                        "execution_lap": self.current_lap,
                        "reasoning": f"Gained track position from {car_id} pit stop",
                        "duration_laps": 5
                    })
            
            elif event["type"] == "track_status_change":
                new_status = event["event_data"].get("new_status")
                if new_status == "green" and event["event_data"].get("old_status") in ["safety_car", "virtual_safety_car"]:
                    # Restart opportunity
                    opportunities.append({
                        "type": "restart_opportunity",
                        "target_car": "field",
                        "probability": 0.6,
                        "execution_lap": self.current_lap,
                        "reasoning": "Race restart - positioning opportunity",
                        "duration_laps": 3
                    })
        
        return opportunities
    
    def _scan_strategic_opportunities(self) -> None:
        """Scan for strategic opportunities based on current competitor states."""
        self.strategic_opportunities = []
        
        for competitor in self.competitors.values():
            # Check for undercut opportunities
            if competitor.pit_probability > 0.6 and competitor.strategic_threat_level in ["medium", "high"]:
                opportunity = {
                    "type": "undercut_window",
                    "target_car": competitor.car_id,
                    "probability": min(0.9, competitor.pit_probability * 
                                     competitor.behavioral_profile["undercut_tendency"]),
                    "execution_lap": max(1, self.current_lap + 1),
                    "reasoning": f"High pit probability ({competitor.pit_probability:.2f}) for {competitor.car_id}"
                }
                self.strategic_opportunities.append(opportunity)
            
            # Check for overcut opportunities
            if (competitor.tire_age > 15 and competitor.pit_probability < 0.3 and 
                competitor.strategic_threat_level != "low"):
                opportunity = {
                    "type": "overcut_window",
                    "target_car": competitor.car_id,
                    "probability": 0.6,
                    "execution_lap": self.current_lap + 3,
                    "reasoning": f"Old tires ({competitor.tire_age} laps) but low pit probability"
                }
                self.strategic_opportunities.append(opportunity)
            
            # Check for DRS overtake opportunities
            gap = abs(competitor.gap_to_leader - self.our_gap_to_leader)
            if (gap < 1.0 and competitor.current_position in [self.our_position - 1, self.our_position + 1] and
                self.track_status == "green"):
                opportunity = {
                    "type": "drs_overtake",
                    "target_car": competitor.car_id,
                    "probability": 0.4,
                    "execution_lap": self.current_lap,
                    "reasoning": f"Close gap ({gap:.1f}s) and adjacent position"
                }
                self.strategic_opportunities.append(opportunity)
        
        # Sort opportunities by probability
        self.strategic_opportunities.sort(key=lambda x: x["probability"], reverse=True)
        
        # Keep only top 5 opportunities
        self.strategic_opportunities = self.strategic_opportunities[:5]
    
    def _get_twin_specific_state(self) -> Dict[str, Any]:
        """
        Get Field Twin specific state data.
        
        Returns:
            Field Twin state dictionary
        """
        competitors_state = []
        for competitor in self.competitors.values():
            competitors_state.append(competitor.get_state_dict())
        
        return {
            "competitors": competitors_state,
            "strategic_opportunities": self.strategic_opportunities,
            "race_context": {
                "current_lap": self.current_lap,
                "total_laps": self.total_laps,
                "session_type": self.session_type,
                "track_status": self.track_status,
                "our_position": self.our_position,
                "our_gap_to_leader": self.our_gap_to_leader
            },
            "recent_events": self.race_events[-10:] if self.race_events else []
        }
    
    def _generate_predictions(self, horizon_seconds: int) -> Dict[str, Any]:
        """
        Generate Field Twin predictions.
        
        Args:
            horizon_seconds: Prediction time horizon
            
        Returns:
            Prediction data dictionary
        """
        predictions = {
            "horizon_seconds": horizon_seconds,
            "competitor_predictions": {},
            "strategic_forecast": [],
            "risk_assessment": {},
            "race_event_predictions": [],
            "strategic_windows": []
        }
        
        future_laps = max(1, horizon_seconds // 90)  # Assume ~90s per lap
        
        # Generate predictions for each competitor
        for car_id, competitor in self.competitors.items():
            competitor_pred = self._predict_competitor_behavior(competitor, future_laps, horizon_seconds)
            predictions["competitor_predictions"][car_id] = competitor_pred
        
        # Predict strategic opportunities and windows
        predictions["strategic_windows"] = self._predict_strategic_windows(future_laps)
        
        # Predict race events
        predictions["race_event_predictions"] = self._predict_race_events(future_laps)
        
        # Strategic forecast
        for opportunity in self.strategic_opportunities:
            if opportunity["execution_lap"] <= self.current_lap + future_laps:
                predictions["strategic_forecast"].append({
                    "opportunity": opportunity,
                    "time_to_execution": (opportunity["execution_lap"] - self.current_lap) * 90,
                    "success_factors": self._analyze_opportunity_factors(opportunity),
                    "predicted_outcome": self._predict_opportunity_outcome(opportunity)
                })
        
        # Risk assessment
        predictions["risk_assessment"] = self._predict_strategic_risks(future_laps)
        
        return predictions
    
    def _analyze_opportunity_factors(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze factors affecting opportunity success.
        
        Args:
            opportunity: Strategic opportunity data
            
        Returns:
            Success factors analysis
        """
        target_car = opportunity["target_car"]
        if target_car not in self.competitors:
            return {"error": "Target car not found"}
        
        competitor = self.competitors[target_car]
        
        factors = {
            "tire_advantage": 0.0,
            "position_advantage": 0.0,
            "timing_advantage": 0.0,
            "behavioral_factor": 0.0
        }
        
        # Analyze tire advantage
        if opportunity["type"] == "undercut_window":
            factors["tire_advantage"] = min(1.0, competitor.tire_age / 20.0)
        
        # Analyze position advantage
        position_diff = abs(competitor.current_position - self.our_position)
        factors["position_advantage"] = max(0.0, 1.0 - (position_diff / 5.0))
        
        # Analyze timing
        if opportunity["execution_lap"] == self.current_lap:
            factors["timing_advantage"] = 1.0
        else:
            factors["timing_advantage"] = max(0.0, 1.0 - abs(opportunity["execution_lap"] - self.current_lap) / 5.0)
        
        # Behavioral factor
        if opportunity["type"] == "undercut_window":
            factors["behavioral_factor"] = 1.0 - competitor.behavioral_profile["aggressive_defense"]
        else:
            factors["behavioral_factor"] = competitor.behavioral_profile["tire_management"]
        
        return factors
    
    def get_competitor_count(self) -> int:
        """Get number of tracked competitors."""
        return len(self.competitors)
    
    def get_competitor(self, car_id: str) -> Optional[CompetitorModel]:
        """
        Get specific competitor model.
        
        Args:
            car_id: Car identifier
            
        Returns:
            Competitor model or None if not found
        """
        return self.competitors.get(car_id)
    
    def get_strategic_opportunities(self) -> List[Dict[str, Any]]:
        """Get current strategic opportunities."""
        return self.strategic_opportunities.copy()
    
    def get_race_events(self) -> List[Dict[str, Any]]:
        """Get recent race events."""
        return self.race_events.copy()
    
    def _predict_competitor_behavior(self, competitor: CompetitorModel, future_laps: int, horizon_seconds: int) -> Dict[str, Any]:
        """
        Predict detailed competitor behavior over time horizon.
        
        Args:
            competitor: Competitor model to predict
            future_laps: Number of future laps to predict
            horizon_seconds: Time horizon in seconds
            
        Returns:
            Detailed competitor predictions
        """
        # Tire degradation prediction
        current_degradation = competitor.tire_age * competitor.degradation_rate
        future_tire_age = competitor.tire_age + future_laps
        future_degradation = future_tire_age * competitor.degradation_rate
        
        # Lap time prediction with degradation
        base_lap_time = competitor.last_lap_time if competitor.last_lap_time > 0 else 85.0
        degradation_impact = future_degradation - current_degradation
        predicted_lap_time = base_lap_time * (1 + degradation_impact)
        
        # Fuel consumption prediction
        fuel_per_lap = competitor.fuel_consumption_rate / 100.0  # Convert to percentage
        predicted_fuel_level = max(0.0, competitor.fuel_level - (fuel_per_lap * future_laps))
        
        # Pit stop prediction
        pit_prediction = self._predict_pit_timing(competitor, future_laps)
        
        # Performance prediction
        performance_prediction = self._predict_performance_evolution(competitor, future_laps)
        
        # Strategic behavior prediction
        strategic_prediction = self._predict_strategic_behavior(competitor, future_laps)
        
        return {
            "predicted_lap_time": predicted_lap_time,
            "lap_time_evolution": self._predict_lap_time_evolution(competitor, future_laps),
            "degradation_factor": future_degradation,
            "predicted_fuel_level": predicted_fuel_level,
            "fuel_critical_lap": self._predict_fuel_critical_lap(competitor),
            "pit_prediction": pit_prediction,
            "performance_prediction": performance_prediction,
            "strategic_behavior": strategic_prediction,
            "position_prediction": self._predict_position_changes(competitor, future_laps),
            "threat_level_evolution": self._predict_threat_evolution(competitor, future_laps)
        }
    
    def _predict_pit_timing(self, competitor: CompetitorModel, future_laps: int) -> Dict[str, Any]:
        """
        Predict when competitor will pit.
        
        Args:
            competitor: Competitor model
            future_laps: Prediction horizon in laps
            
        Returns:
            Pit timing predictions
        """
        pit_windows = []
        current_pit_prob = competitor.pit_probability
        
        # Analyze pit probability evolution
        for lap_offset in range(1, min(future_laps + 1, 20)):  # Look ahead max 20 laps
            future_lap = self.current_lap + lap_offset
            future_tire_age = competitor.tire_age + lap_offset
            
            # Calculate pit probability for this future lap
            tire_factor = min(1.0, (future_tire_age / 25.0) + (competitor.tire_wear * 0.5))
            
            # Strategy-based probability
            strategy_factor = 0.0
            if competitor.predicted_strategy == "two_stop":
                if len(competitor.pit_stops) == 0:
                    if 15 <= future_lap <= 35:
                        strategy_factor = 0.7 - (abs(future_lap - 25) * 0.02)
                elif len(competitor.pit_stops) == 1:
                    if 35 <= future_lap <= 50:
                        strategy_factor = 0.8 - (abs(future_lap - 42) * 0.03)
            elif competitor.predicted_strategy == "one_stop":
                if len(competitor.pit_stops) == 0 and 25 <= future_lap <= 40:
                    strategy_factor = 0.6 - (abs(future_lap - 32) * 0.02)
            
            # Fuel urgency
            fuel_per_lap = competitor.fuel_consumption_rate / 100.0
            predicted_fuel = max(0.0, competitor.fuel_level - (fuel_per_lap * lap_offset))
            fuel_factor = max(0.0, 1.0 - (predicted_fuel / 0.2))  # Critical below 20%
            
            lap_pit_prob = min(1.0, tire_factor * 0.4 + strategy_factor * 0.4 + fuel_factor * 0.2)
            
            if lap_pit_prob > 0.5:
                pit_windows.append({
                    "lap": future_lap,
                    "probability": lap_pit_prob,
                    "tire_age": future_tire_age,
                    "fuel_level": predicted_fuel,
                    "primary_factor": "tire" if tire_factor > strategy_factor else "strategy"
                })
        
        # Find most likely pit window
        most_likely_pit = None
        if pit_windows:
            most_likely_pit = max(pit_windows, key=lambda x: x["probability"])
        
        return {
            "most_likely_lap": most_likely_pit["lap"] if most_likely_pit else None,
            "highest_probability": most_likely_pit["probability"] if most_likely_pit else 0.0,
            "pit_windows": pit_windows[:5],  # Top 5 windows
            "strategy_confidence": self._calculate_strategy_confidence(competitor)
        }
    
    def _predict_performance_evolution(self, competitor: CompetitorModel, future_laps: int) -> Dict[str, Any]:
        """
        Predict how competitor performance will evolve.
        
        Args:
            competitor: Competitor model
            future_laps: Prediction horizon in laps
            
        Returns:
            Performance evolution predictions
        """
        # Base performance from recent lap times
        if len(competitor.lap_times_history) >= 3:
            recent_times = [entry["lap_time"] for entry in list(competitor.lap_times_history)[-5:]]
            base_performance = sum(recent_times) / len(recent_times)
        else:
            base_performance = competitor.last_lap_time if competitor.last_lap_time > 0 else 85.0
        
        # Predict performance degradation
        performance_evolution = []
        for lap_offset in range(1, min(future_laps + 1, 15)):
            future_tire_age = competitor.tire_age + lap_offset
            
            # Tire degradation impact
            degradation_impact = (future_tire_age * competitor.degradation_rate) - (competitor.tire_age * competitor.degradation_rate)
            
            # Fuel weight reduction benefit (lighter car = faster)
            fuel_per_lap = competitor.fuel_consumption_rate / 100.0
            fuel_reduction = fuel_per_lap * lap_offset
            fuel_benefit = fuel_reduction * 0.3  # ~0.3s per 10% fuel reduction
            
            # Track evolution (rubber buildup, temperature changes)
            track_evolution = lap_offset * 0.01  # Slight improvement over time
            
            predicted_lap_time = base_performance + degradation_impact - fuel_benefit - track_evolution
            
            performance_evolution.append({
                "lap_offset": lap_offset,
                "predicted_lap_time": predicted_lap_time,
                "degradation_impact": degradation_impact,
                "fuel_benefit": fuel_benefit,
                "relative_performance": predicted_lap_time - base_performance
            })
        
        return {
            "base_performance": base_performance,
            "evolution": performance_evolution,
            "peak_performance_lap": self._find_peak_performance_lap(performance_evolution),
            "degradation_trend": competitor.degradation_rate,
            "tire_management_factor": competitor.behavioral_profile["tire_management"]
        }
    
    def _predict_strategic_behavior(self, competitor: CompetitorModel, future_laps: int) -> Dict[str, Any]:
        """
        Predict competitor strategic behavior patterns.
        
        Args:
            competitor: Competitor model
            future_laps: Prediction horizon in laps
            
        Returns:
            Strategic behavior predictions
        """
        behavior_predictions = {
            "undercut_likelihood": [],
            "defensive_actions": [],
            "strategic_responses": [],
            "risk_taking_tendency": competitor.behavioral_profile["aggressive_defense"]
        }
        
        # Predict undercut attempts
        for lap_offset in range(1, min(future_laps + 1, 10)):
            future_lap = self.current_lap + lap_offset
            
            # Undercut likelihood based on position and behavioral profile
            undercut_score = 0.0
            
            # Position pressure factor
            if competitor.current_position > 1:  # Not leading
                position_pressure = min(1.0, (competitor.current_position - 1) / 10.0)
                undercut_score += position_pressure * 0.3
            
            # Behavioral tendency
            undercut_score += competitor.behavioral_profile["undercut_tendency"] * 0.4
            
            # Strategic window factor
            if 15 <= future_lap <= 35:  # Prime undercut window
                undercut_score += 0.3
            
            # Tire age factor
            future_tire_age = competitor.tire_age + lap_offset
            if future_tire_age >= 10:
                undercut_score += min(0.2, (future_tire_age - 10) * 0.02)
            
            behavior_predictions["undercut_likelihood"].append({
                "lap": future_lap,
                "probability": min(1.0, undercut_score),
                "confidence": self._calculate_behavior_confidence(competitor)
            })
        
        # Predict defensive actions
        if competitor.current_position <= 5:  # Top 5 positions more likely to defend
            defense_probability = competitor.behavioral_profile["aggressive_defense"]
            behavior_predictions["defensive_actions"] = [{
                "type": "position_defense",
                "probability": defense_probability,
                "triggers": ["close_following_car", "drs_zone_approach"],
                "effectiveness": competitor.behavioral_profile["tire_management"]
            }]
        
        # Predict strategic responses to our actions
        response_patterns = self._analyze_response_patterns(competitor)
        behavior_predictions["strategic_responses"] = response_patterns
        
        return behavior_predictions
    
    def _predict_strategic_windows(self, future_laps: int) -> List[Dict[str, Any]]:
        """
        Predict upcoming strategic windows and opportunities.
        
        Args:
            future_laps: Prediction horizon in laps
            
        Returns:
            List of predicted strategic windows
        """
        windows = []
        
        # Analyze pit window opportunities
        for lap_offset in range(1, min(future_laps + 1, 15)):
            future_lap = self.current_lap + lap_offset
            
            # Count competitors likely to pit
            pit_candidates = []
            for competitor in self.competitors.values():
                pit_pred = self._predict_pit_timing(competitor, lap_offset + 5)
                if pit_pred["most_likely_lap"] and abs(pit_pred["most_likely_lap"] - future_lap) <= 2:
                    pit_candidates.append({
                        "car_id": competitor.car_id,
                        "probability": pit_pred["highest_probability"]
                    })
            
            if len(pit_candidates) >= 2:  # Multiple competitors pitting creates opportunities
                windows.append({
                    "type": "mass_pit_window",
                    "lap": future_lap,
                    "opportunity_type": "track_position_gain",
                    "affected_competitors": pit_candidates,
                    "strategic_value": min(1.0, len(pit_candidates) * 0.3),
                    "execution_complexity": "medium"
                })
        
        # Analyze undercut/overcut windows
        for competitor in self.competitors.values():
            if competitor.strategic_threat_level in ["medium", "high", "critical"]:
                pit_pred = self._predict_pit_timing(competitor, future_laps)
                if pit_pred["most_likely_lap"]:
                    # Undercut window (pit 1-2 laps before competitor)
                    undercut_lap = max(1, pit_pred["most_likely_lap"] - 2)
                    if undercut_lap <= self.current_lap + future_laps:
                        windows.append({
                            "type": "undercut_window",
                            "lap": undercut_lap,
                            "target_competitor": competitor.car_id,
                            "success_probability": pit_pred["highest_probability"] * competitor.behavioral_profile["undercut_tendency"],
                            "strategic_value": self._calculate_strategic_value(competitor, "undercut"),
                            "execution_complexity": "low"
                        })
                    
                    # Overcut window (stay out longer)
                    overcut_lap = pit_pred["most_likely_lap"] + 3
                    if overcut_lap <= self.current_lap + future_laps:
                        windows.append({
                            "type": "overcut_window",
                            "lap": overcut_lap,
                            "target_competitor": competitor.car_id,
                            "success_probability": (1.0 - pit_pred["highest_probability"]) * (1.0 - competitor.behavioral_profile["aggressive_defense"]),
                            "strategic_value": self._calculate_strategic_value(competitor, "overcut"),
                            "execution_complexity": "medium"
                        })
        
        # Sort by strategic value and return top windows
        windows.sort(key=lambda x: x["strategic_value"], reverse=True)
        return windows[:10]
    
    def _predict_race_events(self, future_laps: int) -> List[Dict[str, Any]]:
        """
        Predict likely race events that could affect strategy.
        
        Args:
            future_laps: Prediction horizon in laps
            
        Returns:
            List of predicted race events
        """
        events = []
        
        # Predict pit stop waves
        pit_activity_by_lap = {}
        for competitor in self.competitors.values():
            pit_pred = self._predict_pit_timing(competitor, future_laps)
            for window in pit_pred["pit_windows"]:
                lap = window["lap"]
                if lap not in pit_activity_by_lap:
                    pit_activity_by_lap[lap] = []
                pit_activity_by_lap[lap].append({
                    "car_id": competitor.car_id,
                    "probability": window["probability"]
                })
        
        # Identify high-activity laps
        for lap, activity in pit_activity_by_lap.items():
            if len(activity) >= 3:  # 3+ cars likely to pit
                total_probability = sum(car["probability"] for car in activity)
                events.append({
                    "type": "pit_stop_wave",
                    "lap": lap,
                    "probability": min(1.0, total_probability / len(activity)),
                    "affected_cars": [car["car_id"] for car in activity],
                    "strategic_impact": "high",
                    "preparation_required": True
                })
        
        # Predict position battles
        close_battles = self._identify_close_battles()
        for battle in close_battles:
            events.append({
                "type": "position_battle",
                "lap_range": [self.current_lap + 1, self.current_lap + 5],
                "probability": 0.7,
                "involved_cars": battle["cars"],
                "strategic_impact": "medium",
                "drs_factor": True
            })
        
        # Predict fuel-critical situations
        for competitor in self.competitors.values():
            critical_lap = self._predict_fuel_critical_lap(competitor)
            if critical_lap and critical_lap <= self.current_lap + future_laps:
                events.append({
                    "type": "fuel_critical",
                    "lap": critical_lap,
                    "car_id": competitor.car_id,
                    "probability": 0.8,
                    "strategic_impact": "high",
                    "forced_pit_stop": True
                })
        
        return sorted(events, key=lambda x: x.get("lap", x.get("lap_range", [0])[0]))
    
    def _predict_strategic_risks(self, future_laps: int) -> Dict[str, Any]:
        """
        Predict strategic risks over the time horizon.
        
        Args:
            future_laps: Prediction horizon in laps
            
        Returns:
            Risk assessment predictions
        """
        risks = {
            "undercut_risks": [],
            "overcut_risks": [],
            "position_loss_risks": [],
            "strategic_isolation_risk": 0.0,
            "overall_risk_level": "low"
        }
        
        # Analyze undercut risks
        for competitor in self.competitors.values():
            if (competitor.behavioral_profile["undercut_tendency"] > 0.6 and 
                competitor.strategic_threat_level in ["medium", "high", "critical"]):
                
                pit_pred = self._predict_pit_timing(competitor, future_laps)
                if pit_pred["most_likely_lap"]:
                    risk_score = (competitor.behavioral_profile["undercut_tendency"] * 
                                 pit_pred["highest_probability"] * 
                                 self._get_threat_multiplier(competitor.strategic_threat_level))
                    
                    risks["undercut_risks"].append({
                        "car_id": competitor.car_id,
                        "risk_score": risk_score,
                        "likely_execution_lap": pit_pred["most_likely_lap"] - 1,
                        "mitigation_window": [pit_pred["most_likely_lap"] - 3, pit_pred["most_likely_lap"] - 1]
                    })
        
        # Analyze position loss risks
        position_risks = self._analyze_position_loss_risks(future_laps)
        risks["position_loss_risks"] = position_risks
        
        # Calculate strategic isolation risk
        risks["strategic_isolation_risk"] = self._calculate_isolation_risk()
        
        # Determine overall risk level
        high_risks = len([r for r in risks["undercut_risks"] if r["risk_score"] > 0.7])
        medium_risks = len([r for r in risks["undercut_risks"] if 0.4 <= r["risk_score"] <= 0.7])
        
        if high_risks >= 2 or risks["strategic_isolation_risk"] > 0.8:
            risks["overall_risk_level"] = "critical"
        elif high_risks >= 1 or medium_risks >= 3:
            risks["overall_risk_level"] = "high"
        elif medium_risks >= 1 or risks["strategic_isolation_risk"] > 0.5:
            risks["overall_risk_level"] = "medium"
        
        return risks
    
    def _predict_opportunity_outcome(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict the likely outcome of executing a strategic opportunity.
        
        Args:
            opportunity: Strategic opportunity data
            
        Returns:
            Predicted outcome analysis
        """
        target_car = opportunity["target_car"]
        competitor = self.competitors.get(target_car)
        
        if not competitor:
            return {"success_probability": 0.0, "error": "Target competitor not found"}
        
        outcome = {
            "success_probability": opportunity["probability"],
            "position_gain_expected": 0,
            "time_advantage_expected": 0.0,
            "risk_factors": [],
            "success_scenarios": [],
            "failure_scenarios": []
        }
        
        if opportunity["type"] == "undercut_window":
            # Predict undercut outcome
            tire_advantage = max(0, competitor.tire_age - 5) * 0.1  # Fresher tires advantage
            position_diff = abs(competitor.current_position - self.our_position)
            
            if position_diff <= 1:  # Direct position battle
                outcome["position_gain_expected"] = 1
                outcome["time_advantage_expected"] = 3.0 + tire_advantage
                outcome["success_scenarios"] = [
                    "Clean pit stop execution",
                    "Competitor pits as predicted",
                    "Track position maintained"
                ]
                outcome["failure_scenarios"] = [
                    "Competitor doesn't pit",
                    "Slow pit stop",
                    "Traffic interference"
                ]
            
            # Risk factors
            if competitor.behavioral_profile["aggressive_defense"] > 0.7:
                outcome["risk_factors"].append("Aggressive defensive response expected")
            
            if competitor.pit_probability < 0.6:
                outcome["risk_factors"].append("Uncertain competitor pit timing")
        
        elif opportunity["type"] == "overcut_window":
            # Predict overcut outcome
            tire_degradation_risk = competitor.tire_age * competitor.degradation_rate
            fuel_advantage = (competitor.fuel_level - 0.3) * 2.0  # Fuel weight advantage
            
            outcome["time_advantage_expected"] = fuel_advantage - tire_degradation_risk
            outcome["success_scenarios"] = [
                "Competitor pits early",
                "Tire degradation manageable",
                "Fuel advantage realized"
            ]
            outcome["failure_scenarios"] = [
                "Excessive tire degradation",
                "Competitor stays out longer",
                "Safety car neutralizes advantage"
            ]
        
        # Adjust success probability based on risk factors
        risk_penalty = len(outcome["risk_factors"]) * 0.1
        outcome["success_probability"] = max(0.0, outcome["success_probability"] - risk_penalty)
        
        return outcome
    
    # Helper methods for predictions
    
    def _predict_lap_time_evolution(self, competitor: CompetitorModel, future_laps: int) -> List[Dict[str, Any]]:
        """Predict how lap times will evolve."""
        evolution = []
        base_time = competitor.last_lap_time if competitor.last_lap_time > 0 else 85.0
        
        for lap_offset in range(1, min(future_laps + 1, 10)):
            future_tire_age = competitor.tire_age + lap_offset
            degradation = future_tire_age * competitor.degradation_rate
            fuel_benefit = (lap_offset * competitor.fuel_consumption_rate / 100.0) * 0.3
            
            predicted_time = base_time + degradation - fuel_benefit
            
            evolution.append({
                "lap_offset": lap_offset,
                "predicted_lap_time": predicted_time,
                "tire_age": future_tire_age,
                "degradation_impact": degradation
            })
        
        return evolution
    
    def _predict_fuel_critical_lap(self, competitor: CompetitorModel) -> Optional[int]:
        """Predict when competitor will reach critical fuel level."""
        if competitor.fuel_level <= 0.1:  # Already critical
            return self.current_lap
        
        fuel_per_lap = competitor.fuel_consumption_rate / 100.0
        critical_threshold = 0.05  # 5% fuel remaining
        
        laps_to_critical = (competitor.fuel_level - critical_threshold) / fuel_per_lap
        critical_lap = self.current_lap + int(laps_to_critical)
        
        return critical_lap if laps_to_critical > 0 else None
    
    def _predict_position_changes(self, competitor: CompetitorModel, future_laps: int) -> Dict[str, Any]:
        """Predict likely position changes."""
        return {
            "position_volatility": min(1.0, len(competitor.position_history) * 0.1),
            "likely_position_range": [
                max(1, competitor.current_position - 2),
                min(20, competitor.current_position + 2)
            ],
            "position_trend": "stable"  # Simplified - would analyze historical data
        }
    
    def _predict_threat_evolution(self, competitor: CompetitorModel, future_laps: int) -> List[str]:
        """Predict how threat level will evolve."""
        evolution = []
        current_threat = competitor.strategic_threat_level
        
        # Simplified prediction based on pit probability and position
        if competitor.pit_probability > 0.7:
            evolution.append("threat_increase_pre_pit")
            evolution.append("threat_decrease_post_pit")
        elif competitor.tire_age > 20:
            evolution.append("threat_decrease_degradation")
        else:
            evolution.append("threat_stable")
        
        return evolution
    
    def _find_peak_performance_lap(self, evolution: List[Dict[str, Any]]) -> int:
        """Find lap with best predicted performance."""
        if not evolution:
            return 0
        
        best_lap = min(evolution, key=lambda x: x["predicted_lap_time"])
        return best_lap["lap_offset"]
    
    def _calculate_strategy_confidence(self, competitor: CompetitorModel) -> float:
        """Calculate confidence in strategy predictions."""
        data_quality = min(1.0, len(competitor.lap_times_history) / 10.0)
        behavioral_consistency = competitor.behavioral_profile["tire_management"]
        pit_history_factor = min(1.0, len(competitor.pit_stops) * 0.3)
        
        return (data_quality + behavioral_consistency + pit_history_factor) / 3.0
    
    def _calculate_behavior_confidence(self, competitor: CompetitorModel) -> float:
        """Calculate confidence in behavioral predictions."""
        return min(1.0, len(competitor.position_history) / 20.0)
    
    def _analyze_response_patterns(self, competitor: CompetitorModel) -> List[Dict[str, Any]]:
        """Analyze how competitor responds to strategic moves."""
        patterns = []
        
        # Defensive response pattern
        if competitor.behavioral_profile["aggressive_defense"] > 0.6:
            patterns.append({
                "trigger": "undercut_attempt",
                "response": "early_pit_counter",
                "probability": competitor.behavioral_profile["aggressive_defense"],
                "effectiveness": 0.7
            })
        
        # Conservative response pattern
        if competitor.behavioral_profile["tire_management"] > 0.7:
            patterns.append({
                "trigger": "overcut_attempt",
                "response": "extend_stint",
                "probability": competitor.behavioral_profile["tire_management"],
                "effectiveness": 0.6
            })
        
        return patterns
    
    def _calculate_strategic_value(self, competitor: CompetitorModel, strategy_type: str) -> float:
        """Calculate strategic value of an opportunity."""
        base_value = 0.5
        
        # Position factor
        position_factor = max(0.0, (10 - competitor.current_position) / 10.0)
        
        # Threat factor
        threat_multipliers = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
        threat_factor = threat_multipliers.get(competitor.strategic_threat_level, 0.5)
        
        # Strategy-specific factors
        if strategy_type == "undercut":
            strategy_factor = competitor.behavioral_profile["undercut_tendency"]
        else:  # overcut
            strategy_factor = 1.0 - competitor.behavioral_profile["aggressive_defense"]
        
        return min(1.0, base_value + position_factor * 0.3 + threat_factor * 0.2 + strategy_factor * 0.2)
    
    def _get_threat_multiplier(self, threat_level: str) -> float:
        """Get multiplier for threat level."""
        multipliers = {"low": 0.5, "medium": 0.7, "high": 0.9, "critical": 1.0}
        return multipliers.get(threat_level, 0.5)
    
    def _analyze_position_loss_risks(self, future_laps: int) -> List[Dict[str, Any]]:
        """Analyze risks of losing positions."""
        risks = []
        
        for competitor in self.competitors.values():
            if (competitor.current_position == self.our_position + 1 and  # Directly behind us
                competitor.strategic_threat_level in ["medium", "high", "critical"]):
                
                risk_score = (competitor.behavioral_profile["undercut_tendency"] * 0.4 +
                             competitor.pit_probability * 0.3 +
                             (1.0 - competitor.behavioral_profile["tire_management"]) * 0.3)
                
                risks.append({
                    "car_id": competitor.car_id,
                    "risk_type": "direct_position_loss",
                    "risk_score": risk_score,
                    "mitigation_actions": ["early_pit", "defensive_positioning"]
                })
        
        return risks
    
    def _calculate_isolation_risk(self) -> float:
        """Calculate risk of strategic isolation."""
        # Count competitors with similar strategies
        our_strategy = "two_stop"  # Would be determined from our car twin
        similar_strategies = sum(1 for c in self.competitors.values() 
                               if c.predicted_strategy == our_strategy)
        
        total_competitors = len(self.competitors)
        if total_competitors == 0:
            return 0.0
        
        # High isolation risk if we're alone in our strategy
        isolation_factor = 1.0 - (similar_strategies / total_competitors)
        
        # Adjust for track position
        position_factor = min(1.0, self.our_position / 10.0)  # Higher positions = higher risk
        
        return min(1.0, isolation_factor * 0.7 + position_factor * 0.3)
    
    def _identify_close_battles(self) -> List[Dict[str, Any]]:
        """Identify close position battles."""
        battles = []
        
        # Group competitors by position proximity
        position_groups = {}
        for competitor in self.competitors.values():
            pos = competitor.current_position
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(competitor)
        
        # Find adjacent positions with close gaps
        for pos in sorted(position_groups.keys()):
            if pos + 1 in position_groups:
                car1 = position_groups[pos][0] if position_groups[pos] else None
                car2 = position_groups[pos + 1][0] if position_groups[pos + 1] else None
                
                if car1 and car2:
                    gap = abs(car1.gap_to_leader - car2.gap_to_leader)
                    if gap < 2.0:  # Within 2 seconds
                        battles.append({
                            "cars": [car1.car_id, car2.car_id],
                            "gap": gap,
                            "positions": [pos, pos + 1]
                        })
        
        return battles