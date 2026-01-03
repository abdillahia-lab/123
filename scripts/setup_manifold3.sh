#!/bin/bash
# BAHB - Setup Script for DJI Manifold 3 (NVIDIA Orin NX)
# This script configures the Manifold 3 for optimal AI inference performance

set -e

echo "=========================================="
echo "BAHB - Manifold 3 Setup"
echo "=========================================="

# Check if running on Jetson/Orin
if [ ! -f /etc/nv_tegra_release ]; then
    echo "Warning: Not running on NVIDIA Jetson/Orin platform"
    echo "Some optimizations may not apply"
fi

# Set maximum performance mode
echo "Setting maximum performance mode..."
if command -v nvpmodel &> /dev/null; then
    sudo nvpmodel -m 0  # MAXN mode
    sudo jetson_clocks
    echo "Performance mode: MAXN enabled"
else
    echo "nvpmodel not found, skipping power mode configuration"
fi

# Configure GPU memory
echo "Configuring GPU memory allocation..."
export CUDA_VISIBLE_DEVICES=0
export TF_FORCE_GPU_ALLOW_GROWTH=true

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    libopencv-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libv4l-dev \
    v4l-utils \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev

# Create virtual environment
echo "Creating Python virtual environment..."
cd /home/user/BAHB
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip wheel setuptools

# Install PyTorch for Jetson (JP6.x compatible)
echo "Installing PyTorch for Jetson..."
pip install --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v60 \
    torch \
    torchvision

# Install TensorRT Python bindings
echo "Installing TensorRT bindings..."
pip install tensorrt

# Install project dependencies
echo "Installing BAHB dependencies..."
pip install -e ".[full]"

# Create necessary directories
echo "Creating data directories..."
sudo mkdir -p /data/bahb/{models,inspections,reports,recordings,cache}
sudo chown -R $USER:$USER /data/bahb

# Download model weights
echo "Downloading model weights..."
./scripts/download_models.sh

# Configure camera streams
echo "Configuring H30T camera streams..."
cat > /etc/gstreamer-1.0/registry.x86_64.bin.tmp << 'EOF'
# H30T RTSP stream configuration
# Wide camera: rtsp://192.168.42.2:8554/wide
# Zoom camera: rtsp://192.168.42.2:8554/zoom
# Thermal camera: rtsp://192.168.42.2:8554/thermal
EOF

# Set up systemd service
echo "Setting up systemd service..."
sudo tee /etc/systemd/system/bahb.service > /dev/null << 'EOF'
[Unit]
Description=BAHB Drone Inspection System
After=network.target

[Service]
Type=simple
User=dji
WorkingDirectory=/home/user/BAHB
Environment="PATH=/home/user/BAHB/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/home/user/BAHB/venv/bin/python -m bahb.main --config /home/user/BAHB/configs/production.yaml
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable bahb

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To start BAHB manually:"
echo "  source venv/bin/activate"
echo "  python -m bahb.main --config configs/production.yaml"
echo ""
echo "To start as service:"
echo "  sudo systemctl start bahb"
echo ""
echo "To check status:"
echo "  sudo systemctl status bahb"
echo ""
