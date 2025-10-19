"""
Main system startup script for F1 Race Strategy System

This script starts all components of the system:
- HPC Orchestrator (WebSocket server)
- Telemetry Feed Generator
- Dashboard (Streamlit)
"""

import asyncio
import subprocess
import sys
import os
import time
from multiprocessing import Process
import signal

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from hpc_orchestrator import HPCOrchestrator
from telemetry_feed import TelemetryGenerator, TelemetryStreamer


class SystemManager:
    """Manages all system components"""
    
    def __init__(self):
        self.processes = []
        self.running = False
    
    def start_hpc_orchestrator(self):
        """Start HPC orchestrator in background"""
        print("🔧 Starting HPC Orchestrator...")
        
        async def run_orchestrator():
            orchestrator = HPCOrchestrator("car_44")
            await orchestrator.start_websocket_server()
        
        # Run in new event loop
        asyncio.run(run_orchestrator())
    
    def start_telemetry_feed(self):
        """Start telemetry feed generator"""
        print("📡 Starting Telemetry Feed...")
        
        generator = TelemetryGenerator()
        streamer = TelemetryStreamer(generator, interval=1.5)
        
        async def run_telemetry():
            await streamer.start_streaming()
        
        asyncio.run(run_telemetry())
    
    def start_dashboard(self):
        """Start Streamlit dashboard"""
        print("📊 Starting Dashboard...")
        
        # Run Streamlit dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/dashboard.py", "--server.port", "8501"
        ])
    
    def start_system(self):
        """Start all system components"""
        print("🏎️ Starting F1 Race Strategy System...")
        print("=" * 50)
        
        try:
            # Start HPC Orchestrator in background process
            orchestrator_process = Process(target=self.start_hpc_orchestrator)
            orchestrator_process.start()
            self.processes.append(orchestrator_process)
            
            # Wait a moment for orchestrator to start
            time.sleep(2)
            
            # Start telemetry feed in background process
            telemetry_process = Process(target=self.start_telemetry_feed)
            telemetry_process.start()
            self.processes.append(telemetry_process)
            
            # Wait a moment for telemetry to start
            time.sleep(2)
            
            # Start dashboard (this will block)
            self.start_dashboard()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down system...")
            self.shutdown()
        except Exception as e:
            print(f"❌ Error starting system: {e}")
            self.shutdown()
    
    def shutdown(self):
        """Shutdown all processes"""
        print("🛑 Shutting down all processes...")
        
        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
        
        print("✅ System shutdown complete")


def main():
    """Main function"""
    print("🏎️ F1 Race Strategy System - Startup")
    print("=" * 50)
    print("This will start:")
    print("  - HPC Orchestrator (WebSocket server on port 8765)")
    print("  - Telemetry Feed Generator")
    print("  - Streamlit Dashboard (http://localhost:8501)")
    print("=" * 50)
    
    # Check if required packages are installed
    try:
        import streamlit
        import websockets
        import aiohttp
        print("✅ Required packages are installed")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return
    
    # Check if Mojo is available
    try:
        result = subprocess.run(["mojo", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Mojo available: {result.stdout.strip()}")
        else:
            print("⚠️  Mojo not available - simulation will use mock data")
    except FileNotFoundError:
        print("⚠️  Mojo not found in PATH - simulation will use mock data")
    
    # Start system
    system_manager = SystemManager()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Received interrupt signal...")
        system_manager.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    system_manager.start_system()


if __name__ == "__main__":
    main()
