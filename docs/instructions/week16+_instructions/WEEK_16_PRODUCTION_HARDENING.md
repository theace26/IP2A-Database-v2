# Week 16: Production Hardening & Performance Optimization

**Version:** 1.0.0  
**Created:** February 2, 2026  
**Branch:** `develop`  
**Estimated Effort:** 6-8 hours (2-3 sessions)  
**Dependencies:** Week 15 (Deployment Preparation) complete, leadership demo successful

---

## Overview

After leadership demo approval, this week focuses on **production hardening** to ensure the system is ready for real-world use. This includes performance optimization, security hardening, monitoring setup, and operational readiness.

### Objectives

- [ ] Database performance optimization (indexes, query analysis)
- [ ] Connection pooling configuration
- [ ] Rate limiting implementation
- [ ] Security headers and CORS configuration
- [ ] Logging and monitoring setup
- [ ] Error tracking integration (Sentry)
- [ ] Health check enhancements

### Out of Scope

- Horizontal scaling (multiple instances)
- CDN setup
- Kubernetes deployment
- Read replicas

---

## Pre-Flight Checklist

- [ ] On `develop` branch
- [ ] Leadership demo completed successfully
- [ ] Railway deployment stable
- [ ] All tests passing
- [ ] Baseline performance metrics documented

---

## Phase 1: Database Performance (Session 1)

### 1.1 Index Analysis

Run this analysis to identify missing indexes:

```sql
-- Find slow queries (PostgreSQL)
SELECT 
    query,
    calls,
    total_time / 1000 as total_seconds,
    mean_time / 1000 as mean_seconds,
    rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 20;
```

### 1.2 Create Performance Indexes

Create migration `alembic revision -m "add_performance_indexes"`:

```python
"""Add performance indexes for common queries."""
from alembic import op

def upgrade():
    # Member lookups
    op.create_index('ix_members_member_number', 'members', ['member_number'], unique=True)
    op.create_index('ix_members_status', 'members', ['status'])
    op.create_index('ix_members_last_name', 'members', ['last_name'])
    
    # Audit log queries
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_table_record', 'audit_logs', ['table_name', 'record_id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    
    # Dues queries
    op.create_index('ix_dues_payments_member_id', 'dues_payments', ['member_id'])
    op.create_index('ix_dues_payments_period_id', 'dues_payments', ['period_id'])
    op.create_index('ix_dues_payments_status', 'dues_payments', ['status'])
    
    # Grant enrollment queries
    op.create_index('ix_grant_enrollments_grant_id', 'grant_enrollments', ['grant_id'])
    op.create_index('ix_grant_enrollments_student_id', 'grant_enrollments', ['student_id'])
    
    # Student lookups
    op.create_index('ix_students_cohort_id', 'students', ['cohort_id'])
    op.create_index('ix_students_status', 'students', ['status'])

def downgrade():
    op.drop_index('ix_students_status')
    op.drop_index('ix_students_cohort_id')
    op.drop_index('ix_grant_enrollments_student_id')
    op.drop_index('ix_grant_enrollments_grant_id')
    op.drop_index('ix_dues_payments_status')
    op.drop_index('ix_dues_payments_period_id')
    op.drop_index('ix_dues_payments_member_id')
    op.drop_index('ix_audit_logs_user_id')
    op.drop_index('ix_audit_logs_table_record')
    op.drop_index('ix_audit_logs_created_at')
    op.drop_index('ix_members_last_name')
    op.drop_index('ix_members_status')
    op.drop_index('ix_members_member_number')
```

### 1.3 Connection Pool Configuration

Update `src/config/settings.py`:

```python
class Settings(BaseSettings):
    # Database Pool Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
    DB_ECHO: bool = False
```

Update `src/db/session.py`:

```python
from sqlalchemy.pool import AsyncAdaptedQueuePool

engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)
```

---

## Phase 2: Rate Limiting (Session 1-2)

### 2.1 Install slowapi

Add to `requirements.txt`:
```
slowapi>=0.1.9
```

### 2.2 Rate Limiter Configuration

Create `src/core/rate_limiter.py`:

```python
"""Rate limiting configuration."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])

# Specific limits
AUTH_LIMIT = "5 per minute"
API_WRITE_LIMIT = "30 per minute"
EXPORT_LIMIT = "10 per minute"
PAYMENT_LIMIT = "10 per minute"
```

### 2.3 Apply to Routes

```python
from src.core.rate_limiter import limiter, AUTH_LIMIT

@router.post("/login")
@limiter.limit(AUTH_LIMIT)
async def login(request: Request, ...):
    ...
```

---

## Phase 3: Security Hardening (Session 2)

### 3.1 Security Headers Middleware

Create `src/middleware/security.py`:

```python
"""Security headers middleware."""
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.stripe.com;"
        )
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
```

### 3.2 CORS Configuration

Update `src/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

allowed_origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)
```

---

## Phase 4: Monitoring & Error Tracking (Session 2-3)

### 4.1 Sentry Integration

Add to `requirements.txt`:
```
sentry-sdk[fastapi]>=1.40.0
```

Create `src/core/monitoring.py`:

```python
"""Monitoring and error tracking setup."""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def init_sentry():
    if not settings.SENTRY_DSN:
        return
    
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
```

### 4.2 Structured Logging

Create `src/core/logging_config.py`:

```python
"""Structured logging configuration."""
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
        })

def setup_logging(json_format: bool = True):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    if json_format:
        handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
```

---

## Phase 5: Enhanced Health Checks (Session 3)

### 5.1 Comprehensive Health Check

Update `src/routers/health.py`:

```python
@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_async_session)):
    """Readiness check - verifies all dependencies."""
    checks = {}
    overall_healthy = True
    
    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # S3 check
    if settings.S3_ENDPOINT_URL:
        try:
            async with get_s3_client() as client:
                await client.list_buckets()
            checks["s3"] = {"status": "healthy"}
        except Exception as e:
            checks["s3"] = {"status": "unhealthy", "error": str(e)}
            overall_healthy = False
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "version": settings.APP_VERSION,
    }
```

---

## Testing Requirements

### Test Files

- `src/tests/test_rate_limiting.py`
- `src/tests/test_security_headers.py`
- `src/tests/test_health_checks.py`

### Test Scenarios

1. **Rate Limiting** - 429 when exceeded
2. **Security Headers** - All headers present
3. **Health Checks** - Dependencies verified

---

## Acceptance Criteria

### Required

- [ ] Performance indexes added
- [ ] Connection pooling configured
- [ ] Rate limiting on auth/payment endpoints
- [ ] Security headers on all responses
- [ ] Sentry error tracking configured
- [ ] Structured JSON logging in production
- [ ] Health checks verify dependencies
- [ ] 10-15 new tests passing

---

## 📝 MANDATORY: End-of-Session Documentation

> **REQUIRED:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. **Do not forget about ADRs—update as necessary.**

### Quick Checklist

- [ ] `/CHANGELOG.md` — Version bump (v0.9.1-alpha)
- [ ] `/CLAUDE.md` — Update production config section
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Mark Week 16 complete
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-production-hardening.md` — **Create session log**

---

*Last Updated: February 2, 2026*
