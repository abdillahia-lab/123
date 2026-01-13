// Real-Time Market Data Stream
// WebSocket-based streaming for live market updates

import type { LMPData, GridLoad, ISORegion } from './iso-client';
import { isoClient } from './iso-client';

// ============================================================================
// TYPES
// ============================================================================

export type StreamEventType =
  | 'lmp_update'
  | 'load_update'
  | 'price_alert'
  | 'congestion_alert'
  | 'new_parcel'
  | 'queue_update'
  | 'connection_status';

export interface StreamEvent<T = unknown> {
  type: StreamEventType;
  timestamp: string;
  region?: ISORegion;
  data: T;
}

export interface PriceAlert {
  region: ISORegion;
  nodeId: string;
  currentPrice: number;
  threshold: number;
  direction: 'above' | 'below';
  percentChange: number;
}

export interface MarketStreamConfig {
  regions: ISORegion[];
  updateIntervalMs: number;
  priceAlertThresholds?: {
    high: number;
    low: number;
  };
}

type EventCallback<T> = (event: StreamEvent<T>) => void;

// ============================================================================
// MARKET STREAM CLASS
// ============================================================================

export class MarketStream {
  private config: MarketStreamConfig;
  private isRunning = false;
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private listeners = new Map<StreamEventType, Set<EventCallback<unknown>>>();
  private lastPrices = new Map<string, number>();
  private connectionStatus: 'connected' | 'disconnected' | 'reconnecting' = 'disconnected';

  constructor(config: Partial<MarketStreamConfig> = {}) {
    this.config = {
      regions: config.regions || ['CAISO', 'ERCOT', 'PJM', 'MISO', 'SPP'],
      updateIntervalMs: config.updateIntervalMs || 30000, // 30 seconds default
      priceAlertThresholds: config.priceAlertThresholds || { high: 100, low: 10 },
    };
  }

  // Start the stream
  start(): void {
    if (this.isRunning) return;

    this.isRunning = true;
    this.connectionStatus = 'connected';
    this.emit('connection_status', { status: 'connected' });

    // Initial fetch
    this.fetchAndBroadcast();

    // Set up polling interval
    this.intervalId = setInterval(() => {
      this.fetchAndBroadcast();
    }, this.config.updateIntervalMs);

    console.log('[MarketStream] Started with', this.config.regions.length, 'regions');
  }

  // Stop the stream
  stop(): void {
    if (!this.isRunning) return;

    this.isRunning = false;
    this.connectionStatus = 'disconnected';

    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    this.emit('connection_status', { status: 'disconnected' });
    console.log('[MarketStream] Stopped');
  }

  // Subscribe to events
  subscribe<T>(eventType: StreamEventType, callback: EventCallback<T>): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }

    this.listeners.get(eventType)!.add(callback as EventCallback<unknown>);

    // Return unsubscribe function
    return () => {
      this.listeners.get(eventType)?.delete(callback as EventCallback<unknown>);
    };
  }

  // Emit event to all listeners
  private emit<T>(type: StreamEventType, data: T, region?: ISORegion): void {
    const event: StreamEvent<T> = {
      type,
      timestamp: new Date().toISOString(),
      region,
      data,
    };

    this.listeners.get(type)?.forEach(callback => {
      try {
        callback(event);
      } catch (error) {
        console.error('[MarketStream] Listener error:', error);
      }
    });
  }

  // Fetch data from all regions and broadcast
  private async fetchAndBroadcast(): Promise<void> {
    for (const region of this.config.regions) {
      // Fetch LMP data
      const lmpResult = await isoClient.getLMP(region);
      if (lmpResult.success) {
        this.emit('lmp_update', lmpResult.data, region);
        this.checkPriceAlerts(lmpResult.data);
      }

      // Fetch grid load
      const loadResult = await isoClient.getGridLoad(region);
      if (loadResult.success) {
        this.emit('load_update', loadResult.data, region);
      }

      // Small delay between regions to avoid overwhelming APIs
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  // Check for price alerts
  private checkPriceAlerts(lmpData: LMPData[]): void {
    const { priceAlertThresholds } = this.config;
    if (!priceAlertThresholds) return;

    for (const data of lmpData) {
      const key = `${data.region}-${data.nodeId}`;
      const lastPrice = this.lastPrices.get(key);

      // Check high price alert
      if (data.lmpTotal >= priceAlertThresholds.high) {
        const alert: PriceAlert = {
          region: data.region,
          nodeId: data.nodeId,
          currentPrice: data.lmpTotal,
          threshold: priceAlertThresholds.high,
          direction: 'above',
          percentChange: lastPrice ? ((data.lmpTotal - lastPrice) / lastPrice) * 100 : 0,
        };
        this.emit('price_alert', alert, data.region);
      }

      // Check low price alert
      if (data.lmpTotal <= priceAlertThresholds.low) {
        const alert: PriceAlert = {
          region: data.region,
          nodeId: data.nodeId,
          currentPrice: data.lmpTotal,
          threshold: priceAlertThresholds.low,
          direction: 'below',
          percentChange: lastPrice ? ((data.lmpTotal - lastPrice) / lastPrice) * 100 : 0,
        };
        this.emit('price_alert', alert, data.region);
      }

      // Store last price
      this.lastPrices.set(key, data.lmpTotal);
    }
  }

  // Get current status
  getStatus(): {
    isRunning: boolean;
    connectionStatus: string;
    regions: ISORegion[];
    updateInterval: number;
  } {
    return {
      isRunning: this.isRunning,
      connectionStatus: this.connectionStatus,
      regions: this.config.regions,
      updateInterval: this.config.updateIntervalMs,
    };
  }

  // Update configuration
  updateConfig(config: Partial<MarketStreamConfig>): void {
    const wasRunning = this.isRunning;

    if (wasRunning) {
      this.stop();
    }

    this.config = { ...this.config, ...config };

    if (wasRunning) {
      this.start();
    }
  }
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

let marketStreamInstance: MarketStream | null = null;

export function getMarketStream(): MarketStream {
  if (!marketStreamInstance) {
    marketStreamInstance = new MarketStream();
  }
  return marketStreamInstance;
}

// ============================================================================
// REACT HOOK FOR MARKET STREAM
// ============================================================================

import { useEffect, useState, useCallback } from 'react';

export function useMarketStream(
  regions: ISORegion[] = ['CAISO', 'ERCOT', 'PJM']
): {
  isConnected: boolean;
  lmpData: Map<ISORegion, LMPData[]>;
  loadData: Map<ISORegion, GridLoad>;
  priceAlerts: PriceAlert[];
  start: () => void;
  stop: () => void;
} {
  const [isConnected, setIsConnected] = useState(false);
  const [lmpData, setLmpData] = useState<Map<ISORegion, LMPData[]>>(new Map());
  const [loadData, setLoadData] = useState<Map<ISORegion, GridLoad>>(new Map());
  const [priceAlerts, setPriceAlerts] = useState<PriceAlert[]>([]);

  const stream = getMarketStream();

  useEffect(() => {
    stream.updateConfig({ regions });

    const unsubLmp = stream.subscribe<LMPData[]>('lmp_update', event => {
      if (event.region) {
        setLmpData(prev => new Map(prev).set(event.region!, event.data));
      }
    });

    const unsubLoad = stream.subscribe<GridLoad>('load_update', event => {
      if (event.region) {
        setLoadData(prev => new Map(prev).set(event.region!, event.data));
      }
    });

    const unsubAlert = stream.subscribe<PriceAlert>('price_alert', event => {
      setPriceAlerts(prev => [event.data, ...prev].slice(0, 50));
    });

    const unsubStatus = stream.subscribe<{ status: string }>('connection_status', event => {
      setIsConnected(event.data.status === 'connected');
    });

    return () => {
      unsubLmp();
      unsubLoad();
      unsubAlert();
      unsubStatus();
    };
  }, [regions.join(',')]);

  const start = useCallback(() => stream.start(), []);
  const stop = useCallback(() => stream.stop(), []);

  return { isConnected, lmpData, loadData, priceAlerts, start, stop };
}

// ============================================================================
// PARCEL STREAM FOR NEW LISTINGS
// ============================================================================

export interface NewParcelEvent {
  id: string;
  state: string;
  county: string;
  acreage: number;
  overallScore: number;
  solarCapacityMw: number;
  viability: string;
  detectedAt: string;
  source: 'mls' | 'county' | 'auction' | 'direct';
}

export class ParcelStream {
  private isRunning = false;
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private listeners = new Set<(parcel: NewParcelEvent) => void>();
  private seenParcels = new Set<string>();

  start(checkIntervalMs: number = 60000): void {
    if (this.isRunning) return;
    this.isRunning = true;

    // Simulate checking for new parcels
    this.intervalId = setInterval(() => {
      this.checkForNewParcels();
    }, checkIntervalMs);

    console.log('[ParcelStream] Started monitoring for new parcels');
  }

  stop(): void {
    if (!this.isRunning) return;
    this.isRunning = false;

    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  subscribe(callback: (parcel: NewParcelEvent) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private async checkForNewParcels(): Promise<void> {
    // In production, this would query:
    // - MLS APIs for new commercial listings
    // - County recorder APIs for new deeds
    // - Auction sites for available land
    // - Partner data feeds

    // For demo, occasionally emit a mock new parcel
    if (Math.random() > 0.7) {
      const newParcel = this.generateMockNewParcel();

      if (!this.seenParcels.has(newParcel.id)) {
        this.seenParcels.add(newParcel.id);
        this.listeners.forEach(listener => listener(newParcel));
      }
    }
  }

  private generateMockNewParcel(): NewParcelEvent {
    const states = ['TX', 'CA', 'AZ', 'NV', 'FL', 'NC'];
    const sources: NewParcelEvent['source'][] = ['mls', 'county', 'auction', 'direct'];

    return {
      id: `new-${Date.now()}`,
      state: states[Math.floor(Math.random() * states.length)],
      county: `${['Solar', 'Wind', 'Energy'][Math.floor(Math.random() * 3)]} County`,
      acreage: 100 + Math.floor(Math.random() * 500),
      overallScore: 70 + Math.floor(Math.random() * 25),
      solarCapacityMw: 20 + Math.floor(Math.random() * 100),
      viability: ['excellent', 'good', 'moderate'][Math.floor(Math.random() * 3)],
      detectedAt: new Date().toISOString(),
      source: sources[Math.floor(Math.random() * sources.length)],
    };
  }
}

export const parcelStream = new ParcelStream();
