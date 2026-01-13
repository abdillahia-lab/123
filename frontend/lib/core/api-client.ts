// Enterprise-Grade API Client
// Features: Retry logic, caching, circuit breaker, request deduplication

import {
  AppError,
  RateLimitError,
  ExternalServiceError,
  CircuitBreaker,
  normalizeError,
} from './errors';
import { ApiResponse, ErrorCode } from './types';

// ============================================================================
// CONFIGURATION
// ============================================================================

export interface ApiClientConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  retryDelay: number;
  enableCache: boolean;
  cacheTtlMs: number;
  enableDeduplication: boolean;
  headers?: Record<string, string>;
}

const defaultConfig: ApiClientConfig = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || '',
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
  enableCache: true,
  cacheTtlMs: 60000, // 1 minute
  enableDeduplication: true,
};

// ============================================================================
// CACHE IMPLEMENTATION
// ============================================================================

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class ApiCache {
  private cache = new Map<string, CacheEntry<unknown>>();
  private maxSize = 1000;

  set<T>(key: string, data: T, ttl: number): void {
    // Evict old entries if cache is full
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      if (oldestKey) this.cache.delete(oldestKey);
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  invalidate(pattern?: string): void {
    if (!pattern) {
      this.cache.clear();
      return;
    }

    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }

  size(): number {
    return this.cache.size;
  }
}

// ============================================================================
// REQUEST DEDUPLICATION
// ============================================================================

class RequestDeduplicator {
  private pending = new Map<string, Promise<unknown>>();

  async dedupe<T>(key: string, fn: () => Promise<T>): Promise<T> {
    const existing = this.pending.get(key);
    if (existing) {
      return existing as Promise<T>;
    }

    const promise = fn().finally(() => {
      this.pending.delete(key);
    });

    this.pending.set(key, promise);
    return promise;
  }
}

// ============================================================================
// API CLIENT CLASS
// ============================================================================

export class ApiClient {
  private config: ApiClientConfig;
  private cache: ApiCache;
  private deduplicator: RequestDeduplicator;
  private circuitBreaker: CircuitBreaker;
  private requestId = 0;

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = { ...defaultConfig, ...config };
    this.cache = new ApiCache();
    this.deduplicator = new RequestDeduplicator();
    this.circuitBreaker = new CircuitBreaker('api', {
      failureThreshold: 5,
      resetTimeoutMs: 30000,
      halfOpenRequests: 3,
    });
  }

  // ==========================================================================
  // PUBLIC METHODS
  // ==========================================================================

  async get<T>(
    path: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const cacheKey = this.getCacheKey('GET', path, options.params);

    // Check cache first
    if (this.config.enableCache && !options.skipCache) {
      const cached = this.cache.get<T>(cacheKey);
      if (cached) {
        return cached;
      }
    }

    // Deduplicate concurrent requests
    if (this.config.enableDeduplication) {
      return this.deduplicator.dedupe(cacheKey, () =>
        this.executeRequest<T>('GET', path, options)
      );
    }

    return this.executeRequest<T>('GET', path, options);
  }

  async post<T>(
    path: string,
    body?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.executeRequest<T>('POST', path, { ...options, body });
  }

  async put<T>(
    path: string,
    body?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.executeRequest<T>('PUT', path, { ...options, body });
  }

  async patch<T>(
    path: string,
    body?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.executeRequest<T>('PATCH', path, { ...options, body });
  }

  async delete<T>(
    path: string,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.executeRequest<T>('DELETE', path, options);
  }

  invalidateCache(pattern?: string): void {
    this.cache.invalidate(pattern);
  }

  // ==========================================================================
  // PRIVATE METHODS
  // ==========================================================================

  private async executeRequest<T>(
    method: string,
    path: string,
    options: RequestOptions
  ): Promise<T> {
    const requestId = `req_${++this.requestId}_${Date.now()}`;

    return this.circuitBreaker.execute(async () => {
      return this.fetchWithRetry<T>(method, path, options, requestId);
    });
  }

  private async fetchWithRetry<T>(
    method: string,
    path: string,
    options: RequestOptions,
    requestId: string,
    attempt: number = 1
  ): Promise<T> {
    const url = this.buildUrl(path, options.params);
    const controller = new AbortController();
    const timeoutId = setTimeout(
      () => controller.abort(),
      options.timeout || this.config.timeout
    );

    try {
      const response = await fetch(url, {
        method,
        headers: this.buildHeaders(options.headers),
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        await this.handleErrorResponse(response, requestId);
      }

      const data = await response.json();

      // Cache successful GET requests
      if (method === 'GET' && this.config.enableCache && !options.skipCache) {
        const cacheKey = this.getCacheKey('GET', path, options.params);
        this.cache.set(cacheKey, data, this.config.cacheTtlMs);
      }

      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      // Handle abort (timeout)
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new AppError(
          ErrorCode.SERVICE_UNAVAILABLE,
          'Request timeout',
          408,
          true,
          { path, timeout: this.config.timeout }
        );
      }

      // Retry logic for transient errors
      if (this.shouldRetry(error, attempt)) {
        const delay = this.calculateRetryDelay(attempt);
        await this.sleep(delay);
        return this.fetchWithRetry<T>(method, path, options, requestId, attempt + 1);
      }

      throw normalizeError(error);
    }
  }

  private buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
    const base = this.config.baseUrl || '';
    const url = new URL(path.startsWith('/') ? path : `/${path}`, base || window.location.origin);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return url.toString();
  }

  private buildHeaders(customHeaders?: Record<string, string>): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Client-Version': '3.0.0',
      'X-Request-Time': new Date().toISOString(),
      ...this.config.headers,
      ...customHeaders,
    };
  }

  private getCacheKey(
    method: string,
    path: string,
    params?: Record<string, unknown>
  ): string {
    const paramString = params ? JSON.stringify(params) : '';
    return `${method}:${path}:${paramString}`;
  }

  private async handleErrorResponse(response: Response, requestId: string): Promise<never> {
    let errorData: { message?: string; code?: string } = {};

    try {
      errorData = await response.json();
    } catch {
      // Response body is not JSON
    }

    const message = errorData.message || response.statusText || 'Request failed';

    switch (response.status) {
      case 400:
        throw new AppError(ErrorCode.VALIDATION_ERROR, message, 400, true);
      case 401:
        throw new AppError(ErrorCode.UNAUTHORIZED, message, 401, true);
      case 403:
        throw new AppError(ErrorCode.FORBIDDEN, message, 403, true);
      case 404:
        throw new AppError(ErrorCode.NOT_FOUND, message, 404, true);
      case 409:
        throw new AppError(ErrorCode.CONFLICT, message, 409, true);
      case 429:
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        throw new RateLimitError(retryAfter);
      case 503:
        throw new ExternalServiceError('API');
      default:
        throw new AppError(
          ErrorCode.INTERNAL_ERROR,
          message,
          response.status,
          response.status >= 500
        );
    }
  }

  private shouldRetry(error: unknown, attempt: number): boolean {
    if (attempt >= this.config.retries) return false;

    // Only retry on network errors or 5xx errors
    if (error instanceof AppError) {
      return error.statusCode >= 500 || error.code === ErrorCode.SERVICE_UNAVAILABLE;
    }

    return error instanceof TypeError; // Network error
  }

  private calculateRetryDelay(attempt: number): number {
    // Exponential backoff with jitter
    const base = this.config.retryDelay * Math.pow(2, attempt - 1);
    const jitter = Math.random() * 1000;
    return Math.min(base + jitter, 30000);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ============================================================================
// REQUEST OPTIONS INTERFACE
// ============================================================================

export interface RequestOptions {
  params?: Record<string, string | number | boolean | undefined>;
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
  skipCache?: boolean;
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

let apiClientInstance: ApiClient | null = null;

export function getApiClient(): ApiClient {
  if (!apiClientInstance) {
    apiClientInstance = new ApiClient();
  }
  return apiClientInstance;
}

export function createApiClient(config: Partial<ApiClientConfig>): ApiClient {
  return new ApiClient(config);
}

// ============================================================================
// CONVENIENCE FUNCTIONS
// ============================================================================

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    getApiClient().get<T>(path, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    getApiClient().post<T>(path, body, options),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    getApiClient().put<T>(path, body, options),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    getApiClient().patch<T>(path, body, options),
  delete: <T>(path: string, options?: RequestOptions) =>
    getApiClient().delete<T>(path, options),
  invalidateCache: (pattern?: string) =>
    getApiClient().invalidateCache(pattern),
};
