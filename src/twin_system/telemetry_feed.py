"""
Telemetry ingestion system for F1 Dual Twin System.

This module handles continuous telemetry data collection, validation, and normalization
with support for both live telemetry sources and realistic F1 race data simulation.
"""

import json
import time
import random
import threading
import socket
import asyncio
import websockets
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
import logging
from pathlib import Path
from abc import ABC, abstractmethod

from core.schemas import TELEMETRY_SCHEMA, validate_json_schema
from utils.config import load_config


class TelemetrySimulator:
    """Generates realistic F1 telemetry data for testing and development."""
    
    def __init__(self):
        self.current_lap = 1
        self.session_type = "race"
        self.race_start_time = datetime.now(timezone.utc)
        self.track_conditions = {
            "temperature": 25.0,
            "weather": "sunny",
            "track_status": "green"
        }
        
        # Initialize 20 F1 cars with realistic data
        self.cars = self._initialize_cars()
        
    def _initialize_cars(self) -> List[Dict[str, Any]]:
        """Initialize F1 grid with realistic car data."""
        teams_drivers = [
            ("Red Bull", "Verstappen", "1"),
            ("Red Bull", "Perez", "11"),
            ("Mercedes", "Hamilton", "44"),
            ("Mercedes", "Russell", "63"),
            ("Ferrari", "Leclerc", "16"),
            ("Ferrari", "Sainz", "55"),
            ("McLaren", "Norris", "4"),
            ("McLaren", "Piastri", "81"),
            ("Aston Martin", "Alonso", "14"),
            ("Aston Martin", "Stroll", "18"),
            ("Alpine", "Ocon", "31"),
            ("Alpine", "Gasly", "10"),
            ("Williams", "Albon", "23"),
            ("Williams", "Sargeant", "2"),
            ("AlphaTauri", "Tsunoda", "22"),
            ("AlphaTauri", "Ricciardo", "3"),
            ("Alfa Romeo", "Bottas", "77"),
            ("Alfa Romeo", "Zhou", "24"),
            ("Haas", "Hulkenberg", "27"),
            ("Haas", "Magnussen", "20")
        ]
        
        cars = []
        for i, (team, driver, car_id) in enumerate(teams_drivers):
            car = {
                "car_id": car_id,
                "team": team,
                "driver": driver,
                "position": i + 1,
                "speed": random.uniform(280, 320),
                "tire": {
                    "compound": random.choice(["soft", "medium", "hard"]),
                    "age": random.randint(0, 15),
                    "wear_level": random.uniform(0.0, 0.3)
                },
                "fuel_level": random.uniform(0.6, 1.0),
                "lap_time": random.uniform(78.0, 88.0),
                "sector_times": [
                    random.uniform(25.0, 30.0),
                    random.uniform(28.0, 35.0),
                    random.uniform(22.0, 28.0)
                ]
            }
            cars.append(car)
        
        return cars
    
    def generate_telemetry_update(self) -> Dict[str, Any]:
        """Generate a realistic telemetry update."""
        # Update lap progression (DEMO: 4x faster lap progression)
        if random.random() < 0.2:  # Was 5%, now 20% chance to advance lap
            self.current_lap += 1
            
        # Simulate track condition changes
        self._update_track_conditions()
        
        # Update car data with realistic progression
        self._update_car_data()
        
        telemetry_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lap": self.current_lap,
            "session_type": self.session_type,
            "track_conditions": self.track_conditions.copy(),
            "cars": [car.copy() for car in self.cars]
        }
        
        return telemetry_data
    
    def _update_track_conditions(self):
        """Simulate realistic track condition changes (DEMO: More dramatic changes)."""
        # Temperature variation (DEMO: 10x more dramatic)
        self.track_conditions["temperature"] += random.uniform(-3.0, 3.0)  # Was ±0.5, now ±3.0
        self.track_conditions["temperature"] = max(10.0, min(60.0, self.track_conditions["temperature"]))  # Wider range
        
        # Weather changes (DEMO: 100x more frequent)
        if random.random() < 0.1:  # Was 0.1%, now 10% chance
            weather_options = ["sunny", "cloudy", "drizzle", "rain"]
            self.track_conditions["weather"] = random.choice(weather_options)
        
        # Track status changes (DEMO: 200x more frequent)
        if random.random() < 0.1:  # Was 0.05%, now 10% chance
            status_options = ["green", "yellow", "safety_car", "red"]
            self.track_conditions["track_status"] = random.choice(status_options)
    
    def _update_car_data(self):
        """Update car data with realistic race progression."""
        for car in self.cars:
            # Speed variation based on track conditions and tire wear (DEMO: 10x more dramatic)
            base_speed_variation = random.uniform(-25, 25)  # Was ±5, now ±25
            tire_wear_penalty = car["tire"]["wear_level"] * 50  # Was 10, now 50
            car["speed"] += base_speed_variation - tire_wear_penalty
            car["speed"] = max(180, min(380, car["speed"]))  # Wider range for demo
            
            # Tire wear progression (DEMO: 20x faster degradation)
            car["tire"]["age"] += random.uniform(0, 0.5)  # Was 0.1, now 0.5
            car["tire"]["wear_level"] += random.uniform(0, 0.1)  # Was 0.005, now 0.1
            car["tire"]["wear_level"] = min(1.0, car["tire"]["wear_level"])
            
            # Fuel consumption (DEMO: 10x faster consumption)
            car["fuel_level"] -= random.uniform(0.01, 0.03)  # Was 0.001-0.003, now 0.01-0.03
            car["fuel_level"] = max(0.0, car["fuel_level"])
            
            # Lap time variation (DEMO: 5x more dramatic)
            car["lap_time"] += random.uniform(-5.0, 5.0)  # Was ±1.0, now ±5.0
            car["lap_time"] = max(65.0, min(100.0, car["lap_time"]))  # Wider range
            
            # Update sector times (DEMO: 3x more variation)
            for i in range(3):
                car["sector_times"][i] += random.uniform(-1.5, 1.5)  # Was ±0.5, now ±1.5
                car["sector_times"][i] = max(12.0, min(55.0, car["sector_times"][i]))  # Wider range
            
            # Position changes (DEMO: 10x more frequent overtakes)
            if random.random() < 0.1:  # Was 1%, now 10% chance
                other_car = random.choice(self.cars)
                if abs(car["position"] - other_car["position"]) == 1:
                    car["position"], other_car["position"] = other_car["position"], car["position"]


class BaseTelemetryClient(ABC):
    """Abstract base class for telemetry data sources."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the telemetry source."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the telemetry source."""
        pass
    
    @abstractmethod
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get the latest telemetry data."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the telemetry source."""
        pass


class WebSocketTelemetryClient(BaseTelemetryClient):
    """WebSocket-based live telemetry client for F1 data streams."""
    
    def __init__(self, websocket_url: str, timeout: float = 5.0):
        """
        Initialize WebSocket telemetry client.
        
        Args:
            websocket_url: WebSocket URL for telemetry stream
            timeout: Connection timeout in seconds
        """
        self.websocket_url = websocket_url
        self.timeout = timeout
        self.websocket = None
        self.connected = False
        self.last_data = None
        self.logger = logging.getLogger(__name__)
        
        # Background task for receiving data
        self._receive_task = None
        self._stop_event = threading.Event()
    
    def connect(self) -> bool:
        """Connect to WebSocket telemetry source."""
        try:
            # Start async event loop in background thread
            self._receive_task = threading.Thread(target=self._run_websocket_loop, daemon=True)
            self._receive_task.start()
            
            # Wait for connection
            time.sleep(1)
            return self.connected
            
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        self._stop_event.set()
        self.connected = False
        if self._receive_task and self._receive_task.is_alive():
            self._receive_task.join(timeout=2.0)
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get the latest telemetry data from WebSocket."""
        if not self.connected:
            return None
        
        # Return normalized data
        if self.last_data:
            return self._normalize_websocket_data(self.last_data)
        return None
    
    def is_connected(self) -> bool:
        """Check WebSocket connection status."""
        return self.connected
    
    def _run_websocket_loop(self):
        """Run WebSocket event loop in background thread."""
        try:
            asyncio.run(self._websocket_handler())
        except Exception as e:
            self.logger.error(f"WebSocket loop error: {e}")
            self.connected = False
    
    async def _websocket_handler(self):
        """Handle WebSocket connection and data reception."""
        try:
            # Use ping_timeout instead of timeout for websockets.connect
            async with websockets.connect(self.websocket_url, ping_timeout=self.timeout) as websocket:
                self.websocket = websocket
                self.connected = True
                self.logger.info(f"Connected to WebSocket: {self.websocket_url}")
                
                while not self._stop_event.is_set():
                    try:
                        # Receive data with timeout
                        data = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        
                        # Parse JSON data
                        telemetry_data = json.loads(data)
                        self.last_data = telemetry_data
                        
                    except asyncio.TimeoutError:
                        continue  # No data received, continue loop
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Invalid JSON received: {e}")
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        self.logger.warning("WebSocket connection closed")
                        break
                        
        except Exception as e:
            self.logger.error(f"WebSocket handler error: {e}")
        finally:
            self.connected = False
    
    def _normalize_websocket_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize WebSocket data to standard telemetry format.
        
        Args:
            raw_data: Raw WebSocket telemetry data
            
        Returns:
            Normalized telemetry data matching telemetry_state.json schema
        """
        # Default normalized structure
        normalized = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lap": 1,
            "session_type": "race",
            "track_conditions": {
                "temperature": 25.0,
                "weather": "sunny",
                "track_status": "green"
            },
            "cars": []
        }
        
        # Map common WebSocket fields to our schema
        if "timestamp" in raw_data:
            normalized["timestamp"] = raw_data["timestamp"]
        
        if "lap" in raw_data:
            normalized["lap"] = raw_data["lap"]
        
        if "session_type" in raw_data:
            normalized["session_type"] = raw_data["session_type"]
        
        # Map track conditions
        if "track_conditions" in raw_data:
            normalized["track_conditions"].update(raw_data["track_conditions"])
        
        # Map car data
        if "cars" in raw_data:
            for car_data in raw_data["cars"]:
                normalized_car = self._normalize_car_data(car_data)
                if normalized_car:
                    normalized["cars"].append(normalized_car)
        
        return normalized
    
    def _normalize_car_data(self, car_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize individual car data."""
        try:
            normalized_car = {
                "car_id": str(car_data.get("car_id", "unknown")),
                "team": car_data.get("team", "Unknown"),
                "driver": car_data.get("driver", "Unknown"),
                "position": int(car_data.get("position", 1)),
                "speed": float(car_data.get("speed", 0.0)),
                "tire": {
                    "compound": car_data.get("tire", {}).get("compound", "medium"),
                    "age": float(car_data.get("tire", {}).get("age", 0)),
                    "wear_level": float(car_data.get("tire", {}).get("wear_level", 0.0))
                },
                "fuel_level": float(car_data.get("fuel_level", 1.0)),
                "lap_time": float(car_data.get("lap_time", 90.0)),
                "sector_times": car_data.get("sector_times", [30.0, 30.0, 30.0])
            }
            
            # Ensure sector_times has exactly 3 elements
            if len(normalized_car["sector_times"]) != 3:
                normalized_car["sector_times"] = [30.0, 30.0, 30.0]
            
            return normalized_car
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error normalizing car data: {e}")
            return None


class UDPTelemetryClient(BaseTelemetryClient):
    """UDP-based live telemetry client for F1 game data or custom UDP streams."""
    
    def __init__(self, host: str = "localhost", port: int = 20777, timeout: float = 1.0):
        """
        Initialize UDP telemetry client.
        
        Args:
            host: UDP host address
            port: UDP port number
            timeout: Socket timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.connected = False
        self.last_data = None
        self.logger = logging.getLogger(__name__)
        
        # Background thread for receiving UDP packets
        self._receive_thread = None
        self._stop_event = threading.Event()
    
    def connect(self) -> bool:
        """Connect to UDP telemetry source."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
            self.socket.bind((self.host, self.port))
            
            self.connected = True
            
            # Start background thread for receiving data
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            self.logger.info(f"UDP telemetry client listening on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"UDP connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from UDP source."""
        self._stop_event.set()
        self.connected = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if self._receive_thread and self._receive_thread.is_alive():
            self._receive_thread.join(timeout=2.0)
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get the latest telemetry data from UDP."""
        if not self.connected:
            return None
        
        # Return normalized data
        if self.last_data:
            return self._normalize_udp_data(self.last_data)
        return None
    
    def is_connected(self) -> bool:
        """Check UDP connection status."""
        return self.connected
    
    def _receive_loop(self):
        """Background loop for receiving UDP packets."""
        while not self._stop_event.is_set() and self.connected:
            try:
                # Receive UDP packet
                data, addr = self.socket.recvfrom(4096)  # 4KB buffer
                
                # Try to parse as JSON
                try:
                    telemetry_data = json.loads(data.decode('utf-8'))
                    self.last_data = telemetry_data
                except json.JSONDecodeError:
                    # Handle binary UDP data (F1 game format)
                    parsed_data = self._parse_binary_udp(data)
                    if parsed_data:
                        self.last_data = parsed_data
                
            except socket.timeout:
                continue  # No data received, continue loop
            except Exception as e:
                if self.connected:  # Only log if we're supposed to be connected
                    self.logger.warning(f"UDP receive error: {e}")
                break
    
    def _parse_binary_udp(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse binary UDP data (e.g., from F1 games).
        
        This is a simplified parser - real implementation would need
        to handle specific F1 game UDP packet formats.
        """
        try:
            # This is a placeholder for F1 game UDP parsing
            # Real implementation would parse binary packet structure
            # For now, return None to indicate binary parsing not implemented
            return None
            
        except Exception as e:
            self.logger.warning(f"Binary UDP parsing error: {e}")
            return None
    
    def _normalize_udp_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize UDP data to standard telemetry format.
        
        Args:
            raw_data: Raw UDP telemetry data
            
        Returns:
            Normalized telemetry data matching telemetry_state.json schema
        """
        # Similar normalization logic as WebSocket client
        normalized = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lap": raw_data.get("lap", 1),
            "session_type": raw_data.get("session_type", "race"),
            "track_conditions": {
                "temperature": raw_data.get("track_temperature", 25.0),
                "weather": raw_data.get("weather", "sunny"),
                "track_status": raw_data.get("track_status", "green")
            },
            "cars": []
        }
        
        # Map car data
        if "cars" in raw_data:
            for car_data in raw_data["cars"]:
                normalized_car = self._normalize_car_data_udp(car_data)
                if normalized_car:
                    normalized["cars"].append(normalized_car)
        
        return normalized
    
    def _normalize_car_data_udp(self, car_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize UDP car data."""
        try:
            return {
                "car_id": str(car_data.get("car_id", "unknown")),
                "team": car_data.get("team", "Unknown"),
                "driver": car_data.get("driver", "Unknown"),
                "position": int(car_data.get("position", 1)),
                "speed": float(car_data.get("speed", 0.0)),
                "tire": {
                    "compound": car_data.get("tire_compound", "medium"),
                    "age": float(car_data.get("tire_age", 0)),
                    "wear_level": float(car_data.get("tire_wear", 0.0))
                },
                "fuel_level": float(car_data.get("fuel_level", 1.0)),
                "lap_time": float(car_data.get("lap_time", 90.0)),
                "sector_times": car_data.get("sector_times", [30.0, 30.0, 30.0])[:3]
            }
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error normalizing UDP car data: {e}")
            return None


class LiveTelemetryClient:
    """
    Unified live telemetry client that supports multiple data sources.
    
    This class provides a single interface for different telemetry sources
    (WebSocket, UDP, etc.) with automatic failover and reconnection.
    """
    
    def __init__(self, source_type: str = "websocket", **kwargs):
        """
        Initialize live telemetry client.
        
        Args:
            source_type: Type of telemetry source ("websocket", "udp")
            **kwargs: Source-specific configuration parameters
        """
        self.source_type = source_type
        self.client = None
        self.logger = logging.getLogger(__name__)
        
        # Create appropriate client based on source type
        if source_type == "websocket":
            websocket_url = kwargs.get("websocket_url", "ws://localhost:8080/telemetry")
            timeout = kwargs.get("timeout", 5.0)
            self.client = WebSocketTelemetryClient(websocket_url, timeout)
            
        elif source_type == "udp":
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 20777)
            timeout = kwargs.get("timeout", 1.0)
            self.client = UDPTelemetryClient(host, port, timeout)
            
        else:
            raise ValueError(f"Unsupported telemetry source type: {source_type}")
        
        # Connection management
        self.max_reconnect_attempts = kwargs.get("max_reconnect_attempts", 5)
        self.reconnect_delay = kwargs.get("reconnect_delay", 2.0)
        self.reconnect_attempts = 0
    
    def connect(self) -> bool:
        """Connect to live telemetry source with retry logic."""
        if not self.client:
            return False
        
        for attempt in range(self.max_reconnect_attempts):
            try:
                if self.client.connect():
                    self.reconnect_attempts = 0
                    self.logger.info(f"Connected to {self.source_type} telemetry source")
                    return True
                
                self.reconnect_attempts += 1
                if attempt < self.max_reconnect_attempts - 1:
                    self.logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {self.reconnect_delay}s...")
                    time.sleep(self.reconnect_delay)
                    
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt + 1} error: {e}")
                if attempt < self.max_reconnect_attempts - 1:
                    time.sleep(self.reconnect_delay)
        
        self.logger.error(f"Failed to connect to {self.source_type} telemetry source after {self.max_reconnect_attempts} attempts")
        return False
    
    def disconnect(self) -> None:
        """Disconnect from telemetry source."""
        if self.client:
            self.client.disconnect()
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """
        Get latest telemetry data with automatic reconnection.
        
        Returns:
            Normalized telemetry data or None if unavailable
        """
        if not self.client:
            return None
        
        # Check connection and attempt reconnect if needed
        if not self.client.is_connected():
            self.logger.warning("Telemetry source disconnected, attempting reconnection...")
            if not self.connect():
                return None
        
        # Get data from client
        try:
            return self.client.get_latest_data()
        except Exception as e:
            self.logger.error(f"Error getting telemetry data: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if connected to telemetry source."""
        return self.client and self.client.is_connected()


class TelemetryIngestor:
    """
    Main telemetry ingestion system with validation and normalization.
    
    Supports both live telemetry sources (WebSocket, UDP) and simulated data
    with seamless switching via configuration.
    """
    
    def __init__(self, config_path: str = "config/system_config.json", state_handler=None):
        self.config = load_config(config_path)
        self.telemetry_config = self.config.get("telemetry", {})
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.get("logging", {}).get("level", "INFO")),
            format=self.config.get("logging", {}).get("format", "%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger = logging.getLogger(__name__)
        
        # Data source configuration
        self.use_simulator = self.telemetry_config.get("use_simulator", True)
        self.live_source_type = self.telemetry_config.get("live_source_type", "websocket")
        
        # Initialize data sources
        self.simulator = TelemetrySimulator()
        self.live_telemetry_client = None
        
        # Initialize live client if not using simulator
        if not self.use_simulator:
            self._initialize_live_client()
        
        # State management
        self.state_handler = state_handler
        self.last_valid_data = None
        self.running = False
        self.ingestion_thread = None
        self.data_source_failures = 0
        self.max_failures_before_fallback = self.telemetry_config.get("max_failures_before_fallback", 5)
        
        # Performance tracking
        self.processing_times = []
        self.validation_failures = 0
        self.total_updates = 0
        
        self.logger.info(f"TelemetryIngestor initialized - Mode: {'Simulator' if self.use_simulator else f'Live ({self.live_source_type})'}")
    
    def _initialize_live_client(self) -> None:
        """Initialize live telemetry client based on configuration."""
        try:
            live_config = self.telemetry_config.get("live_source", {})
            
            if self.live_source_type == "websocket":
                websocket_url = live_config.get("websocket_url", "ws://localhost:8080/telemetry")
                timeout = live_config.get("timeout", 5.0)
                
                self.live_telemetry_client = LiveTelemetryClient(
                    source_type="websocket",
                    websocket_url=websocket_url,
                    timeout=timeout,
                    max_reconnect_attempts=live_config.get("max_reconnect_attempts", 5),
                    reconnect_delay=live_config.get("reconnect_delay", 2.0)
                )
                
            elif self.live_source_type == "udp":
                host = live_config.get("host", "localhost")
                port = live_config.get("port", 20777)
                timeout = live_config.get("timeout", 1.0)
                
                self.live_telemetry_client = LiveTelemetryClient(
                    source_type="udp",
                    host=host,
                    port=port,
                    timeout=timeout,
                    max_reconnect_attempts=live_config.get("max_reconnect_attempts", 5),
                    reconnect_delay=live_config.get("reconnect_delay", 2.0)
                )
                
            else:
                raise ValueError(f"Unsupported live source type: {self.live_source_type}")
                
            self.logger.info(f"Live telemetry client initialized: {self.live_source_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize live telemetry client: {e}")
            self.logger.info("Falling back to simulator mode")
            self.use_simulator = True
            self.live_telemetry_client = None
        
    def start_ingestion(self):
        """Start the telemetry ingestion loop."""
        if self.running:
            self.logger.warning("Telemetry ingestion already running")
            return
        
        # Connect to live telemetry source if not using simulator
        if not self.use_simulator and self.live_telemetry_client:
            if not self.live_telemetry_client.connect():
                self.logger.error("Failed to connect to live telemetry source, falling back to simulator")
                self.use_simulator = True
        
        self.running = True
        self.ingestion_thread = threading.Thread(target=self._ingestion_loop, daemon=True)
        self.ingestion_thread.start()
        
        mode = "Simulator" if self.use_simulator else f"Live ({self.live_source_type})"
        self.logger.info(f"Telemetry ingestion started - Mode: {mode}")
    
    def stop_ingestion(self):
        """Stop the telemetry ingestion loop."""
        self.running = False
        
        # Disconnect from live telemetry source
        if self.live_telemetry_client:
            self.live_telemetry_client.disconnect()
        
        # Wait for ingestion thread to finish
        if self.ingestion_thread:
            self.ingestion_thread.join(timeout=5.0)
        
        self.logger.info("Telemetry ingestion stopped")
    
    def _ingestion_loop(self):
        """Main ingestion loop with configurable update cycles for live/simulated data."""
        update_interval = self.telemetry_config.get("update_interval_seconds", 3)
        
        while self.running:
            try:
                start_time = time.time()
                
                # Get telemetry data from appropriate source
                raw_data = self._get_telemetry_data()
                
                if raw_data:
                    # Process the data
                    processed_data = self.ingest_telemetry(raw_data)
                    
                    if processed_data:
                        # Output to shared storage
                        self._output_telemetry_state(processed_data)
                        
                        # Update state handler if available
                        if self.state_handler:
                            try:
                                self.state_handler.update_telemetry_state(processed_data)
                            except Exception as e:
                                self.logger.error(f"Failed to update state handler: {e}")
                        
                        # Reset failure counter on successful processing
                        self.data_source_failures = 0
                    else:
                        self._handle_data_failure("Processing failed")
                else:
                    self._handle_data_failure("No data received")
                    
                # Track processing time
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                self.processing_times.append(processing_time)
                
                # Keep only last 100 measurements
                if len(self.processing_times) > 100:
                    self.processing_times.pop(0)
                
                self.total_updates += 1
                
                # Log performance metrics periodically
                if self.total_updates % 20 == 0:
                    avg_processing_time = sum(self.processing_times) / len(self.processing_times)
                    mode = "Simulator" if self.use_simulator else f"Live ({self.live_source_type})"
                    self.logger.info(f"[{mode}] Avg processing time: {avg_processing_time:.2f}ms, "
                                   f"Validation failures: {self.validation_failures}/{self.total_updates}, "
                                   f"Data failures: {self.data_source_failures}")
                
                # Sleep for remaining time in update cycle
                elapsed = time.time() - start_time
                sleep_time = max(0, update_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Error in ingestion loop: {e}")
                time.sleep(1)  # Brief pause before retry
    
    def _get_telemetry_data(self) -> Optional[Dict[str, Any]]:
        """
        Get telemetry data from the appropriate source (live or simulated).
        
        Returns:
            Raw telemetry data or None if unavailable
        """
        if self.use_simulator:
            # Get data from simulator
            return self.simulator.generate_telemetry_update()
        
        elif self.live_telemetry_client:
            # Get data from live source
            return self.live_telemetry_client.get_latest_data()
        
        else:
            self.logger.error("No telemetry data source available")
            return None
    
    def _handle_data_failure(self, reason: str) -> None:
        """
        Handle telemetry data source failures with automatic fallback.
        
        Args:
            reason: Reason for the failure
        """
        self.data_source_failures += 1
        
        if not self.use_simulator and self.data_source_failures >= self.max_failures_before_fallback:
            self.logger.warning(f"Live telemetry source failed {self.data_source_failures} times ({reason})")
            self.logger.info("Falling back to simulator mode for reliability")
            
            # Disconnect from live source
            if self.live_telemetry_client:
                self.live_telemetry_client.disconnect()
            
            # Switch to simulator mode
            self.use_simulator = True
            self.data_source_failures = 0
            
        elif self.data_source_failures % 5 == 0:  # Log every 5 failures
            self.logger.warning(f"Telemetry data failure #{self.data_source_failures}: {reason}")
    
    def switch_to_live_mode(self, source_type: str = None, **kwargs) -> bool:
        """
        Switch from simulator to live telemetry mode.
        
        Args:
            source_type: Type of live source ("websocket", "udp")
            **kwargs: Source-specific configuration
            
        Returns:
            True if successfully switched to live mode
        """
        if not self.use_simulator:
            self.logger.info("Already in live telemetry mode")
            return True
        
        try:
            # Update configuration if provided
            if source_type:
                self.live_source_type = source_type
                self.telemetry_config["live_source_type"] = source_type
            
            # Initialize new live client
            self._initialize_live_client()
            
            if self.live_telemetry_client and self.live_telemetry_client.connect():
                self.use_simulator = False
                self.data_source_failures = 0
                self.logger.info(f"Switched to live telemetry mode: {self.live_source_type}")
                return True
            else:
                self.logger.error("Failed to connect to live telemetry source")
                return False
                
        except Exception as e:
            self.logger.error(f"Error switching to live mode: {e}")
            return False
    
    def switch_to_simulator_mode(self) -> None:
        """Switch from live to simulator telemetry mode."""
        if self.use_simulator:
            self.logger.info("Already in simulator mode")
            return
        
        # Disconnect from live source
        if self.live_telemetry_client:
            self.live_telemetry_client.disconnect()
        
        # Switch to simulator
        self.use_simulator = True
        self.data_source_failures = 0
        self.logger.info("Switched to simulator telemetry mode")
    
    def get_data_source_status(self) -> Dict[str, Any]:
        """
        Get current data source status and statistics.
        
        Returns:
            Data source status information
        """
        status = {
            "mode": "simulator" if self.use_simulator else "live",
            "live_source_type": self.live_source_type,
            "connected": False,
            "data_failures": self.data_source_failures,
            "max_failures_before_fallback": self.max_failures_before_fallback,
            "total_updates": self.total_updates,
            "validation_failures": self.validation_failures
        }
        
        if not self.use_simulator and self.live_telemetry_client:
            status["connected"] = self.live_telemetry_client.is_connected()
        elif self.use_simulator:
            status["connected"] = True  # Simulator is always "connected"
        
        return status
    
    def ingest_telemetry(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process incoming telemetry data with validation and normalization.
        
        Args:
            raw_data: Raw telemetry data
            
        Returns:
            Processed and validated telemetry data, or None if processing failed
        """
        start_time = time.time()
        
        try:
            # Step 1: Normalize data format
            normalized_data = self.normalize_data(raw_data)
            
            # Step 2: Validate schema compliance
            if self.telemetry_config.get("validation_enabled", True):
                if not self.validate_schema(normalized_data):
                    self.validation_failures += 1
                    return self.handle_missing_data(normalized_data)
            
            # Step 3: Check processing time constraint
            processing_time = (time.time() - start_time) * 1000
            max_processing_time = self.telemetry_config.get("processing_timeout_ms", 250)
            
            if processing_time > max_processing_time:
                self.logger.warning(f"Processing time {processing_time:.2f}ms exceeded limit {max_processing_time}ms")
            
            # Update last valid data
            self.last_valid_data = normalized_data
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Error processing telemetry data: {e}")
            return self.handle_missing_data(raw_data)
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw telemetry data to standardized JSON format.
        
        Args:
            raw_data: Raw telemetry data
            
        Returns:
            Normalized telemetry data
        """
        # Ensure timestamp is in ISO format
        if "timestamp" in raw_data:
            if isinstance(raw_data["timestamp"], str):
                # Already a string, assume it's properly formatted
                pass
            else:
                # Convert to ISO format
                raw_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        else:
            raw_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Ensure required fields have default values
        normalized = {
            "timestamp": raw_data.get("timestamp"),
            "lap": raw_data.get("lap", 1),
            "session_type": raw_data.get("session_type", "race"),
            "track_conditions": raw_data.get("track_conditions", {
                "temperature": 25.0,
                "weather": "sunny",
                "track_status": "green"
            }),
            "cars": raw_data.get("cars", [])
        }
        
        # Normalize car data
        for car in normalized["cars"]:
            # Ensure all required car fields exist
            car.setdefault("car_id", "unknown")
            car.setdefault("team", "unknown")
            car.setdefault("driver", "unknown")
            car.setdefault("position", 1)
            car.setdefault("speed", 0.0)
            car.setdefault("fuel_level", 0.0)
            car.setdefault("lap_time", 90.0)
            
            # Normalize tire data
            if "tire" not in car:
                car["tire"] = {}
            car["tire"].setdefault("compound", "medium")
            car["tire"].setdefault("age", 0)
            car["tire"].setdefault("wear_level", 0.0)
            
            # Normalize sector times
            if "sector_times" not in car or len(car["sector_times"]) != 3:
                car["sector_times"] = [30.0, 30.0, 30.0]
        
        return normalized
    
    def validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        Validate telemetry data against schema.
        
        Args:
            data: Telemetry data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            return validate_json_schema(data, TELEMETRY_SCHEMA)
        except Exception as e:
            self.logger.error(f"Schema validation error: {e}")
            return False
    
    def handle_missing_data(self, corrupted_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle missing or corrupted telemetry data using fallback mechanisms.
        
        Args:
            corrupted_data: Corrupted or incomplete data
            
        Returns:
            Fallback data or None if no fallback available
        """
        if not self.telemetry_config.get("fallback_to_last_valid", True):
            return None
            
        if self.last_valid_data is None:
            self.logger.warning("No last valid data available for fallback")
            return None
        
        # Use last valid data with updated timestamp
        fallback_data = self.last_valid_data.copy()
        fallback_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        self.logger.warning("Using fallback data due to corrupted/missing telemetry")
        return fallback_data
    
    def _output_telemetry_state(self, telemetry_data: Dict[str, Any]):
        """
        Output telemetry state to shared storage.
        
        Args:
            telemetry_data: Processed telemetry data
        """
        output_file = self.telemetry_config.get("output_file", "shared/telemetry_state.json")
        
        try:
            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write telemetry data atomically
            temp_file = output_path.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(telemetry_data, f, indent=2)
            
            # Atomic move
            temp_file.replace(output_path)
            
        except Exception as e:
            self.logger.error(f"Error writing telemetry state: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        if not self.processing_times:
            return {}
            
        return {
            "avg_processing_time_ms": sum(self.processing_times) / len(self.processing_times),
            "max_processing_time_ms": max(self.processing_times),
            "min_processing_time_ms": min(self.processing_times),
            "total_updates": self.total_updates,
            "validation_failures": self.validation_failures,
            "failure_rate": self.validation_failures / max(1, self.total_updates)
        }


# Main execution for testing
if __name__ == "__main__":
    ingestor = TelemetryIngestor()
    
    try:
        ingestor.start_ingestion()
        print("Telemetry ingestion started. Press Ctrl+C to stop.")
        
        # Keep running until interrupted
        while True:
            time.sleep(10)
            metrics = ingestor.get_performance_metrics()
            if metrics:
                print(f"Performance: {metrics['avg_processing_time_ms']:.2f}ms avg, "
                      f"{metrics['total_updates']} updates, "
                      f"{metrics['failure_rate']:.2%} failure rate")
                
    except KeyboardInterrupt:
        print("\nStopping telemetry ingestion...")
        ingestor.stop_ingestion()
        print("Stopped.")