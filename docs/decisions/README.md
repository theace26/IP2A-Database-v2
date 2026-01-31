# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) documenting significant technical decisions made during the development of IP2A.

## What is an ADR?

An ADR captures an important architectural decision along with its context and consequences. They help future maintainers understand WHY something was built a certain way.

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](ADR-001-database-choice.md) | Database Choice (PostgreSQL) | Accepted | 2025-XX-XX |
| [ADR-002](ADR-002-frontend-framework.md) | Frontend Framework (HTMX + Alpine.js) | Accepted | 2026-01-27 |
| [ADR-003](ADR-003-authentication-strategy.md) | Authentication Strategy (JWT) | Accepted | 2025-XX-XX |
| [ADR-004](ADR-004-file-storage-strategy.md) | File Storage (Object Storage) | Accepted | 2025-XX-XX |
| [ADR-005](ADR-005-css-framework.md) | CSS Framework (Tailwind) | Accepted | 2026-01 |
| [ADR-006](ADR-006-background-jobs.md) | Background Jobs (TaskService Abstraction) | Accepted | 2026-01 |
| [ADR-007](ADR-007-observability.md) | Observability Stack (Grafana + Loki) | Accepted | 2026-01 |
| [ADR-008](ADR-008-dues-tracking-system.md) | Dues Tracking System Design | Accepted | 2026-01-28 |
| [ADR-009](ADR-009-migration-safety.md) | Migration Safety | Accepted | 2026-01 |
| [ADR-010](ADR-010-operations-frontend-patterns.md) | Operations Frontend Patterns | Accepted | 2026-01-29 |
| [ADR-011](ADR-011-dues-frontend-patterns.md) | Dues Frontend Patterns | Accepted | 2026-01-30 |
| [ADR-012](ADR-012-audit-logging.md) | Audit Logging Architecture | Accepted | 2026-01-29 |
| [ADR-013](ADR-013-stripe-payment-integration.md) | Stripe Payment Integration | Accepted | 2026-01-30 |

## ADR Template

When creating a new ADR, use this template:

```markdown
# ADR-XXX: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Date
YYYY-MM-DD

## Context
What is the issue that we're seeing that is motivating this decision?

## Options Considered
What alternatives did we evaluate?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

## References
Links to related documentation or resources.
```

## When to Create an ADR

Create an ADR when making decisions about:
- Technology choices (databases, frameworks, libraries)
- Architecture patterns (authentication, caching, scaling)
- Data models and schemas
- API design approaches
- Infrastructure choices
- Security implementations

## How to Propose an ADR

1. Copy the template above
2. Create a new file: `ADR-XXX-descriptive-name.md`
3. Fill in all sections
4. Submit as PR with "ADR: Title" prefix
5. Discuss in PR comments
6. Once accepted, update status and merge

---

*Last Updated: January 30, 2026*
