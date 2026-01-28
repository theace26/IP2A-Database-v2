# ADR-006: Background Jobs Strategy

## Status
Accepted

## Date
2026-01

## Context

IP2A Database needs to run background tasks:
- Email notifications (welcome emails, password resets)
- Report generation (grant reports, membership summaries)
- Data synchronization (future QuickBooks integration)
- Scheduled tasks (daily integrity checks, backups)

Requirements:
1. **Simple start** - Don't over-engineer for current needs
2. **Scalable later** - Can add proper queue when needed
3. **Reliable** - Important tasks shouldn't be lost
4. **Observable** - Can see what's running and what failed

## Decision

Implement a **TaskService abstraction** with:
- **Interface** - Abstract base class defining task operations
- **FastAPI implementation** - Use `BackgroundTasks` for simple cases now
- **Celery-ready** - Can swap to Celery implementation later without changing callers

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

## Consequences

### Positive
- **Simple now** - FastAPI BackgroundTasks works for current load
- **No infrastructure** - No Redis/RabbitMQ needed initially
- **Migration path** - Swap implementation when load requires it
- **Testable** - Can mock TaskService in tests

### Negative
- **Limited durability** - FastAPI tasks lost if server restarts
- **No scheduling** - BackgroundTasks doesn't support scheduled jobs
- **Single server** - Tasks run on same server as web requests

### Neutral
- For scheduled tasks initially, can use cron or systemd timers
- Celery migration will require Redis or RabbitMQ

## Alternatives Considered

### Celery from the start
- **Rejected:** Adds Redis/RabbitMQ complexity we don't need yet
- **Rejected:** Over-engineering for current single-server deployment

### Database-backed queue (DIY)
- **Rejected:** Re-inventing the wheel
- **Rejected:** Would need to build monitoring, retry logic, etc.

### No background tasks (synchronous only)
- **Rejected:** Email sending would block requests
- **Rejected:** Long-running reports would timeout

---

*When Celery is needed, implement `CeleryTaskService` that implements the same interface.*
