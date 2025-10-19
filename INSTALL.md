# Installation Guide - Race Twin Edge

## Prerequisites
- Python 3.12+
- macOS, Linux, or WSL (Windows)
- (Optional) NVIDIA GPU for production deployment

## Quick Setup

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd digital-twin
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Core Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Modular (MAX + Mojo)
```bash
# Install latest nightly build (recommended)
pip install --pre modular --index-url https://dl.modular.com/public/nightly/python/simple/
```

**Important:** Modular packages should be installed from their official index, not PyPI, to get the latest features and GPU support.

### 5. Set Up Hugging Face Token
```bash
export HF_TOKEN="your_hugging_face_token_here"
```

Get your token from: https://huggingface.co/settings/tokens

## Running the System

### Option 1: Full System (Recommended for Demo)
```bash
# Terminal 1: Start MAX Server
source .venv/bin/activate
export HF_TOKEN="your_token"
max serve --model modularai/Llama-3.1-8B-Instruct-GGUF

# Terminal 2: Start Dashboard
source .venv/bin/activate
streamlit run src/dashboard.py
```

Then visit: http://localhost:8501

### Option 2: Quick Demo Script
```bash
source .venv/bin/activate
python demo.py
```

### Option 3: Run Tests
```bash
source .venv/bin/activate
python test_system.py
```

## GPU Deployment (Production)

### Using NVIDIA Brev or Cloud GPU
```bash
# SSH into GPU instance
ssh user@gpu-instance

# Clone and setup (same as above)
git clone <your-repo-url>
cd digital-twin
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install --pre modular --index-url https://dl.modular.com/public/nightly/python/simple/

# Start MAX (will auto-detect GPU)
export HF_TOKEN="your_token"
max serve --model modularai/Llama-3.1-8B-Instruct-GGUF

# You should see: "Using NVIDIA [GPU_MODEL]" instead of "falling back to CPU"
```

### Using Docker with GPU
```bash
# Requires NVIDIA Container Toolkit installed
docker run --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  -e HF_TOKEN="$HF_TOKEN" \
  docker.modular.com/modular/max-nvidia-full:latest \
  --model-path modularai/Llama-3.1-8B-Instruct-GGUF
```

## Troubleshooting

### "No GPUs available, falling back to CPU"
- **On Mac:** This is expected. Apple GPUs aren't supported yet by MAX.
- **On Linux/Cloud:** Check NVIDIA drivers with `nvidia-smi`

### "MAX API error: 400" or "Unknown model"
- Make sure model name is exactly: `modularai/Llama-3.1-8B-Instruct-GGUF`
- Check MAX server is running: `curl http://localhost:8000/health`

### "Module not found: modular"
- Install from Modular's index: `pip install --pre modular --index-url https://dl.modular.com/public/nightly/python/simple/`

### Mojo compilation errors
- Ensure you're using Mojo 0.25.7+
- Check version: `mojo --version`

## Development Workflow

1. **Start MAX server** (once)
   ```bash
   max serve --model modularai/Llama-3.1-8B-Instruct-GGUF
   ```

2. **Run dashboard** (for UI)
   ```bash
   streamlit run src/dashboard.py
   ```

3. **Make changes** to Python files - they'll auto-reload in Streamlit

4. **Test changes**
   ```bash
   python test_system.py
   ```

## Team Roles Setup

### Abi (Telemetry & Twin)
```bash
# Test telemetry feed
python src/telemetry_feed.py

# Test digital twin
python src/twin_model.py
```

### Alan (HPC & Mojo)
```bash
# Test Mojo simulation
mojo src/simulate_strategy.mojo

# Test orchestrator
python src/hpc_orchestrator.py
```

### Chaithu (AI Strategist)
```bash
# Test AI strategist
python src/ai_strategist.py
```

### Akhil (Dashboard)
```bash
# Run dashboard
streamlit run src/dashboard.py
```

## Performance Notes

| Environment | Inference Speed | Notes |
|-------------|----------------|-------|
| **Mac CPU** | 3-5 tok/s | Good for development |
| **Linux CPU** | 5-10 tok/s | Slightly faster |
| **NVIDIA A10** | 50-100 tok/s | Production ready |
| **NVIDIA H100** | 200-500 tok/s | High performance |

## Additional Resources

- [MAX Documentation](https://docs.modular.com/max/)
- [Mojo Documentation](https://docs.modular.com/mojo/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Project README](README.md)

