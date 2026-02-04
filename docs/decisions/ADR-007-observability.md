# ADR-007: Observability Stack

> **Document Created:** 2026-01
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented (partial) — Sentry + structured logging live; Grafana/Loki planned

## Status
Implemented (partial) — Sentry error tracking, structured logging, and admin metrics are live in production (Weeks 16–17). The full Grafana + Loki + Promtail stack is planned for post-v1.0 infrastructure maturation.

## Date
2026-01

## Context

IP2A Database needs monitoring and logging:
- Application logs (errors, warnings, info)
- Request tracing (slow requests, errors)
- System metrics (CPU, memory, disk)
- Alerting (when things go wrong)

Requirements:
1. **Portable** — Must work on local server and cloud
2. **Self-hosted** — No external service dependencies (preferred)
3. **Cost-effective** — Open source, union budget
4. **Docker-based** — Consistent with rest of stack
5. **Industry standard** — Widely used, well-documented

## Decision

### Phase 1 (Implemented — Weeks 16–17): Production-Ready Monitoring

Use **Sentry + structured logging + admin metrics** for immediate production needs:
- **Sentry** — Error tracking and alerting (cloud-hosted, free tier)
- **Structured logging** — JSON-formatted logs with request context
- **Admin metrics endpoint** — System health dashboard for staff
- **Incident response runbook** — Documented procedures

### Phase 2 (Planned — Post-v1.0): Full Observability Stack

Use **Grafana + Loki + Promtail** stack for comprehensive observability:
- **Grafana** — Visualization and dashboards
- **Loki** — Log aggregation (like Prometheus, but for logs)
- **Promtail** — Log collection agent
- **Prometheus** (optional) — Metrics collection

All running in Docker containers, same as application.

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| Sentry error tracking | ✅ | 16 | Cloud-hosted, DSN in Railway env vars |
| Structured JSON logging | ✅ | 16 | Request context, user tracking |
| Security headers monitoring | ✅ | 16 | HSTS, CSP, X-Frame-Options |
| Admin metrics endpoint | ✅ | 17 | System health, user stats, DB status |
| Incident response runbook | ✅ | 17 | `docs/runbooks/incident-response.md` |
| Backup monitoring | ✅ | 17 | Script exit codes + logs |
| Railway deployment logs | ✅ | 16 | Native Railway log viewer |
| Grafana dashboards | 🔜 | — | Post-v1.0 |
| Loki log aggregation | 🔜 | — | Post-v1.0 |
| Promtail log shipping | 🔜 | — | Post-v1.0 |
| Prometheus metrics | 🔜 | — | Post-v1.0 |
| Uptime monitoring | 🔜 | — | Evaluating options |

### What's Working Now

**Sentry (Week 16):**
- Automatic error capture with stack traces
- Request context (URL, method, user)
- Environment tagging (production vs development)
- Email/Slack alerting on new errors
- Performance monitoring (transaction sampling)

**Structured Logging (Week 16):**
- JSON-formatted log entries
- Request ID tracking across log entries
- User identification in log context
- Configurable log levels per module

**Admin Metrics (Week 17):**
- Database connection pool status
- Active user count and recent activity
- System resource usage
- Recent error summary
- Accessible via staff dashboard

## Consequences

### Positive (Current Implementation)
- **Immediate visibility** — Sentry catches errors in real-time
- **Zero infrastructure** — Sentry cloud free tier, no self-hosted overhead
- **Production-ready** — Logging and alerting working in Railway
- **Low maintenance** — No additional containers to manage

### Positive (Planned Grafana Stack)
- **Unified interface** — Logs and metrics in one place (Grafana)
- **Portable** — Entire stack runs in Docker, works anywhere
- **Scalable** — Can handle significant log volume
- **Cost-effective** — All open source
- **Query language** — LogQL for powerful log queries

### Negative
- **Current gap** — No centralized log search (rely on Railway logs + Sentry)
- **Resource usage** — Full Grafana stack adds containers and memory overhead
- **Learning curve** — Need to learn Grafana/Loki query languages

### Neutral
- Sentry free tier sufficient for current scale (~50 users)
- Can start with just Grafana logging, add Prometheus metrics later
- Railway provides basic log viewing that covers most debugging needs

## Alternatives Considered

### ELK Stack (Elasticsearch, Logstash, Kibana)
- **Rejected:** Higher resource requirements
- **Rejected:** More complex to operate

### Cloud logging (CloudWatch, Stackdriver)
- **Rejected:** Vendor lock-in
- **Rejected:** Ongoing cost for log storage

### No centralized logging (just files)
- **Rejected:** Hard to search across containers
- **Rejected:** No visualization or alerting
- **Partially adopted:** Railway logs serve as basic centralized logging for now

### Paid solutions (Datadog, New Relic)
- **Rejected:** Cost prohibitive for union budget
- **Rejected:** External dependency
- **Exception:** Sentry free tier adopted as practical compromise

## References
- Sentry config: `src/config/sentry_config.py`
- Logging config: `src/config/logging_config.py`
- Admin metrics: `src/routers/admin.py` (metrics endpoint)
- Incident runbook: `docs/runbooks/incident-response.md`
- Backup scripts: `scripts/backup_database.py`

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-01 — original specification for Grafana/Loki stack)
