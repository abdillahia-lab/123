# TerraJinki v2.0 - Technical Architecture Document

## Executive Summary

TerraJinki is an AI-powered renewable energy site intelligence platform designed to exponentially surpass PACES capabilities. This document outlines the comprehensive technical architecture for building a production-ready MVP that leverages AI agents, SOTA models, and automated workflows to provide superior renewable energy assessment and financing analysis.

---

## 1. Competitive Analysis: PACES vs TerraJinki

### PACES Core Features (Baseline to Surpass)
| Feature | PACES Capability | TerraJinki Enhancement |
|---------|------------------|------------------------|
| Site Selection | Data-driven parcel discovery | AI-powered multi-factor scoring with real-time optimization |
| Permitting | Permitting Predictor (risk assessment) | Autonomous permitting agent with jurisdiction-specific workflows |
| Grid Analysis | Grid constraint identification | Live grid capacity heatmaps with interconnection queue analysis |
| Environmental | Environmental risk evaluation | Multi-layer environmental screening with mitigation recommendations |
| Pipeline Management | Project tracking | AI orchestrated pipeline with automated stage progression |
| Timeline | 3x faster than traditional | Target: 10x faster with full automation |

### TerraJinki Differentiators
1. **AI Agent Swarm Architecture** - Autonomous agents for each analysis domain
2. **Real-time Data Integration** - Live data from NREL, EIA, utility APIs
3. **Predictive Analytics** - ML models for energy production, ROI, and risk
4. **Automated Financing** - One-click financing proposal generation
5. **Full US Coverage** - All 50 states with complete parcel data structure

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TERRAJINKI PLATFORM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        FRONTEND (Next.js 14)                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │   │
│  │  │Interactive│  │ Analysis │  │Financing │  │  AI Copilot Chat    │ │   │
│  │  │   Map    │  │Dashboard │  │ Console  │  │  (Claude Powered)   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                      API GATEWAY (Next.js Routes)                    │   │
│  │  /api/parcels  /api/analysis  /api/financing  /api/agents  /api/map │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                    AI AGENT ORCHESTRATOR                             │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │ Permitting │ │   Grid     │ │Environment │ │   Land     │       │   │
│  │  │   Agent    │ │   Agent    │ │   Agent    │ │   Agent    │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │ Financial  │ │  Solar     │ │   Wind     │ │  Planning  │       │   │
│  │  │   Agent    │ │   Agent    │ │   Agent    │ │   Agent    │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                      DATA INTEGRATION LAYER                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │  NREL    │ │   EIA    │ │  HIFLD   │ │  Census  │ │ Utility  │  │   │
│  │  │ NSRDB/WTK│ │Power Data│ │Grid Data │ │  Data    │ │   APIs   │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Sources & Integration

### 3.1 Parcel Data
- **Source**: Regrid/ATTOM structure (demo mode with representative data)
- **Coverage**: All 50 US states
- **Attributes**: APN, boundaries, acreage, zoning, owner, land use
- **Update Frequency**: Monthly (production) / Static (demo)

### 3.2 Solar Resource Data
- **Source**: NREL NSRDB API
- **Metrics**: GHI, DNI, DHI (kWh/m²/day)
- **Resolution**: 4km, 30-minute intervals
- **Coverage**: Continental US, 1998-2023

### 3.3 Wind Resource Data
- **Source**: NREL WIND Toolkit
- **Metrics**: Wind speed at multiple hub heights (10m-200m)
- **Resolution**: 2km
- **Coverage**: Continental US, 2007-2022

### 3.4 Grid Infrastructure
- **Source**: HIFLD, EIA Form 860
- **Data**: Transmission lines, substations, generation facilities
- **Attributes**: Voltage, capacity, owner, status

### 3.5 Financial Data
- **ITC**: 30% (through 2032), 26% (2033), 22% (2034)
- **PTC**: $0.0275/kWh for 10 years
- **Energy Community Bonus**: +10%
- **MACRS**: 5-year accelerated depreciation

---

## 4. AI Agent Architecture

### 4.1 Agent Types

#### Permitting Agent
```typescript
interface PermittingAgent {
  analyzeZoning(parcel: Parcel): ZoningAnalysis;
  predictApprovalTimeline(jurisdiction: string): Timeline;
  identifyRequiredPermits(projectType: string): Permit[];
  assessPermittingRisk(): RiskScore;
}
```

#### Grid Agent
```typescript
interface GridAgent {
  findNearestSubstation(location: Coordinates): Substation;
  estimateInterconnectionCost(capacity: number): Cost;
  checkGridCapacity(region: string): CapacityAnalysis;
  predictQueuePosition(): QueueEstimate;
}
```

#### Environmental Agent
```typescript
interface EnvironmentalAgent {
  screenWetlands(parcel: Parcel): WetlandAnalysis;
  checkEndangeredSpecies(location: Coordinates): SpeciesReport;
  assessFloodRisk(parcel: Parcel): FloodAnalysis;
  identifyMitigations(): Mitigation[];
}
```

#### Financial Agent
```typescript
interface FinancialAgent {
  calculateLCOE(project: Project): number;
  estimateROI(project: Project, years: number): ROIProjection;
  generateFinancingProposal(project: Project): FinancingProposal;
  optimizeTaxStrategy(project: Project): TaxStrategy;
}
```

### 4.2 Orchestration Flow
```
User Request → Planning Agent → Parallel Agent Execution → Synthesis Agent → Response
                    │
                    ├── Permitting Agent ──┐
                    ├── Grid Agent ────────┼── Results Aggregation
                    ├── Environmental Agent┤
                    ├── Land Agent ────────┤
                    └── Financial Agent ───┘
```

---

## 5. Scoring System

### 5.1 Overall Site Score (0-100)
```
Overall Score = (
  Permitting Score × 0.25 +
  Grid Score × 0.30 +
  Environmental Score × 0.20 +
  Land Score × 0.15 +
  Financial Score × 0.10
)
```

### 5.2 Component Scores

#### Permitting Score (0-100)
| Factor | Weight | Scoring Criteria |
|--------|--------|------------------|
| Zoning Compatibility | 30% | By-right=100, CUP=70, Variance=40, Prohibited=0 |
| Approval Timeline | 25% | <6mo=100, 6-12mo=75, 12-24mo=50, >24mo=25 |
| Local Precedent | 20% | Many approved=100, Some=70, None=40, Denied=0 |
| Setback Compliance | 15% | Meets all=100, Minor variance=70, Major=30 |
| Community Sentiment | 10% | Supportive=100, Neutral=70, Opposition=30 |

#### Grid Score (0-100)
| Factor | Weight | Scoring Criteria |
|--------|--------|------------------|
| Substation Distance | 35% | <1mi=100, 1-3mi=80, 3-5mi=60, 5-10mi=40, >10mi=20 |
| Available Capacity | 30% | >Project MW=100, 50-100%=70, <50%=40, None=0 |
| Voltage Level | 20% | 345kV+=100, 230kV=85, 138kV=70, 69kV=50 |
| Queue Position | 15% | <50=100, 50-200=70, 200-500=40, >500=20 |

#### Environmental Score (0-100)
| Factor | Weight | Scoring Criteria |
|--------|--------|------------------|
| Wetlands | 25% | None=100, <5%=70, 5-20%=40, >20%=10 |
| Endangered Species | 25% | None=100, Low impact=70, Moderate=40, Critical=0 |
| Flood Zone | 20% | Zone X=100, Zone B=70, Zone A=30, Floodway=0 |
| Cultural Resources | 15% | None=100, Low=80, Moderate=50, High=20 |
| Slope/Terrain | 15% | <5%=100, 5-10%=80, 10-15%=50, >15%=20 |

#### Land Score (0-100)
| Factor | Weight | Scoring Criteria |
|--------|--------|------------------|
| Acreage Suitability | 30% | Optimal=100, Adequate=75, Marginal=50, Insufficient=0 |
| Land Use | 25% | Agricultural=100, Vacant=90, Industrial=70, Other=40 |
| Ownership | 20% | Single=100, Few=80, Multiple=50, Complex=20 |
| Access | 15% | Paved road=100, Gravel=75, Dirt=50, None=20 |
| Topography | 10% | Flat=100, Rolling=80, Hilly=50, Mountainous=20 |

#### Financial Score (0-100)
| Factor | Weight | Scoring Criteria |
|--------|--------|------------------|
| Estimated LCOE | 35% | <$30/MWh=100, $30-40=80, $40-50=60, >$50=40 |
| Land Cost | 25% | <$5k/acre=100, $5-10k=75, $10-20k=50, >$20k=25 |
| Incentive Eligibility | 25% | Full ITC+bonus=100, Full ITC=80, Partial=50 |
| PPA Market | 15% | Strong demand=100, Moderate=70, Weak=40 |

---

## 6. Frontend Components

### 6.1 Interactive Map
- **Base Layer**: MapLibre GL JS with CartoDB tiles
- **Parcel Layer**: GeoJSON polygons with color-coded scores
- **Solar Layer**: Heat map overlay (GHI values)
- **Wind Layer**: Animated wind patterns
- **Grid Layer**: Transmission lines and substations
- **Environmental Layer**: Wetlands, flood zones, protected areas

### 6.2 Dashboard Views
1. **Portfolio Overview** - All parcels, projects, pipeline status
2. **Site Analysis** - Detailed parcel assessment with AI insights
3. **Financing Console** - ROI calculator, proposal generator
4. **Comparison Tool** - Side-by-side parcel evaluation
5. **Reports** - Exportable PDF/Excel reports

### 6.3 AI Copilot
- Natural language queries about parcels and projects
- Automated report generation
- Recommendation engine
- Market intelligence

---

## 7. API Endpoints

### Parcels API
```
GET    /api/parcels              - List all parcels (paginated)
GET    /api/parcels/:id          - Get parcel details
POST   /api/parcels/search       - Search parcels with filters
GET    /api/parcels/:id/analysis - Get AI analysis for parcel
POST   /api/parcels/bulk-analyze - Analyze multiple parcels
```

### Analysis API
```
POST   /api/analysis/quick       - Quick score (5 seconds)
POST   /api/analysis/full        - Full analysis (30 seconds)
GET    /api/analysis/:id         - Get analysis results
POST   /api/analysis/compare     - Compare multiple sites
```

### Financing API
```
POST   /api/financing/calculate  - Calculate project financials
POST   /api/financing/proposal   - Generate financing proposal
GET    /api/financing/incentives - Get applicable incentives
POST   /api/financing/optimize   - Optimize tax strategy
```

### Map API
```
GET    /api/map/parcels          - Get parcel geometries
GET    /api/map/solar/:bounds    - Get solar irradiance data
GET    /api/map/wind/:bounds     - Get wind resource data
GET    /api/map/grid/:bounds     - Get grid infrastructure
GET    /api/map/environmental    - Get environmental layers
```

---

## 8. Demo Data Strategy

For the demo, we'll use realistic representative data:

### State Coverage
All 50 states with varying parcel counts based on renewable energy potential:
- **High Potential**: TX, CA, AZ, NM, NV, CO, FL, NC, VA (100+ parcels each)
- **Medium Potential**: All other contiguous states (50+ parcels each)
- **Lower Potential**: AK, HI (25+ parcels each)

### Data Realism
- Coordinates within actual state boundaries
- Realistic acreage ranges (50-1000 acres)
- Accurate zoning types per jurisdiction
- Representative solar/wind values from NREL averages
- Actual substation locations from HIFLD

---

## 9. Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI**: Tailwind CSS, Framer Motion
- **Maps**: MapLibre GL JS, Deck.gl
- **State**: React Query, Zustand
- **Charts**: Recharts, D3.js

### Backend
- **Runtime**: Node.js (Next.js API Routes)
- **AI**: Claude API (Anthropic)
- **Database**: PostgreSQL with PostGIS (production)
- **Cache**: Redis (production)

### External APIs
- NREL NSRDB/WIND Toolkit
- EIA Open Data
- Census Geocoder
- OpenStreetMap Nominatim

---

## 10. Implementation Phases

### Phase 1: Core Platform (Current Sprint)
- [x] Basic parcel display
- [x] Simple analysis
- [ ] Complete US parcel data structure
- [ ] Fixed scoring calculations
- [ ] Interactive map layers

### Phase 2: AI Integration
- [ ] Agent architecture
- [ ] Claude-powered analysis
- [ ] Natural language queries
- [ ] Automated recommendations

### Phase 3: Financial Tools
- [ ] ROI calculator
- [ ] Financing proposal generator
- [ ] Incentive optimizer
- [ ] Export functionality

### Phase 4: Production Ready
- [ ] Real data integration
- [ ] User authentication
- [ ] API rate limiting
- [ ] Monitoring & analytics

---

## 11. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Analysis Speed | <5s quick, <30s full | API response time |
| Accuracy | >90% vs manual analysis | Validation study |
| Coverage | 100% US states | State count |
| Uptime | 99.9% | Monitoring |
| User Satisfaction | >4.5/5 | Survey |

---

## 12. Deployment

### Vercel Configuration
```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "regions": ["iad1"]
}
```

### Environment Variables
```
ANTHROPIC_API_KEY=     # Claude API
NREL_API_KEY=          # NREL data access
MAPBOX_TOKEN=          # Map tiles (optional)
DATABASE_URL=          # PostgreSQL (production)
```

---

*Document Version: 2.0*
*Last Updated: January 2026*
*Author: TerraJinki Engineering*
