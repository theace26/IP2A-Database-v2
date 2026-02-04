# ADR-001: Database Choice

> **Document Created:** 2025 (backfill — original decision predates ADR process)
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented — PostgreSQL 16 running in production on Railway

## Status
Implemented

## Date
2025 (Backfill — decision made at project inception, before formal ADR process)

## Context

We need a relational database for the IP2A union management system. Requirements:
- ACID compliance for financial data integrity
- Support for complex queries (reporting)
- JSON support for flexible schemas
- Strong ecosystem and long-term support
- Runs well in Docker for development
- Reasonable hosting costs

## Options Considered

### Option A: PostgreSQL
- Industry standard for complex applications
- Excellent JSON support (JSONB)
- Strong typing and data integrity
- Extensive extension ecosystem
- Free and open source

### Option B: MySQL/MariaDB
- Popular, well-understood
- Good performance
- Less robust JSON support
- Fewer advanced features

### Option C: SQLite
- Zero configuration
- File-based (simple backups)
- Not suitable for concurrent web access
- Limited scalability

## Decision

We will use **PostgreSQL 16**.

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| PostgreSQL 16 in Docker (dev) | ✅ | 1 | docker-compose.yml |
| SQLAlchemy 2.x ORM integration | ✅ | 1 | Async-ready, 26 models as of v0.9.4 |
| Alembic migrations | ✅ | 1 | Timestamped naming convention (ADR-009) |
| Railway PostgreSQL (prod) | ✅ | 16 | Managed instance, connection pooling |
| Connection pooling | ✅ | 16 | Week 16 production hardening |
| Audit immutability trigger | ✅ | 11 | NLRA 7-year compliance (ADR-012) |
| JSONB usage (audit logs) | ✅ | 11 | old_values/new_values/changed_fields |
| Nightly backup scripts | ✅ | 17 | `scripts/backup_database.py` |

### Current Scale (v0.9.4-alpha)
- **26 ORM models** across 6 domain areas
- **~150 API endpoints**
- **~470 tests** (165 backend, ~200+ frontend, ~78 production, 25 Stripe)
- **Railway deployment** with managed PostgreSQL

## Consequences

### Positive
- Full ACID compliance protects financial/dues data
- JSONB allows flexible metadata storage (audit logs, grant reporting)
- Array types useful for multi-value fields
- Excellent SQLAlchemy support
- Large community for troubleshooting
- Railway managed PostgreSQL reduces ops burden

### Negative
- Slightly more complex setup than SQLite
- Requires running database server
- Railway PostgreSQL has storage limits on free/starter tiers

### Risks
- PostgreSQL major version upgrades can require migration
  - **Mitigation:** Stay on LTS versions, test upgrades in dev first
  - **Mitigation:** Railway handles minor version updates automatically

## References
- ADR-009: Migration Safety Strategy
- ADR-012: Audit Logging Architecture (uses PostgreSQL triggers)
- `docker-compose.yml` — Local development PostgreSQL
- `src/db/` — Database configuration and models
- `scripts/backup_database.py` — Nightly backup automation (Week 17)
- Railway dashboard — Production database management

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2025 — original decision record, undated)
