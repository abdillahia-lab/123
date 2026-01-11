# TerraJinki - Strategic Plan & Architecture

## The Name: TerraJinki (地霊氣)

**Terra** (Latin: Earth/Land) + **Jinki** (神気: Divine Energy/Spirit)

> "The Spirit of Earth Energy" - AI-powered renewable energy site intelligence that sees what others can't.

---

## Executive Summary

TerraJinki is a next-generation renewable energy site development platform that will leapfrog Paces and all competitors through:

1. **Multi-Agent AI Orchestration** with human-in-the-loop decision gates
2. **Graph Neural Networks** for real-time grid topology analysis (1000-10000x faster)
3. **Satellite Deep Learning** for automated land classification (92%+ accuracy)
4. **LLM-Powered Document Intelligence** with RAG for zoning ordinance parsing
5. **Physics-Guided ML** for solar resource prediction globally
6. **Exceptional UX** with AI copilot and real-time collaboration

---

## Part 1: Competitive Intelligence

### 1.1 Paces (Primary Target)

**Company Profile:**
- Y Combinator S22 | $11M Series A | 40 employees | Brooklyn, NY
- CEO: James McWalter | CTO: Charles Bai (ex-Meta AI)

**Key Features:**
- LLM-powered "text-to-geography mapping" for zoning ordinances
- Pre-vetted database of 100,000 sites
- Accelerated Development Framework (claims 50% faster)
- Grid, environmental, permitting analysis
- Fractional Development Services (FDS)

**2024 Metrics:**
- 7,439 searches conducted
- 40,710 "five-star sites" identified
- Clients: EDF Renewables, AES, Third Pillar Solar

**Weaknesses to Exploit:**
- Limited geographic coverage (Permitting Predictor only in MD, CA, NY)
- No real-time satellite imagery analysis
- Basic grid analysis (no GNN topology awareness)
- No physics-guided solar modeling
- Sequential agent workflows (we'll do parallel)
- No public API or developer ecosystem

### 1.2 PVcase Prospect

**Strengths:**
- Automated constraint analysis on thousands of sites simultaneously
- Full interconnection studies with headroom capacity
- Premium distribution grid data
- 30% reduction in site analysis time
- Seamless transfer to PVcase Ground Mount

**Weaknesses:**
- No LLM document parsing
- Limited AI capabilities
- Enterprise-only pricing
- No human-in-the-loop orchestration

### 1.3 Aurora Solar

**Strengths:**
- 1.6M+ AI runs for residential solar
- LIDAR-based 3D modeling
- 8,760 hourly irradiance simulations
- Strong residential market position

**Weaknesses:**
- Residential/commercial focus (not utility-scale)
- No site prospecting for greenfield development
- No permitting intelligence
- No grid interconnection analysis

### 1.4 Market Opportunity

**Market Size:**
- $2.1T global energy transition investment in 2024 (+11% YoY)
- $12.5B VC funding into clean energy startups (2024)
- 3,940 companies in renewable energy tech globally
- 13 unicorns created

**Pain Point We Solve:**
- 80% of clean energy projects fail due to permitting/interconnection
- $17B in cancelled projects annually
- 4+ years average development timeline
- U.S. needs 2,000 GW new generation by 2035

---

## Part 2: Cutting-Edge Research Integration

### 2.1 Graph Neural Networks for Grid Analysis

**Source:** PowerGNN (arXiv:2503.22721)

**Key Innovation:**
- GraphSAGE convolutions + GRUs for spatio-temporal grid modeling
- Treats buses as nodes, transmission lines as edges
- Achieves RMSE 0.13-0.17 across all variables

**Our Implementation: GridMind GNN**
```
Capabilities:
- Real-time hosting capacity prediction
- Interconnection cost estimation (1000x faster than studies)
- Queue position impact analysis
- Congestion risk forecasting
- Upgrade requirement prediction
```

**Competitive Advantage:** While Paces uses basic distance-to-substation heuristics, we'll model the actual grid topology and predict true connection feasibility.

### 2.2 LLM Document Intelligence with RAG+

**Sources:**
- RAG+ (arXiv:2506.11555) - 3-5% improvement, 13.5% peak
- LexNLP for legal text extraction
- Energy Policy LLM Research (arXiv:2403.12924)

**Key Innovation:**
- Application-aware reasoning for structured document understanding
- Decision tree framework for siting ordinance extraction
- Legal domain NLP with entity recognition

**Our Implementation: OrdinanceAI**
```
Capabilities:
- Automatic zoning ordinance change detection
- Section-by-section parsing with citations
- Variance/appeal probability prediction
- Timeline estimation by jurisdiction
- Automatic notification of regulatory changes
```

**Competitive Advantage:** While Paces parses ordinances, we'll actively monitor for changes and automatically update risk scores.

### 2.3 Satellite Deep Learning for Land Classification

**Sources:**
- Global Renewables Watch (arXiv:2503.14860)
- LinkNet semantic segmentation (92% IoU)
- Land cover change tracking (2016-2024 Sentinel-2)

**Key Innovation:**
- Deep learning segmentation on PlanetScope/Sentinel-2 imagery
- Automatic solar installation detection globally
- Prior land use classification

**Our Implementation: TerraScan Vision**
```
Capabilities:
- Automatic parcel boundary extraction
- Slope/aspect analysis from DEM
- Existing solar/wind installation detection
- Land cover classification (agricultural, forest, wetland, developed)
- Construction activity monitoring
- Seasonal vegetation analysis for shading
```

**Competitive Advantage:** Real-time satellite analysis vs. static data layers. We'll know about land changes within days, not months.

### 2.4 Physics-Guided Solar Resource Modeling

**Sources:**
- Physics-guided ML for solar farms (arXiv:2407.18284)
- SolNet transfer learning (arXiv:2405.14472)
- CNN-LSTM for irradiance forecasting

**Key Innovation:**
- PVZones global climate classification
- Transfer learning for any location worldwide
- Sparse heterogeneous data utilization

**Our Implementation: SolarMind Predictor**
```
Capabilities:
- Global solar resource estimation (any lat/long)
- P50/P90 production confidence intervals
- Degradation modeling with temperature coefficients
- Soiling and snow loss prediction
- Bankability-grade yield reports
```

**Competitive Advantage:** Physics-based accuracy that financiers trust, not just NSRDB lookups.

### 2.5 Multi-Agent Reinforcement Learning

**Sources:**
- MARFT: Multi-Agent Reinforcement Fine-Tuning (arXiv:2504.16129)
- Comprehensive Survey on Multi-Agent Cooperative Decision-Making (arXiv:2503.13415)

**Key Innovation:**
- Hierarchical organization with asynchronous execution
- LLM-based agents with dynamic task decomposition
- Goal-aligned decentralized coordination

**Our Implementation: See Part 3 (Agent Architecture)**

---

## Part 3: AI Agent Architecture (Human-in-the-Loop)

### 3.1 Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                           │
│              (Claude Opus / GPT-4o - Strategic)                 │
│    Plans, delegates, synthesizes, requests human approval       │
└───────────────────────┬─────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬───────────────┐
        │               │               │               │
        ▼               ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ PERMITTING    │ │ GRID          │ │ ENVIRONMENTAL │ │ LAND          │
│ SWARM         │ │ SWARM         │ │ SWARM         │ │ SWARM         │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │                 │
   ┌────┴────┐       ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
   │         │       │         │       │         │       │         │
   ▼         ▼       ▼         ▼       ▼         ▼       ▼         ▼
┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐
│Zone │  │Var- │  │Sub- │  │Queue│  │Wet- │  │FEMA │  │Owner│  │Topo-│
│Parse│  │iance│  │statn│  │Anal │  │land │  │Flood│  │ship │  │graphy│
└─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘
   ▲         ▲       ▲         ▲       ▲         ▲       ▲         ▲
   │         │       │         │       │         │       │         │
   └────┬────┘       └────┬────┘       └────┬────┘       └────┬────┘
        │                 │                 │                 │
   ┌────┴────┐       ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
   │ LLM     │       │ GNN     │       │ Imagery │       │ GIS     │
   │ Claude  │       │ PowerGNN│       │ TerraScan│      │ PostGIS │
   └─────────┘       └─────────┘       └─────────┘       └─────────┘
```

### 3.2 Agent Definitions

#### Orchestrator Agent (Strategic Layer)
```python
class OrchestratorAgent:
    """
    Master coordinator with human approval gates.
    Model: Claude Opus 4.5 / GPT-4o (configurable)
    """

    responsibilities = [
        "Receives user site analysis requests",
        "Decomposes into parallel sub-tasks",
        "Routes to specialized swarms",
        "Aggregates and synthesizes results",
        "Identifies conflicts requiring human review",
        "Generates executive recommendations",
        "Requests human approval for critical decisions"
    ]

    human_approval_gates = [
        "Fatal flaw identified (score < 30)",
        "Cost estimate > $5M",
        "Regulatory ambiguity detected",
        "Conflicting data sources",
        "Novel jurisdiction (no training data)",
        "High-value opportunity (score > 90)"
    ]
```

#### Permitting Swarm
```python
class PermittingSwarm:
    """
    Multi-agent swarm for zoning and permitting analysis.
    Uses RAG+ for document intelligence.
    """

    agents = {
        "ZoningParserAgent": "Extracts solar permissions from ordinance text",
        "SetbackAnalyzerAgent": "Calculates buildable area after setbacks",
        "VariancePredictor": "Predicts variance approval probability",
        "TimelineEstimator": "Estimates permit approval timeline",
        "MoratoriummMonitor": "Tracks moratorium status and expiration",
        "AppealRiskAgent": "Assesses community opposition risk"
    }

    data_sources = [
        "County zoning ordinances (scraped + RAG indexed)",
        "Historical permit decisions",
        "Municipal meeting minutes",
        "Community solar policies",
        "State-level siting preemption laws"
    ]
```

#### Grid Swarm (GNN-Powered)
```python
class GridSwarm:
    """
    Multi-agent swarm for grid interconnection analysis.
    Powered by PowerGNN for topology-aware predictions.
    """

    agents = {
        "SubstationFinderAgent": "Identifies nearest viable POIs",
        "HostingCapacityAgent": "GNN-predicted hosting capacity",
        "QueueAnalyzerAgent": "Analyzes interconnection queue dynamics",
        "CostEstimatorAgent": "Predicts interconnection costs",
        "CongestionRiskAgent": "Assesses curtailment probability",
        "UpgradePredictor": "Identifies likely upgrade requirements"
    }

    models = {
        "PowerGNN": "Topology-aware grid state prediction",
        "QueueLSTM": "Queue withdrawal probability model",
        "CostXGBoost": "Historical cost regression model"
    }
```

#### Environmental Swarm
```python
class EnvironmentalSwarm:
    """
    Multi-agent swarm for environmental constraint analysis.
    Uses satellite imagery + authoritative data sources.
    """

    agents = {
        "WetlandDelineator": "NWI + satellite-based wetland detection",
        "FloodZoneAnalyzer": "FEMA FIRM + climate projections",
        "SpeciesScreener": "USFWS IPaC + state databases",
        "CulturalResourceAgent": "SHPO + tribal consultation tracker",
        "FarmlandAnalyzer": "NRCS prime farmland + soil data",
        "TerraScanAgent": "Satellite imagery land cover analysis"
    }
```

#### Land Intelligence Swarm
```python
class LandSwarm:
    """
    Multi-agent swarm for land and ownership analysis.
    """

    agents = {
        "OwnershipAgent": "Identifies current owners + contact info",
        "ValueEstimator": "Estimates land value and lease rates",
        "TopographyAgent": "Slope, aspect, elevation analysis",
        "AccessAnalyzer": "Road access and easement analysis",
        "NeighborAgent": "Identifies adjacent parcels for expansion",
        "HistoryAgent": "Tracks ownership changes and sales"
    }
```

### 3.3 Human-in-the-Loop Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPROVAL WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘

Level 1: AUTONOMOUS (No human needed)
├── Standard site scoring (score 40-80)
├── Data collection and aggregation
├── Report generation
└── Low-stakes notifications

Level 2: NOTIFY (Human notified, can override)
├── High-potential sites discovered (score > 85)
├── Cost estimates > $1M
├── New data source discrepancies
└── Automated outreach to landowners

Level 3: APPROVE (Human must approve)
├── Fatal flaws requiring confirmation
├── Regulatory ambiguity requiring interpretation
├── Cost estimates > $5M
├── Legal document submissions
└── Financial model assumptions

Level 4: COLLABORATE (Human works with AI)
├── Novel jurisdiction analysis
├── Complex variance applications
├── Multi-parcel assembly strategy
└── Utility negotiation preparation
```

---

## Part 4: System Architecture

### 4.1 Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND                                   │
├─────────────────────────────────────────────────────────────────┤
│  React 19 + TypeScript + Tailwind CSS + Shadcn/UI               │
│  MapLibre GL JS (WebGL maps) + Deck.gl (data visualization)     │
│  TanStack Query (data fetching) + Zustand (state)               │
│  Vercel (hosting) + Edge Functions                              │
└───────────────────────┬─────────────────────────────────────────┘
                        │ REST/GraphQL/WebSocket
┌───────────────────────┴─────────────────────────────────────────┐
│                       API GATEWAY                                │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI + Strawberry GraphQL                                   │
│  JWT Authentication + RBAC                                      │
│  Rate Limiting + Request Validation                             │
│  OpenAPI + AsyncAPI Documentation                               │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────────┐
│                    AGENT ORCHESTRATION                           │
├─────────────────────────────────────────────────────────────────┤
│  LangGraph (agent workflows) + LangChain (LLM integration)      │
│  Temporal (durable execution) + Celery (background tasks)       │
│  Redis (pub/sub + caching) + RabbitMQ (message queue)           │
│  Prometheus + Grafana (observability)                           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────────┐
│                    AI/ML LAYER                                   │
├─────────────────────────────────────────────────────────────────┤
│  Claude API (Opus 4.5, Sonnet 4) - Document intelligence        │
│  OpenAI API (GPT-4o, GPT-4o-mini) - Fallback + specialized      │
│  PyTorch + PyG (Graph Neural Networks)                          │
│  Transformers (Hugging Face) + sentence-transformers            │
│  ONNX Runtime (model inference optimization)                    │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────────┐
│                    DATA LAYER                                    │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL + PostGIS (spatial data)                            │
│  Qdrant (vector embeddings) + pgvector (backup)                 │
│  TimescaleDB (time-series grid data)                            │
│  Redis (caching) + S3 (documents + imagery)                     │
│  Elasticsearch (full-text search on ordinances)                 │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────────┐
│                 EXTERNAL DATA SOURCES                            │
├─────────────────────────────────────────────────────────────────┤
│  Regrid API (parcel data)                                       │
│  EIA + FERC (grid data)                                         │
│  Planet Labs + Sentinel Hub (satellite imagery)                 │
│  NSRDB + PVGIS (solar resource)                                 │
│  NWI + FEMA + USFWS (environmental)                             │
│  Municode + American Legal (ordinances)                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA FLOW                                     │
└─────────────────────────────────────────────────────────────────┘

1. INGESTION LAYER
   ├── Scrapers: Zoning ordinances, grid queues, permits
   ├── APIs: Parcel data, environmental, solar resource
   ├── Satellite: Daily Planet Labs, weekly Sentinel-2
   └── User: Uploaded documents, custom data layers

2. PROCESSING LAYER
   ├── ETL: Apache Airflow DAGs
   ├── Geocoding: PostGIS spatial processing
   ├── ML: Batch inference (imagery, GNN)
   └── Embedding: RAG document chunking + vectorization

3. STORAGE LAYER
   ├── Operational: PostgreSQL (projects, users, analyses)
   ├── Spatial: PostGIS (parcels, boundaries, infrastructure)
   ├── Vectors: Qdrant (ordinance embeddings)
   ├── Time-series: TimescaleDB (grid metrics)
   └── Blob: S3 (imagery, documents, reports)

4. SERVING LAYER
   ├── Real-time: Redis cache + CDN
   ├── API: FastAPI with async queries
   ├── Analytics: ClickHouse for aggregations
   └── Export: PDF, GeoJSON, Shapefile, Excel
```

---

## Part 5: Feature Specification

### 5.1 Core Features (MVP)

#### F1: Intelligent Site Search
```
User Story: As a solar developer, I want to search millions of parcels
with natural language queries like "50+ acre sites in Texas with
existing ag zoning and substations within 5 miles"

Implementation:
- Natural language query parsing (Claude)
- PostGIS spatial queries
- Multi-criteria filtering
- Real-time map visualization
- Saved searches with alerts

Differentiation from Paces:
- Natural language queries (not just filters)
- AI-suggested similar sites
- Predictive scoring before full analysis
```

#### F2: AI Site Analysis (One-Click)
```
User Story: As a developer, I want comprehensive site analysis
in under 60 seconds, not days.

Implementation:
- Orchestrator dispatches to all swarms in parallel
- Real-time progress visualization
- Streaming results as each agent completes
- Confidence scores for each dimension
- Automatic fatal flaw detection

Output:
- Overall score (0-100)
- Permitting risk assessment + timeline
- Grid connection feasibility + cost estimate
- Environmental constraints + mitigation costs
- Financial pro forma with sensitivity analysis
- Recommended next steps

Differentiation:
- 60 seconds vs. Paces' "5-10 days" for reports
- Parallel agent execution (not sequential)
- Real-time streaming results
```

#### F3: Zoning Ordinance Intelligence
```
User Story: As a developer, I want to instantly understand if
a jurisdiction allows utility-scale solar and what the requirements are.

Implementation:
- RAG+ over indexed ordinance corpus
- Section-level citations in results
- Automatic ordinance change monitoring
- Historical ordinance version comparison
- Variance success rate by jurisdiction

Differentiation:
- Automatic change detection + alerts
- Historical trend analysis
- Variance probability modeling
```

#### F4: Grid Connection Analyzer (GNN-Powered)
```
User Story: As a developer, I want accurate interconnection
cost and timeline estimates before spending on studies.

Implementation:
- PowerGNN topology-aware predictions
- Real interconnection queue data (EIA/FERC)
- Historical cost benchmarking
- Upgrade requirement prediction
- Curtailment risk modeling

Differentiation:
- GNN predicts true grid constraints (not distance heuristics)
- 1000x faster than traditional studies
- Historical benchmark database
```

#### F5: Environmental Screening (Satellite-Enhanced)
```
User Story: As a developer, I want to identify all environmental
constraints before site visits.

Implementation:
- NWI + satellite wetland detection
- FEMA + climate-projected flood analysis
- USFWS IPaC species screening
- Satellite land cover classification
- Prime farmland analysis

Differentiation:
- Satellite imagery validation (not just database lookups)
- Climate change projections for flood risk
- Automatic imagery updates
```

#### F6: Financial Modeling Engine
```
User Story: As a developer, I want bankability-grade financial
projections with sensitivity analysis.

Implementation:
- LCOE, NPV, IRR, payback calculations
- Tax equity and ITC/PTC modeling
- PPA pricing optimization
- Debt sizing and DSCR analysis
- Monte Carlo sensitivity analysis
- Scenario comparison

Differentiation:
- Physics-based production modeling (not rules of thumb)
- Tax equity waterfall visualization
- Export to Excel for banker review
```

### 5.2 Differentiated Features (Competitive Moat)

#### F7: TerraScan Vision (Satellite Intelligence)
```
Capability: Real-time satellite imagery analysis for any parcel

Features:
- Current land use classification
- Slope/aspect from DEM
- Existing infrastructure detection
- Construction activity monitoring
- Seasonal vegetation analysis
- Change detection alerts

Technology:
- Planet Labs daily imagery
- Sentinel-2 10m multispectral
- LinkNet/UNet++ segmentation (92% IoU)
- SRTM/ASTER DEM processing

Competitive Advantage:
- No competitor has real-time satellite analysis
- See land changes within days, not months
- Verify ground conditions without site visits
```

#### F8: AI Copilot Chat
```
Capability: Natural language interface for all platform features

Features:
- "Find me sites like [selected parcel] but larger"
- "What's the permitting risk in [county]?"
- "Compare these 5 sites and recommend the best"
- "Generate a feasibility report for my portfolio"
- "Alert me when new 50+ acre parcels list in [state]"

Technology:
- Claude Opus 4.5 for complex reasoning
- Tool use for platform actions
- Memory for user preferences
- Context-aware suggestions

Competitive Advantage:
- Conversational interface vs. form-based UI
- AI remembers user preferences and history
- Proactive suggestions and alerts
```

#### F9: Smart Pipeline Management
```
Capability: AI-assisted project portfolio management

Features:
- Automatic stage progression tracking
- Risk score updates as conditions change
- Document management with OCR extraction
- Task assignment and deadline tracking
- Stakeholder collaboration
- Automated status reports

Differentiation:
- AI predicts project risks before they materialize
- Automatic document data extraction
- Smart reminders based on project stage
```

#### F10: Market Intelligence Dashboard
```
Capability: Real-time market and competitor intelligence

Features:
- Interconnection queue monitoring (all ISOs)
- Permit approval tracking by jurisdiction
- Solar auction results and PPA pricing
- Competitor project tracking
- Policy change alerts
- Market trend analysis

Differentiation:
- Aggregated intelligence across all markets
- AI-generated market reports
- Custom alert configurations
```

---

## Part 6: User Experience Strategy

### 6.1 Design Principles

```
1. SPEED ABOVE ALL
   - Sub-second search results
   - 60-second full site analysis
   - Instant map interactions
   - No loading spinners > 2 seconds

2. PROGRESSIVE DISCLOSURE
   - Show scores first, details on demand
   - Expandable analysis sections
   - "Learn more" for methodology
   - Expert mode toggle

3. AI-FIRST INTERACTION
   - Chat anywhere (⌘+K shortcut)
   - AI suggestions in context
   - Natural language search
   - Smart defaults

4. MOBILE READY
   - Field-usable on tablets
   - Offline capability for site visits
   - Photo/GPS integration
   - Quick data capture

5. COLLABORATIVE BY DEFAULT
   - Real-time multi-user editing
   - Comments and annotations
   - Share links with permissions
   - Team activity feeds
```

### 6.2 Key Screens

```
1. DISCOVERY MAP
   ┌─────────────────────────────────────────────────────────────┐
   │ [Search: "50+ acres TX ag zoning near substations"]    [⌘K]│
   ├─────────────────────────────────────────────────────────────┤
   │ ┌─────────────────────┐ ┌───────────────────────────────┐ │
   │ │                     │ │ RESULTS (847 parcels)         │ │
   │ │                     │ │ ┌───────────────────────────┐ │ │
   │ │    INTERACTIVE      │ │ │ 📍 123 County Rd 45       │ │ │
   │ │       MAP           │ │ │    Score: 87 ⭐           │ │ │
   │ │                     │ │ │    52 ac | $1,200/ac      │ │ │
   │ │  [Deck.gl layers]   │ │ │    🟢 Grid 🟡 Permit     │ │ │
   │ │                     │ │ └───────────────────────────┘ │ │
   │ │                     │ │ ┌───────────────────────────┐ │ │
   │ │                     │ │ │ 📍 FM 2104 Tract          │ │ │
   │ │                     │ │ │    Score: 82 ⭐           │ │ │
   │ └─────────────────────┘ │ └───────────────────────────┘ │ │
   └─────────────────────────────────────────────────────────────┘

2. SITE ANALYSIS
   ┌─────────────────────────────────────────────────────────────┐
   │ 📍 123 County Road 45, Harris County, TX                    │
   │ Score: 87/100 ⭐⭐⭐⭐⭐                                      │
   ├─────────────────────────────────────────────────────────────┤
   │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
   │ │Permitting│ │   Grid   │ │  Enviro  │ │   Land   │       │
   │ │   92/100 │ │   85/100 │ │   88/100 │ │   83/100 │       │
   │ │  🟢 Low  │ │  🟢 Good │ │  🟢 Clear│ │  🟢 Flat │       │
   │ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
   ├─────────────────────────────────────────────────────────────┤
   │ QUICK FACTS                                                 │
   │ • By-right solar in A-1 Agricultural                       │
   │ • 2.3 mi to Centerpoint 138kV substation (45 MW capacity)  │
   │ • No wetlands, flood zone X (minimal)                      │
   │ • Estimated 15 MW capacity | $18.2M CAPEX                  │
   │ • LCOE: $32.40/MWh | IRR: 12.4%                            │
   ├─────────────────────────────────────────────────────────────┤
   │ [📊 Full Analysis] [📄 Generate Report] [💾 Save to Project]│
   └─────────────────────────────────────────────────────────────┘

3. AI COPILOT (⌘+K)
   ┌─────────────────────────────────────────────────────────────┐
   │ 💬 Ask TerraJinki anything...                               │
   ├─────────────────────────────────────────────────────────────┤
   │ 👤 Find similar sites to my saved "Hill County Tract"       │
   │    but with better grid scores                              │
   ├─────────────────────────────────────────────────────────────┤
   │ 🤖 I found 12 similar sites with improved grid access:     │
   │                                                             │
   │    1. McLennan County 47.2ac - Grid: 94 (vs 78)            │
   │       0.8 mi to 345kV, 120 MW capacity                     │
   │                                                             │
   │    2. Falls County 52.1ac - Grid: 91 (vs 78)               │
   │       1.2 mi to 138kV, 85 MW capacity                      │
   │                                                             │
   │    [Show on map] [Compare all] [Add to pipeline]           │
   └─────────────────────────────────────────────────────────────┘

4. PIPELINE KANBAN
   ┌─────────────────────────────────────────────────────────────┐
   │ MY PIPELINE                              [+ New Project]    │
   ├──────────┬──────────┬──────────┬──────────┬────────────────┤
   │PROSPECTING│DUE DILIG│SITE CTRL│PERMITTING│ CONSTRUCTION   │
   │   (12)   │   (5)    │   (3)    │   (2)    │     (1)        │
   ├──────────┼──────────┼──────────┼──────────┼────────────────┤
   │┌────────┐│┌────────┐│┌────────┐│┌────────┐│ ┌────────┐     │
   ││Hill Co ││├────────┤││Brazos  ││├────────┤│ │Grimes  │     │
   ││52 ac   ││├────────┤││85 ac   ││├────────┤│ │120 MW  │     │
   ││⚠️ Risk ││└────────┘││🟢 OnTrk││└────────┘│ │🟢 Active│     │
   │└────────┘│          │└────────┘│          │ └────────┘     │
   └──────────┴──────────┴──────────┴──────────┴────────────────┘
```

---

## Part 7: Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
```
Week 1-2: Core Infrastructure
├── PostgreSQL + PostGIS setup
├── FastAPI with async + WebSocket
├── Authentication (Clerk/Auth0)
├── Basic React + MapLibre frontend
└── CI/CD pipeline (GitHub Actions)

Week 3-4: Agent Framework
├── LangGraph orchestration setup
├── Base agent implementation
├── Claude API integration
├── Mock data layer for testing
└── Basic permitting agent (RAG)
```

### Phase 2: Core Agents (Weeks 5-8)
```
Week 5-6: Permitting + Grid
├── RAG pipeline for ordinances
├── Permitting agent swarm
├── Grid agent with mock GNN
├── Score aggregation
└── Basic analysis API

Week 7-8: Environmental + Financial
├── Environmental screening agents
├── Satellite imagery integration (mock)
├── Financial modeling engine
├── Report generation
└── Full analysis pipeline
```

### Phase 3: Data Integration (Weeks 9-12)
```
Week 9-10: External APIs
├── Regrid parcel data integration
├── EIA grid data pipeline
├── NWI/FEMA/USFWS environmental
├── NSRDB solar resource
└── Data refresh automation

Week 11-12: ML Models
├── PowerGNN implementation
├── Satellite segmentation model
├── RAG+ optimization
├── Model serving infrastructure
└── Batch inference pipelines
```

### Phase 4: UX Excellence (Weeks 13-16)
```
Week 13-14: Frontend Polish
├── Discovery map with all layers
├── Site analysis dashboard
├── Real-time analysis streaming
├── Mobile responsive design
└── Performance optimization

Week 15-16: AI Copilot
├── Chat interface implementation
├── Tool use for platform actions
├── Conversation memory
├── Proactive suggestions
└── Voice input (stretch)
```

### Phase 5: Competitive Moat (Weeks 17-20)
```
Week 17-18: TerraScan Vision
├── Planet Labs integration
├── Segmentation model deployment
├── Change detection pipeline
├── Real-time alerts
└── Historical imagery comparison

Week 19-20: Market Intelligence
├── Queue monitoring scrapers
├── Permit tracking automation
├── Policy change detection
├── Market analytics dashboard
└── Alert system
```

### Phase 6: Scale & Polish (Weeks 21-24)
```
Week 21-22: Performance
├── Query optimization
├── Caching layer (Redis)
├── CDN for static assets
├── Load testing
└── Monitoring (Datadog)

Week 23-24: Launch Prep
├── Security audit
├── Documentation
├── Beta user onboarding
├── Feedback integration
└── Production deployment
```

---

## Part 8: Success Metrics

### 8.1 Product Metrics

| Metric | Target | Paces Benchmark |
|--------|--------|-----------------|
| Site analysis time | < 60 seconds | 5-10 days |
| Parcels searchable | 150M+ | "millions" |
| Analysis accuracy | > 90% | Unknown |
| User sessions/week | > 5 | Unknown |
| Reports generated/user | > 10/month | Unknown |

### 8.2 Business Metrics

| Metric | Year 1 Target |
|--------|---------------|
| Users | 500+ |
| Paying customers | 50+ |
| ARR | $1M+ |
| NPS | > 50 |
| Churn | < 5%/month |

### 8.3 Technical Metrics

| Metric | Target |
|--------|--------|
| API latency (p95) | < 200ms |
| Analysis latency | < 60s |
| Uptime | 99.9% |
| Test coverage | > 80% |
| Deploy frequency | Daily |

---

## Part 9: Competitive Advantages Summary

| Dimension | Paces | PVcase | TerraJinki |
|-----------|-------|--------|------------|
| **AI Analysis Speed** | 5-10 days | Hours | < 60 seconds |
| **Satellite Imagery** | None | None | Real-time ML |
| **Grid Analysis** | Distance heuristics | Queue data | GNN topology |
| **Document Intelligence** | Basic LLM | None | RAG+ with monitoring |
| **Human-in-the-Loop** | Manual | Manual | Smart approval gates |
| **Natural Language** | No | No | AI Copilot |
| **Coverage** | 3 states (Predictor) | US only | Global capable |
| **API Access** | Limited | None | Full REST + GraphQL |

---

## Part 10: Conclusion

TerraJinki will dominate the renewable energy site development market by:

1. **Being 100x faster** - 60 seconds vs. days for full analysis
2. **Seeing more** - Satellite imagery + GNN grid modeling
3. **Understanding deeper** - RAG+ document intelligence
4. **Working smarter** - Multi-agent orchestration with human oversight
5. **Delighting users** - AI copilot + exceptional UX

The $17B annual opportunity from failed projects is ours to capture. With the right execution, TerraJinki will become the default platform for renewable energy development in 2 years.

---

*Document Version: 1.0*
*Created: January 2026*
*Author: TerraJinki AI Architecture Team*
