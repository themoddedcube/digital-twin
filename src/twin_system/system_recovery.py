"""
System recovery and audit logging implementation for the F1 Dual Twin System.

This module provides comprehensive system recovery capabilities and audit logging
to ensure system reliability and data integrity under race conditions.
"""

import json
import sqlite3
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

from core.interfaces import StateConsistencyError
from utils.config import get_config


class RecoveryLevel(Enum):
    """Recovery levels for different types of failures."""
    MINIMAL = "minimal"          # Basic state restoration
    PARTIAL = "partial"          # Component-level recovery
    FULL = "full"               # Complete system recovery
    EMERGENCY = "emergency"      # Emergency fallback mode


class AuditEventType(Enum):
    """Types of audit events for logging."""
    STATE_UPDATE = "state_update"
    STATE_PERSISTENCE = "state_persistence"
    RECOVERY_INITIATED = "recovery_initiated"
    RECOVERY_COMPLETED = "recovery_completed"
    CONSISTENCY_CHECK = "consistency_check"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    PERFORMANCE_METRIC = "performance_metric"


class SystemRecoveryManager:
    """
    Manages system recovery from interruptions and comprehensive audit logging.
    
    Provides recovery mechanisms using last valid state and maintains detailed
    audit logs for debugging and compliance purposes.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize System Recovery Manager.
        
        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = Path(storage_path or get_config("state_management.storage_path", "shared"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Recovery configuration
        self.recovery_enabled = get_config("recovery.enabled", True)
        self.max_recovery_attempts = get_config("recovery.max_attempts", 3)
        self.recovery_timeout_seconds = get_config("recovery.timeout_seconds", 30)
        self.backup_retention_hours = get_config("recovery.backup_retention_hours", 24)
        
        # Audit logging configuration
        self.audit_enabled = get_config("audit.enabled", True)
        self.audit_retention_days = get_config("audit.retention_days", 7)
        self.audit_max_entries = get_config("audit.max_entries", 10000)
        self.audit_performance_tracking = get_config("audit.performance_tracking", True)
        
        # Recovery state tracking
        self._recovery_in_progress = False
        self._recovery_lock = threading.Lock()
        self._last_valid_states: Dict[str, Dict[str, Any]] = {}
        self._recovery_attempts = 0
        
        # Audit logging
        self._audit_lock = threading.Lock()
        self._audit_db_path = self.storage_path / "audit.db"
        
        # Initialize storage
        self._init_recovery_storage()
        self._init_audit_storage()
        
        # Log system startup
        self.log_audit_event(AuditEventType.SYSTEM_STARTUP, {
            "recovery_enabled": self.recovery_enabled,
            "audit_enabled": self.audit_enabled,
            "storage_path": str(self.storage_path)
        })
    
    def create_recovery_checkpoint(self, component_name: str, state_data: Dict[str, Any]) -> bool:
        """
        Create a recovery checkpoint for a system component.
        
        Args:
            component_name: Name of the component (car_twin, field_twin, etc.)
            state_data: Current state data to checkpoint
            
        Returns:
            True if checkpoint was created successfully, False otherwise
        """
        try:
            if not self.recovery_enabled:
                return True
            
            # Validate state data
            if not self._validate_checkpoint_data(state_data):
                self.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                    "error": "Invalid checkpoint data",
                    "component": component_name,
                    "data_keys": list(state_data.keys()) if isinstance(state_data, dict) else "invalid"
                })
                return False
            
            # Create checkpoint with metadata
            checkpoint = {
                "component": component_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "state_data": state_data,
                "checkpoint_id": f"{component_name}_{int(time.time())}"
            }
            
            # Save to multiple locations for redundancy
            checkpoint_file = self.storage_path / f"checkpoint_{component_name}.json"
            backup_file = self.storage_path / f"checkpoint_{component_name}_backup.json"
            
            # Atomic write to primary checkpoint
            temp_file = checkpoint_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            temp_file.replace(checkpoint_file)
            
            # Copy to backup location
            with open(backup_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            # Store in memory for quick access
            self._last_valid_states[component_name] = checkpoint
            
            # Log checkpoint creation
            self.log_audit_event(AuditEventType.STATE_PERSISTENCE, {
                "component": component_name,
                "checkpoint_id": checkpoint["checkpoint_id"],
                "data_size_bytes": len(json.dumps(state_data))
            })
            
            return True
            
        except Exception as e:
            self.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": f"Failed to create checkpoint: {str(e)}",
                "component": component_name
            })
            return False
    
    def recover_from_interruption(self, recovery_level: RecoveryLevel = RecoveryLevel.FULL) -> Tuple[bool, Dict[str, Any]]:
        """
        Recover system state from interruption using last valid state.
        
        Args:
            recovery_level: Level of recovery to perform
            
        Returns:
            Tuple of (success, recovered_state_data)
        """
        with self._recovery_lock:
            if self._recovery_in_progress:
                return False, {}
            
            self._recovery_in_progress = True
            
        try:
            self.log_audit_event(AuditEventType.RECOVERY_INITIATED, {
                "recovery_level": recovery_level.value,
                "attempt": self._recovery_attempts + 1
            })
            
            recovered_states = {}
            
            if recovery_level in [RecoveryLevel.FULL, RecoveryLevel.PARTIAL]:
                # Attempt to recover all component states
                components = ["car_twin", "field_twin", "telemetry", "environment"]
                
                for component in components:
                    recovered_state = self._recover_component_state(component)
                    if recovered_state:
                        recovered_states[component] = recovered_state
                        self.log_audit_event(AuditEventType.STATE_UPDATE, {
                            "component": component,
                            "recovery_source": "checkpoint",
                            "recovered_keys": list(recovered_state.get("state_data", {}).keys())
                        })
            
            elif recovery_level == RecoveryLevel.MINIMAL:
                # Only recover critical components
                critical_components = ["car_twin", "telemetry"]
                
                for component in critical_components:
                    recovered_state = self._recover_component_state(component)
                    if recovered_state:
                        recovered_states[component] = recovered_state
            
            elif recovery_level == RecoveryLevel.EMERGENCY:
                # Emergency fallback - use any available state
                recovered_states = self._emergency_recovery()
            
            # Validate recovered states
            if self._validate_recovered_states(recovered_states):
                self._recovery_attempts = 0  # Reset counter on success
                
                self.log_audit_event(AuditEventType.RECOVERY_COMPLETED, {
                    "recovery_level": recovery_level.value,
                    "recovered_components": list(recovered_states.keys()),
                    "success": True
                })
                
                return True, recovered_states
            else:
                self._recovery_attempts += 1
                
                if self._recovery_attempts < self.max_recovery_attempts:
                    # Try next recovery level
                    next_level = self._get_next_recovery_level(recovery_level)
                    if next_level:
                        return self.recover_from_interruption(next_level)
                
                self.log_audit_event(AuditEventType.RECOVERY_COMPLETED, {
                    "recovery_level": recovery_level.value,
                    "success": False,
                    "attempts": self._recovery_attempts
                })
                
                return False, {}
        
        except Exception as e:
            self.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": f"Recovery failed: {str(e)}",
                "recovery_level": recovery_level.value
            })
            return False, {}
        
        finally:
            with self._recovery_lock:
                self._recovery_in_progress = False
    
    def validate_data_consistency(self, car_twin_state: Dict[str, Any], 
                                field_twin_state: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate data consistency between Car Twin and Field Twin.
        
        Args:
            car_twin_state: Car Twin state data
            field_twin_state: Field Twin state data
            
        Returns:
            Tuple of (is_consistent, list_of_issues)
        """
        issues = []
        
        try:
            self.log_audit_event(AuditEventType.CONSISTENCY_CHECK, {
                "car_twin_present": bool(car_twin_state),
                "field_twin_present": bool(field_twin_state)
            })
            
            # Check timestamp consistency
            car_timestamp = car_twin_state.get("timestamp")
            field_timestamp = field_twin_state.get("timestamp")
            
            if car_timestamp and field_timestamp:
                try:
                    car_time = datetime.fromisoformat(car_timestamp.replace('Z', '+00:00'))
                    field_time = datetime.fromisoformat(field_timestamp.replace('Z', '+00:00'))
                    
                    time_diff = abs((car_time - field_time).total_seconds())
                    if time_diff > 30:  # Allow 30 seconds difference
                        issues.append(f"Timestamp difference too large: {time_diff} seconds")
                
                except ValueError as e:
                    issues.append(f"Invalid timestamp format: {str(e)}")
            
            # Check car ID consistency
            car_id = car_twin_state.get("car_id")
            if car_id:
                # Check if car exists in field twin competitors
                competitors = field_twin_state.get("competitors", [])
                if competitors:
                    competitor_ids = [comp.get("car_id") for comp in competitors]
                    if car_id not in competitor_ids:
                        issues.append(f"Car ID {car_id} not found in field twin competitors")
            
            # Check data freshness
            current_time = datetime.now(timezone.utc)
            
            for state_name, state_data in [("car_twin", car_twin_state), ("field_twin", field_twin_state)]:
                timestamp = state_data.get("timestamp")
                if timestamp:
                    try:
                        state_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        age_seconds = (current_time - state_time).total_seconds()
                        
                        if age_seconds > 300:  # 5 minutes
                            issues.append(f"{state_name} data is stale: {age_seconds} seconds old")
                    
                    except ValueError:
                        issues.append(f"{state_name} has invalid timestamp")
            
            # Check required fields
            car_required_fields = ["car_id", "timestamp", "current_state"]
            for field in car_required_fields:
                if field not in car_twin_state:
                    issues.append(f"Car twin missing required field: {field}")
            
            field_required_fields = ["timestamp", "competitors"]
            for field in field_required_fields:
                if field not in field_twin_state:
                    issues.append(f"Field twin missing required field: {field}")
            
            is_consistent = len(issues) == 0
            
            self.log_audit_event(AuditEventType.CONSISTENCY_CHECK, {
                "is_consistent": is_consistent,
                "issue_count": len(issues),
                "issues": issues[:5]  # Log first 5 issues
            })
            
            return is_consistent, issues
        
        except Exception as e:
            error_msg = f"Consistency check failed: {str(e)}"
            issues.append(error_msg)
            
            self.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": error_msg,
                "operation": "consistency_check"
            })
            
            return False, issues
    
    def log_audit_event(self, event_type: AuditEventType, event_data: Dict[str, Any]) -> None:
        """
        Log an audit event with timestamp and metadata.
        
        Args:
            event_type: Type of audit event
            event_data: Event-specific data
        """
        if not self.audit_enabled:
            return
        
        try:
            with self._audit_lock:
                audit_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_type": event_type.value,
                    "event_data": event_data,
                    "thread_id": threading.get_ident(),
                    "process_id": os.getpid() if 'os' in globals() else None
                }
                
                # Log to SQLite database
                self._log_to_audit_db(audit_entry)
                
                # Also log performance metrics if enabled
                if self.audit_performance_tracking and event_type == AuditEventType.PERFORMANCE_METRIC:
                    self._log_performance_metric(event_data)
        
        except Exception as e:
            # Avoid recursive logging errors
            print(f"Warning: Failed to log audit event: {e}")
    
    def get_audit_log(self, start_time: Optional[datetime] = None, 
                     end_time: Optional[datetime] = None,
                     event_types: Optional[List[AuditEventType]] = None,
                     limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve audit log entries with filtering.
        
        Args:
            start_time: Start time for filtering (optional)
            end_time: End time for filtering (optional)
            event_types: List of event types to filter (optional)
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        try:
            with sqlite3.connect(self._audit_db_path) as conn:
                query = "SELECT timestamp, event_type, event_data FROM audit_log WHERE 1=1"
                params = []
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                if event_types:
                    placeholders = ",".join("?" * len(event_types))
                    query += f" AND event_type IN ({placeholders})"
                    params.extend([et.value for et in event_types])
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                
                entries = []
                for row in cursor.fetchall():
                    entries.append({
                        "timestamp": row[0],
                        "event_type": row[1],
                        "event_data": json.loads(row[2])
                    })
                
                return entries
        
        except Exception as e:
            self.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": f"Failed to retrieve audit log: {str(e)}"
            })
            return []
    
    def cleanup_old_data(self) -> None:
        """Clean up old audit logs and recovery checkpoints."""
        try:
            # Clean up old audit logs
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.audit_retention_days)
            
            with sqlite3.connect(self._audit_db_path) as conn:
                conn.execute(
                    "DELETE FROM audit_log WHERE timestamp < ?",
                    (cutoff_time.isoformat(),)
                )
                conn.commit()
            
            # Clean up old recovery checkpoints
            checkpoint_cutoff = datetime.now(timezone.utc) - timedelta(hours=self.backup_retention_hours)
            
            for checkpoint_file in self.storage_path.glob("checkpoint_*.json"):
                if checkpoint_file.stat().st_mtime < checkpoint_cutoff.timestamp():
                    checkpoint_file.unlink()
            
            self.log_audit_event(AuditEventType.SYSTEM_STARTUP, {
                "operation": "cleanup_completed",
                "cutoff_time": cutoff_time.isoformat()
            })
        
        except Exception as e:
            self.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": f"Cleanup failed: {str(e)}"
            })
    
    def _recover_component_state(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Recover state for a specific component."""
        try:
            # Try memory first
            if component_name in self._last_valid_states:
                return self._last_valid_states[component_name]
            
            # Try primary checkpoint file
            checkpoint_file = self.storage_path / f"checkpoint_{component_name}.json"
            if checkpoint_file.exists():
                with open(checkpoint_file, 'r') as f:
                    return json.load(f)
            
            # Try backup checkpoint file
            backup_file = self.storage_path / f"checkpoint_{component_name}_backup.json"
            if backup_file.exists():
                with open(backup_file, 'r') as f:
                    return json.load(f)
            
            return None
        
        except Exception as e:
            self.log_audit_event(AuditEventType.ERROR_OCCURRED, {
                "error": f"Component recovery failed: {str(e)}",
                "component": component_name
            })
            return None
    
    def _emergency_recovery(self) -> Dict[str, Any]:
        """Emergency recovery using any available state data."""
        recovered = {}
        
        # Try to recover from any available checkpoint files
        for checkpoint_file in self.storage_path.glob("checkpoint_*.json"):
            try:
                component_name = checkpoint_file.stem.replace("checkpoint_", "")
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                    recovered[component_name] = data
            except Exception:
                continue
        
        return recovered
    
    def _validate_checkpoint_data(self, data: Dict[str, Any]) -> bool:
        """Validate checkpoint data integrity."""
        try:
            return isinstance(data, dict) and len(data) > 0
        except Exception:
            return False
    
    def _validate_recovered_states(self, states: Dict[str, Any]) -> bool:
        """Validate recovered states."""
        try:
            return len(states) > 0 and all(isinstance(state, dict) for state in states.values())
        except Exception:
            return False
    
    def _get_next_recovery_level(self, current_level: RecoveryLevel) -> Optional[RecoveryLevel]:
        """Get next recovery level for fallback."""
        level_order = [RecoveryLevel.FULL, RecoveryLevel.PARTIAL, RecoveryLevel.MINIMAL, RecoveryLevel.EMERGENCY]
        
        try:
            current_index = level_order.index(current_level)
            if current_index < len(level_order) - 1:
                return level_order[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    def _init_recovery_storage(self) -> None:
        """Initialize recovery storage directories."""
        recovery_dir = self.storage_path / "recovery"
        recovery_dir.mkdir(exist_ok=True)
    
    def _init_audit_storage(self) -> None:
        """Initialize audit logging database."""
        try:
            with sqlite3.connect(self._audit_db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT NOT NULL,
                        thread_id INTEGER,
                        process_id INTEGER
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                    ON audit_log(timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_event_type 
                    ON audit_log(event_type)
                """)
                
                conn.commit()
        
        except Exception as e:
            print(f"Warning: Failed to initialize audit storage: {e}")
    
    def _log_to_audit_db(self, audit_entry: Dict[str, Any]) -> None:
        """Log audit entry to SQLite database."""
        try:
            with sqlite3.connect(self._audit_db_path) as conn:
                conn.execute("""
                    INSERT INTO audit_log (timestamp, event_type, event_data, thread_id, process_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    audit_entry["timestamp"],
                    audit_entry["event_type"],
                    json.dumps(audit_entry["event_data"]),
                    audit_entry.get("thread_id"),
                    audit_entry.get("process_id")
                ))
                conn.commit()
        
        except Exception as e:
            print(f"Warning: Failed to log to audit database: {e}")
    
    def _log_performance_metric(self, metric_data: Dict[str, Any]) -> None:
        """Log performance metrics for monitoring."""
        # This could be extended to send metrics to monitoring systems
        pass


# Import os for process ID
import os