// Real-Time Data Module
// Exports all real-time data services

export * from './iso-client';
export * from './parcel-alerts';
export * from './market-stream';
export * from './job-scheduler';

// ============================================================================
// INITIALIZATION
// ============================================================================

import { jobScheduler } from './job-scheduler';
import { getMarketStream } from './market-stream';

let initialized = false;

/**
 * Initialize real-time services
 * Call this once on application startup
 */
export function initializeRealTimeServices(): void {
  if (initialized) return;

  // Start job scheduler
  jobScheduler.start();

  // Note: Market stream should be started explicitly when needed
  // to avoid unnecessary API calls when not viewing live data

  initialized = true;
  console.log('[RealTime] Services initialized');
}

/**
 * Shutdown real-time services
 * Call this on application shutdown
 */
export function shutdownRealTimeServices(): void {
  if (!initialized) return;

  jobScheduler.stop();
  getMarketStream().stop();

  initialized = false;
  console.log('[RealTime] Services shutdown');
}

// ============================================================================
// DATA FRESHNESS INDICATORS
// ============================================================================

export interface DataFreshness {
  source: string;
  lastUpdated: string;
  ageMs: number;
  status: 'fresh' | 'stale' | 'expired';
}

const freshnessThresholds = {
  fresh: 5 * 60 * 1000,    // < 5 minutes
  stale: 30 * 60 * 1000,   // < 30 minutes
  // > 30 minutes = expired
};

export function getDataFreshness(lastUpdated: string): DataFreshness['status'] {
  const ageMs = Date.now() - new Date(lastUpdated).getTime();

  if (ageMs < freshnessThresholds.fresh) return 'fresh';
  if (ageMs < freshnessThresholds.stale) return 'stale';
  return 'expired';
}

// ============================================================================
// UTILITY: FORMAT UPDATE TIME
// ============================================================================

export function formatLastUpdated(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();

  if (diffMs < 60000) {
    return 'Just now';
  } else if (diffMs < 3600000) {
    const mins = Math.floor(diffMs / 60000);
    return `${mins} minute${mins !== 1 ? 's' : ''} ago`;
  } else if (diffMs < 86400000) {
    const hours = Math.floor(diffMs / 3600000);
    return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleDateString();
  }
}
