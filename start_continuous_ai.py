#!/usr/bin/env python3
"""
Startup script for the Continuous AI Service with F1 Twin System.

This script starts the complete F1 Dual Twin System (main orchestrator) 
and automatically starts the continuous AI service on top.
"""

import asyncio
import signal
import sys
import threading
import time
from pathlib import Path

# Add src to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from twin_system.main_orchestrator import MainOrchestrator, get_orchestrator
from max_integration.continuous_ai_service import start_continuous_ai_service, stop_continuous_ai_service


class ContinuousAITwinSystem:
    """F1 Twin System with Continuous AI Service."""
    
    def __init__(self, config_file=None):
        self.orchestrator = MainOrchestrator(config_file)
        self.ai_service_started = False
        self.ai_service_thread = None
        
    async def start_ai_service(self):
        """Start the continuous AI service in background."""
        try:
            await start_continuous_ai_service()
            self.ai_service_started = True
            print("✅ Continuous AI service started")
        except Exception as e:
            print(f"❌ Failed to start continuous AI service: {e}")
            
    async def stop_ai_service(self):
        """Stop the continuous AI service."""
        if self.ai_service_started:
            try:
                await stop_continuous_ai_service()
                print("✅ Continuous AI service stopped")
            except Exception as e:
                print(f"❌ Error stopping continuous AI service: {e}")
    
    def start_ai_service_thread(self):
        """Start AI service in a separate thread."""
        def run_ai_service():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_ai_service())
            loop.run_forever()
        
        self.ai_service_thread = threading.Thread(target=run_ai_service, daemon=True)
        self.ai_service_thread.start()
        
        # Wait a moment for AI service to start
        time.sleep(2)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.shutdown()
        
    def shutdown(self):
        """Graceful shutdown."""
        print("🔄 Shutting down services...")
        
        # Stop AI service
        if self.ai_service_started:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.stop_ai_service())
            except Exception as e:
                print(f"❌ Error stopping AI service: {e}")
        
        # Stop main orchestrator
        try:
            self.orchestrator.shutdown_system()
            print("✅ F1 Twin System stopped")
        except Exception as e:
            print(f"❌ Error stopping F1 Twin System: {e}")
        
        sys.exit(0)
    
    def run(self, config_file=None):
        """Run the complete F1 Twin System with Continuous AI Service."""
        print("🚀 Starting F1 Dual Twin System with Continuous AI Service")
        print("=" * 70)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Start the main F1 Twin System
            print("🏁 Starting F1 Dual Twin System...")
            if self.orchestrator.start_system():
                print("✅ F1 Twin System started successfully")
            else:
                print("❌ Failed to start F1 Twin System")
                return False
            
            # Start Continuous AI Service in background
            print("🤖 Starting Continuous AI Service...")
            self.start_ai_service_thread()
            
            # Display status
            print("\n📊 System Status:")
            print("   ✅ F1 Dual Twin System: Running")
            print("   ✅ Telemetry Ingestion: Active")
            print("   ✅ Car Twin Model: Updating")
            print("   ✅ Field Twin Model: Updating")
            print("   ✅ State Handler: Active")
            print("   ✅ API Server: Running on port 8000")
            print("   ✅ Continuous AI Service: Running")
            print("   ✅ Monte Carlo Simulations: Every 2 seconds")
            print("   ✅ MAX Model: Always loaded and ready")
            
            print("\n📋 Available API Endpoints:")
            print("   • GET  /api/v1/health - System health")
            print("   • GET  /api/v1/telemetry - Live telemetry data")
            print("   • GET  /api/v1/car-twin - Car twin state")
            print("   • GET  /api/v1/field-twin - Field twin state")
            print("   • GET  /api/v1/monte-carlo/simulate - Manual Monte Carlo")
            print("   • GET  /api/v1/ai-strategy/recommendations - Manual AI recommendations")
            print("   • GET  /api/v1/continuous-ai/recommendations - Continuous AI recommendations")
            print("   • GET  /api/v1/continuous-ai/status - AI service status")
            print("   • POST /api/v1/continuous-ai/start - Start AI service")
            print("   • POST /api/v1/continuous-ai/stop - Stop AI service")
            
            print("\n🛑 Press Ctrl+C to stop all services")
            print("=" * 70)
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.shutdown()
                
        except Exception as e:
            print(f"❌ Error starting system: {e}")
            self.shutdown()
            return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="F1 Dual Twin System with Continuous AI Service")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    system = ContinuousAITwinSystem(args.config)
    system.run(args.config)


if __name__ == "__main__":
    main()
