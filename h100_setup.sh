#!/bin/bash
set -e

echo "🏎️ F1 Race Twin Edge - H100 Setup Script"
echo "========================================"

# Update system
echo "📦 Updating system packages..."
apt-get update -y

# Install Python 3.12 and dependencies (already installed by system)
echo "🐍 Using Python 3.12 (already installed)..."
apt-get install -y python3.12-venv python3.12-dev python3-pip

# Install build tools
echo "🔨 Installing build tools..."
apt-get install -y build-essential curl git vim

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker $USER

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone the repository
echo "📥 Cloning F1 Race Twin Edge repository..."
cd /root
git clone https://github.com/themoddedcube/digital-twin.git
cd digital-twin

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3.12 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Modular MAX
echo "🤖 Installing Modular MAX..."
pip install --pre modular --index-url https://dl.modular.com/public/nightly/python/simple/

# Set up environment
echo "⚙️ Setting up environment..."
export PYTHONPATH=/root/digital-twin/src
echo "export PYTHONPATH=/root/digital-twin/src" >> ~/.bashrc

# Create shared directories
echo "📁 Creating shared directories..."
mkdir -p shared config

# Set permissions
echo "🔐 Setting permissions..."
chmod +x deploy.sh

# Set HF_TOKEN (you'll need to replace this with your actual token)
echo "🔑 Setting up Hugging Face token..."
# export HF_TOKEN="your_huggingface_token_here"
# echo "export HF_TOKEN=\"your_huggingface_token_here\"" >> ~/.bashrc

# Build Docker image
echo "🏗️ Building Docker image..."
docker build -t f1-race-twin-edge:latest .

# Start the system
echo "🚀 Starting F1 Race Twin Edge system..."
./deploy.sh

echo "✅ Setup complete! F1 Race Twin Edge is running."
echo "🌐 API available at: http://localhost:8000"
echo "🤖 MAX LLM available at: http://localhost:8001"
echo "📊 Check status: docker-compose ps"
echo "📋 View logs: docker-compose logs -f"
