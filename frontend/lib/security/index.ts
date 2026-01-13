// Enterprise-Grade Security Module
// Implements OWASP Top 10 protections, rate limiting, input sanitization

// ============================================================================
// CSRF TOKEN MANAGEMENT
// ============================================================================

const CSRF_TOKEN_KEY = 'csrf_token';
const CSRF_HEADER = 'X-CSRF-Token';

export function generateCsrfToken(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export function getCsrfToken(): string {
  if (typeof window === 'undefined') return '';

  let token = sessionStorage.getItem(CSRF_TOKEN_KEY);
  if (!token) {
    token = generateCsrfToken();
    sessionStorage.setItem(CSRF_TOKEN_KEY, token);
  }
  return token;
}

export function getCsrfHeaders(): Record<string, string> {
  return { [CSRF_HEADER]: getCsrfToken() };
}

// ============================================================================
// INPUT SANITIZATION (XSS Prevention)
// ============================================================================

const HTML_ENTITIES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#x27;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;',
};

export function escapeHtml(str: string): string {
  return str.replace(/[&<>"'`=/]/g, (char) => HTML_ENTITIES[char] || char);
}

export function sanitizeInput(input: string): string {
  return input
    .trim()
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .slice(0, 10000); // Limit length
}

export function sanitizeUrl(url: string): string {
  try {
    const parsed = new URL(url);
    // Only allow http, https protocols
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return '';
    }
    return parsed.toString();
  } catch {
    return '';
  }
}

export function sanitizeFilename(filename: string): string {
  return filename
    .replace(/[^a-zA-Z0-9._-]/g, '_')
    .replace(/\.{2,}/g, '.')
    .slice(0, 255);
}

// ============================================================================
// RATE LIMITING (Client-Side)
// ============================================================================

interface RateLimitConfig {
  maxRequests: number;
  windowMs: number;
}

class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  private config: RateLimitConfig;

  constructor(config: RateLimitConfig) {
    this.config = config;
  }

  checkLimit(key: string): { allowed: boolean; remaining: number; resetIn: number } {
    const now = Date.now();
    const windowStart = now - this.config.windowMs;

    // Get or create request timestamps for this key
    let timestamps = this.requests.get(key) || [];

    // Filter out old timestamps
    timestamps = timestamps.filter((ts) => ts > windowStart);

    const remaining = Math.max(0, this.config.maxRequests - timestamps.length);
    const oldestTimestamp = timestamps[0] || now;
    const resetIn = Math.max(0, oldestTimestamp + this.config.windowMs - now);

    if (timestamps.length >= this.config.maxRequests) {
      return { allowed: false, remaining: 0, resetIn };
    }

    // Add current request
    timestamps.push(now);
    this.requests.set(key, timestamps);

    return { allowed: true, remaining: remaining - 1, resetIn };
  }

  reset(key: string): void {
    this.requests.delete(key);
  }

  clear(): void {
    this.requests.clear();
  }
}

// Global rate limiters
export const apiRateLimiter = new RateLimiter({ maxRequests: 100, windowMs: 60000 });
export const authRateLimiter = new RateLimiter({ maxRequests: 5, windowMs: 300000 });
export const searchRateLimiter = new RateLimiter({ maxRequests: 30, windowMs: 60000 });

// ============================================================================
// CONTENT SECURITY
// ============================================================================

export function isValidJson(str: string): boolean {
  try {
    JSON.parse(str);
    return true;
  } catch {
    return false;
  }
}

export function safeJsonParse<T>(str: string, fallback: T): T {
  try {
    return JSON.parse(str) as T;
  } catch {
    return fallback;
  }
}

// ============================================================================
// SECURE STORAGE
// ============================================================================

const STORAGE_PREFIX = 'tj_';
const ENCRYPTION_KEY = 'terrajinki_secure_storage_v3'; // In production, use proper key management

export function secureSet(key: string, value: unknown): void {
  if (typeof window === 'undefined') return;

  try {
    const serialized = JSON.stringify(value);
    // Simple obfuscation (in production, use proper encryption)
    const encoded = btoa(serialized);
    localStorage.setItem(`${STORAGE_PREFIX}${key}`, encoded);
  } catch (error) {
    console.error('Failed to save to secure storage:', error);
  }
}

export function secureGet<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;

  try {
    const encoded = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
    if (!encoded) return fallback;

    const serialized = atob(encoded);
    return JSON.parse(serialized) as T;
  } catch {
    return fallback;
  }
}

export function secureRemove(key: string): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(`${STORAGE_PREFIX}${key}`);
}

export function secureClear(): void {
  if (typeof window === 'undefined') return;

  const keysToRemove: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith(STORAGE_PREFIX)) {
      keysToRemove.push(key);
    }
  }
  keysToRemove.forEach((key) => localStorage.removeItem(key));
}

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes
const SESSION_ACTIVITY_KEY = 'last_activity';

export function updateSessionActivity(): void {
  secureSet(SESSION_ACTIVITY_KEY, Date.now());
}

export function isSessionValid(): boolean {
  const lastActivity = secureGet<number>(SESSION_ACTIVITY_KEY, 0);
  return Date.now() - lastActivity < SESSION_TIMEOUT_MS;
}

export function invalidateSession(): void {
  secureRemove(SESSION_ACTIVITY_KEY);
  secureClear();
}

// ============================================================================
// PERMISSION CHECKING
// ============================================================================

export type Permission =
  | 'parcel:read'
  | 'parcel:write'
  | 'parcel:delete'
  | 'project:read'
  | 'project:write'
  | 'project:delete'
  | 'report:generate'
  | 'report:export'
  | 'settings:read'
  | 'settings:write'
  | 'admin:full';

const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  admin: ['admin:full'],
  analyst: [
    'parcel:read',
    'parcel:write',
    'project:read',
    'project:write',
    'report:generate',
    'report:export',
    'settings:read',
  ],
  developer: [
    'parcel:read',
    'project:read',
    'project:write',
    'report:generate',
  ],
  viewer: ['parcel:read', 'project:read'],
};

export function hasPermission(role: string, permission: Permission): boolean {
  const permissions = ROLE_PERMISSIONS[role] || [];

  // Admin has all permissions
  if (permissions.includes('admin:full')) {
    return true;
  }

  return permissions.includes(permission);
}

export function getPermissions(role: string): Permission[] {
  const permissions = ROLE_PERMISSIONS[role] || [];

  if (permissions.includes('admin:full')) {
    return Object.values(ROLE_PERMISSIONS).flat();
  }

  return permissions;
}

// ============================================================================
// REQUEST SIGNING (For webhook verification)
// ============================================================================

export async function signPayload(payload: string, secret: string): Promise<string> {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(payload));

  return Array.from(new Uint8Array(signature))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export async function verifySignature(
  payload: string,
  signature: string,
  secret: string
): Promise<boolean> {
  const expectedSignature = await signPayload(payload, secret);
  return signature === expectedSignature;
}

// ============================================================================
// SECURE HEADERS (For Next.js middleware)
// ============================================================================

export const SECURITY_HEADERS = {
  'Content-Security-Policy': [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // Required for Next.js
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https: blob:",
    "font-src 'self' data:",
    "connect-src 'self' https://*.googleapis.com https://*.openstreetmap.org",
    "frame-ancestors 'none'",
    "form-action 'self'",
    "base-uri 'self'",
  ].join('; '),
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(self)',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
};
