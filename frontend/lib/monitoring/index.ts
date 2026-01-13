// Enterprise-Grade Monitoring & Observability
// Performance tracking, error reporting, analytics, and health checks

// ============================================================================
// PERFORMANCE MONITORING
// ============================================================================

export interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: number;
  tags?: Record<string, string>;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private timers: Map<string, number> = new Map();
  private maxMetrics = 1000;

  startTimer(name: string): void {
    this.timers.set(name, performance.now());
  }

  endTimer(name: string, tags?: Record<string, string>): number {
    const startTime = this.timers.get(name);
    if (!startTime) {
      console.warn(`Timer '${name}' not found`);
      return 0;
    }

    const duration = performance.now() - startTime;
    this.timers.delete(name);

    this.recordMetric({
      name,
      value: duration,
      unit: 'ms',
      timestamp: Date.now(),
      tags,
    });

    return duration;
  }

  recordMetric(metric: PerformanceMetric): void {
    this.metrics.push(metric);

    // Keep only last N metrics
    if (this.metrics.length > this.maxMetrics) {
      this.metrics = this.metrics.slice(-this.maxMetrics);
    }

    // In production, send to metrics service
    if (process.env.NODE_ENV === 'production' && metric.value > 1000) {
      console.warn(`[PERF] Slow operation: ${metric.name} took ${metric.value}ms`);
    }
  }

  getMetrics(name?: string): PerformanceMetric[] {
    if (name) {
      return this.metrics.filter((m) => m.name === name);
    }
    return [...this.metrics];
  }

  getAverageMetric(name: string): number {
    const metrics = this.getMetrics(name);
    if (metrics.length === 0) return 0;
    return metrics.reduce((sum, m) => sum + m.value, 0) / metrics.length;
  }

  clear(): void {
    this.metrics = [];
    this.timers.clear();
  }
}

export const performanceMonitor = new PerformanceMonitor();

// ============================================================================
// WEB VITALS TRACKING
// ============================================================================

export interface WebVitalsMetric {
  id: string;
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  navigationType: string;
}

export function reportWebVitals(metric: WebVitalsMetric): void {
  const body = {
    id: metric.id,
    name: metric.name,
    value: metric.value,
    rating: metric.rating,
    delta: metric.delta,
    page: typeof window !== 'undefined' ? window.location.pathname : '',
    timestamp: Date.now(),
  };

  // In production, send to analytics service
  if (process.env.NODE_ENV === 'production') {
    // Use sendBeacon for reliability
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/analytics/vitals', JSON.stringify(body));
    }
  }

  // Log poor ratings
  if (metric.rating === 'poor') {
    console.warn(`[WebVitals] Poor ${metric.name}: ${metric.value}`);
  }
}

// ============================================================================
// ERROR TRACKING
// ============================================================================

export interface ErrorReport {
  id: string;
  message: string;
  stack?: string;
  componentStack?: string;
  url: string;
  timestamp: number;
  userAgent: string;
  metadata?: Record<string, unknown>;
}

class ErrorTracker {
  private errors: ErrorReport[] = [];
  private maxErrors = 100;

  reportError(error: Error, metadata?: Record<string, unknown>): string {
    const id = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const report: ErrorReport = {
      id,
      message: error.message,
      stack: error.stack,
      url: typeof window !== 'undefined' ? window.location.href : '',
      timestamp: Date.now(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
      metadata,
    };

    this.errors.push(report);

    // Keep only last N errors
    if (this.errors.length > this.maxErrors) {
      this.errors = this.errors.slice(-this.maxErrors);
    }

    // Log to console in development
    console.error('[ErrorTracker]', report);

    // In production, send to error tracking service
    if (process.env.NODE_ENV === 'production') {
      this.sendToService(report);
    }

    return id;
  }

  private async sendToService(report: ErrorReport): Promise<void> {
    try {
      await fetch('/api/analytics/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report),
      });
    } catch {
      // Silently fail - don't cause more errors
    }
  }

  getErrors(): ErrorReport[] {
    return [...this.errors];
  }

  clearErrors(): void {
    this.errors = [];
  }
}

export const errorTracker = new ErrorTracker();

// Global error handler
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    errorTracker.reportError(event.error || new Error(event.message), {
      type: 'uncaught',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error
      ? event.reason
      : new Error(String(event.reason));

    errorTracker.reportError(error, { type: 'unhandled_promise' });
  });
}

// ============================================================================
// ANALYTICS
// ============================================================================

export interface AnalyticsEvent {
  name: string;
  properties?: Record<string, unknown>;
  timestamp: number;
  sessionId: string;
  userId?: string;
}

class Analytics {
  private sessionId: string;
  private userId?: string;
  private queue: AnalyticsEvent[] = [];
  private flushInterval: number = 5000;
  private maxQueueSize: number = 100;

  constructor() {
    this.sessionId = this.generateSessionId();

    // Start flush interval
    if (typeof window !== 'undefined') {
      setInterval(() => this.flush(), this.flushInterval);

      // Flush on page unload
      window.addEventListener('beforeunload', () => this.flush());
    }
  }

  private generateSessionId(): string {
    return `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  setUserId(userId: string): void {
    this.userId = userId;
  }

  track(name: string, properties?: Record<string, unknown>): void {
    const event: AnalyticsEvent = {
      name,
      properties,
      timestamp: Date.now(),
      sessionId: this.sessionId,
      userId: this.userId,
    };

    this.queue.push(event);

    // Auto-flush if queue is full
    if (this.queue.length >= this.maxQueueSize) {
      this.flush();
    }
  }

  page(pageName: string, properties?: Record<string, unknown>): void {
    this.track('page_view', {
      page: pageName,
      path: typeof window !== 'undefined' ? window.location.pathname : '',
      referrer: typeof document !== 'undefined' ? document.referrer : '',
      ...properties,
    });
  }

  identify(userId: string, traits?: Record<string, unknown>): void {
    this.setUserId(userId);
    this.track('identify', { userId, ...traits });
  }

  private async flush(): Promise<void> {
    if (this.queue.length === 0) return;

    const events = [...this.queue];
    this.queue = [];

    // In production, send to analytics service
    if (process.env.NODE_ENV === 'production') {
      try {
        await fetch('/api/analytics/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ events }),
        });
      } catch {
        // Re-queue events on failure
        this.queue = [...events, ...this.queue].slice(0, this.maxQueueSize);
      }
    }
  }
}

export const analytics = new Analytics();

// ============================================================================
// HEALTH CHECK
// ============================================================================

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  uptime: number;
  checks: HealthCheck[];
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'warn' | 'fail';
  responseTime?: number;
  message?: string;
}

const startTime = Date.now();

export async function getHealthStatus(): Promise<HealthStatus> {
  const checks: HealthCheck[] = [];

  // Check API connectivity
  try {
    const apiStart = performance.now();
    const response = await fetch('/api/health', { method: 'GET' });
    const apiTime = performance.now() - apiStart;

    checks.push({
      name: 'api',
      status: response.ok ? 'pass' : 'fail',
      responseTime: apiTime,
      message: response.ok ? 'API is responding' : 'API error',
    });
  } catch (error) {
    checks.push({
      name: 'api',
      status: 'fail',
      message: 'API unreachable',
    });
  }

  // Check localStorage
  try {
    localStorage.setItem('health_check', 'ok');
    localStorage.removeItem('health_check');
    checks.push({
      name: 'storage',
      status: 'pass',
      message: 'Local storage available',
    });
  } catch {
    checks.push({
      name: 'storage',
      status: 'warn',
      message: 'Local storage unavailable',
    });
  }

  // Check memory (if available)
  if (typeof performance !== 'undefined' && 'memory' in performance) {
    const memory = (performance as any).memory;
    const usedPercent = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;
    checks.push({
      name: 'memory',
      status: usedPercent > 90 ? 'warn' : 'pass',
      message: `${usedPercent.toFixed(1)}% memory used`,
    });
  }

  // Determine overall status
  const hasFailure = checks.some((c) => c.status === 'fail');
  const hasWarning = checks.some((c) => c.status === 'warn');

  return {
    status: hasFailure ? 'unhealthy' : hasWarning ? 'degraded' : 'healthy',
    timestamp: new Date().toISOString(),
    version: '3.0.0',
    uptime: Date.now() - startTime,
    checks,
  };
}

// ============================================================================
// FEATURE FLAGS (Simple implementation)
// ============================================================================

const defaultFeatureFlags: Record<string, boolean> = {
  'ai-site-scout': true,
  'financial-modeler': true,
  'market-intelligence': true,
  'export-pdf': true,
  'compare-mode': true,
  'dark-mode': true,
  'beta-features': false,
};

let featureFlags = { ...defaultFeatureFlags };

export function isFeatureEnabled(feature: string): boolean {
  return featureFlags[feature] ?? false;
}

export function setFeatureFlags(flags: Record<string, boolean>): void {
  featureFlags = { ...featureFlags, ...flags };
}

export function getFeatureFlags(): Record<string, boolean> {
  return { ...featureFlags };
}
