"""
Configuration management for the F1 Dual Twin System.

This module provides centralized configuration management with support for
environment variables, file-based configuration, and runtime parameter updates.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from core.interfaces import ConfigurationManager, ConfigurationError


class SystemConfig(ConfigurationManager):
    """
    System configuration manager with support for JSON files and environment variables.
    
    Provides hierarchical configuration with the following precedence:
    1. Runtime set values (highest priority)
    2. Environment variables
    3. Configuration file values
    4. Default values (lowest priority)
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self._config: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = self._get_default_config()
        self._runtime_overrides: Dict[str, Any] = {}
        
        if config_file:
            self.load_config(config_file)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key with hierarchical lookup.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'telemetry.update_interval')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        # Check runtime overrides first
        value = self._get_nested_value(self._runtime_overrides, key)
        if value is not None:
            return value
        
        # Check environment variables
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(f"F1_TWIN_{env_key}")
        if env_value is not None:
            return self._parse_env_value(env_value)
        
        # Check loaded configuration
        value = self._get_nested_value(self._config, key)
        if value is not None:
            return value
        
        # Check defaults
        value = self._get_nested_value(self._defaults, key)
        if value is not None:
            return value
        
        return default
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set configuration value at runtime.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Configuration value
        """
        self._set_nested_value(self._runtime_overrides, key, value)
    
    def load_config(self, config_path: str) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            with open(config_file, 'r') as f:
                self._config = json.load(f)
                
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def save_config(self, config_path: str) -> None:
        """
        Save current configuration to JSON file.
        
        Args:
            config_path: Path to save configuration file
            
        Raises:
            ConfigurationError: If file cannot be saved
        """
        try:
            # Merge all configuration sources
            merged_config = {}
            merged_config.update(self._defaults)
            merged_config.update(self._config)
            merged_config.update(self._runtime_overrides)
            
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(merged_config, f, indent=2)
                
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Get all configuration values merged from all sources.
        
        Returns:
            Complete configuration dictionary
        """
        merged_config = {}
        merged_config.update(self._defaults)
        merged_config.update(self._config)
        merged_config.update(self._runtime_overrides)
        return merged_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default system configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "telemetry": {
                "update_interval_seconds": 3,
                "processing_timeout_ms": 250,
                "validation_enabled": True,
                "fallback_to_last_valid": True,
                "output_file": "shared/telemetry_state.json"
            },
            "car_twin": {
                "update_latency_ms": 200,
                "prediction_horizon_laps": 10,
                "tire_degradation_model": "linear",
                "fuel_consumption_model": "track_specific"
            },
            "field_twin": {
                "update_latency_ms": 300,
                "competitor_count": 19,
                "behavioral_analysis_enabled": True,
                "resimulation_triggers": ["pit_stop", "safety_car", "position_change"]
            },
            "state_management": {
                "persistence_interval_seconds": 5,
                "backup_enabled": True,
                "consistency_check_enabled": True,
                "audit_logging_enabled": True,
                "storage_path": "shared"
            },
            "api": {
                "host": "localhost",
                "port": 8000,
                "response_timeout_ms": 50,
                "max_concurrent_connections": 10,
                "enable_cors": True,
                "api_version": "v1"
            },
            "performance": {
                "max_memory_mb": 1024,
                "gc_interval_seconds": 60,
                "profiling_enabled": False,
                "metrics_collection_enabled": True
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_path": "shared/logs/f1_twin.log",
                "max_file_size_mb": 100,
                "backup_count": 5
            }
        }
    
    def _get_nested_value(self, config_dict: Dict[str, Any], key: str) -> Any:
        """
        Get value from nested dictionary using dot notation.
        
        Args:
            config_dict: Dictionary to search
            key: Dot-separated key path
            
        Returns:
            Value if found, None otherwise
        """
        keys = key.split('.')
        current = config_dict
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, config_dict: Dict[str, Any], key: str, value: Any) -> None:
        """
        Set value in nested dictionary using dot notation.
        
        Args:
            config_dict: Dictionary to modify
            key: Dot-separated key path
            value: Value to set
        """
        keys = key.split('.')
        current = config_dict
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _parse_env_value(self, value: str) -> Any:
        """
        Parse environment variable value to appropriate type.
        
        Args:
            value: String value from environment variable
            
        Returns:
            Parsed value (bool, int, float, or string)
        """
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value


# Global configuration instance
config = SystemConfig()


def get_config(key: str, default: Any = None) -> Any:
    """
    Convenience function to get configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    return config.get_config(key, default)


def set_config(key: str, value: Any) -> None:
    """
    Convenience function to set configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
    """
    config.set_config(key, value)


def load_config_file(config_path: str) -> None:
    """
    Convenience function to load configuration from file.
    
    Args:
        config_path: Path to configuration file
    """
    config.load_config(config_path)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Simple function to load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        # Return default config if file cannot be loaded
        return SystemConfig()._get_default_config()