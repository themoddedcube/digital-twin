# 🏎️ Race Twin Edge - F1 Strategy System

A real-time F1 race strategy system powered by Modular's hybrid HPC engine and AI reasoning.

## 🧩 System Architecture

### Three-Layer Brain Design

1. **Sensing Layer** - Collects and streams telemetry data (lap times, tire temps, weather, etc.)
2. **Thinking Layer** - Simulation engine using Modular's hybrid compute (edge/cloud) for Monte Carlo scenarios
3. **Explaining Layer** - AI co-strategist that interprets simulation outputs and provides natural language recommendations

### Data Flow
```
Telemetry → Digital Twin → Mojo Simulation → MAX LLM → Python Middleware → WebSocket Dashboard
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Modular Mojo installed
- Virtual environment activated

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd digital-twin

# Activate virtual environment
source .venv/digital-twin/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the System

#### Option 1: Full System (Recommended)
```bash
python run_system.py
```
This starts:
- HPC Orchestrator (WebSocket server on port 8765)
- Telemetry Feed Generator
- Streamlit Dashboard (http://localhost:8501)

#### Option 2: Individual Components

**Test the system:**
```bash
python test_system.py
```

**Run just the dashboard:**
```bash
streamlit run src/dashboard.py
```

**Run telemetry feed:**
```bash
python src/telemetry_feed.py
```

## 📊 Dashboard Features

The Streamlit dashboard provides:

- **Race Overview**: Current lap, session type, track conditions
- **Leaderboard**: Live race positions with tire/fuel data
- **Digital Twin State**: Real-time car state and predictions
- **AI Recommendations**: Prioritized strategy suggestions (Urgent/Moderate/Optional)
- **Simulation Results**: Monte Carlo simulation outcomes
- **Performance Metrics**: System performance monitoring

## 🔧 Configuration

### MAX LLM Setup
To use the AI strategist with MAX:

1. Start MAX server:
```bash
max serve llama-3.1-8b
```

2. The system will automatically connect to `http://localhost:8000/v1`

### Mojo Simulation
The system includes a Mojo simulation kernel for high-performance race strategy computation. The simulation runs Monte Carlo scenarios to predict optimal pit strategies.

## 📁 Project Structure

```
digital-twin/
├── src/
│   ├── twin_model.py          # Digital twin implementation
│   ├── simulate_strategy.mojo # Mojo simulation kernel
│   ├── hpc_orchestrator.py    # Main orchestration layer
│   ├── ai_strategist.py       # AI strategy recommendations
│   ├── telemetry_feed.py      # Telemetry data generation
│   └── dashboard.py           # Streamlit dashboard
├── shared/
│   └── latest_state.json      # Live state file
├── test_system.py             # System integration tests
├── run_system.py              # Main startup script
└── requirements.txt           # Python dependencies
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_system.py
```

This tests:
- Digital Twin functionality
- Telemetry feed generation
- AI strategist (with fallback to rule-based)
- Mojo simulation availability
- HPC orchestrator
- Full system integration

## 🎯 Key Features

### Digital Twin
- Real-time race state modeling
- Tire degradation prediction
- Fuel consumption tracking
- Performance delta calculation

### AI Strategy Recommendations
- **Urgent**: Critical decisions (pit now, safety car response)
- **Moderate**: Strategic adjustments (tire management, fuel saving)
- **Optional**: Long-term planning (end-of-race strategy)

### Hybrid Compute
- **Edge**: Local simulation for low-latency decisions
- **Cloud**: Modular cloud compute for high-depth parallel simulations

### Real-time Communication
- WebSocket streaming for high-performance updates
- Python middleware for fine-grained control
- Live dashboard with auto-refresh

## 🏁 Demo Flow

1. **Start the system**: `python run_system.py`
2. **Open dashboard**: Navigate to http://localhost:8501
3. **Watch live updates**: Telemetry flows through the system
4. **View recommendations**: AI strategist provides real-time advice
5. **Monitor performance**: Track system metrics and response times

## 🔮 Future Enhancements

- Real F1 telemetry integration (FastF1 API)
- Advanced weather modeling
- Multi-car strategy optimization
- Historical data analysis
- Machine learning model training

## 🤝 Team

- **Alan** - Systems Architect / HPC Lead
- **Abi** - Telemetry & Digital Twin Developer
- **Chaithu** - AI Strategist
- **Akhil** - Frontend Developer

## 📄 License

This project is developed for the HackTX hackathon.
