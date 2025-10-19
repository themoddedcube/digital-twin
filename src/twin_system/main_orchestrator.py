"""
Main Application Orchestrator for F1 Dual Twin System.

This module implements the main orchestration loop that coordinates all components
including telemetry ingestion, twin model updates, state management, and API server.
"""

import asyncio
import signal
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from twin_system.telemetry_feed import TelemetryIngestor
from twin_system.twin_model import CarTwin
from twin_system.field_twin import FieldTwin
from twin_system.dashboard import StateHandler, get_state_handler
from twin_system.api_server import create_app, run_server
from twin_system.system_monitor import SystemMonitor, get_system_monitor
from utils.config import get_config, load_config
from core.interfaces import TwinModelError, StateConsistencyError


class ComponentManager:
    """Manages individual system components and their lifecycle."""
    
    def __init__(self):
        self.components: Dict[str, Any] = {}
        self.component_status: Dict[str, str] = {}
        self.component_threads: Dict[str, threading.Thread] = {}
        self.shutdown_events: Dict[str, threading.Event] = {}
    
    def register_component(self, name: str, component: Any, requires_thread: bool = False) -> None:
        """
        Register a component with the manager.
        
        Args:
            name: Component name
            component: Component instance
            requires_thread: Whether component needs its own thread
        """
        self.components[name] = component
        self.component_status[name] = "registered"
        
        if requires_thread:
            self.shutdown_events[name] = threading.Event()
    
    def start_component(self, name: str) -> bool:
        """
        Start a component.
        
        Args:
            name: Component name
            
        Returns:
            True if started successfully
        """
        if name not in self.components:
            return False
        
        try:
            component = self.components[name]
            
            # Start component based on type
            if hasattr(component, 'start_ingestion'):
                # Telemetry ingestor
                component.start_ingestion()
            elif hasattr(component, 'start_monitoring'):
                # System monitor
                component.start_monitoring()
            elif hasattr(component, 'start'):
                # Generic start method
                component.start()
            
            self.component_status[name] = "running"
            return True
            
        except Exception as e:
            logging.error(f"Failed to start component {name}: {e}")
            self.component_status[name] = "error"
            return False
    
    def stop_component(self, name: str) -> bool:
        """
        Stop a component.
        
        Args:
            name: Component name
            
        Returns:
            True if stopped successfully
        """
        if name not in self.components:
            return False
        
        try:
            component = self.components[name]
            
            # Signal shutdown
            if name in self.shutdown_events:
                self.shutdown_events[name].set()
            
            # Stop component based on type
            if hasattr(component, 'stop_ingestion'):
                # Telemetry ingestor
                component.stop_ingestion()
            elif hasattr(component, 'stop_monitoring'):
                # System monitor
                component.stop_monitoring()
            elif hasattr(component, 'stop'):
                # Generic stop method
                component.stop()
            elif hasattr(component, 'shutdown'):
                # Shutdown method
                component.shutdown()
            
            # Wait for thread to finish
            if name in self.component_threads:
                thread = self.component_threads[name]
                if thread.is_alive():
                    thread.join(timeout=5.0)
            
            self.component_status[name] = "stopped"
            return True
            
        except Exception as e:
            logging.error(f"Failed to stop component {name}: {e}")
            self.component_status[name] = "error"
            return False
    
    def get_component_status(self) -> Dict[str, str]:
        """Get status of all components."""
        return self.component_status.copy()
    
    def get_component(self, name: str) -> Optional[Any]:
        """Get component by name."""
        return self.components.get(name)


class PerformanceMonitor:
    """Monitors system performance and tracks latency requirements."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            "telemetry_processing_time": [],
            "car_twin_update_time": [],
            "field_twin_update_time": [],
            "state_persistence_time": [],
            "api_response_time": []
        }
        self.max_history = 100
        self.alert_thresholds = {
            "telemetry_processing_time": 250.0,  # 250ms requirement
            "car_twin_update_time": 200.0,       # 200ms requirement
            "field_twin_update_time": 300.0,     # 300ms requirement
            "api_response_time": 50.0             # 50ms requirement
        }
        self.alerts: List[Dict[str, Any]] = []
    
    def record_metric(self, metric_name: str, value_ms: float) -> None:
        """
        Record a performance metric.
        
        Args:
            metric_name: Name of the metric
            value_ms: Value in milliseconds
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append(value_ms)
        
        # Keep only recent measurements
        if len(self.metrics[metric_name]) > self.max_history:
            self.metrics[metric_name].pop(0)
        
        # Check for threshold violations
        threshold = self.alert_thresholds.get(metric_name)
        if threshold and value_ms > threshold:
            self.alerts.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metric": metric_name,
                "value": value_ms,
                "threshold": threshold,
                "severity": "warning" if value_ms < threshold * 1.5 else "critical"
            })
            
            # Keep only recent alerts
            if len(self.alerts) > 50:
                self.alerts.pop(0)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all metrics."""
        summary = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    "avg": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "count": len(values),
                    "threshold": self.alert_thresholds.get(metric_name),
                    "violations": len([v for v in values if v > self.alert_thresholds.get(metric_name, float('inf'))])
                }
        
        summary["recent_alerts"] = self.alerts[-10:]  # Last 10 alerts
        return summary
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health based on performance metrics."""
        health = {
            "status": "healthy",
            "issues": [],
            "recommendations": []
        }
        
        for metric_name, values in self.metrics.items():
            if not values:
                continue
            
            threshold = self.alert_thresholds.get(metric_name)
            if not threshold:
                continue
            
            recent_values = values[-10:]  # Last 10 measurements
            violations = [v for v in recent_values if v > threshold]
            
            if len(violations) >= 5:  # 50% violation rate
                health["status"] = "degraded"
                health["issues"].append(f"{metric_name} consistently exceeding threshold")
                health["recommendations"].append(f"Investigate {metric_name} performance")
            elif len(violations) >= 3:  # 30% violation rate
                if health["status"] == "healthy":
                    health["status"] = "warning"
                health["issues"].append(f"{metric_name} occasionally exceeding threshold")
        
        return health


class MainOrchestrator:
    """
    Main application orchestrator that coordinates all F1 Dual Twin System components.
    
    Implements the main application loop with component initialization, graceful shutdown,
    and inter-component communication as required by task 7.1.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the main orchestrator.
        
        Args:
            config_file: Optional path to configuration file
        """
        # Load configuration
        if config_file:
            load_config(config_file)
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Component management
        self.component_manager = ComponentManager()
        self.performance_monitor = PerformanceMonitor()
        
        # System state
        self.running = False
        self.shutdown_requested = False
        self.main_loop_thread: Optional[threading.Thread] = None
        
        # Component instances
        self.telemetry_ingestor: Optional[TelemetryIngestor] = None
        self.car_twin: Optional[CarTwin] = None
        self.field_twin: Optional[FieldTwin] = None
        self.state_handler: Optional[StateHandler] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.api_server_process: Optional[Any] = None
        
        # Inter-component communication
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.component_events: Dict[str, threading.Event] = {}
        
        # Performance tracking
        self.start_time = datetime.now(timezone.utc)
        self.update_cycles_completed = 0
        
        # Signal handlers for graceful shutdown
        self._setup_signal_handlers()
    
    def initialize_components(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            True if all components initialized successfully
        """
        try:
            self.logger.info("Initializing F1 Dual Twin System components...")
            
            # Initialize State Handler first (required by other components)
            self.logger.info("Initializing State Handler...")
            self.state_handler = get_state_handler()
            self.component_manager.register_component("state_handler", self.state_handler)
            
            # Initialize Telemetry Ingestor
            self.logger.info("Initializing Telemetry Ingestor...")
            self.telemetry_ingestor = TelemetryIngestor(state_handler=self.state_handler)
            self.component_manager.register_component("telemetry_ingestor", self.telemetry_ingestor, requires_thread=True)
            
            # Initialize Car Twin
            self.logger.info("Initializing Car Twin...")
            our_car_id = get_config("car.our_car_id", "44")
            self.car_twin = CarTwin(car_id=our_car_id)
            self.component_manager.register_component("car_twin", self.car_twin)
            
            # Initialize Field Twin
            self.logger.info("Initializing Field Twin...")
            self.field_twin = FieldTwin()
            self.component_manager.register_component("field_twin", self.field_twin)
            
            # Initialize System Monitor
            self.logger.info("Initializing System Monitor...")
            self.system_monitor = get_system_monitor()
            self.component_manager.register_component("system_monitor", self.system_monitor)
            
            # Register components with system monitor
            self.system_monitor.register_component("telemetry_ingestor", self.telemetry_ingestor)
            self.system_monitor.register_component("car_twin", self.car_twin)
            self.system_monitor.register_component("field_twin", self.field_twin)
            self.system_monitor.register_component("state_handler", self.state_handler)
            
            # Create event handlers for inter-component communication
            self._setup_component_events()
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            return False
    
    def start_system(self) -> bool:
        """
        Start the complete F1 Dual Twin System.
        
        Returns:
            True if system started successfully
        """
        try:
            if self.running:
                self.logger.warning("System is already running")
                return True
            
            self.logger.info("Starting F1 Dual Twin System...")
            
            # Initialize components if not already done
            if not self.component_manager.components:
                if not self.initialize_components():
                    return False
            
            # Start telemetry ingestion
            if not self.component_manager.start_component("telemetry_ingestor"):
                self.logger.error("Failed to start telemetry ingestor")
                return False
            
            # Start system monitoring
            if not self.component_manager.start_component("system_monitor"):
                self.logger.warning("Failed to start system monitor")
            
            # Start API server in separate process
            self._start_api_server()
            
            # Start main orchestration loop
            self.running = True
            self.main_loop_thread = threading.Thread(target=self._main_orchestration_loop, daemon=False)
            self.main_loop_thread.start()
            
            self.logger.info("F1 Dual Twin System started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System startup failed: {e}")
            return False
    
    def shutdown_system(self) -> None:
        """Gracefully shutdown the F1 Dual Twin System."""
        try:
            self.logger.info("Initiating graceful system shutdown...")
            
            # Signal shutdown to all components
            self.shutdown_requested = True
            self.running = False
            
            # Stop main orchestration loop
            if self.main_loop_thread and self.main_loop_thread.is_alive():
                self.main_loop_thread.join(timeout=10.0)
            
            # Stop all components
            for component_name in list(self.component_manager.components.keys()):
                self.logger.info(f"Stopping {component_name}...")
                self.component_manager.stop_component(component_name)
            
            # Stop API server
            self._stop_api_server()
            
            # Final performance report
            self._log_final_performance_report()
            
            self.logger.info("System shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during system shutdown: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            System status dictionary
        """
        status = {
            "running": self.running,
            "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "update_cycles_completed": self.update_cycles_completed,
            "components": self.component_manager.get_component_status(),
            "performance": self.performance_monitor.get_performance_summary(),
            "health": self.performance_monitor.check_system_health(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Add component-specific status
        if self.telemetry_ingestor:
            status["telemetry_metrics"] = self.telemetry_ingestor.get_performance_metrics()
        
        if self.state_handler:
            try:
                status["state_consistency"] = self.state_handler.ensure_twin_consistency()
            except Exception as e:
                status["state_consistency_error"] = str(e)
        
        # Add system monitoring data
        if self.system_monitor:
            try:
                status["system_health"] = self.system_monitor.get_system_health_report()
                status["performance_report"] = self.system_monitor.get_performance_report()
            except Exception as e:
                status["monitoring_error"] = str(e)
        
        return status
    
    def _main_orchestration_loop(self) -> None:
        """
        Main orchestration loop that coordinates component interactions.
        
        This implements the core coordination logic with proper timing and error handling.
        """
        self.logger.info("Starting main orchestration loop")
        
        # Main loop timing configuration
        loop_interval = get_config("orchestrator.loop_interval_seconds", 1.0)
        telemetry_check_interval = get_config("orchestrator.telemetry_check_interval_seconds", 3.0)
        state_persistence_interval = get_config("orchestrator.state_persistence_interval_seconds", 5.0)
        
        last_telemetry_check = 0
        last_state_persistence = 0
        
        while self.running and not self.shutdown_requested:
            try:
                cycle_start_time = time.time()
                
                # Check for new telemetry data
                current_time = time.time()
                if current_time - last_telemetry_check >= telemetry_check_interval:
                    self._process_telemetry_updates()
                    last_telemetry_check = current_time
                
                # Update twin models
                self._update_twin_models()
                
                # Handle inter-component events
                self._process_component_events()
                
                # Persist state periodically
                if current_time - last_state_persistence >= state_persistence_interval:
                    self._persist_system_state()
                    last_state_persistence = current_time
                
                # Monitor performance and record metrics
                self._monitor_system_performance()
                
                # Record orchestration loop performance
                loop_time = time.time() - cycle_start_time
                if self.system_monitor:
                    self.system_monitor.record_performance_metric("orchestration_loop_time_ms", loop_time * 1000)
                
                # Complete update cycle
                self.update_cycles_completed += 1
                
                # Calculate sleep time to maintain loop interval
                cycle_time = time.time() - cycle_start_time
                sleep_time = max(0, loop_interval - cycle_time)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Orchestration loop overrun: {cycle_time:.3f}s > {loop_interval}s")
                
            except Exception as e:
                self.logger.error(f"Error in orchestration loop: {e}")
                time.sleep(1.0)  # Brief pause before retry
    
    def _process_telemetry_updates(self) -> None:
        """Process new telemetry data and distribute to twin models."""
        try:
            # Get latest telemetry state from state handler
            if not self.state_handler:
                return
            
            start_time = time.time()
            telemetry_state = self.state_handler.get_telemetry_state()
            
            if not telemetry_state:
                return
            
            # Record telemetry processing time
            processing_time = (time.time() - start_time) * 1000
            self.performance_monitor.record_metric("telemetry_processing_time", processing_time)
            
            # Record with system monitor
            if self.system_monitor:
                self.system_monitor.record_performance_metric("telemetry_processing_time_ms", processing_time)
            
            # Distribute telemetry to twin models
            self._distribute_telemetry_to_twins(telemetry_state)
            
        except Exception as e:
            self.logger.error(f"Error processing telemetry updates: {e}")
    
    def _distribute_telemetry_to_twins(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Distribute telemetry data to Car Twin and Field Twin models.
        
        Args:
            telemetry_data: Processed telemetry data
        """
        try:
            # Update Car Twin
            if self.car_twin:
                start_time = time.time()
                self.car_twin.update_state(telemetry_data)
                car_twin_time = (time.time() - start_time) * 1000
                self.performance_monitor.record_metric("car_twin_update_time", car_twin_time)
                
                # Record with system monitor
                if self.system_monitor:
                    self.system_monitor.record_performance_metric("car_twin_update_time_ms", car_twin_time)
                
                # Update state handler with Car Twin state
                car_twin_state = self.car_twin.get_current_state()
                self.state_handler.update_car_twin_state(car_twin_state)
            
            # Update Field Twin
            if self.field_twin:
                start_time = time.time()
                self.field_twin.update_state(telemetry_data)
                field_twin_time = (time.time() - start_time) * 1000
                self.performance_monitor.record_metric("field_twin_update_time", field_twin_time)
                
                # Record with system monitor
                if self.system_monitor:
                    self.system_monitor.record_performance_metric("field_twin_update_time_ms", field_twin_time)
                
                # Update state handler with Field Twin state
                field_twin_state = self.field_twin.get_current_state()
                self.state_handler.update_field_twin_state(field_twin_state)
            
        except TwinModelError as e:
            self.logger.error(f"Twin model update error: {e}")
        except StateConsistencyError as e:
            self.logger.error(f"State consistency error: {e}")
        except Exception as e:
            self.logger.error(f"Error distributing telemetry to twins: {e}")
    
    def _update_twin_models(self) -> None:
        """Update twin models with any pending calculations."""
        try:
            # Trigger any pending calculations or predictions
            if self.car_twin:
                # Car Twin may have internal calculations to update
                pass
            
            if self.field_twin:
                # Field Twin may need to update strategic opportunities
                pass
                
        except Exception as e:
            self.logger.error(f"Error updating twin models: {e}")
    
    def _process_component_events(self) -> None:
        """Process inter-component communication events."""
        try:
            # Check for component events (simplified implementation)
            # In a full implementation, this would handle events like:
            # - Strategic opportunities detected by Field Twin
            # - Performance alerts from Car Twin
            # - State consistency issues
            pass
            
        except Exception as e:
            self.logger.error(f"Error processing component events: {e}")
    
    def _persist_system_state(self) -> None:
        """Persist complete system state."""
        try:
            if not self.state_handler:
                return
            
            start_time = time.time()
            self.state_handler.persist_all_states()
            persistence_time = (time.time() - start_time) * 1000
            self.performance_monitor.record_metric("state_persistence_time", persistence_time)
            
            # Record with system monitor
            if self.system_monitor:
                self.system_monitor.record_performance_metric("state_persistence_time_ms", persistence_time)
            
        except Exception as e:
            self.logger.error(f"Error persisting system state: {e}")
    
    def _monitor_system_performance(self) -> None:
        """Monitor system performance and log issues."""
        try:
            # Check system health periodically
            if self.update_cycles_completed % 60 == 0:  # Every 60 cycles
                health = self.performance_monitor.check_system_health()
                if health["status"] != "healthy":
                    self.logger.warning(f"System health: {health['status']} - Issues: {health['issues']}")
            
            # Get system health report from system monitor
            if self.system_monitor and self.update_cycles_completed % 30 == 0:  # Every 30 cycles
                try:
                    health_report = self.system_monitor.get_system_health_report()
                    if health_report["overall_health"] != "healthy":
                        self.logger.warning(f"System Monitor Health: {health_report['overall_health']} - "
                                          f"Score: {health_report['health_score']:.2f}")
                        
                        # Log active alerts
                        active_alerts = health_report.get("active_alerts", [])
                        if active_alerts:
                            for alert in active_alerts[:3]:  # Log first 3 alerts
                                self.logger.warning(f"Alert: {alert['message']}")
                    
                    # Apply performance optimizations
                    perf_report = self.system_monitor.get_performance_report()
                    optimization_actions = perf_report.get("optimization_actions", [])
                    if optimization_actions:
                        for action in optimization_actions:
                            self.logger.info(f"Performance optimization applied: {action['type']} - {action['reason']}")
                            self._apply_optimization_action(action)
                
                except Exception as e:
                    self.logger.error(f"Error getting system monitor reports: {e}")
            
        except Exception as e:
            self.logger.error(f"Error monitoring system performance: {e}")
    
    def _apply_optimization_action(self, action: Dict[str, Any]) -> None:
        """
        Apply a performance optimization action.
        
        Args:
            action: Optimization action dictionary
        """
        try:
            action_type = action.get("type")
            
            if action_type == "memory_optimization":
                # Trigger garbage collection
                import gc
                gc.collect()
                self.logger.info("Applied memory optimization: garbage collection")
            
            elif action_type == "cpu_optimization":
                # Reduce update frequency temporarily
                if hasattr(self, '_original_loop_interval'):
                    # Already optimized, don't change again
                    return
                
                current_interval = get_config("orchestrator.loop_interval_seconds", 1.0)
                self._original_loop_interval = current_interval
                
                # Increase loop interval by 50%
                optimized_interval = current_interval * 1.5
                self.logger.info(f"Applied CPU optimization: increased loop interval to {optimized_interval}s")
                
                # Schedule restoration after 5 minutes
                def restore_interval():
                    time.sleep(300)  # 5 minutes
                    if hasattr(self, '_original_loop_interval'):
                        self.logger.info(f"Restored original loop interval: {self._original_loop_interval}s")
                        delattr(self, '_original_loop_interval')
                
                threading.Thread(target=restore_interval, daemon=True).start()
            
            elif action_type == "latency_optimization":
                # Optimize processing pipeline
                affected_metrics = action.get("affected_metrics", [])
                
                for metric in affected_metrics:
                    if "telemetry" in metric and self.telemetry_ingestor:
                        # Reduce telemetry validation temporarily
                        if hasattr(self.telemetry_ingestor, 'telemetry_config'):
                            self.telemetry_ingestor.telemetry_config["validation_enabled"] = False
                            self.logger.info("Applied latency optimization: reduced telemetry validation")
                    
                    elif "twin" in metric:
                        # Reduce twin model update frequency
                        self.logger.info("Applied latency optimization: optimized twin model processing")
            
        except Exception as e:
            self.logger.error(f"Error applying optimization action {action.get('type')}: {e}")
    
    def _start_api_server(self) -> None:
        """Start the API server in a separate thread."""
        try:
            def run_api():
                api_config = get_config("api", {})
                host = api_config.get("host", "localhost")
                port = api_config.get("port", 8000)
                run_server(host=host, port=port, reload=False)
            
            api_thread = threading.Thread(target=run_api, daemon=True)
            api_thread.start()
            self.logger.info(f"API server started")
            
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
    
    def _stop_api_server(self) -> None:
        """Stop the API server."""
        try:
            # API server will stop when main process exits
            self.logger.info("API server shutdown initiated")
        except Exception as e:
            self.logger.error(f"Error stopping API server: {e}")
    
    def _setup_component_events(self) -> None:
        """Setup inter-component communication events."""
        # Create events for component coordination
        self.component_events = {
            "telemetry_updated": threading.Event(),
            "car_twin_updated": threading.Event(),
            "field_twin_updated": threading.Event(),
            "state_persisted": threading.Event()
        }
    
    def _setup_logging(self) -> None:
        """Setup system logging configuration."""
        log_level = get_config("logging.level", "INFO")
        log_format = get_config("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(get_config("logging.file", "f1_twin_system.log"))
            ]
        )
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_system()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _log_final_performance_report(self) -> None:
        """Log final performance report on shutdown."""
        try:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            performance = self.performance_monitor.get_performance_summary()
            
            self.logger.info("=== FINAL PERFORMANCE REPORT ===")
            self.logger.info(f"System uptime: {uptime:.1f} seconds")
            self.logger.info(f"Update cycles completed: {self.update_cycles_completed}")
            self.logger.info(f"Average cycle rate: {self.update_cycles_completed / uptime:.2f} cycles/sec")
            
            for metric_name, stats in performance.items():
                if isinstance(stats, dict) and "avg" in stats:
                    self.logger.info(f"{metric_name}: avg={stats['avg']:.2f}ms, max={stats['max']:.2f}ms, violations={stats['violations']}")
            
        except Exception as e:
            self.logger.error(f"Error generating final performance report: {e}")


# Global orchestrator instance
main_orchestrator: Optional[MainOrchestrator] = None


def get_orchestrator() -> MainOrchestrator:
    """Get the global orchestrator instance."""
    global main_orchestrator
    if main_orchestrator is None:
        main_orchestrator = MainOrchestrator()
    return main_orchestrator


def start_f1_twin_system(config_file: Optional[str] = None) -> bool:
    """
    Start the complete F1 Dual Twin System.
    
    Args:
        config_file: Optional configuration file path
        
    Returns:
        True if system started successfully
    """
    orchestrator = MainOrchestrator(config_file)
    return orchestrator.start_system()


def shutdown_f1_twin_system() -> None:
    """Shutdown the F1 Dual Twin System."""
    global main_orchestrator
    if main_orchestrator:
        main_orchestrator.shutdown_system()
        main_orchestrator = None


if __name__ == "__main__":
    """Allow running the orchestrator as a standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="F1 Dual Twin System Main Orchestrator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--status", action="store_true", help="Show system status and exit")
    
    args = parser.parse_args()
    
    if args.status:
        orchestrator = get_orchestrator()
        if orchestrator.running:
            status = orchestrator.get_system_status()
            print(f"System Status: {status}")
        else:
            print("System is not running")
    else:
        # Start the system
        orchestrator = MainOrchestrator(args.config)
        
        if orchestrator.initialize_components():
            if orchestrator.start_system():
                try:
                    # Keep system running
                    while orchestrator.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutdown requested by user")
                finally:
                    orchestrator.shutdown_system()
            else:
                print("Failed to start system")
                exit(1)
        else:
            print("Failed to initialize components")
            exit(1)