# BAHB - Autonomous Drone Inspection System

## Advanced AI-Powered Infrastructure Inspection for Data Centers & Substations

A premier inspection application running on **DJI Manifold 3** mounted on **DJI Matrice 400** with **DJI H30T** multi-sensor camera.

## 🎯 Overview

BAHB (Building And Hardware Baseline) is an enterprise-grade autonomous inspection system that leverages state-of-the-art AI models to detect anomalies, defects, and potential failures in critical infrastructure.

## 🚁 Hardware Platform

| Component | Model | Purpose |
|-----------|-------|---------|
| **Compute** | DJI Manifold 3 | Edge AI inference (NVIDIA Orin NX) |
| **Aircraft** | DJI Matrice 400 | Industrial inspection drone |
| **Camera** | DJI H30T | Thermal + Wide + Zoom + Laser RF |

## 🧠 AI Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      H30T Multi-Sensor Input                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│  │ Thermal  │  │  Wide    │  │  Zoom    │  │  Laser Rangefinder   │ │
│  │ 640x512  │  │ 4K RGB   │  │  8MP     │  │      Distance        │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘ │
└───────┼─────────────┼─────────────┼────────────────────┼────────────┘
        │             │             │                    │
        ▼             ▼             ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PREPROCESSING LAYER                               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────────────┐   │
│  │ Frame Sync     │ │ Color/Thermal  │ │ GPS/IMU Fusion         │   │
│  │ & Alignment    │ │ Calibration    │ │ Geolocation            │   │
│  └────────────────┘ └────────────────┘ └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   YOLOv12     │     │    RF-DETR      │     │   SAM3 Nano     │
│  Ultra-Fast   │     │  Transformer    │     │   Precision     │
│  Detection    │     │  Segmentation   │     │   Segmentation  │
│  ~2ms/frame   │     │  ~15ms/frame    │     │  Point-Prompt   │
└───────┬───────┘     └────────┬────────┘     └────────┬────────┘
        │                      │                       │
        └──────────────────────┼───────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FUSION & ANALYSIS LAYER                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Qwen2.5-VL-3B-AWQ (Visual Language Model)         │ │
│  │  • Contextual Understanding    • Anomaly Description           │ │
│  │  • Natural Language Reports    • Multi-modal Reasoning         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OUTPUT & DECISION LAYER                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Alerts   │ │ Reports  │ │ 3D Map   │ │ Telemetry│ │ Cloud    │  │
│  │ System   │ │ Generator│ │ Builder  │ │ Stream   │ │ Sync     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔍 Detection Capabilities

### Data Center Inspection
- **Thermal Hotspots**: Server overheating, cooling failures
- **Cable Management**: Damaged cables, improper routing
- **Fire Hazards**: Electrical anomalies, smoke detection
- **Security**: Unauthorized access, door status
- **HVAC**: Cooling unit performance, airflow analysis

### Substation Inspection
- **Transformers**: Oil leaks, thermal anomalies, corona discharge
- **Insulators**: Cracks, contamination, flashover damage
- **Conductors**: Sagging, corrosion, hot joints
- **Switchgear**: Overheating, arc damage
- **Vegetation**: Encroachment, clearance violations

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/your-org/BAHB.git
cd BAHB

# Create virtual environment (Python 3.10+ required)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download model weights
./scripts/download_models.sh

# Configure for Manifold 3
./scripts/setup_manifold3.sh
```

## 🚀 Quick Start

```bash
# Start inspection system
python -m bahb.main --config configs/production.yaml

# Run with specific inspection profile
python -m bahb.main --profile substation --output /data/inspections

# Development mode with visualization
python -m bahb.main --dev --visualize
```

## 📁 Project Structure

```
BAHB/
├── bahb/                    # Main application package
│   ├── core/               # Core infrastructure
│   ├── camera/             # DJI H30T interface
│   ├── models/             # AI model implementations
│   │   ├── yolov12/       # YOLOv12 detection
│   │   ├── rf_detr/       # RF-DETR segmentation
│   │   ├── sam3/          # SAM3 Nano segmentation
│   │   └── qwen_vl/       # Qwen2.5-VL analysis
│   ├── thermal/            # Thermal analysis
│   ├── inspection/         # Inspection logic
│   ├── reporting/          # Report generation
│   ├── mapping/            # 3D mapping
│   └── streaming/          # Real-time streaming
├── configs/                 # Configuration files
├── scripts/                 # Setup and utility scripts
├── tests/                   # Test suite
└── docs/                    # Documentation
```

## ⚙️ Configuration

See `configs/production.yaml` for full configuration options.

## 📊 Performance Targets (Manifold 3)

| Model | Resolution | Inference Time | FPS |
|-------|------------|----------------|-----|
| YOLOv12-L | 1280x720 | ~2ms | 500 |
| RF-DETR | 640x640 | ~15ms | 66 |
| SAM3 Nano | 1024x1024 | ~8ms | 125 |
| Qwen2.5-VL-3B | 448x448 | ~50ms | 20 |

## 🔐 Safety Features

- Automatic RTH on critical anomaly detection
- Obstacle avoidance integration
- Geofence enforcement
- Emergency landing protocols
- Real-time health monitoring

## 📄 License

Proprietary - All Rights Reserved

## 🤝 Support

For support and inquiries, contact your system administrator.
