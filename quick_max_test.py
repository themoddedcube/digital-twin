#!/usr/bin/env python3
"""
Quick MAX Test - Direct API calls

This script tests MAX directly with live data from orchestrator.
"""

import requests
import json
import time
import sys
import asyncio
from datetime import datetime

def test_services():
    """Quick service check."""
    try:
        # Test orchestrator
        orchestrator_response = requests.get("http://localhost:8000/api/v1/health", timeout=3)
        print(f"Orchestrator: {orchestrator_response.status_code}")
        
        # Test MAX
        max_response = requests.get("http://localhost:8001/health", timeout=3)
        print(f"MAX: {max_response.status_code}")
        
        return orchestrator_response.status_code == 200
    except Exception as e:
        print(f"Service check error: {e}")
        return False

def get_live_data():
    """Get live data from orchestrator."""
    try:
        telemetry_response = requests.get("http://localhost:8000/api/v1/telemetry", timeout=5)
        car_twin_response = requests.get("http://localhost:8000/api/v1/car-twin", timeout=5)
        
        if telemetry_response.status_code == 200 and car_twin_response.status_code == 200:
            return {
                "telemetry": telemetry_response.json()["telemetry"],
                "car_twin": car_twin_response.json()["car_twin"]
            }
        return None
    except Exception as e:
        print(f"Error getting live data: {e}")
        return None

def call_max_directly():
    """Call MAX directly with a simple test."""
    try:
        payload = {
            "model": "llama-3.1-8b",
            "messages": [{"role": "user", "content": "Hello, this is a test. Respond with 'MAX is working'"}],
            "max_tokens": 50
        }
        
        response = requests.post(
            "http://localhost:8001/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        else:
            return f"Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error calling MAX: {e}"

def main():
    """Main test function."""
    print("🏎️  QUICK MAX TEST")
    print("=" * 40)
    
    # Check services
    print("🔍 Checking services...")
    if not test_services():
        print("❌ Services not ready")
        return False
    
    print("✅ Services running")
    
    # Get live data
    print("\n📊 Getting live data...")
    live_data = get_live_data()
    if not live_data:
        print("❌ No live data")
        return False
    
    telemetry = live_data["telemetry"]
    car_twin = live_data["car_twin"]
    
    print(f"✅ Live data: Lap {telemetry.get('lap', 'N/A')}, Speed: {car_twin.get('current_state', {}).get('speed', 'N/A'):.1f} km/h")
    
    # Test MAX directly
    print("\n🤖 Testing MAX directly...")
    max_response = call_max_directly()
    print(f"MAX Response: {max_response}")
    
    if "MAX is working" in max_response or "working" in max_response.lower():
        print("✅ MAX is working!")
        return True
    else:
        print("❌ MAX test failed")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Quick test passed!")
    else:
        print("\n❌ Quick test failed!")
        sys.exit(1)
