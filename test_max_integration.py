#!/usr/bin/env python3
"""
MAX Integration Test
Tests the complete MAX LLM integration with real race data
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from max_integration import AIStrategist


async def test_max_with_real_data():
    """Test MAX with realistic F1 race data"""
    print("=" * 70)
    print("🏎️  MAX INTEGRATION TEST - REAL F1 RACE DATA")
    print("=" * 70)
    
    # Create realistic race context
    race_data = {
        'car_twin': None,  # AIStrategist handles None gracefully
        'field_twin': None,
        'simulation_results': [
            {
                'pit_lap': 23,
                'final_position': 3,
                'total_time': 2670.1,
                'success_probability': 0.78,
                'tire_life_remaining': 15,
                'fuel_laps_remaining': 20,
                'strategy_type': 'aggressive_undercut'
            },
            {
                'pit_lap': 24,
                'final_position': 3,
                'total_time': 2675.4,
                'success_probability': 0.85,
                'tire_life_remaining': 12,
                'fuel_laps_remaining': 18,
                'strategy_type': 'standard_undercut'
            },
            {
                'pit_lap': 26,
                'final_position': 4,
                'total_time': 2680.2,
                'success_probability': 0.92,
                'tire_life_remaining': 8,
                'fuel_laps_remaining': 16,
                'strategy_type': 'conservative'
            }
        ],
        'race_context': {
            'lap': 22,
            'session_type': 'race'
        }
    }
    
    print("\n📊 Race Scenario:")
    print(f"   Lap: {race_data['race_context']['lap']}")
    print(f"   Simulations: {len(race_data['simulation_results'])}")
    
    # Generate recommendations with MAX
    print("\n🤖 Calling MAX AI Strategist...")
    async with AIStrategist() as strategist:
        recommendations = await strategist.generate_recommendations(race_data)
        
        print(f"\n✅ Received {len(recommendations)} AI Recommendations")
        print("=" * 70)
        
        # Display by priority
        urgent = [r for r in recommendations if r.get('priority') == 'urgent']
        moderate = [r for r in recommendations if r.get('priority') == 'moderate']
        optional = [r for r in recommendations if r.get('priority') == 'optional']
        
        if urgent:
            print("\n🚨 URGENT RECOMMENDATIONS:")
            for i, rec in enumerate(urgent, 1):
                print(f"\n  {i}. {rec.get('title', 'N/A')}")
                print(f"     📝 {rec.get('description', 'N/A')}")
                print(f"     💰 Benefit: {rec.get('expected_benefit', 'N/A')}")
                print(f"     🧠 Reasoning: {rec.get('reasoning', 'N/A')[:100]}...")
                if rec.get('execution_lap'):
                    print(f"     ⏱️  Execute: Lap {rec.get('execution_lap')}")
        
        if moderate:
            print("\n⚠️  MODERATE RECOMMENDATIONS:")
            for i, rec in enumerate(moderate, 1):
                print(f"\n  {i}. {rec.get('title', 'N/A')}")
                print(f"     📝 {rec.get('description', 'N/A')}")
                print(f"     💰 Benefit: {rec.get('expected_benefit', 'N/A')}")
        
        if optional:
            print("\nℹ️  OPTIONAL RECOMMENDATIONS:")
            for i, rec in enumerate(optional, 1):
                print(f"\n  {i}. {rec.get('title', 'N/A')}")
                print(f"     📝 {rec.get('description', 'N/A')[:80]}...")
        
        print("\n" + "=" * 70)
        print("✅ MAX INTEGRATION TEST COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_max_with_real_data())
