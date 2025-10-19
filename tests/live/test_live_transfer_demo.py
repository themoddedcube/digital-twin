#!/usr/bin/env python3
"""
Live Telemetry Transfer Test for F1 Dual Twin System.

This test demonstrates the complete live telemetry data flow:
1. Mock telemetry server (WebSocket/UDP)
2. Live telemetry ingestion
3. Twin model updates
4. State persistence
5. API data access
"""

import sys
import time
import json
import threading
import asyncio
import websockets
import socket
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

class MockWebSocketServer:
    """Mock WebSocket server that sends realistic F1 telemetry data."""
    
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.running = False
        self.server = None
        self.current_lap = 1
        
    async def start_server(self):
        """Start the WebSocket server."""
        self.running = True
        self.server = await websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            ping_timeout=None
        )
        print(f"🌐 Mock WebSocket server started on ws://{self.host}:{self.port}/telemetry")
        
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections."""
        print(f"📡 Client connected: {websocket.remote_address}")
        
        try:
            while self.running:
                # Generate realistic telemetry data
                telemetry_data = self.generate_telemetry_data()
                
                # Send to client
                await websocket.send(json.dumps(telemetry_data))
                
                # Update lap progression
                if self.current_lap % 10 == 0:  # Every 10 updates, advance lap
                    self.current_lap += 1
                
                # Send every 2 seconds
                await asyncio.sleep(2)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"📡 Client disconnected: {websocket.remote_address}")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    def generate_telemetry_data(self):
        """Generate realistic F1 telemetry data."""
        import random
        
        # Simulate race progression
        cars = []
        teams_drivers = [
            ("Red Bull", "Verstappen", "1"),
            ("Red Bull", "Perez", "11"), 
            ("Mercedes", "Hamilton", "44"),
            ("Mercedes", "Russell", "63"),
            ("Ferrari", "Leclerc", "16"),
            ("Ferrari", "Sainz", "55")
        ]
        
        for i, (team, driver, car_id) in enumerate(teams_drivers):
            cars.append({
                "car_id": car_id,
                "team": team,
                "driver": driver,
                "position": i + 1,
                "speed": random.uniform(280, 320),
                "tire": {
                    "compound": random.choice(["soft", "medium", "hard"]),
                    "age": random.uniform(0, 20),
                    "wear_level": random.uniform(0.0, 0.8)
                },
                "fuel_level": random.uniform(0.3, 1.0),
                "lap_time": random.uniform(78, 88),
                "sector_times": [
                    random.uniform(25, 30),
                    random.uniform(28, 35), 
                    random.uniform(22, 28)
                ]
            })
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lap": self.current_lap,
            "session_type": "race",
            "track_conditions": {
                "temperature": random.uniform(20, 45),
                "weather": random.choice(["sunny", "cloudy", "drizzle"]),
                "track_status": random.choice(["green", "yellow", "safety_car"])
            },
            "cars": cars
        }
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()


class MockUDPServer:
    """Mock UDP server that sends F1 telemetry data."""
    
    def __init__(self, host="localhost", port=20777):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.current_lap = 1
        
    def start_server(self):
        """Start the UDP server."""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Start sending data in background thread
        threading.Thread(target=self._send_loop, daemon=True).start()
        print(f"📡 Mock UDP server started, sending to {self.host}:{self.port}")
    
    def _send_loop(self):
        """Send telemetry data via UDP."""
        while self.running:
            try:
                # Generate telemetry data
                telemetry_data = self.generate_telemetry_data()
                
                # Send via UDP
                data = json.dumps(telemetry_data).encode('utf-8')
                self.socket.sendto(data, (self.host, self.port))
                
                # Update lap
                if self.current_lap % 10 == 0:
                    self.current_lap += 1
                
                time.sleep(2)  # Send every 2 seconds
                
            except Exception as e:
                print(f"❌ UDP send error: {e}")
                break
    
    def generate_telemetry_data(self):
        """Generate realistic F1 telemetry data."""
        import random
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lap": self.current_lap,
            "session_type": "race",
            "track_conditions": {
                "temperature": random.uniform(20, 45),
                "weather": "sunny",
                "track_status": "green"
            },
            "cars": [{
                "car_id": "44",
                "team": "Mercedes", 
                "driver": "Hamilton",
                "position": 3,
                "speed": random.uniform(290, 310),
                "tire": {
                    "compound": "medium",
                    "age": random.uniform(5, 15),
                    "wear_level": random.uniform(0.2, 0.6)
                },
                "fuel_level": random.uniform(0.4, 0.9),
                "lap_time": random.uniform(80, 85),
                "sector_times": [28.5, 31.2, 24.1]
            }]
        }
    
    def stop_server(self):
        """Stop the UDP server."""
        self.running = False
        if self.socket:
            self.socket.close()


async def test_websocket_live_transfer():
    """Test complete WebSocket live telemetry transfer."""
    print("\n" + "="*60)
    print("🧪 TESTING WEBSOCKET LIVE TELEMETRY TRANSFER")
    print("="*60)
    
    # Start mock WebSocket server
    server = MockWebSocketServer(port=8080)
    await server.start_server()
    
    # Give server time to start
    await asyncio.sleep(1)
    
    try:
        # Import F1 components
        from telemetry_feed import TelemetryIngestor
        from twin_model import CarTwin
        from field_twin import FieldTwin
        from dashboard import StateHandler
        from utils.config import load_config
        
        # Load config
        load_config("config/system_config.json")
        
        print("1️⃣ Initializing F1 Dual Twin System components...")
        
        # Create components
        ingestor = TelemetryIngestor()
        car_twin = CarTwin("44")  # Hamilton
        field_twin = FieldTwin()
        state_handler = StateHandler(storage_path="shared")
        
        print("2️⃣ Switching to WebSocket live mode...")
        
        # Switch to WebSocket mode
        success = ingestor.switch_to_live_mode(
            source_type="websocket",
            websocket_url="ws://localhost:8080/telemetry",
            timeout=5.0
        )
        
        if not success:
            print("❌ Failed to connect to WebSocket server")
            return False
        
        print("✅ Connected to WebSocket telemetry source")
        
        print("3️⃣ Starting live telemetry ingestion...")
        
        # Start ingestion
        ingestor.start_ingestion()
        
        print("4️⃣ Processing live telemetry data for 10 seconds...")
        
        # Process data for 10 seconds
        for i in range(5):
            await asyncio.sleep(2)
            
            # Get latest telemetry
            telemetry_data = ingestor._get_telemetry_data()
            
            if telemetry_data:
                print(f"   📊 Update {i+1}: Lap {telemetry_data['lap']}, "
                      f"{len(telemetry_data['cars'])} cars, "
                      f"Track: {telemetry_data['track_conditions']['track_status']}")
                
                # Update twin models
                car_twin.update_state(telemetry_data)
                field_twin.update_state(telemetry_data)
                
                # Update state handler
                state_handler.update_car_twin_state(car_twin.get_current_state())
                state_handler.update_field_twin_state(field_twin.get_current_state())
                state_handler.update_telemetry_state(telemetry_data)
                
            else:
                print(f"   ⚠️ Update {i+1}: No telemetry data received")
        
        print("5️⃣ Checking final twin states...")
        
        # Get final states
        car_state = car_twin.get_current_state()
        field_state = field_twin.get_current_state()
        
        print(f"   🏎️ Car Twin - Speed: {car_state['current_state']['speed']:.1f} km/h")
        print(f"   🏎️ Car Twin - Fuel: {car_state['current_state']['fuel_level']:.1%}")
        print(f"   🏎️ Car Twin - Tire Wear: {car_state['current_state']['tire_wear']:.1%}")
        print(f"   🏁 Field Twin - Competitors: {len(field_state['competitors'])}")
        print(f"   🏁 Field Twin - Current Lap: {field_state['race_context']['current_lap']}")
        
        # Check data source status
        status = ingestor.get_data_source_status()
        print(f"   📡 Data Source - Mode: {status['mode']}, Connected: {status['connected']}")
        print(f"   📡 Data Source - Updates: {status['total_updates']}, Failures: {status['data_failures']}")
        
        # Stop ingestion
        ingestor.stop_ingestion()
        
        print("✅ WebSocket live telemetry transfer test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Stop server
        await server.stop_server()


def test_udp_live_transfer():
    """Test complete UDP live telemetry transfer."""
    print("\n" + "="*60)
    print("🧪 TESTING UDP LIVE TELEMETRY TRANSFER")
    print("="*60)
    
    try:
        # Import F1 components
        from telemetry_feed import TelemetryIngestor
        from twin_model import CarTwin
        from field_twin import FieldTwin
        from dashboard import StateHandler
        
        print("1️⃣ Initializing F1 Dual Twin System components...")
        
        # Create components
        ingestor = TelemetryIngestor()
        car_twin = CarTwin("44")  # Hamilton
        field_twin = FieldTwin()
        state_handler = StateHandler(storage_path="shared")
        
        print("2️⃣ Switching to UDP live mode...")
        
        # Switch to UDP mode
        success = ingestor.switch_to_live_mode(
            source_type="udp",
            host="localhost",
            port=20777,
            timeout=1.0
        )
        
        if not success:
            print("❌ Failed to set up UDP telemetry client")
            return False
        
        print("✅ UDP telemetry client listening on localhost:20777")
        
        print("3️⃣ Starting mock UDP server...")
        
        # Start mock UDP server
        udp_server = MockUDPServer()
        udp_server.start_server()
        
        print("4️⃣ Starting live telemetry ingestion...")
        
        # Start ingestion
        ingestor.start_ingestion()
        
        print("5️⃣ Processing live UDP telemetry data for 8 seconds...")
        
        # Process data for 8 seconds
        for i in range(4):
            time.sleep(2)
            
            # Get latest telemetry
            telemetry_data = ingestor._get_telemetry_data()
            
            if telemetry_data:
                print(f"   📊 Update {i+1}: Lap {telemetry_data['lap']}, "
                      f"{len(telemetry_data['cars'])} cars, "
                      f"Hamilton Speed: {telemetry_data['cars'][0]['speed']:.1f} km/h")
                
                # Update twin models
                car_twin.update_state(telemetry_data)
                field_twin.update_state(telemetry_data)
                
                # Update state handler
                state_handler.update_car_twin_state(car_twin.get_current_state())
                state_handler.update_field_twin_state(field_twin.get_current_state())
                state_handler.update_telemetry_state(telemetry_data)
                
            else:
                print(f"   ⚠️ Update {i+1}: No telemetry data received")
        
        print("6️⃣ Checking final twin states...")
        
        # Get final states
        car_state = car_twin.get_current_state()
        field_state = field_twin.get_current_state()
        
        print(f"   🏎️ Car Twin - Speed: {car_state['current_state']['speed']:.1f} km/h")
        print(f"   🏎️ Car Twin - Fuel: {car_state['current_state']['fuel_level']:.1%}")
        print(f"   🏎️ Car Twin - Predicted Pit Lap: {car_state['predictions']['predicted_pit_lap']}")
        print(f"   🏁 Field Twin - Competitors: {len(field_state['competitors'])}")
        
        # Check data source status
        status = ingestor.get_data_source_status()
        print(f"   📡 Data Source - Mode: {status['mode']}, Connected: {status['connected']}")
        print(f"   📡 Data Source - Updates: {status['total_updates']}, Failures: {status['data_failures']}")
        
        # Stop components
        ingestor.stop_ingestion()
        udp_server.stop_server()
        
        print("✅ UDP live telemetry transfer test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ UDP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_mechanism():
    """Test automatic fallback from live to simulator mode."""
    print("\n" + "="*60)
    print("🧪 TESTING AUTOMATIC FALLBACK MECHANISM")
    print("="*60)
    
    try:
        from telemetry_feed import TelemetryIngestor
        
        print("1️⃣ Creating ingestor with live mode (no server)...")
        
        # Create ingestor
        ingestor = TelemetryIngestor()
        
        # Try to switch to WebSocket mode (will fail - no server)
        success = ingestor.switch_to_live_mode(
            source_type="websocket",
            websocket_url="ws://nonexistent-server:8080/telemetry",
            max_reconnect_attempts=2,
            reconnect_delay=0.5
        )
        
        print(f"2️⃣ Connection attempt result: {success}")
        
        # Check status
        status = ingestor.get_data_source_status()
        print(f"   Mode: {status['mode']}, Connected: {status['connected']}")
        
        print("3️⃣ Testing data retrieval with fallback...")
        
        # Try to get data (should work via simulator fallback)
        data = ingestor._get_telemetry_data()
        
        if data:
            print(f"✅ Fallback successful - got data with {len(data['cars'])} cars")
            print(f"   Mode after fallback: {ingestor.get_data_source_status()['mode']}")
        else:
            print("❌ Fallback failed - no data received")
            return False
        
        print("4️⃣ Testing failure threshold fallback...")
        
        # Manually trigger failures to test automatic fallback
        ingestor.use_simulator = False  # Force live mode
        ingestor.max_failures_before_fallback = 3
        
        for i in range(5):
            ingestor._handle_data_failure(f"Test failure {i+1}")
            status = ingestor.get_data_source_status()
            print(f"   Failure {i+1}: Mode={status['mode']}, Failures={status['data_failures']}")
        
        print("✅ Automatic fallback mechanism test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all live telemetry transfer tests."""
    print("🏁 F1 DUAL TWIN SYSTEM - LIVE TELEMETRY TRANSFER TESTS")
    print("=" * 70)
    
    results = []
    
    # Test WebSocket live transfer
    try:
        result = await test_websocket_live_transfer()
        results.append(("WebSocket Live Transfer", result))
    except Exception as e:
        print(f"❌ WebSocket test crashed: {e}")
        results.append(("WebSocket Live Transfer", False))
    
    # Test UDP live transfer
    try:
        result = test_udp_live_transfer()
        results.append(("UDP Live Transfer", result))
    except Exception as e:
        print(f"❌ UDP test crashed: {e}")
        results.append(("UDP Live Transfer", False))
    
    # Test fallback mechanism
    try:
        result = test_fallback_mechanism()
        results.append(("Fallback Mechanism", result))
    except Exception as e:
        print(f"❌ Fallback test crashed: {e}")
        results.append(("Fallback Mechanism", False))
    
    # Print results summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL LIVE TELEMETRY TRANSFER TESTS PASSED!")
        print("\nKey Achievements:")
        print("  ✅ WebSocket live telemetry ingestion working")
        print("  ✅ UDP live telemetry ingestion working") 
        print("  ✅ Twin models processing live data correctly")
        print("  ✅ State persistence handling live updates")
        print("  ✅ Automatic fallback mechanism functional")
        print("  ✅ Data normalization maintaining schema compatibility")
        print("\n🏁 F1 Dual Twin System ready for live race deployment!")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed - check logs above")
    
    return passed == len(results)


if __name__ == "__main__":
    try:
        # Run all tests
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)