"""
Base state management implementation for the F1 Dual Twin System.

This module provides the foundational state management functionality
including persistence, recovery, and consistency checking.
"""

import json
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from interfaces import StateManager, StateConsistencyError
from utils.config import get_config


class BaseStateManager(StateManager):
    """
    Base implementation for state management and persistence.
    
    Provides atomic operations, concurrency control, and dual storage
    (JSON files for readability, SQLite for transactional integrity).
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize base state manager.
        
        Args:
            storage_path: Path to storage directory (uses config if not provided)
        """
        self.storage_path = Path(storage_path or get_config("state_management.storage_path", "shared"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.persistence_interval = get_config("state_management.persistence_interval_seconds", 5)
        self.backup_enabled = get_config("state_management.backup_enabled", True)
        self.consistency_check_enabled = get_config("state_management.consistency_check_enabled", True)
        self.audit_logging_enabled = get_config("state_management.audit_logging_enabled", True)
        
        # State storage
        self._state_data: Dict[str, Any] = {}
        self._state_lock = threading.RLock()
        self._last_persistence = time.time()
        
        # Audit logging
        self._audit_log: List[Dict[str, Any]] = []
        self._audit_lock = threading.Lock()
        
        # Initialize storage
        self._init_storage()
        
        # Load existing state
        self._load_initial_state()
    
    def persist_state(self, state_data: Dict[str, Any]) -> None:
        """
        Persist state data to storage with atomic operations.
        
        Args:
            state_data: State data to persist
            
        Raises:
            StateConsistencyError: If persistence fails
        """
        try:
            with self._state_lock:
                # Update internal state
                self._state_data.update(state_data)
                
                # Add timestamp metadata
                persistence_metadata = {
                    "persistence_timestamp": datetime.now(timezone.utc).isoformat(),
                    "persistence_count": self._state_data.get("persistence_count", 0) + 1
                }
                self._state_data.update(persistence_metadata)
                
                # Perform atomic write operations
                self._atomic_write_json()
                if self.backup_enabled:
                    self._atomic_write_sqlite()
                
                # Log the persistence operation
                if self.audit_logging_enabled:
                    self._log_audit_event("state_persisted", {
                        "data_keys": list(state_data.keys()),
                        "total_size_bytes": len(json.dumps(self._state_data))
                    })
                
                self._last_persistence = time.time()
                
        except Exception as e:
            raise StateConsistencyError(f"Failed to persist state: {str(e)}")
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Load state data from storage.
        
        Returns:
            Loaded state data or None if no valid state exists
        """
        try:
            with self._state_lock:
                # Try loading from JSON first (primary storage)
                json_state = self._load_from_json()
                
                if json_state and self._validate_state_integrity(json_state):
                    self._state_data = json_state
                    return json_state.copy()
                
                # Fallback to SQLite if JSON is corrupted
                if self.backup_enabled:
                    sqlite_state = self._load_from_sqlite()
                    if sqlite_state and self._validate_state_integrity(sqlite_state):
                        self._state_data = sqlite_state
                        # Restore JSON from SQLite
                        self._atomic_write_json()
                        return sqlite_state.copy()
                
                return None
                
        except Exception as e:
            print(f"Warning: Failed to load state: {e}")
            return None
    
    def ensure_consistency(self) -> bool:
        """
        Verify state consistency across storage mechanisms.
        
        Returns:
            True if state is consistent, False otherwise
        """
        if not self.consistency_check_enabled:
            return True
        
        try:
            with self._state_lock:
                json_state = self._load_from_json()
                sqlite_state = self._load_from_sqlite() if self.backup_enabled else None
                
                # If only one storage mechanism is used, it's consistent by definition
                if not self.backup_enabled:
                    return json_state is not None
                
                # Both should exist and match
                if not json_state or not sqlite_state:
                    return False
                
                # Compare critical fields (excluding timestamps which may differ slightly)
                json_clean = self._clean_state_for_comparison(json_state)
                sqlite_clean = self._clean_state_for_comparison(sqlite_state)
                
                consistent = json_clean == sqlite_clean
                
                if not consistent and self.audit_logging_enabled:
                    self._log_audit_event("consistency_check_failed", {
                        "json_keys": list(json_clean.keys()),
                        "sqlite_keys": list(sqlite_clean.keys())
                    })
                
                return consistent
                
        except Exception as e:
            print(f"Warning: Consistency check failed: {e}")
            return False
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current state data (thread-safe).
        
        Returns:
            Current state data copy
        """
        with self._state_lock:
            return self._state_data.copy()
    
    def get_audit_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        with self._audit_lock:
            if limit:
                return self._audit_log[-limit:]
            return self._audit_log.copy()
    
    def clear_audit_log(self) -> None:
        """Clear audit log entries."""
        with self._audit_lock:
            self._audit_log.clear()
    
    def force_consistency_repair(self) -> bool:
        """
        Attempt to repair state consistency issues.
        
        Returns:
            True if repair was successful, False otherwise
        """
        try:
            with self._state_lock:
                # Load from both sources
                json_state = self._load_from_json()
                sqlite_state = self._load_from_sqlite() if self.backup_enabled else None
                
                # Determine which source is more recent/reliable
                primary_state = None
                
                if json_state and sqlite_state:
                    json_timestamp = json_state.get("persistence_timestamp")
                    sqlite_timestamp = sqlite_state.get("persistence_timestamp")
                    
                    if json_timestamp and sqlite_timestamp:
                        if json_timestamp >= sqlite_timestamp:
                            primary_state = json_state
                        else:
                            primary_state = sqlite_state
                    else:
                        primary_state = json_state  # Prefer JSON as primary
                elif json_state:
                    primary_state = json_state
                elif sqlite_state:
                    primary_state = sqlite_state
                
                if primary_state:
                    # Restore both storage mechanisms from primary
                    self._state_data = primary_state
                    self._atomic_write_json()
                    if self.backup_enabled:
                        self._atomic_write_sqlite()
                    
                    if self.audit_logging_enabled:
                        self._log_audit_event("consistency_repaired", {
                            "primary_source": "json" if primary_state == json_state else "sqlite"
                        })
                    
                    return True
                
                return False
                
        except Exception as e:
            print(f"Error during consistency repair: {e}")
            return False
    
    @contextmanager
    def atomic_update(self):
        """
        Context manager for atomic state updates.
        
        Usage:
            with state_manager.atomic_update() as state:
                state["key"] = "value"
                # Changes are automatically persisted on exit
        """
        with self._state_lock:
            # Yield a copy of current state for modification
            state_copy = self._state_data.copy()
            try:
                yield state_copy
                # Persist changes if no exception occurred
                self.persist_state(state_copy)
            except Exception:
                # Don't persist if an exception occurred
                raise
    
    def _init_storage(self) -> None:
        """Initialize storage mechanisms."""
        # Create storage directories
        self.json_file = self.storage_path / "state.json"
        self.sqlite_file = self.storage_path / "state.db"
        
        # Initialize SQLite database if backup is enabled
        if self.backup_enabled:
            self._init_sqlite_db()
    
    def _init_sqlite_db(self) -> None:
        """Initialize SQLite database schema."""
        try:
            with sqlite3.connect(self.sqlite_file) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS state_data (
                        id INTEGER PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        data TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT NOT NULL
                    )
                """)
                
                conn.commit()
        except Exception as e:
            print(f"Warning: Failed to initialize SQLite database: {e}")
    
    def _load_initial_state(self) -> None:
        """Load initial state from storage."""
        loaded_state = self.load_state()
        if loaded_state:
            print(f"Loaded state with {len(loaded_state)} keys from storage")
        else:
            print("No existing state found, starting with empty state")
    
    def _atomic_write_json(self) -> None:
        """Atomically write state to JSON file."""
        temp_file = self.json_file.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w') as f:
                json.dump(self._state_data, f, indent=2)
            
            # Atomic move
            temp_file.replace(self.json_file)
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _atomic_write_sqlite(self) -> None:
        """Atomically write state to SQLite database."""
        try:
            with sqlite3.connect(self.sqlite_file) as conn:
                timestamp = datetime.now(timezone.utc).isoformat()
                data_json = json.dumps(self._state_data)
                
                # Replace existing state (keep only latest)
                conn.execute("DELETE FROM state_data")
                conn.execute(
                    "INSERT INTO state_data (timestamp, data) VALUES (?, ?)",
                    (timestamp, data_json)
                )
                conn.commit()
                
        except Exception as e:
            raise StateConsistencyError(f"SQLite write failed: {e}")
    
    def _load_from_json(self) -> Optional[Dict[str, Any]]:
        """Load state from JSON file."""
        try:
            if self.json_file.exists():
                with open(self.json_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load JSON state: {e}")
        return None
    
    def _load_from_sqlite(self) -> Optional[Dict[str, Any]]:
        """Load state from SQLite database."""
        try:
            with sqlite3.connect(self.sqlite_file) as conn:
                cursor = conn.execute(
                    "SELECT data FROM state_data ORDER BY id DESC LIMIT 1"
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except Exception as e:
            print(f"Warning: Failed to load SQLite state: {e}")
        return None
    
    def _validate_state_integrity(self, state: Dict[str, Any]) -> bool:
        """
        Validate state data integrity.
        
        Args:
            state: State data to validate
            
        Returns:
            True if state is valid, False otherwise
        """
        try:
            # Basic validation
            if not isinstance(state, dict):
                return False
            
            # Check for required metadata
            if "persistence_timestamp" not in state:
                return False
            
            # Validate timestamp format
            datetime.fromisoformat(state["persistence_timestamp"].replace('Z', '+00:00'))
            
            return True
            
        except Exception:
            return False
    
    def _clean_state_for_comparison(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean state data for consistency comparison.
        
        Args:
            state: State data to clean
            
        Returns:
            Cleaned state data
        """
        cleaned = state.copy()
        
        # Remove timestamp fields that may differ slightly
        timestamp_fields = ["persistence_timestamp", "last_update_timestamp"]
        for field in timestamp_fields:
            cleaned.pop(field, None)
        
        return cleaned
    
    def _log_audit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            event_data: Event-specific data
        """
        if not self.audit_logging_enabled:
            return
        
        try:
            with self._audit_lock:
                audit_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_type": event_type,
                    "event_data": event_data
                }
                
                self._audit_log.append(audit_entry)
                
                # Keep audit log size manageable
                max_audit_entries = get_config("state_management.max_audit_entries", 1000)
                if len(self._audit_log) > max_audit_entries:
                    self._audit_log = self._audit_log[-max_audit_entries:]
                
                # Also log to SQLite if available
                if self.backup_enabled:
                    self._log_audit_to_sqlite(audit_entry)
                    
        except Exception as e:
            print(f"Warning: Failed to log audit event: {e}")
    
    def _log_audit_to_sqlite(self, audit_entry: Dict[str, Any]) -> None:
        """Log audit entry to SQLite database."""
        try:
            with sqlite3.connect(self.sqlite_file) as conn:
                conn.execute(
                    "INSERT INTO audit_log (timestamp, event_type, event_data) VALUES (?, ?, ?)",
                    (
                        audit_entry["timestamp"],
                        audit_entry["event_type"],
                        json.dumps(audit_entry["event_data"])
                    )
                )
                conn.commit()
        except Exception as e:
            print(f"Warning: Failed to log audit to SQLite: {e}")