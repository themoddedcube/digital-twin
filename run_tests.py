#!/usr/bin/env python3
"""
Master Test Runner for F1 Race Twin Edge System

Runs all tests with proper categorization and reporting.
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class TestRunner:
    """Main test runner for the F1 system"""
    
    def __init__(self):
        self.tests_dir = Path(__file__).parent / "tests"
        self.results = {
            "unit": {},
            "integration": {},
            "live": {}
        }
    
    async def run_unit_tests(self):
        """Run unit tests"""
        print("\n" + "=" * 70)
        print("🧪 UNIT TESTS")
        print("=" * 70)
        
        unit_tests = [
            ("Field Twin", "tests/unit/test_field_twin.py"),
            ("Core Components", "tests/unit/test_core_components.py"),
            ("System Setup", "tests/unit/test_system_setup.py"),
        ]
        
        for name, test_file in unit_tests:
            if Path(test_file).exists():
                print(f"\n▶ Running {name}...")
                result = await self._run_test(test_file)
                self.results["unit"][name] = result
            else:
                print(f"⚠️  {name} not found: {test_file}")
    
    async def run_integration_tests(self):
        """Run integration tests"""
        print("\n" + "=" * 70)
        print("🔗 INTEGRATION TESTS")
        print("=" * 70)
        
        integration_tests = [
            ("API Server", "tests/integration/test_api_server.py"),
            ("HPC Orchestrator", "tests/integration/test_orchestrator.py"),
            ("Full System", "tests/integration/test_system.py"),
        ]
        
        for name, test_file in integration_tests:
            if Path(test_file).exists():
                print(f"\n▶ Running {name}...")
                result = await self._run_test(test_file)
                self.results["integration"][name] = result
            else:
                print(f"⚠️  {name} not found: {test_file}")
    
    async def run_live_tests(self):
        """Run live telemetry tests"""
        print("\n" + "=" * 70)
        print("📡 LIVE TELEMETRY TESTS")
        print("=" * 70)
        
        live_tests = [
            ("Live Telemetry", "tests/live/test_live_telemetry.py"),
            ("Live Transfer Simple", "tests/live/test_live_transfer_simple.py"),
            ("Live Transfer Demo", "tests/live/test_live_transfer_demo.py"),
            ("Orchestrator Live", "tests/live/test_orchestrator_live.py"),
        ]
        
        for name, test_file in live_tests:
            if Path(test_file).exists():
                print(f"\n▶ Running {name}...")
                result = await self._run_test(test_file)
                self.results["live"][name] = result
            else:
                print(f"⚠️  {name} not found: {test_file}")
    
    async def _run_test(self, test_file: str) -> bool:
        """Run a single test file"""
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"  ✅ PASSED")
                return True
            else:
                print(f"  ❌ FAILED")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  TIMEOUT")
            return False
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_passed = 0
        total_failed = 0
        
        for category, tests in self.results.items():
            if tests:
                print(f"\n{category.upper()}:")
                for name, passed in tests.items():
                    status = "✅ PASS" if passed else "❌ FAIL"
                    print(f"  {name}: {status}")
                    if passed:
                        total_passed += 1
                    else:
                        total_failed += 1
        
        total = total_passed + total_failed
        print(f"\n{'=' * 70}")
        print(f"Total: {total_passed}/{total} tests passed")
        
        if total_failed == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {total_failed} test(s) failed")
        
        return total_failed == 0


async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run F1 Race Twin Edge tests")
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "live", "all"],
        default="all",
        help="Test category to run"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only quick unit tests"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    print(f"\n🏎️ F1 Race Twin Edge - Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.quick or args.category == "unit":
        await runner.run_unit_tests()
    elif args.category == "integration":
        await runner.run_integration_tests()
    elif args.category == "live":
        await runner.run_live_tests()
    else:  # all
        await runner.run_unit_tests()
        await runner.run_integration_tests()
        await runner.run_live_tests()
    
    success = runner.print_summary()
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

