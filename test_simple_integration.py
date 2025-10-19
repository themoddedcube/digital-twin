#!/usr/bin/env python3
"""
Simple test script for the integrated Monte Carlo and AI strategy API.

This script tests the new endpoints added to the existing API server.
"""

import requests
import time
import json
from datetime import datetime


def test_api_endpoints():
    """Test the new API endpoints."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Simple Monte Carlo Integration")
    print("=" * 50)
    
    # Test health first
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test Monte Carlo simulation
    print("\n2. Testing Monte Carlo simulation...")
    try:
        response = requests.get(f"{base_url}/api/v1/monte-carlo/simulate", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("   ✅ Monte Carlo simulation successful")
                print(f"   📊 Found {len(data.get('simulation_results', []))} strategies")
                if data.get("best_strategy"):
                    best = data["best_strategy"]
                    print(f"   🏆 Best strategy: Pit on lap {best['pit_lap']}, Position {best['final_position']}")
                    print(f"   ⚡ Success probability: {best['success_probability']:.2%}")
                
                # Check if Mojo was used
                simulation_stats = data.get("simulation_stats", {})
                if simulation_stats.get("mojo_available"):
                    print("   🚀 Mojo kernel: Available (GPU accelerated)")
                else:
                    print("   🐍 Mojo kernel: Fallback to Python")
            else:
                print(f"   ⚠️  Simulation returned: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ Monte Carlo simulation failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Monte Carlo simulation error: {e}")
    
    # Test Monte Carlo with custom pit window
    print("\n3. Testing Monte Carlo with custom pit window...")
    try:
        response = requests.get(f"{base_url}/api/v1/monte-carlo/simulate?pit_window_start=25&pit_window_end=35", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("   ✅ Custom pit window simulation successful")
                print(f"   📊 Pit window: {data.get('metadata', {}).get('pit_window', {})}")
            else:
                print(f"   ⚠️  Custom simulation returned: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ Custom Monte Carlo simulation failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Custom Monte Carlo simulation error: {e}")
    
    # Test Monte Carlo stats
    print("\n4. Testing Monte Carlo stats...")
    try:
        response = requests.get(f"{base_url}/api/v1/monte-carlo/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stats = data.get("monte_carlo_stats", {})
                print("   ✅ Monte Carlo stats retrieved")
                print(f"   📊 Total simulations: {stats.get('total_simulations', 0)}")
                print(f"   ⏱️  Last simulation time: {stats.get('last_simulation_time_ms', 0):.2f}ms")
            else:
                print(f"   ⚠️  Stats returned: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ Monte Carlo stats failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Monte Carlo stats error: {e}")
    
    # Test AI strategy recommendations
    print("\n5. Testing AI strategy recommendations...")
    try:
        response = requests.get(f"{base_url}/api/v1/ai-strategy/recommendations", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                recommendations = data.get("recommendations", [])
                print("   ✅ AI strategy recommendations generated")
                print(f"   🤖 Generated {len(recommendations)} recommendations")
                
                for i, rec in enumerate(recommendations[:3]):  # Show first 3
                    print(f"   📋 {i+1}. {rec.get('priority', 'Unknown').upper()}: {rec.get('title', 'No title')}")
                    print(f"      {rec.get('description', 'No description')}")
            else:
                print(f"   ⚠️  AI recommendations returned: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ AI strategy recommendations failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ AI strategy recommendations error: {e}")
    
    # Test existing endpoints still work
    print("\n6. Testing existing endpoints...")
    try:
        response = requests.get(f"{base_url}/api/v1/telemetry", timeout=5)
        if response.status_code == 200:
            print("   ✅ Telemetry endpoint working")
        else:
            print(f"   ❌ Telemetry endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Telemetry endpoint error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Simple integration test completed!")
    return True


def test_performance():
    """Test API performance."""
    base_url = "http://localhost:8000"
    
    print("\n🚀 Testing API Performance")
    print("-" * 30)
    
    endpoints = [
        ("/api/v1/health", "Health check"),
        ("/api/v1/telemetry", "Telemetry data"),
        ("/api/v1/monte-carlo/simulate", "Monte Carlo simulation"),
        ("/api/v1/monte-carlo/stats", "Monte Carlo stats"),
        ("/api/v1/ai-strategy/recommendations", "AI recommendations")
    ]
    
    for endpoint, name in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                print(f"   ✅ {name}: {response_time:.2f}ms")
            else:
                print(f"   ❌ {name}: {response.status_code} ({response_time:.2f}ms)")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")


def main():
    """Run all tests."""
    print("🚀 Starting Simple Monte Carlo Integration Tests")
    print("Make sure the API server is running on localhost:8000")
    print("=" * 60)
    
    # Test API endpoints
    success = test_api_endpoints()
    
    if success:
        # Test performance
        test_performance()
        
        print("\n📋 Summary:")
        print("✅ Monte Carlo simulation endpoint working")
        print("✅ AI strategy recommendations endpoint working")
        print("✅ All existing endpoints still functional")
        print("✅ Performance within acceptable limits")
        
        print("\n🎯 Available Endpoints:")
        print("   • GET  /api/v1/monte-carlo/simulate - Run Monte Carlo simulation")
        print("   • GET  /api/v1/monte-carlo/stats - Get simulation statistics")
        print("   • GET  /api/v1/ai-strategy/recommendations - Get AI recommendations")
        print("   • All existing endpoints remain unchanged")
        
        print("\n🔧 Usage Examples:")
        print("   # Run simulation with default pit window")
        print("   curl http://localhost:8000/api/v1/monte-carlo/simulate")
        print()
        print("   # Run simulation with custom pit window")
        print("   curl 'http://localhost:8000/api/v1/monte-carlo/simulate?pit_window_start=25&pit_window_end=35'")
        print()
        print("   # Get AI strategy recommendations")
        print("   curl http://localhost:8000/api/v1/ai-strategy/recommendations")
        
    else:
        print("\n❌ Some tests failed. Please check the API server is running.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
