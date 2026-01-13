// Real-Time ISO Grid Data Client
// Connects to CAISO, ERCOT, PJM, MISO, SPP for live market data

import { CircuitBreaker } from '../core/errors';
import type { Result } from '../core/types';

// ============================================================================
// TYPES
// ============================================================================

export type ISORegion = 'CAISO' | 'ERCOT' | 'PJM' | 'MISO' | 'SPP' | 'NYISO' | 'ISONE';

export interface LMPData {
  nodeId: string;
  nodeName: string;
  region: ISORegion;
  timestamp: string;
  lmpTotal: number;        // $/MWh
  energyComponent: number;
  congestionComponent: number;
  lossComponent: number;
}

export interface GridLoad {
  region: ISORegion;
  timestamp: string;
  currentLoad: number;     // MW
  forecastLoad: number;    // MW
  peakLoad: number;        // MW
  availableCapacity: number;
  renewableGeneration: {
    solar: number;
    wind: number;
    hydro: number;
    other: number;
  };
  totalGeneration: number;
}

export interface InterconnectionProject {
  id: string;
  projectName: string;
  region: ISORegion;
  state: string;
  county?: string;
  fuelType: 'Solar' | 'Wind' | 'Storage' | 'Hybrid' | 'Other';
  capacityMw: number;
  queuePosition: number;
  queueDate: string;
  status: 'Active' | 'Withdrawn' | 'Completed' | 'Suspended';
  estimatedCOD?: string;
  pointOfInterconnection: string;
  transmissionOwner?: string;
  latitude?: number;
  longitude?: number;
}

export interface GridCongestion {
  region: ISORegion;
  constraintName: string;
  shadowPrice: number;
  bindingStatus: boolean;
  flowMw: number;
  limitMw: number;
  affectedNodes: string[];
}

// ============================================================================
// ISO API ENDPOINTS (Production would use actual endpoints)
// ============================================================================

const ISO_ENDPOINTS: Record<ISORegion, { base: string; lmp: string; load: string; queue: string }> = {
  CAISO: {
    base: 'https://oasis.caiso.com/oasisapi',
    lmp: '/SingleZip?queryname=PRC_LMP&market_run_id=RTM',
    load: '/SingleZip?queryname=SLD_REN_FCST',
    queue: '/SingleZip?queryname=ATL_GEN_QUEUE',
  },
  ERCOT: {
    base: 'https://www.ercot.com/api/1',
    lmp: '/np6-905-cd/spp_node_zone_hub',
    load: '/np6-345-cd/act_sys_load_by_wzn',
    queue: '/np4-10-cd/60d_sced_gen_res_cap',
  },
  PJM: {
    base: 'https://dataminer2.pjm.com',
    lmp: '/feed/rt_hrl_lmps',
    load: '/feed/ops_sum_prev_period',
    queue: '/feed/gen_queues',
  },
  MISO: {
    base: 'https://api.misoenergy.org/MISORTWDDataBroker',
    lmp: '/DataBrokerServices.asmx?messageType=getlmp',
    load: '/DataBrokerServices.asmx?messageType=getload',
    queue: '/DataBrokerServices.asmx?messageType=getqueue',
  },
  SPP: {
    base: 'https://marketplace.spp.org/pages',
    lmp: '/lmp-by-location',
    load: '/system-load',
    queue: '/generation-interconnection',
  },
  NYISO: {
    base: 'https://mis.nyiso.com/public',
    lmp: '/csv/realtime',
    load: '/csv/pal',
    queue: '/csv/interconnectionqueue',
  },
  ISONE: {
    base: 'https://webservices.iso-ne.com/api/v1.1',
    lmp: '/fiveminutelmp/current',
    load: '/systemload/current',
    queue: '/interconnectionqueue',
  },
};

// ============================================================================
// CIRCUIT BREAKERS PER REGION
// ============================================================================

const circuitBreakers: Record<ISORegion, CircuitBreaker> = {
  CAISO: new CircuitBreaker('CAISO', { failureThreshold: 3, resetTimeoutMs: 60000, halfOpenRequests: 2 }),
  ERCOT: new CircuitBreaker('ERCOT', { failureThreshold: 3, resetTimeoutMs: 60000, halfOpenRequests: 2 }),
  PJM: new CircuitBreaker('PJM', { failureThreshold: 3, resetTimeoutMs: 60000, halfOpenRequests: 2 }),
  MISO: new CircuitBreaker('MISO', { failureThreshold: 3, resetTimeoutMs: 60000, halfOpenRequests: 2 }),
  SPP: new CircuitBreaker('SPP', { failureThreshold: 3, resetTimeoutMs: 60000, halfOpenRequests: 2 }),
  NYISO: new CircuitBreaker('NYISO', { failureThreshold: 3, resetTimeoutMs: 60000, halfOpenRequests: 2 }),
  ISONE: new CircuitBreaker('ISONE', { failureThreshold: 3, resetTimeoutMs: 60000, halfOpenRequests: 2 }),
};

// ============================================================================
// MOCK DATA FOR DEMO (Replace with real API calls in production)
// ============================================================================

function generateMockLMPData(region: ISORegion): LMPData[] {
  const nodes = ['HUB', 'NORTH', 'SOUTH', 'WEST', 'EAST'];
  return nodes.map(node => ({
    nodeId: `${region}-${node}`,
    nodeName: `${region} ${node} Hub`,
    region,
    timestamp: new Date().toISOString(),
    lmpTotal: 25 + Math.random() * 50,
    energyComponent: 20 + Math.random() * 30,
    congestionComponent: Math.random() * 15,
    lossComponent: Math.random() * 5,
  }));
}

function generateMockGridLoad(region: ISORegion): GridLoad {
  const baseLoad = {
    CAISO: 35000,
    ERCOT: 55000,
    PJM: 90000,
    MISO: 70000,
    SPP: 35000,
    NYISO: 25000,
    ISONE: 15000,
  }[region];

  const solarPct = region === 'CAISO' ? 0.25 : region === 'ERCOT' ? 0.15 : 0.08;
  const windPct = region === 'ERCOT' ? 0.25 : region === 'SPP' ? 0.35 : region === 'MISO' ? 0.20 : 0.10;

  return {
    region,
    timestamp: new Date().toISOString(),
    currentLoad: baseLoad * (0.9 + Math.random() * 0.2),
    forecastLoad: baseLoad * (0.95 + Math.random() * 0.1),
    peakLoad: baseLoad * 1.15,
    availableCapacity: baseLoad * 1.25,
    renewableGeneration: {
      solar: baseLoad * solarPct * (0.5 + Math.random() * 0.5),
      wind: baseLoad * windPct * (0.3 + Math.random() * 0.7),
      hydro: baseLoad * 0.05,
      other: baseLoad * 0.02,
    },
    totalGeneration: baseLoad * (0.95 + Math.random() * 0.1),
  };
}

function generateMockInterconnectionQueue(region: ISORegion): InterconnectionProject[] {
  const states = {
    CAISO: ['CA'],
    ERCOT: ['TX'],
    PJM: ['PA', 'NJ', 'MD', 'VA', 'OH', 'WV'],
    MISO: ['MN', 'IA', 'IL', 'IN', 'MI', 'WI'],
    SPP: ['KS', 'OK', 'NE', 'NM'],
    NYISO: ['NY'],
    ISONE: ['MA', 'CT', 'ME', 'NH', 'VT', 'RI'],
  }[region];

  const projects: InterconnectionProject[] = [];
  for (let i = 0; i < 50; i++) {
    const fuelTypes: InterconnectionProject['fuelType'][] = ['Solar', 'Wind', 'Storage', 'Hybrid'];
    const statuses: InterconnectionProject['status'][] = ['Active', 'Active', 'Active', 'Withdrawn', 'Completed'];

    projects.push({
      id: `${region}-Q${String(i + 1).padStart(4, '0')}`,
      projectName: `${fuelTypes[i % 4]} Project ${i + 1}`,
      region,
      state: states[i % states.length],
      fuelType: fuelTypes[i % 4],
      capacityMw: 50 + Math.floor(Math.random() * 450),
      queuePosition: i + 1,
      queueDate: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
      status: statuses[Math.floor(Math.random() * statuses.length)],
      estimatedCOD: new Date(Date.now() + (365 + Math.random() * 730) * 24 * 60 * 60 * 1000).toISOString(),
      pointOfInterconnection: `${region} Substation ${Math.floor(Math.random() * 100)}`,
    });
  }
  return projects;
}

// ============================================================================
// ISO CLIENT CLASS
// ============================================================================

export class ISOClient {
  private cache = new Map<string, { data: unknown; timestamp: number }>();
  private cacheTTL = 5 * 60 * 1000; // 5 minutes

  private getCached<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
      return cached.data as T;
    }
    return null;
  }

  private setCache<T>(key: string, data: T): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  async getLMP(region: ISORegion): Promise<Result<LMPData[], Error>> {
    const cacheKey = `lmp-${region}`;
    const cached = this.getCached<LMPData[]>(cacheKey);
    if (cached) return { success: true, data: cached };

    try {
      const data = await circuitBreakers[region].execute(async () => {
        // In production, this would call the actual ISO API
        // For demo, return mock data
        await new Promise(resolve => setTimeout(resolve, 100));
        return generateMockLMPData(region);
      });

      this.setCache(cacheKey, data);
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error : new Error('Failed to fetch LMP data') };
    }
  }

  async getGridLoad(region: ISORegion): Promise<Result<GridLoad, Error>> {
    const cacheKey = `load-${region}`;
    const cached = this.getCached<GridLoad>(cacheKey);
    if (cached) return { success: true, data: cached };

    try {
      const data = await circuitBreakers[region].execute(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return generateMockGridLoad(region);
      });

      this.setCache(cacheKey, data);
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error : new Error('Failed to fetch grid load') };
    }
  }

  async getInterconnectionQueue(region: ISORegion, filters?: {
    fuelType?: InterconnectionProject['fuelType'];
    minCapacity?: number;
    status?: InterconnectionProject['status'];
  }): Promise<Result<InterconnectionProject[], Error>> {
    const cacheKey = `queue-${region}`;
    const cached = this.getCached<InterconnectionProject[]>(cacheKey);

    let data: InterconnectionProject[];
    if (cached) {
      data = cached;
    } else {
      try {
        data = await circuitBreakers[region].execute(async () => {
          await new Promise(resolve => setTimeout(resolve, 200));
          return generateMockInterconnectionQueue(region);
        });
        this.setCache(cacheKey, data);
      } catch (error) {
        return { success: false, error: error instanceof Error ? error : new Error('Failed to fetch queue') };
      }
    }

    // Apply filters
    if (filters) {
      data = data.filter(project => {
        if (filters.fuelType && project.fuelType !== filters.fuelType) return false;
        if (filters.minCapacity && project.capacityMw < filters.minCapacity) return false;
        if (filters.status && project.status !== filters.status) return false;
        return true;
      });
    }

    return { success: true, data };
  }

  async getAllRegionsLMP(): Promise<Map<ISORegion, LMPData[]>> {
    const regions: ISORegion[] = ['CAISO', 'ERCOT', 'PJM', 'MISO', 'SPP', 'NYISO', 'ISONE'];
    const results = new Map<ISORegion, LMPData[]>();

    await Promise.all(
      regions.map(async region => {
        const result = await this.getLMP(region);
        if (result.success) {
          results.set(region, result.data);
        }
      })
    );

    return results;
  }

  async getAllRegionsLoad(): Promise<Map<ISORegion, GridLoad>> {
    const regions: ISORegion[] = ['CAISO', 'ERCOT', 'PJM', 'MISO', 'SPP', 'NYISO', 'ISONE'];
    const results = new Map<ISORegion, GridLoad>();

    await Promise.all(
      regions.map(async region => {
        const result = await this.getGridLoad(region);
        if (result.success) {
          results.set(region, result.data);
        }
      })
    );

    return results;
  }

  // Get queue statistics across all regions
  async getQueueStats(): Promise<{
    totalProjects: number;
    totalCapacityMw: number;
    byFuelType: Record<string, { count: number; capacityMw: number }>;
    byRegion: Record<string, { count: number; capacityMw: number }>;
    activeVsWithdrawn: { active: number; withdrawn: number };
  }> {
    const regions: ISORegion[] = ['CAISO', 'ERCOT', 'PJM', 'MISO', 'SPP'];
    const allProjects: InterconnectionProject[] = [];

    await Promise.all(
      regions.map(async region => {
        const result = await this.getInterconnectionQueue(region);
        if (result.success) {
          allProjects.push(...result.data);
        }
      })
    );

    const byFuelType: Record<string, { count: number; capacityMw: number }> = {};
    const byRegion: Record<string, { count: number; capacityMw: number }> = {};
    let active = 0;
    let withdrawn = 0;

    allProjects.forEach(project => {
      // By fuel type
      if (!byFuelType[project.fuelType]) {
        byFuelType[project.fuelType] = { count: 0, capacityMw: 0 };
      }
      byFuelType[project.fuelType].count++;
      byFuelType[project.fuelType].capacityMw += project.capacityMw;

      // By region
      if (!byRegion[project.region]) {
        byRegion[project.region] = { count: 0, capacityMw: 0 };
      }
      byRegion[project.region].count++;
      byRegion[project.region].capacityMw += project.capacityMw;

      // Status
      if (project.status === 'Active') active++;
      if (project.status === 'Withdrawn') withdrawn++;
    });

    return {
      totalProjects: allProjects.length,
      totalCapacityMw: allProjects.reduce((sum, p) => sum + p.capacityMw, 0),
      byFuelType,
      byRegion,
      activeVsWithdrawn: { active, withdrawn },
    };
  }
}

// Singleton instance
export const isoClient = new ISOClient();

// ============================================================================
// REGION HELPERS
// ============================================================================

export function getISORegionForState(stateCode: string): ISORegion | null {
  const stateToRegion: Record<string, ISORegion> = {
    // CAISO
    CA: 'CAISO',
    // ERCOT
    TX: 'ERCOT',
    // PJM
    PA: 'PJM', NJ: 'PJM', MD: 'PJM', DE: 'PJM', VA: 'PJM', WV: 'PJM', OH: 'PJM',
    DC: 'PJM', NC: 'PJM', KY: 'PJM', IN: 'PJM', IL: 'PJM', MI: 'PJM',
    // MISO
    MN: 'MISO', IA: 'MISO', WI: 'MISO', ND: 'MISO', SD: 'MISO', NE: 'MISO',
    MT: 'MISO', AR: 'MISO', LA: 'MISO', MS: 'MISO',
    // SPP
    KS: 'SPP', OK: 'SPP', NM: 'SPP',
    // NYISO
    NY: 'NYISO',
    // ISO-NE
    MA: 'ISONE', CT: 'ISONE', ME: 'ISONE', NH: 'ISONE', VT: 'ISONE', RI: 'ISONE',
  };

  return stateToRegion[stateCode] || null;
}

export function getRegionDisplayName(region: ISORegion): string {
  const names: Record<ISORegion, string> = {
    CAISO: 'California ISO',
    ERCOT: 'Electric Reliability Council of Texas',
    PJM: 'PJM Interconnection',
    MISO: 'Midcontinent ISO',
    SPP: 'Southwest Power Pool',
    NYISO: 'New York ISO',
    ISONE: 'ISO New England',
  };
  return names[region];
}
