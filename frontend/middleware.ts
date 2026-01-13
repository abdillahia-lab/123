// Next.js Middleware for Security & Monitoring
// Implements secure headers, rate limiting, and request logging

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// ============================================================================
// SECURITY HEADERS
// ============================================================================

const securityHeaders = {
  'Content-Security-Policy': [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https: blob:",
    "font-src 'self' data:",
    "connect-src 'self' https://*.googleapis.com https://*.openstreetmap.org https://*.maptiler.com",
    "frame-ancestors 'none'",
    "form-action 'self'",
    "base-uri 'self'",
  ].join('; '),
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(self)',
};

// ============================================================================
// RATE LIMITING (In-Memory for demo, use Redis in production)
// ============================================================================

const rateLimitMap = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT_MAX = 100;
const RATE_LIMIT_WINDOW_MS = 60000;

function checkRateLimit(ip: string): { allowed: boolean; remaining: number } {
  const now = Date.now();
  const record = rateLimitMap.get(ip);

  if (!record || now > record.resetTime) {
    rateLimitMap.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW_MS });
    return { allowed: true, remaining: RATE_LIMIT_MAX - 1 };
  }

  if (record.count >= RATE_LIMIT_MAX) {
    return { allowed: false, remaining: 0 };
  }

  record.count++;
  return { allowed: true, remaining: RATE_LIMIT_MAX - record.count };
}

// Clean up old entries periodically
setInterval(() => {
  const now = Date.now();
  for (const [ip, record] of rateLimitMap.entries()) {
    if (now > record.resetTime) {
      rateLimitMap.delete(ip);
    }
  }
}, 60000);

// ============================================================================
// REQUEST LOGGING
// ============================================================================

function logRequest(request: NextRequest, status: number, duration: number): void {
  const log = {
    timestamp: new Date().toISOString(),
    method: request.method,
    path: request.nextUrl.pathname,
    status,
    duration: `${duration}ms`,
    userAgent: request.headers.get('user-agent')?.slice(0, 100),
    ip: request.ip || request.headers.get('x-forwarded-for') || 'unknown',
  };

  // In production, send to logging service
  if (process.env.NODE_ENV === 'production') {
    console.log(JSON.stringify(log));
  }
}

// ============================================================================
// MIDDLEWARE FUNCTION
// ============================================================================

export function middleware(request: NextRequest) {
  const startTime = Date.now();
  const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Get client IP
  const ip = request.ip || request.headers.get('x-forwarded-for') || 'unknown';

  // Check rate limit for API routes
  if (request.nextUrl.pathname.startsWith('/api/')) {
    const { allowed, remaining } = checkRateLimit(ip);

    if (!allowed) {
      return new NextResponse(
        JSON.stringify({
          success: false,
          error: {
            code: 'RATE_LIMITED',
            message: 'Too many requests. Please try again later.',
          },
        }),
        {
          status: 429,
          headers: {
            'Content-Type': 'application/json',
            'Retry-After': '60',
            'X-RateLimit-Limit': RATE_LIMIT_MAX.toString(),
            'X-RateLimit-Remaining': '0',
            'X-Request-Id': requestId,
          },
        }
      );
    }

    // Continue with rate limit headers
    const response = NextResponse.next();
    response.headers.set('X-RateLimit-Limit', RATE_LIMIT_MAX.toString());
    response.headers.set('X-RateLimit-Remaining', remaining.toString());
    response.headers.set('X-Request-Id', requestId);

    // Log API request
    logRequest(request, 200, Date.now() - startTime);

    return response;
  }

  // Apply security headers to all responses
  const response = NextResponse.next();

  // Add security headers
  Object.entries(securityHeaders).forEach(([key, value]) => {
    response.headers.set(key, value);
  });

  // Add request tracking headers
  response.headers.set('X-Request-Id', requestId);
  response.headers.set('X-Response-Time', `${Date.now() - startTime}ms`);

  return response;
}

// ============================================================================
// MATCHER CONFIGURATION
// ============================================================================

export const config = {
  matcher: [
    // Match all paths except static files and images
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
