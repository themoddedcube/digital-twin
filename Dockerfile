FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Install Python and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev \
    build-essential curl git vim \
    && rm -rf /var/lib/apt/lists/*

# Create a symbolic link for python3.11 to python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-docker.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Modular MAX
RUN pip install --pre modular --index-url https://dl.modular.com/public/nightly/python/simple/

# Copy source code
COPY . /app

# Expose ports for API and MAX
EXPOSE 8000
EXPOSE 8001

# Set environment variables
ENV PYTHONPATH=/app/src
ENV HF_TOKEN=${HF_TOKEN}

# Command to run the application (orchestrator will start everything)
CMD ["python", "-m", "twin_system.main_orchestrator"]