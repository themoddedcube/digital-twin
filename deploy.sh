#!/bin/bash
set -e

echo "🏎️ F1 Race Twin Edge - H100 Deployment"
echo "======================================"

# 1. Check for NVIDIA GPU
echo "🔍 Checking for NVIDIA GPU..."
if ! command -v nvidia-smi &> /dev/null
then
    echo "❌ NVIDIA GPU not detected. This deployment requires an NVIDIA H100."
    exit 1
fi
echo "✅ NVIDIA GPU detected."

# 2. Check for Docker and Docker Compose
echo "🔍 Checking for Docker and Docker Compose..."
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null
then
    echo "❌ Docker or Docker Compose not found. Please install them."
    exit 1
fi
echo "✅ Docker and Docker Compose found."

# 3. Check for HF_TOKEN
echo "🔍 Checking for HF_TOKEN environment variable..."
if [ -z "$HF_TOKEN" ]; then
    echo "❌ HF_TOKEN is not set. Please set your Hugging Face token."
    echo "   Example: export HF_TOKEN=\"hf_YOUR_TOKEN\""
    exit 1
fi
echo "✅ HF_TOKEN is set."

# 4. Build Docker image
echo "🏗️ Building Docker image..."
docker-compose build --no-cache
echo "✅ Docker image built successfully."

# 5. Start services
echo "🚀 Starting services with Docker Compose..."
docker-compose up -d
echo "✅ Services started in detached mode."

# 6. Health check
echo "💖 Performing health check..."
for i in $(seq 1 10); do
    if docker-compose ps | grep f1-twin-edge-app | grep "(healthy)" &> /dev/null; then
        echo "✅ F1 Race Twin Edge is healthy!"
        break
    else
        echo "⏳ Waiting for F1 Race Twin Edge to become healthy ($i/10)..."
        sleep 10
    fi
    if [ $i -eq 10 ]; then
        echo "❌ F1 Race Twin Edge did not become healthy in time."
        echo "   Check logs for details: docker-compose logs f1-twin-edge-app"
        exit 1
    fi
done

echo "🎉 Deployment complete! Your F1 Race Twin Edge system is running."
echo "Access API at http://localhost:8000/api/v1/health"
echo "View logs: docker-compose logs -f"
