# Paces - AI-Powered Renewable Energy Site Development Platform

A superior site prospecting, permitting analysis, and project development platform for solar, wind, and energy storage projects. Powered by agentic AI for automated due diligence.

## Overview

Paces helps renewable energy developers find viable sites, de-risk development, and get to power faster:

- **Parcel Search & Discovery** - Search millions of parcels with custom filters
- **LLM-Powered Permitting Analysis** - Parse zoning ordinances to predict permitting risk
- **Grid Interconnection Analysis** - Analyze queue, capacity, and estimate costs
- **Environmental Screening** - Screen for wetlands, flood zones, endangered species
- **AI Site Scoring** - Comprehensive scoring across all development factors
- **Financial Modeling** - LCOE, NPV, IRR, and PPA analysis
- **Automated Reports** - Generate detailed feasibility reports

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PACES PLATFORM                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        AI AGENT PIPELINE                                │ │
│  │                                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │  Permitting  │  │    Grid      │  │Environmental │                  │ │
│  │  │    Agent     │  │   Agent      │  │    Agent     │                  │ │
│  │  │              │  │              │  │              │                  │ │
│  │  │ • LLM Parse  │  │ • Substation │  │ • Wetlands   │                  │ │
│  │  │ • Zoning Map │  │ • Queue      │  │ • Flood Zone │                  │ │
│  │  │ • Risk Score │  │ • Cost Est   │  │ • Species    │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  │                            ▼                                            │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    SITE ANALYSIS AGENT                            │  │ │
│  │  │     Orchestrates all agents • Calculates site scores             │  │ │
│  │  │     Generates recommendations • Identifies fatal flaws           │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Parcel     │  │   Solar      │  │  Financial   │  │   Report     │    │
│  │   Search     │  │   Resource   │  │   Analyzer   │  │   Generator  │    │
│  │              │  │              │  │              │  │              │    │
│  │ • GIS Query  │  │ • Irradiance │  │ • LCOE       │  │ • Markdown   │    │
│  │ • Filters    │  │ • Capacity   │  │ • NPV/IRR    │  │ • HTML/PDF   │    │
│  │ • Ranking    │  │ • Weather    │  │ • PPA Price  │  │ • Comparison │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                         REST API (FastAPI)                                   │
│    /parcels  /sites/analyze  /permitting  /grid  /environmental  /financial │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Features

### LLM-Powered Permitting Analysis
Uses Claude/GPT-4 to parse zoning ordinances and extract:
- Solar permission status (by-right, conditional use, prohibited)
- Permitted and prohibited zones
- Setback and height requirements
- Screening and decommissioning requirements
- Permitting risk scores

### Grid Interconnection Analysis
- Find nearest substations and transmission lines
- Analyze interconnection queue position
- Estimate interconnection and upgrade costs
- Predict study and construction timelines
- Assess congestion risk

### Environmental Screening
- Wetlands (NWI data)
- FEMA flood zones
- Endangered species habitat (USFWS IPaC)
- Cultural/historic resources
- Prime farmland
- Environmental risk scoring

### Financial Modeling
- CAPEX estimation ($0.65/W default)
- OPEX projection
- NPV and IRR calculation
- LCOE computation
- Minimum PPA price for target IRR
- Sensitivity analysis

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

# Start API server
python -m paces.main api --port 8000
```

## Quick Start

### Start the API Server

```bash
python -m paces.main api --port 8000
```

### Python SDK Usage

```python
import asyncio
from paces import PacesEngine
from paces.core.types import Parcel, GeoPoint, ZoningType

async def main():
    # Initialize engine
    engine = PacesEngine()
    await engine.initialize()

    # Create a parcel
    parcel = Parcel(
        apn="1234-56-7890",
        state="NC",
        county="Wake",
        municipality="Raleigh",
        acreage=50.0,
        zoning_type=ZoningType.AGRICULTURAL,
        centroid=GeoPoint(35.7796, -78.6382),
    )
    engine.add_parcel(parcel)

    # Analyze the site
    report = await engine.analyze_site(
        parcel=parcel,
        target_capacity_mw=5.0,
    )

    print(f"Overall Score: {report.site_score.overall_score:.0f}/100")
    print(f"Recommendation: {report.proceed_recommendation}")
    print(f"Viability: {report.overall_viability}")

    # Analyze financials
    financials = engine.analyze_financials(parcel)
    print(f"LCOE: ${financials['lcoe']:.3f}/kWh")
    print(f"NPV: ${financials['npv']:,.0f}")
    print(f"IRR: {financials['irr']:.1%}")

    await engine.shutdown()

asyncio.run(main())
```

## API Endpoints

### Parcels
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/parcels` | POST | Create a parcel |
| `/parcels` | GET | Search parcels |
| `/parcels/{id}` | GET | Get parcel by ID |

### Site Analysis
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sites/analyze` | POST | Comprehensive site analysis |
| `/sites/analyze-batch` | POST | Analyze multiple sites |

### Permitting
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/permitting/analyze` | POST | Analyze permitting requirements |

### Grid
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/grid/analyze` | POST | Grid interconnection analysis |

### Environmental
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/environmental/screen` | POST | Environmental screening |

### Financial
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/financial/analyze` | POST | Financial analysis |
| `/financial/min-ppa` | POST | Calculate minimum PPA price |

### Projects
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects` | POST | Create project |
| `/projects` | GET | List projects |
| `/projects/{id}` | GET | Get project |

### Reports
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reports/feasibility` | POST | Generate feasibility report |

## Project Structure

```
paces/
├── paces/
│   ├── agents/              # AI Agents
│   │   ├── base.py         # Base agent class
│   │   ├── permitting.py   # LLM permitting analysis
│   │   ├── grid.py         # Grid interconnection
│   │   ├── environmental.py # Environmental screening
│   │   ├── site.py         # Site analysis orchestrator
│   │   └── report.py       # Report generation
│   ├── core/
│   │   ├── types.py        # Data models (1000+ lines)
│   │   ├── config.py       # Configuration
│   │   └── engine.py       # Main orchestration
│   ├── financial/
│   │   └── analyzer.py     # Financial modeling
│   ├── api/
│   │   └── app.py          # FastAPI application
│   └── main.py             # CLI entry point
├── configs/
│   └── paces.yaml          # Configuration
└── requirements.txt
```

## Site Scoring

Sites are scored on a 0-100 scale across four categories:

| Category | Weight | Factors |
|----------|--------|---------|
| **Permitting** | 30% | Permission type, public hearing, moratoriums |
| **Grid** | 30% | Distance, capacity, queue, cost |
| **Environmental** | 20% | Wetlands, flood, species, farmland |
| **Land** | 20% | Acreage, slope, access |

**Recommendations:**
- Score >= 70: **Proceed**
- Score 50-70: **Conditional** (address risks)
- Score < 50: **Avoid**

## Data Sources

- **Parcels**: Regrid, county assessor data
- **Zoning**: Municipal ordinances, LLM parsing
- **Grid**: EIA, utility queue data
- **Environmental**: NWI, FEMA, USFWS IPaC, NRCS
- **Solar Resource**: NSRDB, PVGIS

## License

Proprietary - All Rights Reserved

## Support

For support and inquiries, contact your system administrator.
