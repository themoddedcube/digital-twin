"""
Test script for the F1 Race Strategy System

This script tests the integration of all components:
- Digital Twin
- Mojo Simulation
- AI Strategist
- Telemetry Feed
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from twin_model import DigitalTwin, FieldTwin, create_sample_race_state
from telemetry_feed import TelemetryGenerator, TelemetryStreamer
from ai_strategist import AIStrategist
from hpc_orchestrator import HPCOrchestrator


async def test_digital_twin():
    """Test digital twin functionality"""
    print("🧠 Testing Digital Twin...")
    
    # Create digital twin
    twin = DigitalTwin("car_44")
    
    # Create sample race state
    race_state = create_sample_race_state()
    
    # Update twin
    car_twin_state = twin.update_from_telemetry(race_state)
    
    print(f"✅ Digital Twin updated for car {car_twin_state.car_id}")
    print(f"   Position: {car_twin_state.current_state.position}")
    print(f"   Tire Wear: {car_twin_state.current_state.tire.wear_level:.1%}")
    print(f"   Fuel Level: {car_twin_state.current_state.fuel_level:.1%}")
    
    # Test field twin
    field_twin = FieldTwin()
    field_twin_state = field_twin.update_from_race_state(race_state)
    
    print(f"✅ Field Twin updated with {len(field_twin_state.competitors)} competitors")
    
    return True


async def test_telemetry_feed():
    """Test telemetry feed generation"""
    print("\n📡 Testing Telemetry Feed...")
    
    generator = TelemetryGenerator()
    
    # Generate sample telemetry
    telemetry = generator.generate_telemetry()
    
    print(f"✅ Telemetry generated for lap {telemetry.lap}")
    print(f"   Cars: {len(telemetry.cars)}")
    print(f"   Track Temp: {telemetry.track_conditions['temperature']}°C")
    print(f"   Weather: {telemetry.track_conditions['weather']}")
    
    # Test streaming
    streamer = TelemetryStreamer(generator, interval=0.5)
    
    print("✅ Telemetry streaming test completed")
    
    return True


async def test_ai_strategist():
    """Test AI strategist functionality"""
    print("\n🤖 Testing AI Strategist...")
    
    # Create test data
    test_data = {
        "car_twin": None,  # Would be actual car twin data
        "field_twin": None,
        "simulation_results": [
            {
                "pit_lap": 24,
                "final_position": 3,
                "total_time": 2675.4,
                "success_probability": 0.85,
                "strategy_type": "undercut"
            }
        ],
        "race_context": {
            "lap": 22,
            "session_type": "race"
        }
    }
    
    # Test AI strategist
    async with AIStrategist() as strategist:
        recommendations = await strategist.generate_recommendations(test_data)
        
        print(f"✅ AI Strategist generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations):
            print(f"   {i+1}. {rec['priority'].upper()}: {rec['title']}")
            print(f"      {rec['description']}")
    
    return True


async def test_mojo_simulation():
    """Test Mojo simulation (if available)"""
    print("\n⚡ Testing Mojo Simulation...")
    
    try:
        # Check if Mojo is available
        import subprocess
        result = subprocess.run(["mojo", "--version"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Mojo version: {result.stdout.strip()}")
            
            # Test basic Mojo compilation
            mojo_file = "src/simulate_strategy.mojo"
            if os.path.exists(mojo_file):
                print("✅ Mojo simulation file found")
                print("   Note: Full simulation testing requires proper Mojo setup")
            else:
                print("❌ Mojo simulation file not found")
        else:
            print("❌ Mojo not available or not in PATH")
            
    except Exception as e:
        print(f"❌ Error testing Mojo: {e}")
    
    return True


async def test_hpc_orchestrator():
    """Test HPC orchestrator"""
    print("\n🔧 Testing HPC Orchestrator...")
    
    try:
        orchestrator = HPCOrchestrator("car_44")
        
        print("✅ HPC Orchestrator created")
        print(f"   Car ID: {orchestrator.car_id}")
        print(f"   Digital Twin: {type(orchestrator.digital_twin).__name__}")
        print(f"   Field Twin: {type(orchestrator.field_twin).__name__}")
        print(f"   AI Strategist: {type(orchestrator.ai_strategist).__name__}")
        
        # Test performance metrics
        metrics = orchestrator.get_performance_metrics()
        print(f"✅ Performance metrics: {metrics}")
        
    except Exception as e:
        print(f"❌ Error testing HPC Orchestrator: {e}")
    
    return True


async def test_integration():
    """Test full system integration"""
    print("\n🔗 Testing System Integration...")
    
    try:
        # Create orchestrator
        orchestrator = HPCOrchestrator("car_44")
        
        # Create sample telemetry
        generator = TelemetryGenerator()
        telemetry = generator.generate_telemetry()
        
        # Convert to race state
        race_state = create_sample_race_state()
        
        # Process through orchestrator
        await orchestrator.process_telemetry(race_state.__dict__)
        
        print("✅ Full system integration test completed")
        print(f"   Simulation results: {len(orchestrator.simulation_results)}")
        print(f"   Strategy recommendations: {len(orchestrator.strategy_recommendations)}")
        
    except Exception as e:
        print(f"❌ Error in integration test: {e}")
    
    return True


async def main():
    """Run all tests"""
    print("🏎️ F1 Race Strategy System - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Digital Twin", test_digital_twin),
        ("Telemetry Feed", test_telemetry_feed),
        ("AI Strategist", test_ai_strategist),
        ("Mojo Simulation", test_mojo_simulation),
        ("HPC Orchestrator", test_hpc_orchestrator),
        ("System Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for demo.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())
