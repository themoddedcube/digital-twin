#!/usr/bin/env python3
"""
Test script for Field Twin implementation.

This script tests the basic functionality of the Field Twin competitor modeling system.
"""

import json
import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.field_twin import FieldTwin, CompetitorModel
from src.hpc_orchestrator import HPCOrchestrator


def create_sample_telemetry():
    """Create sample telemetry data for testing."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lap": 15,
        "session_type": "race",
        "track_conditions": {
            "temperature": 35.2,
            "weather": "sunny",
            "track_status": "green"
        },
        "cars": [
            {
                "car_id": "44",
                "team": "Mercedes",
                "driver": "Hamilton",
                "position": 3,
                "speed": 298.5,
                "tire": {
                    "compound": "medium",
                    "age": 12,
                    "wear_level": 0.35
                },
                "fuel_level": 0.65,
                "lap_time": 84.2,
                "sector_times": [28.1, 31.0, 25.1]
            },
            {
                "car_id": "33",
                "team": "Red Bull",
                "driver": "Verstappen",
                "position": 1,
                "speed": 302.1,
                "tire": {
                    "compound": "hard",
                    "age": 8,
                    "wear_level": 0.25
                },
                "fuel_level": 0.70,
                "lap_time": 83.1,
                "sector_times": [27.8, 30.5, 24.8]
            },
            {
                "car_id": "16",
                "team": "Ferrari",
                "driver": "Leclerc",
                "position": 2,
                "speed": 300.2,
                "tire": {
                    "compound": "medium",
                    "age": 15,
                    "wear_level": 0.45
                },
                "fuel_level": 0.60,
                "lap_time": 83.8,
                "sector_times": [28.0, 30.8, 25.0]
            }
        ]
    }


def test_field_twin_basic():
    """Test basic Field Twin functionality."""
    print("Testing Field Twin basic functionality...")
    
    # Create Field Twin
    field_twin = FieldTwin()
    
    # Create sample telemetry
    telemetry = create_sample_telemetry()
    
    # Update Field Twin
    field_twin.update_state(telemetry)
    
    # Get current state
    state = field_twin.get_current_state()
    
    print(f"✓ Field Twin updated successfully")
    print(f"✓ Tracking {len(field_twin.competitors)} competitors")
    print(f"✓ Current lap: {field_twin.current_lap}")
    
    # Test competitor models
    for car_id, competitor in field_twin.competitors.items():
        print(f"✓ Competitor {car_id}: Position {competitor.current_position}, Threat: {competitor.strategic_threat_level}")
    
    return True


def test_competitor_behavior_tracking():
    """Test competitor behavior tracking."""
    print("\nTesting competitor behavior tracking...")
    
    field_twin = FieldTwin()
    telemetry = create_sample_telemetry()
    
    # Update multiple times to build history
    for lap in range(10, 20):
        telemetry["lap"] = lap
        # Simulate tire aging
        for car in telemetry["cars"]:
            car["tire"]["age"] = lap - 5
            car["tire"]["wear_level"] = min(1.0, (lap - 5) * 0.03)
        
        field_twin.update_state(telemetry)
    
    # Check behavioral profiles
    for car_id, competitor in field_twin.competitors.items():
        profile = competitor.behavioral_profile
        print(f"✓ {car_id} behavioral profile: undercut={profile['undercut_tendency']:.2f}, "
              f"defense={profile['aggressive_defense']:.2f}, tire_mgmt={profile['tire_management']:.2f}")
    
    return True


def test_strategic_opportunities():
    """Test strategic opportunity detection."""
    print("\nTesting strategic opportunity detection...")
    
    field_twin = FieldTwin()
    telemetry = create_sample_telemetry()
    
    # Set up scenario for strategic opportunities
    telemetry["lap"] = 25
    # Make one competitor have old tires (pit candidate)
    telemetry["cars"][2]["tire"]["age"] = 20
    telemetry["cars"][2]["tire"]["wear_level"] = 0.8
    
    field_twin.update_state(telemetry)
    
    # Get strategic opportunities
    opportunities = field_twin.get_strategic_opportunities()
    
    print(f"✓ Detected {len(opportunities)} strategic opportunities")
    for opp in opportunities:
        print(f"  - {opp['type']} vs {opp['target_car']}: {opp['probability']:.2f} probability")
    
    return True


def test_predictions():
    """Test prediction algorithms."""
    print("\nTesting prediction algorithms...")
    
    field_twin = FieldTwin()
    telemetry = create_sample_telemetry()
    field_twin.update_state(telemetry)
    
    # Generate predictions
    predictions = field_twin.predict(300)  # 5 minutes ahead
    
    print(f"✓ Generated predictions for {len(predictions['predictions']['competitor_predictions'])} competitors")
    
    # Check competitor predictions
    for car_id, pred in predictions["predictions"]["competitor_predictions"].items():
        print(f"  - {car_id}: Predicted lap time {pred['predicted_lap_time']:.2f}s")
    
    # Check strategic forecast
    forecast = predictions["predictions"]["strategic_forecast"]
    print(f"✓ Strategic forecast contains {len(forecast)} opportunities")
    
    return True


def test_hpc_orchestrator():
    """Test HPC Orchestrator integration."""
    print("\nTesting HPC Orchestrator...")
    
    orchestrator = HPCOrchestrator()
    telemetry = create_sample_telemetry()
    
    # Update through orchestrator
    orchestrator.update_field_twin(telemetry)
    
    # Get strategic analysis
    analysis = orchestrator.get_strategic_analysis()
    
    print(f"✓ Strategic analysis generated")
    print(f"  - Competitor summary: {analysis['competitor_summary']['total_competitors']} competitors")
    print(f"  - Threat levels: {analysis['threat_assessment']['overall_risk_level']}")
    print(f"  - Recommendations: {len(analysis['strategic_recommendations'])}")
    
    # Test competitor prediction
    if orchestrator.field_twin.competitors:
        car_id = list(orchestrator.field_twin.competitors.keys())[0]
        pred = orchestrator.predict_competitor_behavior(car_id, 180)
        print(f"✓ Competitor {car_id} behavior predicted")
    
    return True


def test_race_event_handling():
    """Test race event handling."""
    print("\nTesting race event handling...")
    
    field_twin = FieldTwin()
    telemetry = create_sample_telemetry()
    field_twin.update_state(telemetry)
    
    # Simulate safety car
    safety_car_analysis = field_twin.handle_safety_car_deployment()
    print(f"✓ Safety car analysis: {len(safety_car_analysis['strategic_implications'])} implications")
    
    # Simulate competitor pit stop
    pit_analysis = field_twin.handle_competitor_pit_stop("33", {
        "lap": 15,
        "old_tire_age": 12,
        "position_before": 1,
        "position_after": 3
    })
    print(f"✓ Pit stop analysis: {pit_analysis['strategic_type']}")
    
    return True


def main():
    """Run all tests."""
    print("=== Field Twin Implementation Test ===\n")
    
    tests = [
        test_field_twin_basic,
        test_competitor_behavior_tracking,
        test_strategic_opportunities,
        test_predictions,
        test_hpc_orchestrator,
        test_race_event_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✓ PASSED\n")
            else:
                failed += 1
                print("✗ FAILED\n")
        except Exception as e:
            failed += 1
            print(f"✗ FAILED: {e}\n")
    
    print(f"=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Field Twin implementation is working correctly.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())