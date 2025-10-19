"""
JSON schemas for telemetry, car twin, and field twin data structures.

This module defines the data schemas used throughout the F1 Dual Twin System
to ensure consistent data formats and enable validation.
"""

from typing import Dict, Any
import json


# Telemetry State Schema
TELEMETRY_SCHEMA = {
    "type": "object",
    "required": ["timestamp", "lap", "session_type", "track_conditions", "cars"],
    "properties": {
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the telemetry data"
        },
        "lap": {
            "type": "integer",
            "minimum": 0,
            "description": "Current lap number"
        },
        "session_type": {
            "type": "string",
            "enum": ["practice", "qualifying", "race", "sprint"],
            "description": "Type of racing session"
        },
        "track_conditions": {
            "type": "object",
            "required": ["temperature", "weather", "track_status"],
            "properties": {
                "temperature": {
                    "type": "number",
                    "minimum": -10,
                    "maximum": 60,
                    "description": "Track temperature in Celsius"
                },
                "weather": {
                    "type": "string",
                    "enum": ["sunny", "cloudy", "rain", "drizzle", "storm"],
                    "description": "Weather conditions"
                },
                "track_status": {
                    "type": "string",
                    "enum": ["green", "yellow", "red", "safety_car", "virtual_safety_car"],
                    "description": "Track status flags"
                }
            }
        },
        "cars": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["car_id", "team", "driver", "position", "speed", "tire", "fuel_level", "lap_time"],
                "properties": {
                    "car_id": {
                        "type": "string",
                        "description": "Unique car identifier"
                    },
                    "team": {
                        "type": "string",
                        "description": "Team name"
                    },
                    "driver": {
                        "type": "string",
                        "description": "Driver name"
                    },
                    "position": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "Current race position"
                    },
                    "speed": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 400,
                        "description": "Current speed in km/h"
                    },
                    "tire": {
                        "type": "object",
                        "required": ["compound", "age", "wear_level"],
                        "properties": {
                            "compound": {
                                "type": "string",
                                "enum": ["soft", "medium", "hard", "intermediate", "wet"],
                                "description": "Tire compound type"
                            },
                            "age": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Tire age in laps"
                            },
                            "wear_level": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Tire wear level (0=new, 1=completely worn)"
                            }
                        }
                    },
                    "fuel_level": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Fuel level (0=empty, 1=full)"
                    },
                    "lap_time": {
                        "type": "number",
                        "minimum": 60,
                        "maximum": 200,
                        "description": "Last lap time in seconds"
                    },
                    "sector_times": {
                        "type": "array",
                        "items": {
                            "type": "number",
                            "minimum": 10,
                            "maximum": 100
                        },
                        "minItems": 3,
                        "maxItems": 3,
                        "description": "Sector times in seconds"
                    }
                }
            }
        }
    }
}


# Car Twin State Schema
CAR_TWIN_SCHEMA = {
    "type": "object",
    "required": ["car_id", "timestamp", "current_state", "predictions", "strategy_metrics"],
    "properties": {
        "car_id": {
            "type": "string",
            "description": "Unique car identifier"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the state"
        },
        "current_state": {
            "type": "object",
            "required": ["speed", "tire_temp", "tire_wear", "fuel_level", "lap_time"],
            "properties": {
                "speed": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 400,
                    "description": "Current speed in km/h"
                },
                "tire_temp": {
                    "type": "array",
                    "items": {
                        "type": "number",
                        "minimum": 20,
                        "maximum": 150
                    },
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "Tire temperatures [FL, FR, RL, RR] in Celsius"
                },
                "tire_wear": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Average tire wear level"
                },
                "fuel_level": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Current fuel level"
                },
                "lap_time": {
                    "type": "number",
                    "minimum": 60,
                    "maximum": 200,
                    "description": "Last lap time in seconds"
                }
            }
        },
        "predictions": {
            "type": "object",
            "required": ["tire_degradation_rate", "fuel_consumption_rate", "predicted_pit_lap", "performance_delta"],
            "properties": {
                "tire_degradation_rate": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 0.1,
                    "description": "Tire degradation rate per lap"
                },
                "fuel_consumption_rate": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 10,
                    "description": "Fuel consumption rate per lap"
                },
                "predicted_pit_lap": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Predicted optimal pit stop lap"
                },
                "performance_delta": {
                    "type": "number",
                    "minimum": -10,
                    "maximum": 10,
                    "description": "Performance delta vs optimal in seconds"
                }
            }
        },
        "strategy_metrics": {
            "type": "object",
            "required": ["optimal_pit_window", "tire_life_remaining", "fuel_laps_remaining"],
            "properties": {
                "optimal_pit_window": {
                    "type": "array",
                    "items": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100
                    },
                    "minItems": 2,
                    "maxItems": 2,
                    "description": "Optimal pit window [start_lap, end_lap]"
                },
                "tire_life_remaining": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 50,
                    "description": "Estimated tire life remaining in laps"
                },
                "fuel_laps_remaining": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Fuel remaining in laps"
                }
            }
        }
    }
}


# Field Twin State Schema
FIELD_TWIN_SCHEMA = {
    "type": "object",
    "required": ["timestamp", "competitors", "strategic_opportunities"],
    "properties": {
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the state"
        },
        "competitors": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["car_id", "team", "current_position", "gap_to_leader", "predicted_strategy", "pit_probability", "strategic_threat_level", "behavioral_profile"],
                "properties": {
                    "car_id": {
                        "type": "string",
                        "description": "Unique car identifier"
                    },
                    "team": {
                        "type": "string",
                        "description": "Team name"
                    },
                    "current_position": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "Current race position"
                    },
                    "gap_to_leader": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Gap to race leader in seconds"
                    },
                    "predicted_strategy": {
                        "type": "string",
                        "enum": ["one_stop", "two_stop", "three_stop", "unknown"],
                        "description": "Predicted pit stop strategy"
                    },
                    "pit_probability": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Probability of pitting in next 5 laps"
                    },
                    "strategic_threat_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Strategic threat assessment"
                    },
                    "behavioral_profile": {
                        "type": "object",
                        "required": ["undercut_tendency", "aggressive_defense", "tire_management"],
                        "properties": {
                            "undercut_tendency": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Tendency to attempt undercuts"
                            },
                            "aggressive_defense": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Aggressiveness in defending position"
                            },
                            "tire_management": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Tire management skill level"
                            }
                        }
                    }
                }
            }
        },
        "strategic_opportunities": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type", "target_car", "probability", "execution_lap"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["undercut_window", "overcut_window", "drs_overtake", "pit_window", "safety_car_opportunity"],
                        "description": "Type of strategic opportunity"
                    },
                    "target_car": {
                        "type": "string",
                        "description": "Target competitor car ID"
                    },
                    "probability": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Success probability of the opportunity"
                    },
                    "execution_lap": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Recommended execution lap"
                    }
                }
            }
        }
    }
}


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate JSON data against a schema.
    
    Args:
        data: JSON data to validate
        schema: JSON schema to validate against
        
    Returns:
        True if data is valid, False otherwise
    """
    try:
        # Basic type checking - in production, use jsonschema library
        return _validate_object(data, schema)
    except Exception:
        return False


def _validate_object(data: Any, schema: Dict[str, Any]) -> bool:
    """Helper function for basic schema validation."""
    if schema.get("type") == "object":
        if not isinstance(data, dict):
            return False
        
        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                return False
        
        # Validate properties
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                if not _validate_field(value, properties[key]):
                    return False
        
        return True
    
    return True


def _validate_field(value: Any, field_schema: Dict[str, Any]) -> bool:
    """Helper function to validate individual fields."""
    field_type = field_schema.get("type")
    
    if field_type == "string":
        return isinstance(value, str)
    elif field_type == "number":
        return isinstance(value, (int, float))
    elif field_type == "integer":
        return isinstance(value, int)
    elif field_type == "boolean":
        return isinstance(value, bool)
    elif field_type == "array":
        return isinstance(value, list)
    elif field_type == "object":
        return _validate_object(value, field_schema)
    
    return True


# Schema registry for easy access
SCHEMAS = {
    "telemetry": TELEMETRY_SCHEMA,
    "car_twin": CAR_TWIN_SCHEMA,
    "field_twin": FIELD_TWIN_SCHEMA
}


def get_schema(schema_name: str) -> Dict[str, Any]:
    """
    Get schema by name.
    
    Args:
        schema_name: Name of the schema
        
    Returns:
        Schema dictionary
        
    Raises:
        KeyError: If schema name not found
    """
    if schema_name not in SCHEMAS:
        raise KeyError(f"Schema '{schema_name}' not found")
    
    return SCHEMAS[schema_name]