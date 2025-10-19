"""
System initialization module for the F1 Dual Twin System.

This module provides system-wide initialization, component registration,
and dependency injection setup for the twin system.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Type

from interfaces import (
    TelemetryProcessor, TwinModel, StateManager, ConfigurationManager,
    TelemetryValidationError, StateConsistencyError, ConfigurationError
)
from base_telemetry import BaseTelemetryProcessor
from base_twin import BaseTwinModel
from base_state import BaseStateManager
from utils.config import SystemConfig, load_config_file


class SystemInitializer:
    """
    System initialization and component management.
    
    Handles system startup, component registration, and provides
    a central registry for all system components.
    """
    
    def __init__(self):
        """Initialize system initializer."""
        self._components: Dict[str, Any] = {}
        self._config_manager: Optional[ConfigurationManager] = None
        self._state_manager: Optional[StateManager] = None
        self._initialized = False
    
    def initialize_system(self, config_file: Optional[str] = None) -> bool:
        """
        Initialize the complete F1 Dual Twin System.
        
        Args:
            config_file: Optional path to configuration file
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            print("Initializing F1 Dual Twin System...")
            
            # Step 1: Initialize configuration
            self._init_configuration(config_file)
            
            # Step 2: Create shared directory structure
            self._create_directory_structure()
            
            # Step 3: Initialize state management
            self._init_state_management()
            
            # Step 4: Register core components
            self._register_core_components()
            
            # Step 5: Validate system integrity
            self._validate_system_integrity()
            
            self._initialized = True
            print("F1 Dual Twin System initialized successfully")
            return True
            
        except Exception as e:
            print(f"System initialization failed: {e}")
            return False
    
    def get_component(self, component_name: str) -> Any:
        """
        Get registered component by name.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Component instance
            
        Raises:
            KeyError: If component not found
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        if component_name not in self._components:
            raise KeyError(f"Component '{component_name}' not found")
        
        return self._components[component_name]
    
    def register_component(self, name: str, component: Any) -> None:
        """
        Register a component in the system.
        
        Args:
            name: Component name
            component: Component instance
        """
        self._components[name] = component
    
    def get_config_manager(self) -> ConfigurationManager:
        """Get the system configuration manager."""
        if not self._config_manager:
            raise RuntimeError("Configuration manager not initialized")
        return self._config_manager
    
    def get_state_manager(self) -> StateManager:
        """Get the system state manager."""
        if not self._state_manager:
            raise RuntimeError("State manager not initialized")
        return self._state_manager
    
    def shutdown_system(self) -> None:
        """Gracefully shutdown the system."""
        try:
            print("Shutting down F1 Dual Twin System...")
            
            # Persist final state
            if self._state_manager:
                current_state = {}
                for name, component in self._components.items():
                    if hasattr(component, 'get_current_state'):
                        current_state[name] = component.get_current_state()
                
                if current_state:
                    self._state_manager.persist_state({
                        "shutdown_timestamp": self._get_current_timestamp(),
                        "final_component_states": current_state
                    })
            
            # Clear components
            self._components.clear()
            self._initialized = False
            
            print("System shutdown complete")
            
        except Exception as e:
            print(f"Error during system shutdown: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status and health information.
        
        Returns:
            System status dictionary
        """
        status = {
            "initialized": self._initialized,
            "timestamp": self._get_current_timestamp(),
            "components": {}
        }
        
        if self._initialized:
            # Get component status
            for name, component in self._components.items():
                component_status = {"registered": True}
                
                # Get performance metrics if available
                if hasattr(component, 'get_performance_metrics'):
                    component_status["performance"] = component.get_performance_metrics()
                
                # Get processing stats if available
                if hasattr(component, 'get_processing_stats'):
                    component_status["processing"] = component.get_processing_stats()
                
                status["components"][name] = component_status
            
            # Get state manager status
            if self._state_manager:
                status["state_consistency"] = self._state_manager.ensure_consistency()
                status["audit_log_entries"] = len(self._state_manager.get_audit_log())
        
        return status
    
    def _init_configuration(self, config_file: Optional[str]) -> None:
        """Initialize configuration management."""
        self._config_manager = SystemConfig(config_file)
        
        # Load additional config file if specified
        if config_file and os.path.exists(config_file):
            load_config_file(config_file)
        
        print(f"Configuration initialized from: {config_file or 'defaults'}")
    
    def _create_directory_structure(self) -> None:
        """Create required directory structure."""
        from utils.config import get_config
        
        # Get storage paths from configuration
        shared_path = Path(get_config("state_management.storage_path", "shared"))
        log_path = Path(get_config("logging.file_path", "shared/logs/f1_twin.log")).parent
        
        # Create directories
        directories = [shared_path, log_path]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
    
    def _init_state_management(self) -> None:
        """Initialize state management system."""
        self._state_manager = BaseStateManager()
        
        # Load existing state if available
        existing_state = self._state_manager.load_state()
        if existing_state:
            print(f"Loaded existing state with {len(existing_state)} keys")
        
        # Register state manager as component
        self.register_component("state_manager", self._state_manager)
    
    def _register_core_components(self) -> None:
        """Register core system components."""
        # Register telemetry processor
        telemetry_processor = BaseTelemetryProcessor()
        self.register_component("telemetry_processor", telemetry_processor)
        
        print("Core components registered")
    
    def _validate_system_integrity(self) -> None:
        """Validate system integrity after initialization."""
        # Check state consistency
        if not self._state_manager.ensure_consistency():
            print("Warning: State consistency check failed")
        
        # Validate configuration
        from utils.config import get_config
        critical_configs = [
            "telemetry.update_interval_seconds",
            "car_twin.update_latency_ms",
            "field_twin.update_latency_ms",
            "state_management.persistence_interval_seconds"
        ]
        
        for config_key in critical_configs:
            value = get_config(config_key)
            if value is None:
                raise ConfigurationError(f"Critical configuration missing: {config_key}")
        
        print("System integrity validation passed")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


# Global system initializer instance
system_initializer = SystemInitializer()


def initialize_system(config_file: Optional[str] = None) -> bool:
    """
    Convenience function to initialize the system.
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        True if initialization successful, False otherwise
    """
    return system_initializer.initialize_system(config_file)


def get_component(component_name: str) -> Any:
    """
    Convenience function to get a system component.
    
    Args:
        component_name: Name of the component
        
    Returns:
        Component instance
    """
    return system_initializer.get_component(component_name)


def get_system_status() -> Dict[str, Any]:
    """
    Convenience function to get system status.
    
    Returns:
        System status dictionary
    """
    return system_initializer.get_system_status()


def shutdown_system() -> None:
    """Convenience function to shutdown the system."""
    system_initializer.shutdown_system()


if __name__ == "__main__":
    """Allow running system initialization as a script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize F1 Dual Twin System")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--status", action="store_true", help="Show system status")
    
    args = parser.parse_args()
    
    if args.status:
        try:
            status = get_system_status()
            print(json.dumps(status, indent=2))
        except Exception as e:
            print(f"Failed to get system status: {e}")
            sys.exit(1)
    else:
        success = initialize_system(args.config)
        if not success:
            sys.exit(1)
        
        print("\nSystem Status:")
        status = get_system_status()
        print(f"Initialized: {status['initialized']}")
        print(f"Components: {len(status['components'])}")
        
        # Keep system running for demonstration
        try:
            input("Press Enter to shutdown system...")
        except KeyboardInterrupt:
            pass
        finally:
            shutdown_system()