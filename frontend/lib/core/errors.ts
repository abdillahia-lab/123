// Enterprise-Grade Error Handling System
// Provides consistent error management across the application

import { ErrorCode, DomainError, createError } from './types';

// ============================================================================
// CUSTOM ERROR CLASSES
// ============================================================================

export class AppError extends Error {
  public readonly code: ErrorCode;
  public readonly statusCode: number;
  public readonly isOperational: boolean;
  public readonly details?: Record<string, unknown>;
  public readonly timestamp: string;
  public readonly requestId?: string;

  constructor(
    code: ErrorCode,
    message: string,
    statusCode: number = 500,
    isOperational: boolean = true,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AppError';
    this.code = code;
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    this.details = details;
    this.timestamp = new Date().toISOString();

    // Capture stack trace
    Error.captureStackTrace(this, this.constructor);
  }

  toJSON(): DomainError {
    return {
      code: this.code,
      message: this.message,
      details: this.details,
      timestamp: this.timestamp,
      requestId: this.requestId,
      stack: process.env.NODE_ENV === 'development' ? this.stack : undefined,
    };
  }
}

// ============================================================================
// SPECIFIC ERROR TYPES
// ============================================================================

export class ValidationError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(ErrorCode.VALIDATION_ERROR, message, 400, true, details);
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends AppError {
  constructor(message: string = 'Authentication required') {
    super(ErrorCode.UNAUTHORIZED, message, 401, true);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends AppError {
  constructor(message: string = 'Insufficient permissions') {
    super(ErrorCode.FORBIDDEN, message, 403, true);
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id?: string) {
    const message = id
      ? `${resource} with ID '${id}' not found`
      : `${resource} not found`;
    super(ErrorCode.NOT_FOUND, message, 404, true, { resource, id });
    this.name = 'NotFoundError';
  }
}

export class ConflictError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(ErrorCode.CONFLICT, message, 409, true, details);
    this.name = 'ConflictError';
  }
}

export class RateLimitError extends AppError {
  public readonly retryAfter: number;

  constructor(retryAfter: number = 60) {
    super(
      ErrorCode.RATE_LIMITED,
      `Rate limit exceeded. Please retry after ${retryAfter} seconds`,
      429,
      true,
      { retryAfter }
    );
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

export class ExternalServiceError extends AppError {
  constructor(service: string, originalError?: Error) {
    super(
      ErrorCode.EXTERNAL_SERVICE_ERROR,
      `External service '${service}' is unavailable`,
      503,
      true,
      {
        service,
        originalError: originalError?.message,
      }
    );
    this.name = 'ExternalServiceError';
  }
}

// ============================================================================
// ERROR HANDLING UTILITIES
// ============================================================================

export function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
}

export function isOperationalError(error: unknown): boolean {
  if (isAppError(error)) {
    return error.isOperational;
  }
  return false;
}

export function normalizeError(error: unknown): AppError {
  if (isAppError(error)) {
    return error;
  }

  if (error instanceof Error) {
    return new AppError(
      ErrorCode.INTERNAL_ERROR,
      error.message,
      500,
      false,
      { originalError: error.name }
    );
  }

  return new AppError(
    ErrorCode.INTERNAL_ERROR,
    'An unexpected error occurred',
    500,
    false
  );
}

export function getHttpStatusCode(error: unknown): number {
  if (isAppError(error)) {
    return error.statusCode;
  }
  return 500;
}

// ============================================================================
// ERROR RESPONSE FORMATTER
// ============================================================================

export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    timestamp: string;
    requestId?: string;
  };
  meta: {
    version: string;
    documentation?: string;
  };
}

export function formatErrorResponse(
  error: AppError,
  requestId?: string
): ErrorResponse {
  return {
    success: false,
    error: {
      code: error.code,
      message: error.message,
      details: process.env.NODE_ENV === 'development' ? error.details : undefined,
      timestamp: error.timestamp,
      requestId,
    },
    meta: {
      version: '3.0.0',
      documentation: 'https://docs.terrajinki.com/errors',
    },
  };
}

// ============================================================================
// ASYNC ERROR WRAPPER
// ============================================================================

export type AsyncFunction<T> = () => Promise<T>;

export async function tryCatch<T>(
  fn: AsyncFunction<T>,
  fallback?: T
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (fallback !== undefined) {
      console.error('Error caught, using fallback:', error);
      return fallback;
    }
    throw normalizeError(error);
  }
}

export function withErrorHandling<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  errorHandler?: (error: AppError) => void
): T {
  return (async (...args: Parameters<T>) => {
    try {
      return await fn(...args);
    } catch (error) {
      const appError = normalizeError(error);
      if (errorHandler) {
        errorHandler(appError);
      }
      throw appError;
    }
  }) as T;
}

// ============================================================================
// ERROR LOGGING
// ============================================================================

export interface ErrorLogEntry {
  timestamp: string;
  level: 'error' | 'warn' | 'info';
  code: string;
  message: string;
  stack?: string;
  details?: Record<string, unknown>;
  context?: {
    requestId?: string;
    userId?: string;
    path?: string;
    method?: string;
  };
}

export function logError(
  error: AppError,
  context?: ErrorLogEntry['context']
): void {
  const entry: ErrorLogEntry = {
    timestamp: new Date().toISOString(),
    level: error.statusCode >= 500 ? 'error' : 'warn',
    code: error.code,
    message: error.message,
    stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
    details: error.details,
    context,
  };

  // In production, this would send to a logging service
  if (entry.level === 'error') {
    console.error('[ERROR]', JSON.stringify(entry, null, 2));
  } else {
    console.warn('[WARN]', JSON.stringify(entry, null, 2));
  }
}

// ============================================================================
// CIRCUIT BREAKER PATTERN
// ============================================================================

export interface CircuitBreakerOptions {
  failureThreshold: number;
  resetTimeoutMs: number;
  halfOpenRequests: number;
}

export enum CircuitState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN',
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount: number = 0;
  private lastFailureTime?: number;
  private halfOpenSuccesses: number = 0;

  constructor(
    private readonly name: string,
    private readonly options: CircuitBreakerOptions = {
      failureThreshold: 5,
      resetTimeoutMs: 30000,
      halfOpenRequests: 3,
    }
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.state = CircuitState.HALF_OPEN;
        this.halfOpenSuccesses = 0;
      } else {
        throw new ExternalServiceError(this.name);
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private shouldAttemptReset(): boolean {
    if (!this.lastFailureTime) return true;
    return Date.now() - this.lastFailureTime >= this.options.resetTimeoutMs;
  }

  private onSuccess(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      this.halfOpenSuccesses++;
      if (this.halfOpenSuccesses >= this.options.halfOpenRequests) {
        this.reset();
      }
    } else {
      this.failureCount = 0;
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === CircuitState.HALF_OPEN) {
      this.state = CircuitState.OPEN;
    } else if (this.failureCount >= this.options.failureThreshold) {
      this.state = CircuitState.OPEN;
      console.warn(`[CircuitBreaker] ${this.name} opened after ${this.failureCount} failures`);
    }
  }

  private reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.halfOpenSuccesses = 0;
    console.info(`[CircuitBreaker] ${this.name} reset to closed state`);
  }

  getState(): CircuitState {
    return this.state;
  }
}
