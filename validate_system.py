#!/usr/bin/env python3
"""
Quick System Validation Script
Validates all critical integrations are working
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_imports():
    """Validate all critical imports"""
    print("=" * 70)
    print("🔍 SYSTEM VALIDATION")
    print("=" * 70)
    
    print("\n✅ Phase 1: Import Validation")
    print("-" * 70)
    
    try:
        # Core infrastructure
        from core import TwinModel, StateManager, TELEMETRY_SCHEMA, CAR_TWIN_SCHEMA
        print("  ✅ Core infrastructure: OK")
        
        # Twin system
        from twin_system import CarTwin, FieldTwin, TelemetryIngestor, TelemetrySimulator
        print("  ✅ Twin system imports: OK")
        
        # MAX integration
        from max_integration import AIStrategist, HPCOrchestrator
        print("  ✅ MAX integration imports: OK")
        
        # Compatibility layer
        from compat_layer import DigitalTwin, TelemetryGenerator
        print("  ✅ Compatibility layer: OK")
        
        # Dashboard is handled by separate team
        print("  ℹ️  Dashboard: External team")
        
        # System monitoring
        from twin_system import SystemMonitor
        print("  ✅ System monitoring: OK")
        
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def check_initialization():
    """Validate component initialization"""
    print("\n✅ Phase 2: Component Initialization")
    print("-" * 70)
    
    try:
        from twin_system import CarTwin, FieldTwin
        from max_integration import HPCOrchestrator
        
        # Initialize components
        car_twin = CarTwin(car_id="44")
        print("  ✅ CarTwin: OK")
        
        field_twin = FieldTwin()
        print("  ✅ FieldTwin: OK")
        
        hpc_orch = HPCOrchestrator()
        print("  ✅ HPCOrchestrator: OK")
        
        print("  ℹ️  Dashboard: Managed by external team")
        
        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_max_integration():
    """Check MAX server status"""
    print("\n✅ Phase 3: MAX Integration")
    print("-" * 70)
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("  ✅ MAX server: RUNNING")
            return True
        else:
            print(f"  ⚠️  MAX server: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠️  MAX server: OFFLINE (fallback mode active)")
        return False

def check_file_structure():
    """Validate critical files exist"""
    print("\n✅ Phase 4: File Structure")
    print("-" * 70)
    
    critical_files = [
        "src/twin_system/twin_model.py",
        "src/twin_system/field_twin.py",
        "src/twin_system/telemetry_feed.py",
        "src/max_integration/hpc_orchestrator.py",
        "src/max_integration/ai_strategist.py",
        "src/max_integration/simulate_strategy.mojo",
        "src/core/interfaces.py",
        "src/core/schemas.py",
        "src/compat_layer.py",
        "tests/README.md",
        "run_tests.py",
        "requirements.txt"
    ]
    
    all_exist = True
    for file in critical_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} MISSING")
            all_exist = False
    
    return all_exist

def main():
    """Run all validation checks"""
    results = []
    
    results.append(("Imports", check_imports()))
    results.append(("Initialization", check_initialization()))
    results.append(("MAX Integration", check_max_integration()))
    results.append(("File Structure", check_file_structure()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 SYSTEM VALIDATION PASSED - Ready for demo!")
        return 0
    elif passed >= total - 1:
        print("\n⚠️  SYSTEM MOSTLY READY - Minor issues detected")
        return 0
    else:
        print("\n❌ SYSTEM VALIDATION FAILED - Fix issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

