# Cloudflare Edge Deployment Guide

## Overview

This guide covers deploying to Cloudflare Workers for edge computing in the CFZT system.

## Prerequisites

- Node.js 18+
- Wrangler CLI
- Cloudflare account

## Installation

```bash
# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Verify installation
wrangler --version
```

## Basic Worker Setup

### 1. Create Worker

```bash
# Create new worker
wrangler init cfzt-edge

# Or create from template
wrangler init cfzt-edge --template https://github.com/cloudflare/templates/worker-typescript
```

### 2. Worker Code

```typescript
// src/index.ts
export interface Env {
  AUTH_SERVICE: Fetcher;
  FACE_ML_SERVICE: Fetcher;
  PQC_CRYPTO_SERVICE: Fetcher;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    
    // Route requests
    if (url.pathname.startsWith('/api/v1/auth')) {
      return env.AUTH_SERVICE.fetch(request);
    }
    
    if (url.pathname.startsWith('/api/v1/face')) {
      return env.FACE_ML_SERVICE.fetch(request);
    }
    
    if (url.pathname.startsWith('/api/v1/crypto')) {
      return env.PQC_CRYPTO_SERVICE.fetch(request);
    }
    
    // Default response
    return new Response('CFZT Edge Gateway', { status: 200 });
  },
};
```

### 3. Configuration

```toml
# wrangler.toml
name = "cfzt-edge"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[env.production]
name = "cfzt-edge-production"
routes = [
  { pattern = "api.cfzt.io/*", zone_name = "cfzt.io" }
]

[env.staging]
name = "cfzt-edge-staging"
routes = [
  { pattern = "staging-api.cfzt.io/*", zone_name = "cfzt.io" }
]

[[services]]
binding = "AUTH_SERVICE"
service = "auth-service"

[[services]]
binding = "FACE_ML_SERVICE"
service = "face-ml-service"

[[services]]
binding = "PQC_CRYPTO_SERVICE"
service = "pqc-crypto-service"
```

## Advanced Features

### 1. Rate Limiting

```typescript
// src/middleware/rate-limiter.ts
export class RateLimiter {
  private static MAX_REQUESTS = 100;
  private static WINDOW_MS = 60000; // 1 minute

  async isAllowed(key: string, kv: KVNamespace): Promise<boolean> {
    const now = Date.now();
    const windowStart = now - this.WINDOW_MS;
    
    // Get current count
    const data = await kv.get(key, { type: 'json' });
    const count = data?.count || 0;
    const timestamp = data?.timestamp || now;
    
    if (timestamp < windowStart) {
      // Reset window
      await kv.put(key, JSON.stringify({ count: 1, timestamp: now }), {
        expirationTtl: 60,
      });
      return true;
    }
    
    if (count >= this.MAX_REQUESTS) {
      return false;
    }
    
    // Increment count
    await kv.put(key, JSON.stringify({ count: count + 1, timestamp }), {
      expirationTtl: 60,
    });
    
    return true;
  }
}
```

### 2. WAF Rules

```typescript
// src/middleware/waf.ts
export class WAF {
  private static BLOCKED_IPS = new Set(['192.168.1.1']);
  private static BLOCKED_PATHS = ['/admin', '/debug'];

  async checkRequest(request: Request): Promise<boolean> {
    const url = new URL(request.url);
    
    // Check blocked IPs
    const clientIP = request.headers.get('CF-Connecting-IP');
    if (clientIP && this.BLOCKED_IPS.has(clientIP)) {
      return false;
    }
    
    // Check blocked paths
    if (this.BLOCKED_PATHS.some(path => url.pathname.startsWith(path))) {
      return false;
    }
    
    // Check for SQL injection
    if (this.detectSQLInjection(request)) {
      return false;
    }
    
    // Check for XSS
    if (this.detectXSS(request)) {
      return false;
    }
    
    return true;
  }

  private detectSQLInjection(request: Request): boolean {
    const body = request.clone().text();
    const patterns = [
      /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|FETCH|DECLARE|TRUNCATE|COMMENT)\b)/i,
      /(--|#|\/\*|\*\/|;)/,
      /(\b(OR|AND)\b\s+\d+\s*=\s*\d+)/i,
    ];
    
    return patterns.some(pattern => pattern.test(body));
  }

  private detectXSS(request: Request): boolean {
    const body = request.clone().text();
    const patterns = [
      /<script\b[^>]*>[\s\S]*?<\/script>/i,
      /javascript:/i,
      /on\w+\s*=/i,
    ];
    
    return patterns.some(pattern => pattern.test(body));
  }
}
```

### 3. Authentication

```typescript
// src/middleware/auth.ts
export class Authenticator {
  async verifyToken(token: string, kv: KVNamespace): Promise<boolean> {
    // Check if token is blacklisted
    const blacklisted = await kv.get(`blacklist:${token}`);
    if (blacklisted) {
      return false;
    }
    
    // Verify token signature
    try {
      const payload = await this.verifyJWT(token);
      return payload.exp > Date.now() / 1000;
    } catch {
      return false;
    }
  }

  private async verifyJWT(token: string): Promise<any> {
    // Verify JWT token
    const [header, payload, signature] = token.split('.');
    
    // Verify signature
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode('secret'),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['verify']
    );
    
    const valid = await crypto.subtle.verify(
      'HMAC',
      key,
      Uint8Array.from(atob(signature), c => c.charCodeAt(0)),
      encoder.encode(`${header}.${payload}`)
    );
    
    if (!valid) {
      throw new Error('Invalid signature');
    }
    
    return JSON.parse(atob(payload));
  }
}
```

### 4. Caching

```typescript
// src/middleware/cache.ts
export class Cache {
  async get(key: string, kv: KVNamespace): Promise<string | null> {
    return kv.get(key);
  }

  async set(key: string, value: string, kv: KVNamespace, ttl: number = 300): Promise<void> {
    await kv.put(key, value, { expirationTtl: ttl });
  }

  async delete(key: string, kv: KVNamespace): Promise<void> {
    await kv.delete(key);
  }

  async cacheResponse(request: Request, response: Response, kv: KVNamespace, ttl: number = 300): Promise<Response> {
    const cacheKey = new Request(request.url, request);
    const cached = await this.get(cacheKey.url, kv);
    
    if (cached) {
      return new Response(cached, {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    
    const newResponse = response.clone();
    const body = await newResponse.text();
    await this.set(cacheKey.url, body, kv, ttl);
    
    return response;
  }
}
```

## Deployment

### 1. Deploy to Production

```bash
# Deploy to production
wrangler deploy --env production

# Or deploy with custom config
wrangler deploy --config wrangler.toml --env production
```

### 2. Deploy to Staging

```bash
# Deploy to staging
wrangler deploy --env staging
```

### 3. Deploy with CI/CD

```yaml
# .github/workflows/deploy-cloudflare.yml
name: Deploy to Cloudflare

on:
  push:
    branches: [main]
    paths:
      - 'edge/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install dependencies
        run: npm install
      
      - name: Deploy to Cloudflare
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: deploy --env production
```

## Monitoring

### 1. Logs

```bash
# View logs
wrangler tail --env production

# Or view specific service
wrangler tail --env production --service auth-service
```

### 2. Metrics

```typescript
// src/middleware/metrics.ts
export class Metrics {
  private static requests = new Map<string, number>();
  private static errors = new Map<string, number>();

  static recordRequest(path: string): void {
    const count = this.requests.get(path) || 0;
    this.requests.set(path, count + 1);
  }

  static recordError(path: string): void {
    const count = this.errors.get(path) || 0;
    this.errors.set(path, count + 1);
  }

  static getMetrics(): object {
    return {
      requests: Object.fromEntries(this.requests),
      errors: Object.fromEntries(this.errors),
    };
  }
}
```

## Testing

### 1. Unit Tests

```typescript
// test/index.test.ts
import { describe, it, expect } from 'vitest';
import worker from '../src/index';

describe('Worker', () => {
  it('should route to auth service', async () => {
    const request = new Request('https://api.cfzt.io/api/v1/auth/login');
    const response = await worker.fetch(request, {
      AUTH_SERVICE: {
        fetch: async () => new Response('auth'),
      },
    } as any);
    
    expect(response.status).toBe(200);
  });
});
```

### 2. Integration Tests

```bash
# Run tests
npm test

# Or run with wrangler
wrangler dev --env staging
```

## Resources

- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [Wrangler CLI Documentation](https://developers.cloudflare.com/workers/wrangler/)
- [Workers TypeScript Documentation](https://developers.cloudflare.com/workers/languages/typescript/)
