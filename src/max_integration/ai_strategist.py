"""
AI Strategist for F1 Race Strategy System

This module integrates with MAX (Modular's LLM serving) to generate
intelligent strategy recommendations for race engineers.
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class StrategyRecommendation:
    """Structure for strategy recommendations"""
    priority: str  # "urgent", "moderate", "optional"
    category: str  # "pit_strategy", "tire_management", "fuel_saving", "overtaking"
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    expected_benefit: str  # e.g., "+1.4s gain", "P2 position"
    execution_lap: Optional[int]
    reasoning: str
    risks: List[str]
    alternatives: List[str]


class AIStrategist:
    """AI strategist that generates recommendations using MAX LLM"""
    
    def __init__(self, max_endpoint: str = "http://localhost:8000/v1"):
        self.max_endpoint = max_endpoint
        self.model_name = "llama-3.1-8b"  # Default model
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Strategy templates for different scenarios
        self.strategy_templates = {
            "urgent": {
                "pit_strategy": "URGENT: Pit stop required within 2 laps",
                "tire_management": "URGENT: Tire degradation critical",
                "fuel_saving": "URGENT: Fuel level critical",
                "overtaking": "URGENT: Immediate overtaking opportunity"
            },
            "moderate": {
                "pit_strategy": "MODERATE: Consider pit stop in next 3-5 laps",
                "tire_management": "MODERATE: Monitor tire wear closely",
                "fuel_saving": "MODERATE: Consider fuel saving mode",
                "overtaking": "MODERATE: Plan overtaking maneuver"
            },
            "optional": {
                "pit_strategy": "OPTIONAL: Long-term pit strategy planning",
                "tire_management": "OPTIONAL: Optimize tire usage",
                "fuel_saving": "OPTIONAL: Consider fuel efficiency",
                "overtaking": "OPTIONAL: Look for overtaking opportunities"
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def generate_recommendations(self, strategy_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategy recommendations based on simulation data"""
        try:
            # Extract key information
            car_twin = strategy_data.get("car_twin")
            field_twin = strategy_data.get("field_twin")
            simulation_results = strategy_data.get("simulation_results", [])
            race_context = strategy_data.get("race_context", {})
            
            # Generate recommendations using MAX
            recommendations = await self._generate_with_max(
                car_twin, field_twin, simulation_results, race_context
            )
            
            # Fallback to rule-based recommendations if MAX fails
            if not recommendations:
                recommendations = self._generate_rule_based_recommendations(
                    car_twin, field_twin, simulation_results, race_context
                )
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self._generate_emergency_recommendations()
    
    async def _generate_with_max(self, car_twin, field_twin, simulation_results, 
                                race_context) -> List[Dict[str, Any]]:
        """Generate recommendations using MAX LLM"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Prepare prompt for MAX
            prompt = self._build_strategy_prompt(car_twin, field_twin, simulation_results, race_context)
            
            # Call MAX API
            payload = {
                "model": "modularai/Llama-3.1-8B-Instruct-GGUF",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert F1 race strategist. Analyze the race data and provide clear, actionable strategy recommendations for the race engineer. Focus on immediate tactical decisions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            async with self.session.post(
                f"{self.max_endpoint}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    return self._parse_llm_response(content, car_twin, simulation_results)
                else:
                    print(f"MAX API error: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"Error calling MAX API: {e}")
            # Fallback to rule-based recommendations
            return self._generate_rule_based_recommendations(car_twin, field_twin, simulation_results, race_context)
    
    def _build_strategy_prompt(self, car_twin, field_twin, simulation_results, race_context) -> str:
        """Build prompt for MAX LLM"""
        prompt = f"""
Race Strategy Analysis Request

Current Race Context:
- Lap: {race_context.get('lap', 'Unknown')}
- Session: {race_context.get('session_type', 'Unknown')}

Car State:
- Position: {car_twin.get('current_state', {}).get('position', 'Unknown') if car_twin else 'Unknown'}
- Tire: {car_twin.get('current_state', {}).get('tire', {}).get('compound', 'Unknown') if car_twin else 'Unknown'} (wear: {car_twin.get('current_state', {}).get('tire', {}).get('wear_level', 'Unknown') if car_twin else 'Unknown'})
- Fuel: {car_twin.get('current_state', {}).get('fuel_level', 'Unknown') if car_twin else 'Unknown'}
- Lap Time: {car_twin.get('current_state', {}).get('lap_time', 'Unknown') if car_twin else 'Unknown'}s

Simulation Results:
"""
        
        for i, result in enumerate(simulation_results[:3]):  # Top 3 results
            prompt += f"""
Strategy {i+1}:
- Pit Lap: {result.get('pit_lap', 'Unknown')}
- Final Position: {result.get('final_position', 'Unknown')}
- Success Probability: {result.get('success_probability', 'Unknown')}
- Total Time: {result.get('total_time', 'Unknown')}s
"""
        
        prompt += """
Please provide 3 strategy recommendations in this format:
1. URGENT/MODERATE/OPTIONAL: [Category] - [Title]
   Description: [Clear description]
   Expected Benefit: [Quantified benefit]
   Execution: [When to execute]
   Reasoning: [Why this strategy]
   Risks: [Potential risks]
   Alternatives: [Other options]

Focus on immediate tactical decisions that the race engineer can communicate to the driver.
"""
        
        return prompt
    
    def _parse_llm_response(self, content: str, car_twin, simulation_results) -> List[Dict[str, Any]]:
        """Parse LLM response into structured recommendations"""
        recommendations = []
        
        try:
            # Simple parsing - in production, use more robust parsing
            lines = content.split('\n')
            current_rec = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith(('1.', '2.', '3.')):
                    if current_rec:
                        recommendations.append(current_rec)
                    current_rec = {"raw_text": line}
                elif line.startswith('Description:'):
                    current_rec['description'] = line.replace('Description:', '').strip()
                elif line.startswith('Expected Benefit:'):
                    current_rec['expected_benefit'] = line.replace('Expected Benefit:', '').strip()
                elif line.startswith('Execution:'):
                    current_rec['execution'] = line.replace('Execution:', '').strip()
                elif line.startswith('Reasoning:'):
                    current_rec['reasoning'] = line.replace('Reasoning:', '').strip()
                elif line.startswith('Risks:'):
                    current_rec['risks'] = line.replace('Risks:', '').strip()
                elif line.startswith('Alternatives:'):
                    current_rec['alternatives'] = line.replace('Alternatives:', '').strip()
            
            if current_rec:
                recommendations.append(current_rec)
            
            # Convert to structured format
            structured_recs = []
            for i, rec in enumerate(recommendations):
                structured_recs.append({
                    "priority": self._extract_priority(rec.get('raw_text', '')),
                    "category": self._extract_category(rec.get('raw_text', '')),
                    "title": rec.get('raw_text', f'Strategy {i+1}'),
                    "description": rec.get('description', ''),
                    "confidence": 0.8,  # Default confidence
                    "expected_benefit": rec.get('expected_benefit', ''),
                    "execution_lap": self._extract_execution_lap(rec.get('execution', '')),
                    "reasoning": rec.get('reasoning', ''),
                    "risks": [rec.get('risks', '')],
                    "alternatives": [rec.get('alternatives', '')]
                })
            
            return structured_recs
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return []
    
    def _extract_priority(self, text: str) -> str:
        """Extract priority from text"""
        if 'URGENT' in text.upper():
            return 'urgent'
        elif 'MODERATE' in text.upper():
            return 'moderate'
        else:
            return 'optional'
    
    def _extract_category(self, text: str) -> str:
        """Extract category from text"""
        text_upper = text.upper()
        if 'PIT' in text_upper:
            return 'pit_strategy'
        elif 'TIRE' in text_upper:
            return 'tire_management'
        elif 'FUEL' in text_upper:
            return 'fuel_saving'
        elif 'OVERTAKING' in text_upper:
            return 'overtaking'
        else:
            return 'general'
    
    def _extract_execution_lap(self, text: str) -> Optional[int]:
        """Extract execution lap from text"""
        import re
        match = re.search(r'lap (\d+)', text.lower())
        return int(match.group(1)) if match else None
    
    def _generate_rule_based_recommendations(self, car_twin, field_twin, simulation_results, 
                                           race_context) -> List[Dict[str, Any]]:
        """Generate rule-based recommendations as fallback"""
        recommendations = []
        
        if not car_twin:
            return recommendations
        
        # Analyze tire wear
        tire_wear = car_twin.get('current_state', {}).get('tire', {}).get('wear_level', 0.5)
        if tire_wear > 0.8:
            recommendations.append({
                "priority": "urgent",
                "category": "pit_strategy",
                "title": "URGENT: Pit Stop Required",
                "description": f"Tire wear at {tire_wear:.1%} - pit stop required within 2 laps",
                "confidence": 0.95,
                "expected_benefit": "Prevent tire failure",
                "execution_lap": race_context.get('lap', 0) + 1,
                "reasoning": "Tire wear exceeds safe threshold",
                "risks": ["Tire failure if delayed"],
                "alternatives": ["Extend current stint if track position critical"]
            })
        elif tire_wear > 0.6:
            recommendations.append({
                "priority": "moderate",
                "category": "tire_management",
                "title": "MODERATE: Monitor Tire Wear",
                "description": f"Tire wear at {tire_wear:.1%} - monitor closely for pit window",
                "confidence": 0.8,
                "expected_benefit": "Optimal pit timing",
                "execution_lap": None,
                "reasoning": "Tire wear approaching critical level",
                "risks": ["Premature pit stop"],
                "alternatives": ["Extend stint if pace is good"]
            })
        
        # Analyze fuel level
        fuel_level = car_twin.get('current_state', {}).get('fuel_level', 0.5)
        if fuel_level < 0.15:
            recommendations.append({
                "priority": "urgent",
                "category": "fuel_saving",
                "title": "URGENT: Fuel Saving Mode",
                "description": f"Fuel level at {fuel_level:.1%} - switch to fuel saving mode",
                "confidence": 0.9,
                "expected_benefit": "Complete race distance",
                "execution_lap": race_context.get('lap', 0),
                "reasoning": "Fuel level critically low",
                "risks": ["Running out of fuel"],
                "alternatives": ["Pit for fuel if necessary"]
            })
        
        # Analyze simulation results
        if simulation_results:
            best_result = min(simulation_results, key=lambda x: x.total_time if hasattr(x, 'total_time') else x.get('total_time', float('inf')))
            recommendations.append({
                "priority": "moderate",
                "category": "pit_strategy",
                "title": f"MODERATE: Optimal Pit Strategy",
                "description": f"Pit on lap {best_result.pit_lap if hasattr(best_result, 'pit_lap') else best_result.get('pit_lap', 'Unknown')} for best result",
                "confidence": best_result.success_probability if hasattr(best_result, 'success_probability') else best_result.get('success_probability', 0.8),
                "expected_benefit": f"Position {best_result.final_position if hasattr(best_result, 'final_position') else best_result.get('final_position', 'Unknown')}",
                "execution_lap": best_result.pit_lap if hasattr(best_result, 'pit_lap') else best_result.get('pit_lap'),
                "reasoning": "Simulation shows this is the optimal strategy",
                "risks": ["Strategy may not account for race dynamics"],
                "alternatives": ["Alternative pit windows available"]
            })
        
        return recommendations
    
    def _generate_emergency_recommendations(self) -> List[Dict[str, Any]]:
        """Generate emergency recommendations when all else fails"""
        return [{
            "priority": "urgent",
            "category": "general",
            "title": "URGENT: System Error",
            "description": "AI strategist encountered an error - use manual judgment",
            "confidence": 1.0,
            "expected_benefit": "Safe operation",
            "execution_lap": None,
            "reasoning": "System error requires manual intervention",
            "risks": ["No AI guidance available"],
            "alternatives": ["Manual strategy decisions"]
        }]


async def test_ai_strategist():
    """Test function for AI strategist"""
    async with AIStrategist() as strategist:
        # Create test data
        test_data = {
            "car_twin": None,  # Would be actual car twin data
            "field_twin": None,
            "simulation_results": [
                {
                    "pit_lap": 24,
                    "final_position": 3,
                    "total_time": 2675.4,
                    "success_probability": 0.85
                }
            ],
            "race_context": {
                "lap": 22,
                "session_type": "race"
            }
        }
        
        recommendations = await strategist.generate_recommendations(test_data)
        print("AI Strategy Recommendations:")
        for rec in recommendations:
            print(f"- {rec['priority'].upper()}: {rec['title']}")
            print(f"  {rec['description']}")
            print(f"  Expected Benefit: {rec['expected_benefit']}")
            print()


if __name__ == "__main__":
    asyncio.run(test_ai_strategist())
