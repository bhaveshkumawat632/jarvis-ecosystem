# Use a verified CUDA runtime image with Python 3.11 pre-installed
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Enforce clean environment dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up runtime symlinks
RUN ln -sf /usr/bin/python3.11 /usr/bin/python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3

WORKDIR /workspace
# Upgrade packaging utilities and deploy targeted tensor extensions
RUN python3.11 -m pip install --no-cache-dir --upgrade pip setuptools wheel
RUN python3.11 -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

COPY requirements.txt .
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "movie_generator.py"]
