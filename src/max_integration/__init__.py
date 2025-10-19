"""
MAX Integration Module

Modular AI integration for race strategy simulation and AI-powered recommendations.
Includes Mojo simulation kernels and MAX LLM integration.
"""

from max_integration.ai_strategist import AIStrategist, StrategyRecommendation
from max_integration.hpc_orchestrator import HPCOrchestrator

# Note: simulate_strategy.mojo is imported via subprocess/Mojo runtime

__all__ = [
    'AIStrategist',
    'StrategyRecommendation',
    'HPCOrchestrator'
]

