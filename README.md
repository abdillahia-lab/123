# Paces - State-of-the-Art Renewable Energy Management Platform

A comprehensive AI-powered platform for renewable energy asset management, combining autonomous drone inspection (BAHB) with predictive analytics and portfolio optimization.

## Overview

Paces integrates cutting-edge AI models with real-time monitoring to deliver:
- **Solar Farm Analytics** - Panel defect detection, thermal analysis, performance monitoring
- **Wind Turbine Inspection** - Blade inspection, vibration analysis, component health
- **Battery Storage Management** - SOC/SOH tracking, dispatch optimization, thermal management
- **AI-Powered Forecasting** - Multi-model energy production and price predictions
- **Portfolio Optimization** - Real-time dispatch, risk management, investment analysis
- **Carbon & ESG Tracking** - CO2 avoidance, carbon credits, sustainability reporting
- **Predictive Maintenance** - ML-based failure prediction, optimized scheduling
- **Financial Analytics** - ROI, LCOE, revenue forecasting

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PACES PLATFORM                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    Solar     │  │     Wind     │  │   Battery    │  │     Grid     │    │
│  │   Analyzer   │  │   Analyzer   │  │   Manager    │  │   Manager    │    │
│  │              │  │              │  │              │  │              │    │
│  │ • Defect Det │  │ • Blade Insp │  │ • SOC/SOH    │  │ • Power Flow │    │
│  │ • Thermal    │  │ • Vibration  │  │ • Dispatch   │  │ • Curtailment│    │
│  │ • PR Calc    │  │ • Power Curve│  │ • Thermal    │  │ • Markets    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      AI INFERENCE PIPELINE                            │  │
│  │                                                                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │  │
│  │  │  YOLOv12   │  │  RF-DETR   │  │  SAM3 Nano │  │   Qwen2.5-VL   │  │  │
│  │  │            │  │            │  │            │  │                │  │  │
│  │  │ Ultra-Fast │  │ Transformer│  │  Precision │  │ Visual Language│  │  │
│  │  │ Detection  │  │ Segmentation│ │   Masks    │  │   Analysis     │  │  │
│  │  │   ~2ms     │  │   ~15ms    │  │   ~8ms     │  │    ~50ms       │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Forecasting │  │  Portfolio   │  │   Carbon     │  │  Financial   │    │
│  │    Engine    │  │  Optimizer   │  │   Tracker    │  │   Analyzer   │    │
│  │              │  │              │  │              │  │              │    │
│  │ • TFT/Prophet│  │ • Dispatch   │  │ • CO2 Track  │  │ • ROI/NPV    │    │
│  │ • Weather    │  │ • Risk Mgmt  │  │ • ESG Report │  │ • LCOE       │    │
│  │ • Ensemble   │  │ • Investment │  │ • RECs       │  │ • Revenue    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    PREDICTIVE MAINTENANCE ENGINE                      │  │
│  │   • ML-based failure prediction  • Cost-benefit optimization          │  │
│  │   • Work order management        • Spare parts optimization          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                            REST API (FastAPI)                                │
│                    /api/portfolio  /api/forecast  /api/analytics             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## AI Models

| Model | Purpose | Performance |
|-------|---------|-------------|
| **YOLOv12-L** | Defect detection (solar/wind) | ~2ms/frame |
| **RF-DETR** | Precision segmentation | ~15ms/frame |
| **SAM3 Nano** | Point-prompt masking | ~8ms/frame |
| **Qwen2.5-VL-3B-AWQ** | Visual language analysis | ~50ms/frame |
| **Temporal Fusion Transformer** | Energy forecasting | 48h horizon |
| **Prophet + Ensemble** | Price/load forecasting | Multi-model |

## Installation

```bash
# Clone repository
git clone https://github.com/your-org/paces.git
cd paces

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Paces
pip install -e .

# Download AI models
./scripts/download_models.sh
```

## Quick Start

### Start the API Server

```bash
# Start with default configuration
python -m paces.main api --port 8080

# Or with custom config
python -m paces.main --config configs/paces.yaml api
```

### Python SDK Usage

```python
import asyncio
from paces import PacesEngine
from paces.core.types import SolarFarm, WindFarm, Portfolio

async def main():
    # Initialize engine
    engine = PacesEngine()
    await engine.initialize()

    # Generate forecasts
    solar_forecast = await engine.forecast_solar_production("solar_farm_1", hours=48)
    print(f"Expected solar: {solar_forecast.total_energy_kwh:.0f} kWh")

    wind_forecast = await engine.forecast_wind_production("wind_farm_1", hours=48)
    print(f"Expected wind: {wind_forecast.total_energy_kwh:.0f} kWh")

    # Get carbon metrics
    carbon = await engine.get_carbon_metrics(period="monthly")
    print(f"CO2 avoided: {carbon.co2_avoided_tonnes:.1f} tonnes")

    # Predictive maintenance
    failures = await engine.predict_failures("turbine_1", horizon_days=30)
    for f in failures:
        print(f"Predicted: {f.failure_type} ({f.probability:.0%} probability)")

    await engine.shutdown()

asyncio.run(main())
```

## API Endpoints

### Portfolio
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portfolio` | GET | Get portfolio summary |
| `/api/portfolio/assets` | GET | List all assets |

### Forecasting
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/forecast/solar` | POST | Solar production forecast |
| `/api/forecast/wind` | POST | Wind production forecast |
| `/api/forecast/weather` | GET | Weather forecast |

### Battery
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/battery/{id}/status` | GET | Battery status |
| `/api/battery/{id}/optimize` | POST | Optimize dispatch |

### Analytics
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/carbon/metrics` | GET | Carbon metrics |
| `/api/financial/metrics` | GET | Financial metrics |
| `/api/financial/roi/{id}` | GET | ROI analysis |
| `/api/maintenance/{id}/predictions` | GET | Failure predictions |

## Project Structure

```
paces/
├── paces/                    # Paces renewable energy platform
│   ├── core/                # Core infrastructure
│   │   ├── types.py        # Data models
│   │   ├── config.py       # Configuration
│   │   └── engine.py       # Main orchestration
│   ├── solar/               # Solar analytics
│   ├── wind/                # Wind analytics
│   ├── battery/             # Battery management
│   ├── forecasting/         # Energy forecasting
│   ├── grid/                # Grid integration
│   ├── portfolio/           # Portfolio optimization
│   ├── carbon/              # Carbon tracking
│   ├── maintenance/         # Predictive maintenance
│   ├── financial/           # Financial analytics
│   ├── api/                 # REST API
│   └── main.py              # CLI entry point
├── bahb/                     # BAHB drone inspection (integrated)
├── configs/                  # Configuration files
└── requirements.txt          # Dependencies
```

---

# BAHB - Autonomous Drone Inspection System

Integrated drone inspection platform for renewable energy assets.

## Hardware Platform

| Component | Model | Purpose |
|-----------|-------|---------|
| **Compute** | DJI Manifold 3 | Edge AI inference (NVIDIA Orin NX) |
| **Aircraft** | DJI Matrice 400 | Industrial inspection drone |
| **Camera** | DJI H30T | Thermal + Wide + Zoom + Laser RF |

## Inspection Capabilities

### Solar Farm Inspection
- **Panel Defects**: Cell cracks, hotspots, snail trails, delamination
- **Thermal Imaging**: Temperature mapping, hotspot detection
- **Soiling Analysis**: Dust, bird droppings, shading detection
- **Performance Impact**: Power loss estimation

### Wind Turbine Inspection
- **Blade Defects**: Cracks, erosion, lightning damage
- **Component Analysis**: Nacelle, hub, tower inspection
- **Thermal Anomalies**: Gearbox, generator overheating

### Substation & Grid Inspection
- **Transformers**: Oil leaks, thermal anomalies, corona discharge
- **Insulators**: Cracks, contamination, flashover damage
- **Conductors**: Sagging, corrosion, hot joints

## Performance Targets (Manifold 3)

| Model | Resolution | Inference Time | FPS |
|-------|------------|----------------|-----|
| YOLOv12-L | 1280x720 | ~2ms | 500 |
| RF-DETR | 640x640 | ~15ms | 66 |
| SAM3 Nano | 1024x1024 | ~8ms | 125 |
| Qwen2.5-VL-3B | 448x448 | ~50ms | 20 |

## Usage

```bash
# Start inspection system
python -m bahb.main --config configs/production.yaml

# Solar farm inspection
python -m bahb.main --profile solar --site "Solar Farm Alpha"

# Wind turbine inspection
python -m bahb.main --profile wind --site "Wind Farm Beta"
```

## License

Proprietary - All Rights Reserved

## Support

For support and inquiries, contact your system administrator.
