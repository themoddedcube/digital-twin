"""
Demo script for F1 Race Strategy System

This script demonstrates the complete system in action with live updates.
"""

import asyncio
import json
import time
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from twin_model import DigitalTwin, FieldTwin, create_sample_race_state
from telemetry_feed import TelemetryGenerator, TelemetryStreamer
from ai_strategist import AIStrategist
from hpc_orchestrator import HPCOrchestrator


class SystemDemo:
    """Demonstrates the complete F1 strategy system"""
    
    def __init__(self):
        self.orchestrator = HPCOrchestrator("car_44")
        self.telemetry_generator = TelemetryGenerator()
        self.running = False
    
    async def run_demo(self, duration_minutes: int = 5):
        """Run the complete system demo"""
        print("🏎️ F1 Race Strategy System - Live Demo")
        print("=" * 60)
        print(f"Running for {duration_minutes} minutes...")
        print("Press Ctrl+C to stop early")
        print("=" * 60)
        
        self.running = True
        start_time = time.time()
        lap_count = 0
        
        try:
            while self.running and (time.time() - start_time) < duration_minutes * 60:
                # Generate telemetry
                telemetry = self.telemetry_generator.generate_telemetry()
                lap_count += 1
                
                print(f"\n🏁 Lap {telemetry.lap} - {datetime.now().strftime('%H:%M:%S')}")
                print("-" * 40)
                
                # Process through orchestrator
                await self.orchestrator.process_telemetry(telemetry.__dict__)
                
                # Display current state
                await self._display_current_state()
                
                # Display recommendations
                await self._display_recommendations()
                
                # Wait for next lap
                await asyncio.sleep(2.0)  # 2 seconds per lap for demo
                
        except KeyboardInterrupt:
            print("\n🛑 Demo stopped by user")
        finally:
            self.running = False
            await self._display_final_summary(lap_count)
    
    async def _display_current_state(self):
        """Display current race state"""
        if not self.orchestrator.current_race_state:
            return
        
        race_state = self.orchestrator.current_race_state
        
        # Show top 3 positions
        print("🏆 Top 3 Positions:")
        for i, car in enumerate(race_state.cars[:3]):
            tire_info = f"{car.tire.compound} ({car.tire.wear_level:.1%})"
            print(f"  {i+1}. {car.driver} - {car.lap_time:.2f}s - {tire_info}")
        
        # Show our car's state
        if self.orchestrator.digital_twin.current_state:
            twin = self.orchestrator.digital_twin.current_state
            print(f"\n🚗 Our Car ({twin.current_state.driver}):")
            print(f"   Position: P{twin.current_state.position}")
            print(f"   Tire: {twin.current_state.tire.compound} ({twin.current_state.tire.wear_level:.1%})")
            print(f"   Fuel: {twin.current_state.fuel_level:.1%}")
            print(f"   Lap Time: {twin.current_state.lap_time:.2f}s")
    
    async def _display_recommendations(self):
        """Display AI recommendations"""
        recommendations = self.orchestrator.strategy_recommendations
        
        if not recommendations:
            print("🤖 No AI recommendations available")
            return
        
        print(f"\n🤖 AI Strategy Recommendations ({len(recommendations)} total):")
        
        # Group by priority
        urgent = [r for r in recommendations if r.get("priority") == "urgent"]
        moderate = [r for r in recommendations if r.get("priority") == "moderate"]
        optional = [r for r in recommendations if r.get("priority") == "optional"]
        
        if urgent:
            print("  🚨 URGENT:")
            for rec in urgent[:2]:  # Show top 2
                print(f"    • {rec.get('title', 'Unknown')}")
                print(f"      {rec.get('description', 'No description')}")
        
        if moderate:
            print("  ⚠️  MODERATE:")
            for rec in moderate[:2]:  # Show top 2
                print(f"    • {rec.get('title', 'Unknown')}")
                print(f"      {rec.get('description', 'No description')}")
        
        if optional:
            print("  ℹ️  OPTIONAL:")
            for rec in optional[:1]:  # Show top 1
                print(f"    • {rec.get('title', 'Unknown')}")
                print(f"      {rec.get('description', 'No description')}")
    
    async def _display_final_summary(self, total_laps: int):
        """Display final demo summary"""
        print("\n" + "=" * 60)
        print("📊 Demo Summary")
        print("=" * 60)
        print(f"Total laps processed: {total_laps}")
        print(f"Simulation results: {len(self.orchestrator.simulation_results)}")
        print(f"AI recommendations: {len(self.orchestrator.strategy_recommendations)}")
        
        # Performance metrics
        metrics = self.orchestrator.get_performance_metrics()
        print(f"\n⚡ Performance Metrics:")
        print(f"  Average simulation time: {metrics['avg_simulation_time']:.3f}s")
        print(f"  Average LLM response time: {metrics['avg_llm_response_time']:.3f}s")
        print(f"  Total simulations: {metrics['total_simulations']}")
        print(f"  Active connections: {metrics['active_connections']}")
        
        print("\n🎉 Demo completed successfully!")
        print("To see the full dashboard, run: streamlit run src/dashboard.py")


async def main():
    """Main demo function"""
    demo = SystemDemo()
    
    print("Choose demo duration:")
    print("1. Quick demo (2 minutes)")
    print("2. Standard demo (5 minutes)")
    print("3. Extended demo (10 minutes)")
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            duration = 2
        elif choice == "2":
            duration = 5
        elif choice == "3":
            duration = 10
        else:
            print("Invalid choice, using standard demo (5 minutes)")
            duration = 5
        
        await demo.run_demo(duration)
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted")
    except Exception as e:
        print(f"❌ Demo error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
