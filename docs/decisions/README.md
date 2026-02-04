# Architecture Decision Records

> **Document Created:** January 2026
> **Last Updated:** February 4, 2026
> **Version:** 2.2
> **Status:** Active — 16 ADRs documented through v0.9.8-alpha

This directory contains Architecture Decision Records (ADRs) documenting significant technical decisions made during the development of IP2A Database v2 (UnionCore) — the union operations management platform for IBEW Local 46.

## What is an ADR?

An ADR captures an important architectural decision along with its context and consequences. They help future maintainers understand WHY something was built a certain way. ADRs are living documents — when a decision is implemented, the ADR is updated with implementation status, lessons learned, and references to the actual code.

## ADR Index

| ADR | Title | Status | Date | Implementation |
|-----|-------|--------|------|----------------|
| [ADR-001](ADR-001-database-choice.md) | Database Choice (PostgreSQL 16) | Implemented | 2025 (backfill) | Week 1+ — Railway production |
| [ADR-002](ADR-002-frontend-framework.md) | Frontend Framework (Jinja2 + HTMX + Alpine.js) | Implemented | 2026-01-27 | Weeks 1–19 |
| [ADR-003](ADR-003-authentication-strategy.md) | Authentication Strategy (JWT + Cookie) | Implemented | 2026-01-28 | Week 1, enhanced Week 16 |
| [ADR-004](ADR-004-file-storage-strategy.md) | File Storage (Object Storage) | Implemented (partial) | 2026-01-28 | Week 5–6 (local), S3 planned |
| [ADR-005](ADR-005-css-framework.md) | CSS Framework (Tailwind + DaisyUI) | Implemented | 2026-01 | Weeks 1–19 |
| [ADR-006](ADR-006-background-jobs.md) | Background Jobs (TaskService Abstraction) | Accepted (partial) | 2026-01 | FastAPI BackgroundTasks in use |
| [ADR-007](ADR-007-observability.md) | Observability Stack | Implemented (partial) | 2026-01 | Week 16 (Sentry + structured logging) |
| [ADR-008](ADR-008-dues-tracking-system.md) | Dues Tracking System Design | Implemented | 2026-01-28 | Weeks 10–11, Stripe in Week 11 |
| [ADR-009](ADR-009-migration-safety.md) | Migration Safety Strategy | Implemented | 2026-01-29 | Active since adoption |
| [ADR-010](ADR-010-operations-frontend-patterns.md) | Operations Frontend Patterns | Implemented | 2026-01-29 | Week 7 |
| [ADR-011](ADR-011-dues-frontend-patterns.md) | Dues Frontend Patterns | Implemented | 2026-01-30 | Week 10 |
| [ADR-012](ADR-012-audit-logging.md) | Audit Logging Architecture | Implemented | 2026-01-29 | Week 11 (NLRA compliant) |
| [ADR-013](ADR-013-stripe-payment-integration.md) | Stripe Payment Integration | Implemented | 2026-01-30 | Week 11 — live in production |
| [ADR-014](ADR-014-grant-compliance-reporting.md) | Grant Compliance Reporting | Implemented | 2026-02-02 | Week 14 |
| [ADR-015](ADR-015-referral-dispatch-architecture.md) | Referral & Dispatch Architecture | Implemented (partial) | 2026-02-04 | Weeks 20-25 — backend complete |
| [ADR-016](ADR-016-phase7-frontend-ui-patterns.md) | Phase 7 Frontend UI Patterns | Implemented | 2026-02-04 | Weeks 26-27 — Books & Dispatch UI |

### Status Legend

| Status | Meaning |
|--------|---------|
| **Implemented** | Decision made and fully built into the codebase |
| **Implemented (partial)** | Core decision implemented, some planned features still pending |
| **Accepted** | Decision made, not yet fully implemented |
| **Accepted (partial)** | Decision made, initial implementation in use, full scope pending |
| **Proposed** | Under discussion |
| **Deprecated** | No longer relevant |
| **Superseded** | Replaced by a newer ADR |

## ADR Template

When creating a new ADR, use this template:

```markdown
# ADR-XXX: Title

> **Document Created:** YYYY-MM-DD
> **Last Updated:** YYYY-MM-DD
> **Version:** 1.0
> **Status:** Proposed | Accepted | Implemented | Deprecated | Superseded

## Status
Proposed | Accepted | Implemented | Deprecated | Superseded

## Date
YYYY-MM-DD

## Context
What is the issue that we're seeing that is motivating this decision?

## Options Considered
What alternatives did we evaluate?

## Decision
What is the change that we're proposing and/or doing?

## Implementation Status
(Add after implementation begins)

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| ... | ✅ / 🔜 / ❌ | N | ... |

## Consequences
What becomes easier or more difficult to do because of this change?

## References
Links to related documentation or resources.

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan /docs/* and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 1.0
Last Updated: YYYY-MM-DD
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

## Phase 7 Note

ADR-015 documents the Referral & Dispatch system architecture decisions made during Weeks 20-22. This covers the 6 Phase 7 models, 19 enums, and key schema decisions including APN as DECIMAL(10,2) and the dual audit pattern. The remaining Phase 7 work (API routers, frontend UI, 78 reports) may warrant additional ADRs as implementation progresses. See `docs/phase7/` for detailed planning documentation.

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.2
Last Updated: February 4, 2026
Previous Version: 2.1 (February 4, 2026 — 15 ADRs through v0.9.5-alpha)
