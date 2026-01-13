// Enterprise-Grade Integration Layer
// External service connectors with resilience patterns

import { api } from '../core/api-client';
import { CircuitBreaker } from '../core/errors';
import type { Result } from '../core/types';

// ============================================================================
// EXTERNAL SERVICE TYPES
// ============================================================================

export interface WeatherData {
  location: { lat: number; lon: number };
  solarIrradiance: {
    ghi: number;
    dni: number;
    dhi: number;
  };
  windSpeed: {
    avg: number;
    max: number;
    direction: number;
  };
  temperature: {
    avg: number;
    min: number;
    max: number;
  };
  humidity: number;
  cloudCover: number;
  timestamp: string;
}

export interface GridData {
  substations: Array<{
    id: string;
    name: string;
    location: { lat: number; lon: number };
    voltage: number;
    capacity: number;
    availableCapacity: number;
    distance: number;
  }>;
  transmissionLines: Array<{
    id: string;
    voltage: number;
    distance: number;
    congestionLevel: 'low' | 'moderate' | 'high';
  }>;
  interconnectionQueue: {
    position: number;
    estimatedWait: number;
    avgProcessingTime: number;
  };
}

export interface MarketData {
  region: string;
  prices: {
    lmp: number;
    energy: number;
    capacity: number;
    rec: number;
  };
  demand: {
    current: number;
    peak: number;
    forecast: number[];
  };
  supply: {
    solar: number;
    wind: number;
    natural_gas: number;
    nuclear: number;
    hydro: number;
  };
  carbonIntensity: number;
  timestamp: string;
}

export interface LandData {
  parcelId: string;
  ownership: {
    type: 'private' | 'corporate' | 'government' | 'trust';
    owner: string;
    contactAvailable: boolean;
  };
  legal: {
    easements: string[];
    liens: boolean;
    encumbrances: string[];
  };
  zoning: {
    current: string;
    solarAllowed: boolean;
    windAllowed: boolean;
    storageAllowed: boolean;
    maxHeight: number;
    setbacks: { front: number; side: number; rear: number };
  };
  tax: {
    assessment: number;
    annualTax: number;
    exemptions: string[];
  };
}

export interface EnvironmentalData {
  wetlands: {
    present: boolean;
    type: string | null;
    acreage: number;
  };
  endangered: {
    species: string[];
    criticalHabitat: boolean;
  };
  cultural: {
    historicSites: boolean;
    archaeologicalSurveyRequired: boolean;
  };
  floodZone: {
    zone: string;
    baseFloodElevation: number | null;
  };
  soilType: {
    classification: string;
    drainage: 'excellent' | 'good' | 'moderate' | 'poor';
    bearing: number;
  };
}

// ============================================================================
// HELPER FUNCTION
// ============================================================================

async function safeApiCall<T>(fn: () => Promise<T>): Promise<Result<T, Error>> {
  try {
    const data = await fn();
    return { success: true, data };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error : new Error('Unknown error'),
    };
  }
}

// ============================================================================
// SERVICE CONNECTORS
// ============================================================================

const weatherCircuitBreaker = new CircuitBreaker('weather', { failureThreshold: 3, resetTimeoutMs: 30000, halfOpenRequests: 2 });
const gridCircuitBreaker = new CircuitBreaker('grid', { failureThreshold: 3, resetTimeoutMs: 30000, halfOpenRequests: 2 });
const marketCircuitBreaker = new CircuitBreaker('market', { failureThreshold: 3, resetTimeoutMs: 30000, halfOpenRequests: 2 });

export const integrations = {
  // Weather & Solar Resource Data
  weather: {
    async getCurrent(lat: number, lon: number): Promise<Result<WeatherData, Error>> {
      return safeApiCall(() =>
        weatherCircuitBreaker.execute(async () =>
          api.get<WeatherData>(`/api/weather?lat=${lat}&lon=${lon}`)
        )
      );
    },

    async getHistorical(lat: number, lon: number, years: number = 10): Promise<Result<WeatherData[], Error>> {
      return safeApiCall(() =>
        weatherCircuitBreaker.execute(async () =>
          api.get<WeatherData[]>(`/api/weather/historical?lat=${lat}&lon=${lon}&years=${years}`)
        )
      );
    },

    async getSolarResource(lat: number, lon: number): Promise<Result<{
      annualGhi: number;
      monthlyGhi: number[];
      optimalTilt: number;
      azimuth: number;
    }, Error>> {
      return safeApiCall(() =>
        weatherCircuitBreaker.execute(async () =>
          api.get<{ annualGhi: number; monthlyGhi: number[]; optimalTilt: number; azimuth: number }>(
            `/api/solar-resource?lat=${lat}&lon=${lon}`
          )
        )
      );
    },
  },

  // Grid Infrastructure Data
  grid: {
    async getSubstations(lat: number, lon: number, radiusMiles: number = 25): Promise<Result<GridData['substations'], Error>> {
      return safeApiCall(() =>
        gridCircuitBreaker.execute(async () =>
          api.get<GridData['substations']>(`/api/grid/substations?lat=${lat}&lon=${lon}&radius=${radiusMiles}`)
        )
      );
    },

    async getTransmissionLines(lat: number, lon: number, radiusMiles: number = 10): Promise<Result<GridData['transmissionLines'], Error>> {
      return safeApiCall(() =>
        gridCircuitBreaker.execute(async () =>
          api.get<GridData['transmissionLines']>(`/api/grid/transmission?lat=${lat}&lon=${lon}&radius=${radiusMiles}`)
        )
      );
    },

    async getInterconnectionQueue(utilityId: string): Promise<Result<GridData['interconnectionQueue'], Error>> {
      return safeApiCall(() =>
        gridCircuitBreaker.execute(async () =>
          api.get<GridData['interconnectionQueue']>(`/api/grid/queue/${utilityId}`)
        )
      );
    },
  },

  // Energy Market Data
  market: {
    async getPrices(region: string): Promise<Result<MarketData['prices'], Error>> {
      return safeApiCall(() =>
        marketCircuitBreaker.execute(async () =>
          api.get<MarketData['prices']>(`/api/market/prices/${region}`)
        )
      );
    },

    async getDemand(region: string): Promise<Result<MarketData['demand'], Error>> {
      return safeApiCall(() =>
        marketCircuitBreaker.execute(async () =>
          api.get<MarketData['demand']>(`/api/market/demand/${region}`)
        )
      );
    },

    async getRECPrices(state: string): Promise<Result<{ price: number; trend: 'up' | 'down' | 'stable'; forecast: number[] }, Error>> {
      return safeApiCall(() =>
        marketCircuitBreaker.execute(async () =>
          api.get<{ price: number; trend: 'up' | 'down' | 'stable'; forecast: number[] }>(`/api/market/rec/${state}`)
        )
      );
    },
  },

  // Land & Property Data
  land: {
    async getOwnership(parcelId: string): Promise<Result<LandData['ownership'], Error>> {
      return safeApiCall(() => api.get<LandData['ownership']>(`/api/land/ownership/${parcelId}`));
    },

    async getZoning(parcelId: string): Promise<Result<LandData['zoning'], Error>> {
      return safeApiCall(() => api.get<LandData['zoning']>(`/api/land/zoning/${parcelId}`));
    },

    async getTaxInfo(parcelId: string): Promise<Result<LandData['tax'], Error>> {
      return safeApiCall(() => api.get<LandData['tax']>(`/api/land/tax/${parcelId}`));
    },
  },

  // Environmental Data
  environmental: {
    async getWetlands(lat: number, lon: number, radiusMiles: number = 1): Promise<Result<EnvironmentalData['wetlands'], Error>> {
      return safeApiCall(() =>
        api.get<EnvironmentalData['wetlands']>(`/api/environmental/wetlands?lat=${lat}&lon=${lon}&radius=${radiusMiles}`)
      );
    },

    async getEndangeredSpecies(lat: number, lon: number): Promise<Result<EnvironmentalData['endangered'], Error>> {
      return safeApiCall(() =>
        api.get<EnvironmentalData['endangered']>(`/api/environmental/endangered?lat=${lat}&lon=${lon}`)
      );
    },

    async getFloodZone(lat: number, lon: number): Promise<Result<EnvironmentalData['floodZone'], Error>> {
      return safeApiCall(() =>
        api.get<EnvironmentalData['floodZone']>(`/api/environmental/flood?lat=${lat}&lon=${lon}`)
      );
    },

    async getSoilData(lat: number, lon: number): Promise<Result<EnvironmentalData['soilType'], Error>> {
      return safeApiCall(() =>
        api.get<EnvironmentalData['soilType']>(`/api/environmental/soil?lat=${lat}&lon=${lon}`)
      );
    },
  },
};

// ============================================================================
// BATCH DATA FETCHER
// ============================================================================

export async function fetchAllParcelData(
  parcelId: string,
  lat: number,
  lon: number
): Promise<{
  weather: WeatherData | null;
  grid: GridData['substations'] | null;
  land: LandData['zoning'] | null;
  environmental: EnvironmentalData['floodZone'] | null;
  errors: string[];
}> {
  const errors: string[] = [];

  const [weatherResult, gridResult, landResult, envResult] = await Promise.allSettled([
    integrations.weather.getCurrent(lat, lon),
    integrations.grid.getSubstations(lat, lon, 25),
    integrations.land.getZoning(parcelId),
    integrations.environmental.getFloodZone(lat, lon),
  ]);

  return {
    weather:
      weatherResult.status === 'fulfilled' && weatherResult.value.success
        ? weatherResult.value.data
        : (errors.push('Failed to fetch weather data'), null),
    grid:
      gridResult.status === 'fulfilled' && gridResult.value.success
        ? gridResult.value.data
        : (errors.push('Failed to fetch grid data'), null),
    land:
      landResult.status === 'fulfilled' && landResult.value.success
        ? landResult.value.data
        : (errors.push('Failed to fetch land data'), null),
    environmental:
      envResult.status === 'fulfilled' && envResult.value.success
        ? envResult.value.data
        : (errors.push('Failed to fetch environmental data'), null),
    errors,
  };
}

// ============================================================================
// WEBHOOK DISPATCHER
// ============================================================================

export interface WebhookPayload {
  event: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export async function dispatchWebhook(
  url: string,
  payload: WebhookPayload,
  secret?: string
): Promise<Result<void, Error>> {
  const body = JSON.stringify(payload);
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (secret) {
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(body));
    headers['X-Webhook-Signature'] = btoa(String.fromCharCode(...new Uint8Array(signature)));
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body,
    });

    if (!response.ok) {
      return {
        success: false,
        error: new Error(`Webhook failed: ${response.status} ${response.statusText}`),
      };
    }

    return { success: true, data: undefined };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error : new Error('Webhook dispatch failed'),
    };
  }
}
