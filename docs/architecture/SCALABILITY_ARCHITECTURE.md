# IP2A Database Scalability Architecture
## Multi-User Environment: 4,000 Members + 40 Staff

**Document Created:** January 27, 2026
**Last Updated:** February 3, 2026
**Version:** v0.9.4-alpha (FEATURE-COMPLETE, Weeks 1–19)
**Status:** 🔶 PARTIALLY IMPLEMENTED — Connection pooling and Auth/RBAC operational; caching, read replicas, and rate limiting remain future work

---

## Implementation Status

> **This document was originally written as a pre-implementation scaling roadmap (v1.0, January 27, 2026).**
> As of v0.9.4-alpha, the system is production-deployed on Railway with connection pooling and full JWT auth/RBAC. The remaining phases (read replicas, Redis caching, rate limiting) are deferred until user load requires them.

| Phase | Status | Implemented In |
|-------|--------|----------------|
| Phase 1: Connection Pooling | ✅ Implemented | Week 16 (Production Hardening) |
| Phase 2: Read Replicas | 🔜 Future | Deferred — single Railway PostgreSQL sufficient for current load |
| Phase 3: Redis Caching | 🔜 Future | Deferred — response times acceptable without caching |
| Phase 4: Auth & RBAC | ✅ Implemented | Week 1 (Core Auth), Week 16 (Security Headers) |
| Phase 5: Rate Limiting | 🔜 Future | Deferred — not needed for ~40 staff users pre-launch |
| Phase 6: Monitoring | ✅ Partial | Sentry (Week 16), structured logging, admin metrics (Week 17) |

### What's Running in Production Now

- **Connection pooling**: SQLAlchemy `QueuePool` with `pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`, `pool_recycle=3600`
- **JWT Authentication**: Access + refresh tokens via HTTP-only cookies
- **RBAC**: 7 roles (admin, officer, staff, organizer, instructor, member, applicant) with granular permissions
- **Security Headers**: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **Error Tracking**: Sentry with sensitive data scrubbing
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Admin Metrics**: System health dashboard (Week 17)

---

## Requirements Analysis

### User Types & Access Patterns

| User Type | Count | Access Level | Usage Pattern | Peak Load |
|-----------|-------|--------------|---------------|-----------|
| **Staff Users** | ~40 | Admin/Staff (R/W) | Heavy writes, complex queries | 40 concurrent |
| **Union Members** | ~4,000 | Self-Service | View profile, pay dues, view referral history | 200–400 concurrent (estimated) |
| **Instructors** | ~10 | Instructor | Student grades, attendance | 10 concurrent |
| **Applicants** | ~100 | Applicant | Submit applications, check status | 20 concurrent |
| **API Integrations** | TBD | R/W | Future automated operations | TBD |

**Current Capacity Target:** ~40 staff users + occasional member self-service
**Future Capacity Target (post-member portal launch):** 500+ concurrent users, 200–500 RPS

### Current vs Target Performance

| Metric | Pre-Week 16 | Current (v0.9.4) | Target (Post-Scale) |
|--------|-------------|-------------------|---------------------|
| Max Concurrent Users | ~50 | ~200 | 5,000+ |
| Requests/Second | ~100 | ~300–500 | 2,000+ |
| Avg Response Time | 50–200ms | 20–100ms | 10–50ms |
| Database Connections | 1 per request | 20 pooled + 10 overflow | 200 pooled (PgBouncer) |
| Cache Hit Rate | 0% | 0% | 80–90% |
| Error Tracking | None | Sentry | Sentry + Prometheus |

---

## Current Architecture (Production)

```
                    ┌─────────────────────┐
                    │      Browser        │
                    │  (PWA / Desktop)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     Railway CDN     │
                    │   (HTTPS + TLS)     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     FastAPI App     │
                    │   (Dockerized)      │
                    │                     │
                    │  • JWT Auth         │
                    │  • Security Headers │
                    │  • Sentry           │
                    │  • Structured Logs  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   SQLAlchemy Pool   │
                    │                     │
                    │  pool_size=20       │
                    │  max_overflow=10    │
                    │  pool_pre_ping=True │
                    │  pool_recycle=3600  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    PostgreSQL 16    │
                    │  (Railway Managed)  │
                    │                     │
                    │  Single instance    │
                    │  Daily backups      │
                    └─────────────────────┘
```

---

## Implemented: Phase 1 — Connection Pooling ✅

Implemented in **Week 16 (Production Hardening)** as part of the broader security and performance package.

### SQLAlchemy Connection Pool Configuration

```python
# src/database.py — PRODUCTION CONFIGURATION (Week 16)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from src.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Base connections per worker
    max_overflow=10,           # Extra connections under load
    pool_pre_ping=True,        # Verify connection health before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_timeout=30,           # Wait 30s for connection from pool
    echo=False,                # Disable SQL logging in production
    connect_args={
        "application_name": "ip2a_api",
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30s query timeout
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session with connection pooling."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Returns connection to pool (doesn't close it)
```

**Capacity:**
- 20 base connections + 10 overflow = 30 max per worker
- Railway single-instance deployment handles current ~40 staff users comfortably
- Connection health checks (`pool_pre_ping`) prevent stale connections after Railway restarts

### Validation

- 32 production tests validate connection pooling, security headers, and hardening measures
- Sentry monitors connection pool exhaustion in production

---

## Implemented: Phase 4 — Authentication & RBAC ✅

Implemented in **Week 1** (core auth) with security hardening in **Week 16**.

Full details in [AUTHENTICATION_ARCHITECTURE.md](AUTHENTICATION_ARCHITECTURE.md).

### Summary

- **JWT tokens** via HTTP-only cookies (access + refresh)
- **7 roles**: admin, officer, staff, organizer, instructor, member, applicant
- **Permission-based access**: `{resource}:{action}` format (e.g., `members:read`, `dues:pay`)
- **Account lockout**: `locked_until` datetime after 5 failed attempts
- **Security headers**: CSP, HSTS, X-Frame-Options, etc. (Week 16)
- **Sentry error tracking** with sensitive data scrubbing (Week 16)

---

## Implemented: Phase 6 — Monitoring (Partial) ✅

| Component | Status | Details |
|-----------|--------|---------|
| Sentry error tracking | ✅ Implemented (Week 16) | Production errors with stack traces, sensitive data scrubbed |
| Structured JSON logging | ✅ Implemented (Week 16) | Correlation IDs, request/response timing |
| Admin metrics dashboard | ✅ Implemented (Week 17) | System health visible to admin users |
| Prometheus + Grafana | 🔜 Future | Not needed until scaling beyond Railway |
| Automated alerting | 🔜 Future | Currently relying on Sentry alerts |

---

## Future: Phase 2 — Read Replicas

**When to implement:** When member self-service portal launches and read traffic exceeds what a single PostgreSQL instance can handle (likely 500+ concurrent users).

### Design

```python
# src/database.py — FUTURE READ/WRITE SPLIT

# Primary database (writes)
write_engine = create_engine(
    settings.DATABASE_WRITE_URL,
    pool_size=20,
    max_overflow=10,
)

# Read replica (reads — 90% of traffic)
read_engine = create_engine(
    settings.DATABASE_READ_URL,
    pool_size=30,
    max_overflow=20,
)

WriteSession = sessionmaker(bind=write_engine)
ReadSession = sessionmaker(bind=read_engine)

def get_db_write():
    """Get write session (primary)."""
    db = WriteSession()
    try:
        yield db
    finally:
        db.close()

def get_db_read():
    """Get read session (replica)."""
    db = ReadSession()
    try:
        yield db
    finally:
        db.close()
```

**Capacity Increase:**
- 2 read replicas = 3x read capacity
- Expected read:write ratio of 90:10 for member portal traffic
- Can add more replicas as needed

---

## Future: Phase 3 — Redis Caching

**When to implement:** When response times degrade under load or when the same data is fetched repeatedly (e.g., member profiles, organization lists, static reference data).

### Design

```yaml
# docker-compose.yml addition
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

**What to Cache (when implemented):**

| Data Type | TTL | Invalidation |
|-----------|-----|--------------|
| Member profiles | 5 min | On update |
| Organization lists | 10 min | On create/update |
| Static reference data | 1 hour | Manual |
| Session data | 24 hours | On logout |
| Rate limit counters | 1 min | Automatic |

**Expected Improvement:**
- 80–90% of reads served from cache
- <1ms cache latency vs 10–50ms database
- 5–10x read performance improvement

---

## Future: Phase 5 — Rate Limiting

**When to implement:** When the system is exposed to external users (member self-service portal, public API).

**Planned Rate Limits:**

| User Type | Requests/Minute | Requests/Hour |
|-----------|-----------------|---------------|
| Public/Unauthenticated | 10 | 100 |
| Member | 60 | 1,000 |
| Staff | 300 | 10,000 |
| Admin | 1,000 | 50,000 |
| API Key | 1,000 | 100,000 |

---

## Scaling Roadmap

### Target Architecture (When Scaling Required)

```
                           ┌─────────────────┐
                           │   CloudFlare    │
                           │   CDN + DDoS    │
                           └────────┬────────┘
                                    │
                           ┌────────▼────────┐
                           │  Load Balancer  │
                           │   (AWS ALB)     │
                           └────────┬────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼─────┐ ┌──────▼──────┐ ┌─────▼──────┐
            │  FastAPI    │ │  FastAPI    │ │  FastAPI   │
            │  Instance 1 │ │  Instance 2 │ │  Instance N│
            └──────┬──────┘ └──────┬──────┘ └──────┬─────┘
                   │               │               │
                   └───────────────┼───────────────┘
                                   │
                          ┌────────▼────────┐
                          │   PgBouncer     │
                          │  (Connection    │
                          │   Pooler)       │
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
            ┌───────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
            │  PostgreSQL  │ │   Read   │ │   Read     │
            │   Primary    │ │ Replica 1│ │ Replica 2  │
            │   (Write)    │ │  (Read)  │ │  (Read)    │
            └──────────────┘ └──────────┘ └────────────┘
                   │
            ┌──────▼──────┐
            │    Redis    │
            │   Cache +   │
            │   Sessions  │
            └─────────────┘
```

### Scaling Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Response time P95 > 500ms | Sustained over 1 hour | Investigate, consider caching |
| Database connections > 80% pool | Sustained under load | Add PgBouncer, increase pool |
| Concurrent users > 200 | Regular occurrence | Evaluate read replicas |
| Error rate > 1% | Any period | Investigate via Sentry |
| Member portal launch | N/A | Pre-deploy caching + read replicas |

---

## Cost Estimates

### Current Production (Railway)

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| FastAPI App | Railway (Dockerized) | ~$5–20 |
| PostgreSQL 16 | Railway Managed | ~$5–20 |
| Render (backup) | Render Free/Starter | $0–7 |
| Sentry | Free tier | $0 |
| **Total** | | **~$10–47/month** |

### Future Scaling (AWS — When Needed)

| Component | Instance Type | Monthly Cost |
|-----------|---------------|--------------|
| Load Balancer | ALB | $20 |
| FastAPI (3 instances) | t3.medium | $90 |
| PostgreSQL Primary | db.t3.large | $120 |
| Read Replica (2) | db.t3.medium | $140 |
| PgBouncer | Included in app | $0 |
| Redis Cache | cache.t3.small | $40 |
| CloudFlare | Free tier | $0 |
| **Total** | | **~$410/month** |

### High Performance (AWS — 4,000+ Members Active)

| Component | Instance Type | Monthly Cost |
|-----------|---------------|--------------|
| Load Balancer | ALB | $20 |
| FastAPI (5 instances) | t3.large | $250 |
| PostgreSQL Primary | db.r5.xlarge | $350 |
| Read Replica (3) | db.r5.large | $525 |
| PgBouncer | t3.small | $15 |
| Redis Cache | cache.r5.large | $180 |
| CloudFlare | Pro | $20 |
| **Total** | | **~$1,360/month** |

---

## Security Checklist

- [x] SSL/TLS for all connections (Railway enforces HTTPS)
- [x] Environment variables for secrets (Railway env vars)
- [x] JWT token-based authentication (Week 1)
- [x] Role-based access control with 7 roles (Week 1)
- [x] Account lockout via `locked_until` datetime (Week 1)
- [x] Security headers (CSP, HSTS, etc.) (Week 16)
- [x] Sentry error tracking with data scrubbing (Week 16)
- [x] Structured logging with correlation IDs (Week 16)
- [x] Audit logging for all data access (NLRA compliant)
- [x] Stripe payment security (PCI compliance via Checkout Sessions, Week 11)
- [ ] Row-level security (RLS) in PostgreSQL
- [ ] API key authentication for integrations
- [ ] CloudFlare DDoS protection
- [ ] Web Application Firewall (WAF)
- [ ] IP whitelisting for admin access
- [ ] Rate limiting per user type
- [ ] Regular penetration testing

---

## Implementation Priority (Going Forward)

| Priority | Phase | When | Effort |
|----------|-------|------|--------|
| 🔴 Done | Connection Pooling | ✅ Week 16 | ✅ |
| 🔴 Done | Auth/RBAC | ✅ Week 1 + 16 | ✅ |
| 🔴 Done | Monitoring (Sentry + Logs) | ✅ Week 16–17 | ✅ |
| 🟡 Next | S3 File Storage (production) | Pre-member portal | 8–12 hours |
| 🟡 Next | Redis Caching | Pre-member portal | 16–20 hours |
| 🟠 Later | Read Replicas | When load demands | 12–16 hours |
| 🟠 Later | PgBouncer (external pooler) | When multi-instance | 8–12 hours |
| 🟢 Future | Rate Limiting | When external access | 8–12 hours |
| 🟢 Future | Load Balancer + Multi-Instance | When scaling to AWS | 12–16 hours |

---

> **⚠️ SESSION RULE — MANDATORY:**
> At the end of every development session, update *ANY* and *ALL* relevant documents to capture progress made. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.
> See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md`

---

*Document Version: 2.0*
*Last Updated: February 3, 2026*
*Previous Version: 1.0 (January 27, 2026 — pre-implementation scaling roadmap with full code examples)*
