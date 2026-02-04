# IP2A Documentation

> **Document Created:** January 2025 (original)
> **Last Updated:** February 3, 2026
> **Version:** v0.9.4-alpha (FEATURE-COMPLETE)
> **Status:** Phase 7 Planning — Referral & Dispatch
> **Repository:** https://github.com/theace26/IP2A-Database-v2

Welcome to the IP2A Database documentation. This index helps you find what you need.

---

## Quick Links

| I want to... | Go to... |
|--------------|----------|
| Understand the system | [System Overview](architecture/SYSTEM_OVERVIEW.md) |
| Set up development | [Getting Started](guides/getting-started.md) |
| See current progress | [Milestone Checklist](IP2A_MILESTONE_CHECKLIST.md) |
| See the development roadmap | [Backend Roadmap v3.0](IP2A_BACKEND_ROADMAP.md) |
| Use the CLI tools | [ip2adb Reference](reference/ip2adb-cli.md) |
| Track member dues | [Dues Tracking Guide](guides/dues-tracking.md) |
| Implement audit logging | [Audit Logging Guide](guides/audit-logging.md) |
| Understand audit architecture | [ADR-012: Audit Logging](decisions/ADR-012-audit-logging.md) |
| Phase 7: Referral & Dispatch | [Phase 7 Plan](phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md) |
| Phase 7: Full project context | [Consolidated Continuity Doc](phase7/UnionCore_Continuity_Document_Consolidated.md) |
| LaborPower report inventory | [Reports Inventory](phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md) |
| End-of-session docs rules | [Documentation Mandate](standards/END_OF_SESSION_DOCUMENTATION.md) |
| Understand a decision | [Architecture Decisions](decisions/README.md) |
| See what changed | [CHANGELOG](../CHANGELOG.md) |
| Contribute | [Contributing Guide](../CONTRIBUTING.md) |

---

## Documentation Structure

### `/architecture`
Technical architecture documents describing how the system is built.
- [System Overview](architecture/SYSTEM_OVERVIEW.md) — High-level architecture
- [Authentication Architecture](architecture/AUTHENTICATION_ARCHITECTURE.md) — Auth system design
- [File Storage Architecture](architecture/FILE_STORAGE_ARCHITECTURE.md) — File handling
- [Scalability Architecture](architecture/SCALABILITY_ARCHITECTURE.md) — Scaling to 4,000+ users
- [Audit Architecture](architecture/AUDIT_ARCHITECTURE.md) — Compliance and audit trail design
- [Diagrams](architecture/diagrams/) — Mermaid diagrams

### `/decisions`
Architecture Decision Records (ADRs) explaining WHY we made specific choices.
- [ADR Index](decisions/README.md) — All 14 decision records (ADR-001 through ADR-014)
- [ADR-007: Observability](decisions/ADR-007-observability.md) — Sentry integration, structured logging
- [ADR-012: Audit Logging](decisions/ADR-012-audit-logging.md) — NLRA compliance, role-based access
- [ADR-013: Stripe Integration](decisions/ADR-013-stripe-payment-integration.md) — Payment processing
- [ADR-014: Grant Compliance](decisions/ADR-014-grant-compliance-reporting.md) — Grant tracking and reporting

### `/guides`
How-to guides for common tasks and workflows.
- [Audit Logging Guide](guides/audit-logging.md) — Implement audit trails (CRITICAL)
- [Dues Tracking Guide](guides/dues-tracking.md) — Member dues management
- [Project Strategy](guides/project-strategy.md) — Overall project approach
- [Testing Strategy](guides/testing-strategy.md) — Testing philosophy

### `/reference`
Quick reference for CLI tools and commands.
- [ip2adb CLI](reference/ip2adb-cli.md) — Database management tool
- [Dues API Reference](reference/dues-api.md) — Dues tracking endpoints
- [Audit API Reference](reference/audit-api.md) — Audit log endpoints
- [Phase 2 Quick Reference](reference/phase2-quick-reference.md) — Union operations models and endpoints
- [Integrity Check](reference/integrity-check.md) — Data quality checks

### `/reports`
Generated reports from testing, assessments, and sessions.
- [Phase 2.1 Summary](reports/phase-2.1-summary.md) — Auto-healing implementation
- [Scaling Readiness](reports/scaling-readiness.md) — Production capacity assessment
- [Stress Test Analytics](reports/stress-test-analytics.md) — Performance benchmarks
- [Session Logs](reports/session-logs/) — Development session summaries

### `/runbooks`
Operational procedures for deployment and maintenance.
- [Deployment](runbooks/deployment.md) — Deploy new versions
- [Backup & Restore](runbooks/backup-restore.md) — Database backups
- [Disaster Recovery](runbooks/disaster-recovery.md) — Emergency procedures
- [Audit Log Maintenance](runbooks/audit-maintenance.md) — Archive and retention procedures
- [Incident Response](runbooks/incident-response.md) — Emergency incident procedures

### `/standards`
Coding standards and conventions for contributors.
- [End-of-Session Documentation](standards/END_OF_SESSION_DOCUMENTATION.md) — **MANDATORY** session close procedure
- [Audit Logging Standards](standards/audit-logging.md) — Compliance requirements (MUST READ)
- [Coding Standards](standards/coding-standards.md) — Code style guide
- [Naming Conventions](standards/naming-conventions.md) — Naming patterns

### `/phase7`
Phase 7: Referral & Dispatch System documentation. This is the project's next major phase, replacing LaborPower's referral module with UnionCore's native dispatch system.

**Planning & Architecture:**
- [Phase 7 Plan](phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md) — Full implementation plan
- [Implementation Plan v2](phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md) — Technical details and corrected data model
- [Implementation Plan (original)](phase7/LABORPOWER_IMPLEMENTATION_PLAN.md) — Original planning doc

**Data Analysis & Schema Guidance:**
- [Consolidated Continuity Document](phase7/UnionCore_Continuity_Document_Consolidated.md) — Full project context: architecture, business rules, gap analysis, schema corrections
- [LaborPower Gap Analysis](phase7/LABORPOWER_GAP_ANALYSIS.md) — Coverage analysis of current system vs UnionCore

**Reference Data:**
- [LaborPower Reports Inventory](phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md) — 78 de-duplicated reports (91 raw) organized by priority tier
- [Local 46 Referral Books](phase7/LOCAL46_REFERRAL_BOOKS.md) — Seed data for referral books

**Session Continuity:**
- [Phase 7 Continuity Document](phase7/PHASE7_CONTINUITY_DOC.md) — Session handoff doc for Phase 7 development
- [Phase 7 Continuity Addendum](phase7/PHASE7_CONTINUITY_DOC_ADDENDUM.md) — Schedule reconciliation, report sprint overlap

### `/instructions`
Claude Code instruction documents for development sessions.
- [Week 19 Instructions](instructions/) — Analytics Dashboard (Complete)
- [Week 18 Instructions](instructions/) — Mobile PWA (Complete)
- [Week 17 Instructions](instructions/) — Post-Launch Ops (Complete)
- [Week 16 Instructions](instructions/) — Production Hardening (Complete)
- [Week 14 Instructions](instructions/week12_overlooked/) — Grant Compliance (Complete)
- [Week 13 Instructions](instructions/week12_overlooked/) — Entity Audit (Complete)
- [Week 12 Instructions](instructions/week12_istructions/) — Profile & Settings (Complete)
- [Week 11 Instructions](instructions/week11–stripe/) — Audit Infrastructure + Stripe (Complete)
- [Week 10 Instructions](instructions/dues/) — Dues UI (Complete)
- [Week 9 Instructions](instructions/week9_instructions/) — Documents Frontend (Complete)
- [Week 8 Instructions](instructions/week8_instructions/) — Reports & Export (Complete)
- [Earlier weeks...](instructions/)

---

## Current Status

**Version:** v0.9.4-alpha (FEATURE-COMPLETE — Weeks 1-19)

| Component | Status | Tests |
|-----------|--------|-------|
| Backend API | ✅ Complete | 165 |
| Frontend UI (Weeks 1-14) | ✅ Complete | 200+ |
| Stripe Payment Integration | ✅ Complete | 25 |
| Audit Infrastructure | ✅ Complete | 19 |
| Grant Compliance | ✅ Complete | ~20 |
| Production Hardening (Week 16) | ✅ Complete | 32 |
| Post-Launch Operations (Week 17) | ✅ Complete | 13 |
| Mobile PWA (Week 18) | ✅ Complete | 14 |
| Analytics Dashboard (Week 19) | ✅ Complete | 19 |
| **Total** | **Feature Complete** | **~470** |

### Recent Milestones
- **v0.9.4-alpha** — Analytics dashboard with Chart.js, custom report builder
- **v0.9.3-alpha** — Mobile PWA with offline support and service worker
- **v0.9.2-alpha** — Backup scripts, admin metrics, incident response runbook
- **v0.9.1-alpha** — Security headers, Sentry integration, structured logging
- **v0.9.0-alpha** — Grant compliance reporting with Excel export

---

## Next: Phase 7 — Referral & Dispatch

Implements the out-of-work referral and dispatch system for IBEW Local 46, building UnionCore's native replacement for LaborPower's referral module. Estimated at **100-150 hours** across 7 sub-phases.

### Report Parity Target

| Priority | Reports | Description |
|----------|---------|-------------|
| P0 | 16 | Dispatch, Book Status, Referral Activity |
| P1 | 33 | Employment Tracking, Contractor Workforce |
| P2 | 22 | Analytics, Historical Trends |
| P3 | 7 | Advanced Analytics, Projections |
| **Total** | **78** | **De-duplicated from 91 raw reports** |

### Sub-Phase Breakdown (7a–7g)

| Sub-Phase | Focus | Hours | Blocked By |
|-----------|-------|-------|------------|
| 7a | Data Collection — 3 Priority 1 exports from LaborPower | 3-5 | ⛔ LaborPower access |
| 7b | Schema Finalization — DDL, Alembic migrations, seed data | 10-15 | 7a |
| 7c | Core Services + API — 14 business rules, CRUD, dispatch logic | 25-35 | 7b |
| 7d | Import Tooling — CSV pipeline | 15-20 | 7b |
| 7e | Frontend UI — book management, dispatch board, web bidding | 20-30 | 7c |
| 7f | Reports P0+P1 — 49 reports | 20-30 | 7c |
| 7g | Reports P2+P3 — 29 reports | 10-15 | 7f |

> **Current blocker:** Sub-Phase 7a requires 3 Priority 1 data exports from LaborPower.

### Critical Schema Reminders

1. **APN = DECIMAL(10,2)**, NOT INTEGER
2. **Duplicate APNs exist** — unique constraint must be `UNIQUE(member_id, book_id, book_priority_number)`
3. **Member ≠ Student** — separate entities
4. **Book Name ≠ Contract Code** — STOCKMAN book maps to STOCKPERSON contract
5. **RESIDENTIAL is the 8th contract code** — 259 employers
6. **11 known books**, not 8 — includes TERO APPR WIRE (compound book)
7. **14 business rules** from Referral Procedures (Oct 2024)

See [Phase 7 Plan](phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md) and [Consolidated Continuity Doc](phase7/UnionCore_Continuity_Document_Consolidated.md) for full details.

---

## Audit Logging Quick Reference

### What Gets Audited

All changes to member-related data are automatically logged:

| Table | Tracked Actions |
|-------|-----------------|
| `members` | READ, CREATE, UPDATE, DELETE |
| `member_notes` | CREATE, UPDATE, DELETE |
| `member_employments` | CREATE, UPDATE, DELETE |
| `students` | READ, CREATE, UPDATE, DELETE |
| `users` | CREATE, UPDATE, DELETE |
| `dues_payments` | CREATE, UPDATE, DELETE |
| `grievances` | All actions |
| `benevolence_applications` | All actions |

> **Phase 7 additions:** `registrations`, `dispatches`, and `check_marks` tables will require full audit coverage per [Audit Architecture](architecture/AUDIT_ARCHITECTURE.md).

### How to Add Auditing to New Endpoints

```python
from src.services import audit_service
from src.middleware import get_audit_context

@router.post("/")
def create_record(data: CreateSchema, db: Session = Depends(get_db)):
    record = service.create(db, data)

    # Log the creation
    audit_context = get_audit_context()
    audit_service.log_create(
        db=db,
        table_name="your_table",
        record_id=record.id,
        new_values=record_to_dict(record),
        **audit_context
    )

    return record
```

### Compliance Requirements

- **Retention:** 7 years minimum (NLRA)
- **Immutability:** Audit logs cannot be modified or deleted (PostgreSQL triggers)
- **Access:** Role-based, with sensitive field redaction
- **Archive:** Logs older than 3 years moved to S3 Glacier

---

## Getting Help

- **GitHub Issues**: https://github.com/theace26/IP2A-Database-v2/issues
- **Documentation Updates**: Submit PRs to improve these docs
- **Questions**: Open a discussion or issue

---

## 📝 End-of-Session Documentation (MANDATORY)

**Before completing ANY development session:**

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

See [End-of-Session Documentation](standards/END_OF_SESSION_DOCUMENTATION.md) for full checklist.

---

**Document Version:** 3.0
**Last Updated:** February 3, 2026
**Previous Version:** 2.0 (February 2, 2026 — v0.9.4-alpha status, basic Phase 7 section)
