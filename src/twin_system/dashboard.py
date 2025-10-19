"""
State Handler implementation for the F1 Dual Twin System.

This module provides the main State Handler class that coordinates state management
between Car Twin and Field Twin models with atomic operations and persistence.
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.base_state import BaseStateManager
from core.interfaces import StateManager, StateConsistencyError
from utils.config import get_config
from twin_system.system_recovery import SystemRecoveryManager, RecoveryLevel, AuditEventType


class StateHandler(BaseStateManager):
    """
    Main State Handler for coordinating state management across twin models.
    
    Provides atomic operations, concurrency control, and 5-second update cycles
    as required by the system specifications.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize State Handler.
        
        Args:
            storage_path: Path to storage directory (uses config if not provided)
        """
        super().__init__(storage_path)
        
        # State management configuration
        self.update_cycle_seconds = get_config("state_management.persistence_interval_seconds", 5)
        self.auto_persistence_enabled = get_config("state_management.auto_persistence_enabled", True)
        
        # Twin state tracking
        self._car_twin_state: Dict[str, Any] = {}
        self._field_twin_state: Dict[str, Any] = {}
        self._telemetry_state: Dict[str, Any] = {}
        self._environment_state: Dict[str, Any] = {}
        
        # Concurrency control
        self._car_twin_lock = threading.RLock()
        self._field_twin_lock = threading.RLock()
        self._telemetry_lock = threading.RLock()
        self._environment_lock = threading.RLock()
        
        # Persistence control
        self._persistence_thread: Optional[threading.Thread] = None
        self._persistence_stop_event = threading.Event()
        self._last_car_twin_update = 0
        self._last_field_twin_update = 0
        self._last_telemetry_update = 0
        
        # Initialize recovery manager
        self.recovery_manager = SystemRecoveryManager(storage_path)
        
        # Attempt system recovery on startup
        self._perform_startup_recovery()
        
        # Initialize persistence thread if auto-persistence is enabled
        if self.auto_persistence_enabled:
            self._start_persistence_thread()
    
    def update_car_twin_state(self, state_data: Dict[str, Any]) -> None:
        """
        Update Car Twin state with atomic operations.
        
        Args:
            state_data: Car Twin state data
            
        Raises:
            StateConsistencyError: If update fails
        """
        try:
            with self._car_twin_lock:
                # Add update metadata
                state_data["last_update_timestamp"] = datetime.now(timezone.utc).isoformat()
                state_data["update_source"] = "car_twin"
                
                # Validate state data
                if not self._validate_car_twin_state(state_data):
                    raise StateConsistencyError("Invalid Car Twin state data")
                
                # Update internal state
                self._car_twin_state.update(state_data)
                self._last_car_twin_update = time.time()
                
                # Log the update
                if self.audit_logging_enabled:
                    self._log_audit_event("car_twin_state_updated", {
                        "car_id": state_data.get("car_id"),
                        "data_keys": list(state_data.keys()),
                        "timestamp": state_data["last_update_timestamp"]
                    })
                
                # Create recovery checkpoint
                self.recovery_manager.create_recovery_checkpoint("car_twin", state_data)
                
        except Exception as e:
            raise StateConsistencyError(f"Failed to update Car Twin state: {str(e)}")
    
    def update_field_twin_state(self, state_data: Dict[str, Any]) -> None:
        """
        Update Field Twin state with atomic operations.
        
        Args:
            state_data: Field Twin state data
            
        Raises:
            StateConsistencyError: If update fails
        """
        try:
            with self._field_twin_lock:
                # Add update metadata
                state_data["last_update_timestamp"] = datetime.now(timezone.utc).isoformat()
                state_data["update_source"] = "field_twin"
                
                # Validate state data
                if not self._validate_field_twin_state(state_data):
                    raise StateConsistencyError("Invalid Field Twin state data")
                
                # Update internal state
                self._field_twin_state.update(state_data)
                self._last_field_twin_update = time.time()
                
                # Log the update
                if self.audit_logging_enabled:
                    self._log_audit_event("field_twin_state_updated", {
                        "competitor_count": len(state_data.get("competitors", [])),
                        "opportunity_count": len(state_data.get("strategic_opportunities", [])),
                        "data_keys": list(state_data.keys()),
                        "timestamp": state_data["last_update_timestamp"]
                    })
                
                # Create recovery checkpoint
                self.recovery_manager.create_recovery_checkpoint("field_twin", state_data)
                
        except Exception as e:
            raise StateConsistencyError(f"Failed to update Field Twin state: {str(e)}")
    
    def update_telemetry_state(self, state_data: Dict[str, Any]) -> None:
        """
        Update telemetry state with atomic operations.
        
        Args:
            state_data: Telemetry state data
            
        Raises:
            StateConsistencyError: If update fails
        """
        try:
            with self._telemetry_lock:
                # Add update metadata
                state_data["last_update_timestamp"] = datetime.now(timezone.utc).isoformat()
                state_data["update_source"] = "telemetry_ingestor"
                
                # Validate state data
                if not self._validate_telemetry_state(state_data):
                    raise StateConsistencyError("Invalid telemetry state data")
                
                # Update internal state
                self._telemetry_state.update(state_data)
                self._last_telemetry_update = time.time()
                
                # Log the update
                if self.audit_logging_enabled:
                    self._log_audit_event("telemetry_state_updated", {
                        "lap": state_data.get("lap"),
                        "car_count": len(state_data.get("cars", [])),
                        "session_type": state_data.get("session_type"),
                        "timestamp": state_data["last_update_timestamp"]
                    })
                
                # Create recovery checkpoint
                self.recovery_manager.create_recovery_checkpoint("telemetry", state_data)
                
        except Exception as e:
            raise StateConsistencyError(f"Failed to update telemetry state: {str(e)}")
    
    def update_environment_state(self, state_data: Dict[str, Any]) -> None:
        """
        Update environment state (track conditions, weather, flags).
        
        Args:
            state_data: Environment state data
        """
        try:
            with self._environment_lock:
                # Add update metadata
                state_data["last_update_timestamp"] = datetime.now(timezone.utc).isoformat()
                state_data["update_source"] = "environment_monitor"
                
                # Update internal state
                self._environment_state.update(state_data)
                
                # Log the update
                if self.audit_logging_enabled:
                    self._log_audit_event("environment_state_updated", {
                        "data_keys": list(state_data.keys()),
                        "timestamp": state_data["last_update_timestamp"]
                    })
                
        except Exception as e:
            print(f"Warning: Failed to update environment state: {e}")
    
    def get_car_twin_state(self) -> Dict[str, Any]:
        """
        Get current Car Twin state (thread-safe).
        
        Returns:
            Car Twin state data copy
        """
        with self._car_twin_lock:
            return self._car_twin_state.copy()
    
    def get_field_twin_state(self) -> Dict[str, Any]:
        """
        Get current Field Twin state (thread-safe).
        
        Returns:
            Field Twin state data copy
        """
        with self._field_twin_lock:
            return self._field_twin_state.copy()
    
    def get_telemetry_state(self) -> Dict[str, Any]:
        """
        Get current telemetry state (thread-safe).
        
        Returns:
            Telemetry state data copy
        """
        with self._telemetry_lock:
            return self._telemetry_state.copy()
    
    def get_environment_state(self) -> Dict[str, Any]:
        """
        Get current environment state (thread-safe).
        
        Returns:
            Environment state data copy
        """
        with self._environment_lock:
            return self._environment_state.copy()
    
    def get_complete_system_state(self) -> Dict[str, Any]:
        """
        Get complete system state from all components.
        
        Returns:
            Complete system state with all twin data
        """
        return {
            "car_twin": self.get_car_twin_state(),
            "field_twin": self.get_field_twin_state(),
            "telemetry": self.get_telemetry_state(),
            "environment": self.get_environment_state(),
            "system_metadata": {
                "last_car_twin_update": self._last_car_twin_update,
                "last_field_twin_update": self._last_field_twin_update,
                "last_telemetry_update": self._last_telemetry_update,
                "state_handler_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def persist_all_states(self) -> None:
        """
        Persist all twin states to storage with atomic operations.
        
        This method implements the 5-second update cycle requirement.
        """
        try:
            # Get complete system state
            complete_state = self.get_complete_system_state()
            
            # Persist using base class atomic operations
            self.persist_state(complete_state)
            
            # Also write individual state files for component access
            self._write_individual_state_files()
            
        except Exception as e:
            print(f"Error persisting states: {e}")
            if self.audit_logging_enabled:
                self._log_audit_event("persistence_failed", {
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    def ensure_twin_consistency(self) -> bool:
        """
        Verify data consistency between Car Twin and Field Twin models.
        
        Returns:
            True if twins are consistent, False otherwise
        """
        try:
            car_twin_state = self.get_car_twin_state()
            field_twin_state = self.get_field_twin_state()
            
            # Use recovery manager for comprehensive consistency validation
            is_consistent, issues = self.recovery_manager.validate_data_consistency(
                car_twin_state, field_twin_state
            )
            
            if not is_consistent:
                # Log consistency issues
                if self.audit_logging_enabled:
                    self._log_audit_event("consistency_check_failed", {
                        "issues": issues,
                        "car_twin_keys": list(car_twin_state.keys()) if car_twin_state else [],
                        "field_twin_keys": list(field_twin_state.keys()) if field_twin_state else []
                    })
                
                # Attempt automatic recovery if enabled
                recovery_enabled = get_config("recovery.auto_recovery_on_inconsistency", True)
                if recovery_enabled:
                    success, recovered_states = self.recovery_manager.recover_from_interruption(RecoveryLevel.PARTIAL)
                    if success:
                        # Apply recovered states
                        if "car_twin" in recovered_states:
                            self._car_twin_state = recovered_states["car_twin"].get("state_data", {})
                        if "field_twin" in recovered_states:
                            self._field_twin_state = recovered_states["field_twin"].get("state_data", {})
                        
                        # Re-check consistency after recovery
                        return self.ensure_twin_consistency()
            
            return is_consistent
            
        except Exception as e:
            self.recovery_manager.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": f"Consistency check failed: {str(e)}",
                "operation": "ensure_twin_consistency"
            })
            return False
    
    def recover_system_state(self, recovery_level: RecoveryLevel = RecoveryLevel.FULL) -> bool:
        """
        Recover system state from interruption.
        
        Args:
            recovery_level: Level of recovery to perform
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            success, recovered_states = self.recovery_manager.recover_from_interruption(recovery_level)
            
            if success and recovered_states:
                # Apply recovered states to internal state
                with self._state_lock:
                    if "car_twin" in recovered_states:
                        checkpoint_data = recovered_states["car_twin"]
                        if "state_data" in checkpoint_data:
                            self._car_twin_state = checkpoint_data["state_data"]
                    
                    if "field_twin" in recovered_states:
                        checkpoint_data = recovered_states["field_twin"]
                        if "state_data" in checkpoint_data:
                            self._field_twin_state = checkpoint_data["state_data"]
                    
                    if "telemetry" in recovered_states:
                        checkpoint_data = recovered_states["telemetry"]
                        if "state_data" in checkpoint_data:
                            self._telemetry_state = checkpoint_data["state_data"]
                    
                    if "environment" in recovered_states:
                        checkpoint_data = recovered_states["environment"]
                        if "state_data" in checkpoint_data:
                            self._environment_state = checkpoint_data["state_data"]
                
                # Persist recovered state
                self.persist_all_states()
                
                self.recovery_manager.log_audit_event(AuditEventType.RECOVERY_COMPLETED, {
                    "recovery_level": recovery_level.value,
                    "recovered_components": list(recovered_states.keys()),
                    "success": True
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.recovery_manager.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": f"System recovery failed: {str(e)}",
                "recovery_level": recovery_level.value
            })
            return False
    
    def get_audit_log(self, hours_back: int = 24, event_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get audit log entries for the specified time period.
        
        Args:
            hours_back: Number of hours to look back
            event_types: List of event type strings to filter (optional)
            
        Returns:
            List of audit log entries
        """
        try:
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            # Convert string event types to enum if provided
            audit_event_types = None
            if event_types:
                audit_event_types = []
                for event_type_str in event_types:
                    try:
                        audit_event_types.append(AuditEventType(event_type_str))
                    except ValueError:
                        continue
            
            return self.recovery_manager.get_audit_log(
                start_time=start_time,
                event_types=audit_event_types
            )
            
        except Exception as e:
            print(f"Error retrieving audit log: {e}")
            return []
    
    def cleanup_old_data(self) -> None:
        """Clean up old audit logs and recovery data."""
        try:
            self.recovery_manager.cleanup_old_data()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def shutdown(self) -> None:
        """
        Gracefully shutdown the State Handler.
        
        Stops persistence thread and performs final state save.
        """
        try:
            # Log shutdown initiation
            self.recovery_manager.log_audit_event(AuditEventType.SYSTEM_SHUTDOWN, {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "graceful": True
            })
            
            # Stop persistence thread
            if self._persistence_thread and self._persistence_thread.is_alive():
                self._persistence_stop_event.set()
                self._persistence_thread.join(timeout=5)
            
            # Perform final state persistence
            self.persist_all_states()
            
            # Clean up old data
            self.cleanup_old_data()
            
            if self.audit_logging_enabled:
                self._log_audit_event("state_handler_shutdown", {
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
        except Exception as e:
            self.recovery_manager.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": f"Shutdown error: {str(e)}",
                "operation": "shutdown"
            })
            print(f"Error during State Handler shutdown: {e}")
    
    def _start_persistence_thread(self) -> None:
        """Start the automatic persistence thread."""
        def persistence_loop():
            while not self._persistence_stop_event.is_set():
                try:
                    # Wait for the configured interval
                    if self._persistence_stop_event.wait(self.update_cycle_seconds):
                        break  # Stop event was set
                    
                    # Persist all states
                    self.persist_all_states()
                    
                except Exception as e:
                    print(f"Error in persistence loop: {e}")
        
        self._persistence_thread = threading.Thread(target=persistence_loop, daemon=True)
        self._persistence_thread.start()
    
    def _write_individual_state_files(self) -> None:
        """Write individual state files for component access."""
        try:
            # Write telemetry state to the specified output file
            telemetry_output_file = get_config("telemetry.output_file", "shared/telemetry_state.json")
            telemetry_path = Path(telemetry_output_file)
            telemetry_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            
            # Write telemetry state
            telemetry_state = self.get_telemetry_state()
            if telemetry_state:
                temp_file = telemetry_path.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(telemetry_state, f, indent=2)
                temp_file.replace(telemetry_path)
            
            # Write car twin state
            car_twin_path = self.storage_path / "car_twin_state.json"
            car_twin_state = self.get_car_twin_state()
            if car_twin_state:
                temp_file = car_twin_path.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(car_twin_state, f, indent=2)
                temp_file.replace(car_twin_path)
            
            # Write field twin state
            field_twin_path = self.storage_path / "field_twin_state.json"
            field_twin_state = self.get_field_twin_state()
            if field_twin_state:
                temp_file = field_twin_path.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(field_twin_state, f, indent=2)
                temp_file.replace(field_twin_path)
            
        except Exception as e:
            print(f"Warning: Failed to write individual state files: {e}")
    
    def _validate_car_twin_state(self, state_data: Dict[str, Any]) -> bool:
        """
        Validate Car Twin state data.
        
        Args:
            state_data: State data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - check for required fields
            required_fields = ["car_id", "timestamp"]
            for field in required_fields:
                if field not in state_data:
                    return False
            
            # Validate car_id format
            car_id = state_data.get("car_id")
            if not isinstance(car_id, str) or not car_id.strip():
                return False
            
            # Validate timestamp format
            timestamp = state_data.get("timestamp")
            if timestamp:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            return True
            
        except Exception:
            return False
    
    def _validate_field_twin_state(self, state_data: Dict[str, Any]) -> bool:
        """
        Validate Field Twin state data.
        
        Args:
            state_data: State data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - check for required fields
            required_fields = ["timestamp"]
            for field in required_fields:
                if field not in state_data:
                    return False
            
            # Validate timestamp format
            timestamp = state_data.get("timestamp")
            if timestamp:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Validate competitors structure if present
            competitors = state_data.get("competitors")
            if competitors and not isinstance(competitors, list):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_telemetry_state(self, state_data: Dict[str, Any]) -> bool:
        """
        Validate telemetry state data.
        
        Args:
            state_data: State data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - check for required fields
            required_fields = ["timestamp", "lap"]
            for field in required_fields:
                if field not in state_data:
                    return False
            
            # Validate timestamp format
            timestamp = state_data.get("timestamp")
            if timestamp:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Validate lap number
            lap = state_data.get("lap")
            if not isinstance(lap, int) or lap < 0:
                return False
            
            # Validate cars structure if present
            cars = state_data.get("cars")
            if cars and not isinstance(cars, list):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _perform_startup_recovery(self) -> None:
        """Perform system recovery during startup."""
        try:
            self.recovery_manager.log_audit_event(AuditEventType.SYSTEM_STARTUP, {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "recovery_enabled": get_config("recovery.enabled", True)
            })
            
            # Attempt to recover from last valid state
            recovery_enabled = get_config("recovery.startup_recovery_enabled", True)
            if recovery_enabled:
                success = self.recover_system_state(RecoveryLevel.FULL)
                if success:
                    print("System state recovered successfully from last valid checkpoint")
                else:
                    print("No valid recovery state found, starting with empty state")
            
        except Exception as e:
            self.recovery_manager.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": f"Startup recovery failed: {str(e)}",
                "operation": "startup_recovery"
            })
            print(f"Warning: Startup recovery failed: {e}")


# Global state handler instance
state_handler: Optional[StateHandler] = None


def get_state_handler() -> StateHandler:
    """
    Get the global state handler instance.
    
    Returns:
        StateHandler instance
    """
    global state_handler
    if state_handler is None:
        state_handler = StateHandler()
    return state_handler


def initialize_state_handler(storage_path: Optional[str] = None) -> StateHandler:
    """
    Initialize the global state handler.
    
    Args:
        storage_path: Path to storage directory
        
    Returns:
        StateHandler instance
    """
    global state_handler
    state_handler = StateHandler(storage_path)
    return state_handler


def shutdown_state_handler() -> None:
    """Shutdown the global state handler."""
    global state_handler
    if state_handler:
        state_handler.shutdown()
        state_handler = None