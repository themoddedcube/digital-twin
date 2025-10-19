# F1 Race Twin Edge - Test Suite

Comprehensive test suite for the F1 Race Strategy System.

## 📁 Test Organization

```
tests/
├── unit/              # Unit tests for individual components
│   ├── test_field_twin.py
│   ├── test_core_components.py
│   └── test_system_setup.py
├── integration/       # Integration tests for component interactions
│   ├── test_api_server.py
│   ├── test_orchestrator.py
│   └── test_system.py
└── live/             # Live telemetry and real-time system tests
    ├── test_live_telemetry.py
    ├── test_live_transfer_simple.py
    ├── test_live_transfer_demo.py
    └── test_orchestrator_live.py
```

## 🚀 Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Categories
```bash
# Unit tests only
python run_tests.py --category unit

# Integration tests only
python run_tests.py --category integration

# Live tests only
python run_tests.py --category live
```

### Quick Tests (Unit Only)
```bash
python run_tests.py --quick
```

### Run Individual Tests
```bash
# Unit test
python tests/unit/test_core_components.py

# Integration test
python tests/integration/test_system.py

# Live test
python tests/live/test_live_telemetry.py
```

## 📊 Test Categories

### Unit Tests
Tests for individual components in isolation:
- **Field Twin**: Competitor modeling and strategic analysis
- **Core Components**: Telemetry, twins, state management
- **System Setup**: Configuration and initialization

### Integration Tests
Tests for component interactions:
- **API Server**: REST API endpoints and data serving
- **HPC Orchestrator**: Hybrid compute orchestration
- **Full System**: End-to-end system integration

### Live Tests
Tests for real-time telemetry and live data:
- **Live Telemetry**: WebSocket/UDP telemetry ingestion
- **Live Transfer**: Data transfer between components
- **Orchestrator Live**: Real-time orchestration

## ✅ Test Status

Run `python run_tests.py` to see current test status.

## 🔧 Prerequisites

Ensure you have:
- Virtual environment activated
- All dependencies installed: `pip install -r requirements.txt`
- MAX server running (for AI strategist tests): `max serve --model modularai/Llama-3.1-8B-Instruct-GGUF`

## 📝 Writing New Tests

Follow these guidelines:

1. **Unit tests** - Test single component
2. **Integration tests** - Test component interactions
3. **Live tests** - Test with real/simulated telemetry

Example test structure:
```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_component():
    """Test description"""
    # Your test code
    pass

if __name__ == "__main__":
    test_component()
```

## 🐛 Debugging Failed Tests

If tests fail:
1. Check virtual environment is activated
2. Ensure all dependencies are installed
3. Verify MAX server is running (if needed)
4. Check logs in the test output
5. Run individual test for detailed error messages

## 📈 Coverage

To run tests with coverage:
```bash
pip install pytest pytest-cov
pytest tests/ --cov=src --cov-report=html
```

View coverage report: `open htmlcov/index.html`

