# ADR-006: Background Jobs Strategy

> **Document Created:** 2026-01
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Accepted (partial) — FastAPI BackgroundTasks in active use; full TaskService abstraction planned

## Status
Accepted (partial) — The decision to use a TaskService abstraction layer is accepted. Currently using FastAPI `BackgroundTasks` for immediate needs. Full abstraction layer with Celery migration path is planned for post-v1.0 scaling.

## Date
2026-01

## Context

IP2A Database needs to run background tasks:
- Email notifications (welcome emails, password resets)
- Report generation (grant reports, membership summaries)
- Data synchronization (future QuickBooks integration)
- Scheduled tasks (daily integrity checks, backups)
- Stripe webhook processing

Requirements:
1. **Simple start** — Don't over-engineer for current needs
2. **Scalable later** — Can add proper queue when needed
3. **Reliable** — Important tasks shouldn't be lost
4. **Observable** — Can see what's running and what failed

## Decision

Implement a **TaskService abstraction** with:
- **Interface** — Abstract base class defining task operations
- **FastAPI implementation** — Use `BackgroundTasks` for simple cases now
- **Celery-ready** — Can swap to Celery implementation later without changing callers

```python
class TaskService(ABC):
    @abstractmethod
    def enqueue(self, func: Callable, *args, **kwargs) -> str:
        """Add task to queue, return task ID."""
        pass

    @abstractmethod
    def schedule(self, func: Callable, run_at: datetime, *args, **kwargs) -> str:
        """Schedule task for future execution."""
        pass

    @abstractmethod
    def get_status(self, task_id: str) -> TaskResult:
        """Get task status and result."""
        pass
```

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| FastAPI BackgroundTasks usage | ✅ | Various | Used for report generation, webhook processing |
| Stripe webhook processing | ✅ | 11 | Async payment confirmation via webhooks |
| Report generation (WeasyPrint/openpyxl) | ✅ | 8, 14 | PDF and Excel exports |
| Nightly backup scripts | ✅ | 17 | Cron-based, not TaskService |
| Admin metrics collection | ✅ | 17 | Runs on-demand via admin endpoint |
| TaskService abstract base class | 🔜 | — | Post-v1.0 formalization |
| Celery + Redis/RabbitMQ | 🔜 | — | When load requires distributed queue |
| Email notification system | 🔜 | — | Phase 7+ (referral notifications) |
| QuickBooks sync jobs | 🔜 | — | Future integration |

### Current Background Task Usage

The following operations currently use FastAPI `BackgroundTasks`:
- Stripe webhook event processing (payment confirmation, session expiry)
- Grant report Excel generation (multi-sheet workbooks)
- Audit log archival operations

Scheduled/recurring tasks currently use external mechanisms:
- Database backups: Cron job running `scripts/backup_database.py` (Week 17)
- No in-app scheduled task system yet

## Consequences

### Positive
- **Simple now** — FastAPI BackgroundTasks works for current load
- **No infrastructure** — No Redis/RabbitMQ needed initially
- **Migration path** — Swap implementation when load requires it
- **Testable** — Can mock TaskService in tests

### Negative
- **Limited durability** — FastAPI tasks lost if server restarts
- **No scheduling** — BackgroundTasks doesn't support scheduled jobs natively
- **Single server** — Tasks run on same server as web requests

### Neutral
- For scheduled tasks initially, using cron/systemd timers (confirmed in Week 17)
- Celery migration will require Redis or RabbitMQ
- Railway supports cron jobs for scheduled tasks

## Phase 7 Note

The Referral & Dispatch system may require more robust background processing for:
- LaborPower report imports (~78 report types)
- Referral notification dispatch
- Book position recalculation

This may accelerate the timeline for implementing the full TaskService abstraction with Celery.

## Alternatives Considered

### Celery from the start
- **Rejected:** Adds Redis/RabbitMQ complexity we don't need yet
- **Rejected:** Over-engineering for current single-server deployment

### Database-backed queue (DIY)
- **Rejected:** Re-inventing the wheel
- **Rejected:** Would need to build monitoring, retry logic, etc.

### No background tasks (synchronous only)
- **Rejected:** Report generation would block requests
- **Rejected:** Webhook processing needs to be async

## References
- `src/routers/webhooks/stripe_webhook.py` — Stripe webhook background processing
- `scripts/backup_database.py` — Cron-based backup script (Week 17)
- `scripts/audit_maintenance.py` — Audit log archival
- ADR-013: Stripe Payment Integration (webhook processing)

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-01 — original specification)
