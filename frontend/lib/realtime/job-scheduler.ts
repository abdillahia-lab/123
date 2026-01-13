// Background Job Scheduler
// Manages periodic data refresh and processing tasks

import { alertService } from './parcel-alerts';
import { isoClient } from './iso-client';

// ============================================================================
// TYPES
// ============================================================================

export type JobPriority = 'critical' | 'high' | 'normal' | 'low';

export interface JobDefinition {
  id: string;
  name: string;
  description: string;
  handler: () => Promise<void>;
  schedule: {
    type: 'interval' | 'cron';
    value: number | string; // milliseconds for interval, cron string for cron
  };
  priority: JobPriority;
  timeout: number;
  retries: number;
  enabled: boolean;
}

export interface JobRun {
  jobId: string;
  startedAt: string;
  completedAt?: string;
  status: 'running' | 'completed' | 'failed' | 'timeout';
  error?: string;
  duration?: number;
}

export interface JobStats {
  jobId: string;
  totalRuns: number;
  successfulRuns: number;
  failedRuns: number;
  avgDuration: number;
  lastRun?: JobRun;
  nextRun?: string;
}

// ============================================================================
// JOB SCHEDULER CLASS
// ============================================================================

class JobScheduler {
  private jobs = new Map<string, JobDefinition>();
  private intervals = new Map<string, ReturnType<typeof setInterval>>();
  private runHistory = new Map<string, JobRun[]>();
  private isRunning = false;

  // Register a new job
  registerJob(job: JobDefinition): void {
    this.jobs.set(job.id, job);
    this.runHistory.set(job.id, []);
    console.log(`[JobScheduler] Registered job: ${job.name}`);
  }

  // Start the scheduler
  start(): void {
    if (this.isRunning) return;
    this.isRunning = true;

    for (const [id, job] of this.jobs) {
      if (job.enabled && job.schedule.type === 'interval') {
        this.startJob(id);
      }
    }

    console.log('[JobScheduler] Started');
  }

  // Stop the scheduler
  stop(): void {
    if (!this.isRunning) return;
    this.isRunning = false;

    for (const [id] of this.intervals) {
      this.stopJob(id);
    }

    console.log('[JobScheduler] Stopped');
  }

  // Start a specific job
  private startJob(jobId: string): void {
    const job = this.jobs.get(jobId);
    if (!job || job.schedule.type !== 'interval') return;

    // Run immediately first
    this.runJob(jobId);

    // Then schedule periodic runs
    const interval = setInterval(() => {
      this.runJob(jobId);
    }, job.schedule.value as number);

    this.intervals.set(jobId, interval);
  }

  // Stop a specific job
  private stopJob(jobId: string): void {
    const interval = this.intervals.get(jobId);
    if (interval) {
      clearInterval(interval);
      this.intervals.delete(jobId);
    }
  }

  // Run a job
  async runJob(jobId: string): Promise<JobRun> {
    const job = this.jobs.get(jobId);
    if (!job) {
      throw new Error(`Job not found: ${jobId}`);
    }

    const run: JobRun = {
      jobId,
      startedAt: new Date().toISOString(),
      status: 'running',
    };

    try {
      // Run with timeout
      await Promise.race([
        job.handler(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Job timeout')), job.timeout)
        ),
      ]);

      run.status = 'completed';
    } catch (error) {
      run.status = error instanceof Error && error.message === 'Job timeout' ? 'timeout' : 'failed';
      run.error = error instanceof Error ? error.message : 'Unknown error';

      console.error(`[JobScheduler] Job failed: ${job.name}`, error);
    }

    run.completedAt = new Date().toISOString();
    run.duration = new Date(run.completedAt).getTime() - new Date(run.startedAt).getTime();

    // Store run history
    const history = this.runHistory.get(jobId) || [];
    history.unshift(run);
    this.runHistory.set(jobId, history.slice(0, 100)); // Keep last 100 runs

    return run;
  }

  // Get job stats
  getJobStats(jobId: string): JobStats | null {
    const job = this.jobs.get(jobId);
    const history = this.runHistory.get(jobId);

    if (!job || !history) return null;

    const successfulRuns = history.filter(r => r.status === 'completed').length;
    const failedRuns = history.filter(r => r.status === 'failed' || r.status === 'timeout').length;
    const durations = history.filter(r => r.duration).map(r => r.duration!);
    const avgDuration = durations.length > 0
      ? durations.reduce((a, b) => a + b, 0) / durations.length
      : 0;

    let nextRun: string | undefined;
    if (job.schedule.type === 'interval' && this.intervals.has(jobId)) {
      nextRun = new Date(Date.now() + (job.schedule.value as number)).toISOString();
    }

    return {
      jobId,
      totalRuns: history.length,
      successfulRuns,
      failedRuns,
      avgDuration,
      lastRun: history[0],
      nextRun,
    };
  }

  // Get all jobs with stats
  getAllJobStats(): JobStats[] {
    return Array.from(this.jobs.keys())
      .map(id => this.getJobStats(id))
      .filter((s): s is JobStats => s !== null);
  }

  // Enable/disable a job
  setJobEnabled(jobId: string, enabled: boolean): void {
    const job = this.jobs.get(jobId);
    if (!job) return;

    job.enabled = enabled;

    if (enabled && this.isRunning && !this.intervals.has(jobId)) {
      this.startJob(jobId);
    } else if (!enabled && this.intervals.has(jobId)) {
      this.stopJob(jobId);
    }
  }

  // Trigger a job manually
  async triggerJob(jobId: string): Promise<JobRun> {
    return this.runJob(jobId);
  }
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

export const jobScheduler = new JobScheduler();

// ============================================================================
// PREDEFINED JOBS
// ============================================================================

// Job: Refresh ISO grid data
jobScheduler.registerJob({
  id: 'refresh-iso-data',
  name: 'Refresh ISO Grid Data',
  description: 'Fetches latest LMP and load data from all ISO regions',
  handler: async () => {
    const regions = ['CAISO', 'ERCOT', 'PJM', 'MISO', 'SPP'] as const;
    for (const region of regions) {
      await isoClient.getLMP(region);
      await isoClient.getGridLoad(region);
    }
  },
  schedule: { type: 'interval', value: 5 * 60 * 1000 }, // Every 5 minutes
  priority: 'high',
  timeout: 60000,
  retries: 3,
  enabled: true,
});

// Job: Refresh interconnection queues
jobScheduler.registerJob({
  id: 'refresh-queues',
  name: 'Refresh Interconnection Queues',
  description: 'Updates interconnection queue data from all ISOs',
  handler: async () => {
    const regions = ['CAISO', 'ERCOT', 'PJM', 'MISO', 'SPP'] as const;
    for (const region of regions) {
      await isoClient.getInterconnectionQueue(region);
    }
  },
  schedule: { type: 'interval', value: 60 * 60 * 1000 }, // Every hour
  priority: 'normal',
  timeout: 120000,
  retries: 2,
  enabled: true,
});

// Job: Check new parcels against alert subscriptions
jobScheduler.registerJob({
  id: 'check-parcel-alerts',
  name: 'Check Parcel Alerts',
  description: 'Evaluates new parcels against user alert subscriptions',
  handler: async () => {
    // Get all active subscriptions
    // In production, this would fetch from database
    // For demo, we simulate checking a few subscriptions
    console.log('[Job] Checking parcel alerts...');
  },
  schedule: { type: 'interval', value: 15 * 60 * 1000 }, // Every 15 minutes
  priority: 'high',
  timeout: 60000,
  retries: 2,
  enabled: true,
});

// Job: Generate daily digest emails
jobScheduler.registerJob({
  id: 'daily-digest',
  name: 'Generate Daily Digest',
  description: 'Creates and sends daily digest emails to subscribers',
  handler: async () => {
    console.log('[Job] Generating daily digests...');
    // In production, this would:
    // 1. Find all subscriptions with frequency='daily'
    // 2. Generate digest for each
    // 3. Queue emails for sending
  },
  schedule: { type: 'interval', value: 24 * 60 * 60 * 1000 }, // Daily
  priority: 'normal',
  timeout: 300000,
  retries: 1,
  enabled: true,
});

// Job: Refresh parcel data from external sources
jobScheduler.registerJob({
  id: 'refresh-parcel-data',
  name: 'Refresh Parcel Data',
  description: 'Updates parcel data from county assessors and MLS feeds',
  handler: async () => {
    console.log('[Job] Refreshing parcel data from external sources...');
    // In production, this would:
    // 1. Poll MLS APIs for new listings
    // 2. Check county recorder APIs for ownership changes
    // 3. Update local database with new/changed parcels
  },
  schedule: { type: 'interval', value: 6 * 60 * 60 * 1000 }, // Every 6 hours
  priority: 'normal',
  timeout: 600000,
  retries: 2,
  enabled: true,
});

// Job: Update solar/weather forecasts
jobScheduler.registerJob({
  id: 'update-solar-forecasts',
  name: 'Update Solar Forecasts',
  description: 'Fetches latest solar irradiance and weather forecast data',
  handler: async () => {
    console.log('[Job] Updating solar/weather forecasts...');
    // In production, this would call:
    // - NREL NSRDB/PVWatts API
    // - OpenWeather or Tomorrow.io API
    // - Update cached forecasts
  },
  schedule: { type: 'interval', value: 3 * 60 * 60 * 1000 }, // Every 3 hours
  priority: 'normal',
  timeout: 120000,
  retries: 3,
  enabled: true,
});

// Job: Clean up old cache entries
jobScheduler.registerJob({
  id: 'cache-cleanup',
  name: 'Cache Cleanup',
  description: 'Removes expired cache entries to free memory',
  handler: async () => {
    console.log('[Job] Cleaning up expired cache entries...');
    // In production, this would iterate through caches and remove expired entries
  },
  schedule: { type: 'interval', value: 60 * 60 * 1000 }, // Every hour
  priority: 'low',
  timeout: 30000,
  retries: 1,
  enabled: true,
});

// Job: Update market prices (RECs, PPAs)
jobScheduler.registerJob({
  id: 'update-market-prices',
  name: 'Update Market Prices',
  description: 'Fetches latest REC and PPA market prices',
  handler: async () => {
    console.log('[Job] Updating market prices...');
    // In production, this would:
    // 1. Fetch REC prices from trading platforms
    // 2. Update PPA benchmark prices
    // 3. Store in database/cache
  },
  schedule: { type: 'interval', value: 24 * 60 * 60 * 1000 }, // Daily
  priority: 'normal',
  timeout: 120000,
  retries: 2,
  enabled: true,
});
