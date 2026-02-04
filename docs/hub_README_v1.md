# UnionCore Documentation

> **Document Created:** January 2025 (original)
> **Last Updated:** February 4, 2026
> **Version:** v0.9.6-alpha — Phase 7 IN PROGRESS (Weeks 20-25 Complete)
> **Status:** Phase 7 Referral & Dispatch — Services + API Complete, Frontend Next
> **Repository:** https://github.com/theace26/IP2A-Database-v2

Welcome to the UnionCore (IP2A Database v2) documentation. This index helps you find what you need.

---

## Hub/Spoke Project Structure

Development planning and coordination uses a **Hub/Spoke model** organized across Claude AI projects (claude.ai). This does NOT affect the codebase architecture — it controls how development conversations and instruction documents are organized.

| Project | Scope | What Goes There | Status |
|---------|-------|-----------------|--------|
| **Hub** | Strategy, architecture, cross-cutting decisions, roadmap, docs | "How should we approach X?" | Active |
| **Spoke 2: Operations** | Dispatch/Referral, Pre-Apprenticeship, SALTing, Benevolence | Phase 7 implementation, instruction docs | Active — Phase 7 |
| **Spoke 1: Core Platform** | Members, Dues, Employers, Member Portal | Core module work | Create when needed |
| **Spoke 3: Infrastructure** | Dashboard/UI, Reports, Documents, Import/Export, Logging | Cross-cutting UI, observability, reporting | Create when needed |

**Key rules:**
- Claude AI cannot access conversations across projects. When a decision in the Hub affects a Spoke (or vice versa), provide a brief **handoff note** in the target project.
- **Claude Code** operates directly on the single codebase regardless of which Spoke produced the instruction document.
- **Sprint Weeks ≠ Calendar Weeks.** Instruction document "weeks" (Week 20, Week 25, etc.) are sprint numbers. At 5-10 hours/week development pace, each sprint takes 1-2 calendar weeks to complete.

### Cross-Cutting Concerns Protocol

Some files are shared across all Spokes and require coordination to avoid merge conflicts:

| Shared Resource | Location | Coordination Rule |
|----------------|----------|-------------------|
| Router registration | `src/main.py` | When adding new routers, note in session summary for Hub handoff |
| Test fixtures | `tests/conftest.py` | Auth and seed data fixtures shared across all test modules — do not duplicate |
| Base templates | `src/templates/base.html`, `_sidebar.html` | Sidebar navigation changes affect all modules — note in session summary |
| Alembic migrations | `alembic/versions/` | Only one Spoke should create migrations at a time to avoid conflicts |
| CLAUDE.md | `CLAUDE.md` (repo root) | Updated by Claude Code at end of each session — reflects all Spokes |

**When in doubt:** If your Spoke work touches a shared file, add a note to your session summary and the user will create a Hub handoff note.

### What Lives Where

| Document Type | Location | Maintained By |
|--------------|----------|---------------|
| Architecture decisions (ADRs) | `docs/decisions/` | Hub |
| Roadmap and milestone tracking | `docs/` | Hub |
| Phase 7 planning & schema guidance | `docs/phase7/` | Hub + Spoke 2 |
| Instruction documents (week-by-week) | `docs/instructions/` | Spoke that owns the phase |
| Session logs | `docs/reports/session-logs/` | Claude Code (all Spokes) |
| Standards and coding conventions | `docs/standards/` | Hub |
| Runbooks and operational procedures | `docs/runbooks/` | Hub (policy) + Spoke 3 (implementation) |

---

## Quick Links

| I want to... | Go to... |
|--------------|----------|
| Understand the system | [System Overview](architecture/SYSTEM_OVERVIEW.md) |
| Set up development | [Getting Started](guides/getting-started.md) |
| See current progress | [Milestone Checklist](IP2A_MILESTONE_CHECKLIST.md) |
| See the development roadmap | [Backend Roadmap v4.0](IP2A_BACKEND_ROADMAP.md) |
| Use the CLI tools | [ip2adb Reference](reference/ip2adb-cli.md) |
| Track member dues | [Dues Tracking Guide](guides/dues-tracking.md) |
| Implement audit logging | [Audit Logging Guide](guides/audit-logging.md) |
| Understand audit architecture | [ADR-008: Audit Logging](decisions/ADR-008-audit-logging.md) |
| Phase 7: Referral & Dispatch | [Phase 7 Plan](phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md) |
| Phase 7: Schema guidance | [Schema Guidance Vol. 1](phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE.md) |
| Phase 7: Batch 2 data findings | [Schema Guidance Vol. 2](phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE_VOL2.md) |
| Phase 7: Full project context | [Consolidated Continuity Doc](phase7/UNIONCORE_CONTINUITY_DOCUMENT_CONSOLIDATED.md) |
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
- [ADR Index](decisions/README.md) — All 15 decision records (ADR-001 through ADR-015) *(⚠️ VERIFY count)*
- [ADR-008: Audit Logging](decisions/ADR-008-audit-logging.md) — NLRA compliance, role-based access
- [ADR-009: Dependency Management](decisions/ADR-009-dependency-management.md) — Long-term maintainability strategy
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
Phase 7: Referral & Dispatch System documentation. This is the project's current major phase, replacing LaborPower's referral module with UnionCore's native dispatch system. **Owned by: Spoke 2 (Operations)**

**Planning & Architecture:**
- [Phase 7 Plan](phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md) — Full implementation plan
- [Implementation Plan v2](phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md) — Technical details and corrected data model

**Data Analysis & Schema Guidance:**
- [Schema Guidance Vol. 1](phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE.md) — Batch 1 analysis: 12 PDF exports, 7 critical schema findings, corrected DDL
- [Schema Guidance Vol. 2](phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE_VOL2.md) — Batch 2 analysis: 12 additional exports, RESIDENTIAL contract code discovery, complete book catalog
- [Consolidated Continuity Document](phase7/UNIONCORE_CONTINUITY_DOCUMENT_CONSOLIDATED.md) — Full project context: architecture, business rules, gap analysis, schema corrections, data gaps

**Reference Data:**
- [LaborPower Reports Inventory](phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md) — 78 de-duplicated reports (91 raw) organized by priority tier
- [Local 46 Referral Books](phase7/LOCAL46_REFERRAL_BOOKS.md) — Seed data for referral books
- [LaborPower Gap Analysis](phase7/LABORPOWER_GAP_ANALYSIS.md) — Coverage analysis of current system vs UnionCore

**Session Continuity:**
- [Phase 7 Continuity Document](phase7/PHASE7_CONTINUITY_DOC.md) — Session handoff doc (superseded by Consolidated Continuity Doc)

### `/instructions`
Claude Code instruction documents for development sessions.

| Week | Focus | Spoke | Status |
|------|-------|-------|--------|
| 20-22 | Phase 7 Models, Enums, Foundation Services | Spoke 2 | ✅ Complete |
| 23-25 | Phase 7 Services + API Routers | Spoke 2 | ✅ Complete |
| 26 | Books & Registration UI | Spoke 2 | 🔜 Next |
| 27 | Dispatch Workflow UI | Spoke 2 | Planned |
| 28 | Reports Navigation & Dashboard | Spoke 2 | Planned |
| 19 | Analytics Dashboard | *(pre-Hub/Spoke)* | ✅ Complete |
| 18 | Mobile PWA | *(pre-Hub/Spoke)* | ✅ Complete |
| 17 | Post-Launch Ops | *(pre-Hub/Spoke)* | ✅ Complete |
| 16 | Production Hardening | *(pre-Hub/Spoke)* | ✅ Complete |
| 14 | Grant Compliance | *(pre-Hub/Spoke)* | ✅ Complete |
| 1-13 | Phase 6 Frontend Build | *(pre-Hub/Spoke)* | ✅ Complete |

### `/historical`
Archived documentation from previous iterations. Retained for reference only.

---

## Current Status

**Version:** v0.9.6-alpha — Phase 7 Weeks 20-25 Complete (Services + API)

| Component | Status | Tests | Spoke |
|-----------|--------|-------|-------|
| Backend API (Phases 0-4) | ✅ Complete | 165+ | *(pre-Hub/Spoke)* |
| Frontend UI (Weeks 1-14) | ✅ Complete | 200+ | *(pre-Hub/Spoke)* |
| Stripe Payment Integration | ✅ Complete | 25 | *(pre-Hub/Spoke)* |
| Audit Infrastructure | ✅ Complete | 19 | *(pre-Hub/Spoke)* |
| Grant Compliance | ✅ Complete | ~20 | *(pre-Hub/Spoke)* |
| Production Hardening (Week 16) | ✅ Complete | 32 | *(pre-Hub/Spoke)* |
| Post-Launch Operations (Week 17) | ✅ Complete | 13 | *(pre-Hub/Spoke)* |
| Mobile PWA (Week 18) | ✅ Complete | 14 | *(pre-Hub/Spoke)* |
| Analytics Dashboard (Week 19) | ✅ Complete | 19 | *(pre-Hub/Spoke)* |
| Phase 7 Foundation — Weeks 20-22 | ✅ Complete | 20+ | Spoke 2 |
| Phase 7 Services — Weeks 23-24 | ✅ Complete | *(included above)* | Spoke 2 |
| Phase 7 API Routers — Week 25 | ✅ Complete | *(included above)* | Spoke 2 |
| **Total** | **Phase 7 Services + API Complete** | **~490+ ⚠️ VERIFY** | |

### Phase 7 Progress Summary (Weeks 20-25) — Spoke 2

| Sprint | What Was Built | Key Artifacts |
|--------|---------------|---------------|
| Weeks 20-21 | 6 ORM models, 19 enums, Pydantic schemas | Models: ReferralBook, BookRegistration, RegistrationActivity, LaborRequest, JobBid, Dispatch |
| Week 22 | 2 foundation services | ReferralBookService, BookRegistrationService |
| Weeks 23-24 | 5 additional services | LaborRequestService, JobBidService, DispatchService, QueueService, EnforcementService |
| Week 25 | 5 API routers (~51 endpoints) | referral_books_api, registration_api, labor_request_api, job_bid_api, dispatch_api |

### What's Next — Spoke 2

| Sprint | Focus | Sub-Phase |
|--------|-------|-----------|
| Week 26 | Books & Registration UI | 7e |
| Week 27 | Dispatch Workflow UI | 7e |
| Week 28 | Reports Navigation & Dashboard | 7e/7f |

### Recent Milestones
- **v0.9.6-alpha** — Phase 7 Weeks 20-25: 7 services, 5 routers, ~51 API endpoints
- **v0.9.5-alpha** — Phase 7 Weeks 20-22: Models, enums, foundation services
- **v0.9.4-alpha** — Analytics dashboard with Chart.js, custom report builder
- **v0.9.3-alpha** — Mobile PWA with offline support and service worker
- **v0.9.2-alpha** — Backup scripts, admin metrics, incident response runbook
- **v0.9.1-alpha** — Security headers, Sentry integration, structured logging

---

## Phase 7 Overview — Referral & Dispatch (Spoke 2)

### Report Priority Tiers

| Priority | Reports | Scope |
|----------|---------|-------|
| P0 | 16 | Daily Operational (dispatch logs, book status) |
| P1 | 33 | Employment Tracking, Contractor Workforce |
| P2 | 22 | Analytics, Historical Trends |
| P3 | 7 | Advanced Analytics, Projections |
| **Total** | **78** | **De-duplicated from 91 raw reports** |

### Sub-Phase Breakdown (7a–7g)

| Sub-Phase | Focus | Hours | Status | Spoke |
|-----------|-------|-------|--------|-------|
| 7a | Data Collection — 3 Priority 1 exports from LaborPower | 3-5 | ⛔ Blocked (LaborPower access) | Spoke 2 |
| 7b | Schema Finalization — DDL, Alembic migrations, seed data | 10-15 | ✅ Complete (Weeks 20-21) | Spoke 2 |
| 7c | Core Services + API — 14 business rules, CRUD, dispatch logic | 25-35 | ✅ Complete (Weeks 22-25) | Spoke 2 |
| 7d | Import Tooling — CSV pipeline: employers → registrations → dispatch | 15-20 | ⬜ Pending | Spoke 2 |
| 7e | Frontend UI — book management, dispatch board, web bidding | 20-30 | 🔜 Next (Weeks 26-28) | Spoke 2 |
| 7f | Reports P0+P1 — 49 reports via WeasyPrint + Chart.js | 20-30 | ⬜ Pending | Spoke 2 or 3 |
| 7g | Reports P2+P3 — 29 reports, analytics, projections | 10-15 | ⬜ Pending | Spoke 2 or 3 |

> **Note:** Sub-Phase 7a (data collection) remains blocked pending 3 Priority 1 data exports from LaborPower. Sub-Phases 7b and 7c were completed using available data from Batch 1 and Batch 2 analysis. Schema will be refined when Priority 1 data becomes available.

### Phase 7 Key Documents

| Document | Purpose | Location |
|----------|---------|----------|
| Consolidated Continuity Doc | Complete project context, all findings, full gap analysis | [phase7/](phase7/UNIONCORE_CONTINUITY_DOCUMENT_CONSOLIDATED.md) |
| Backend Roadmap v4.0 | Master plan with §7.1–§7.9 subsections | [docs/](IP2A_BACKEND_ROADMAP.md) |
| Milestone Checklist | Actionable task lists for all 7 sub-phases | [docs/](IP2A_MILESTONE_CHECKLIST.md) |
| Schema Guidance Vol. 1 | Batch 1 data analysis, 7 critical findings, corrected DDL | [phase7/](phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE.md) |
| Schema Guidance Vol. 2 | Batch 2 analysis, RESIDENTIAL discovery, book catalog | [phase7/](phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE_VOL2.md) |
| Reports Inventory | 78 reports organized by priority with filter dimensions | [phase7/](phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md) |
| Implementation Plan v2 | Technical details, corrected data model, 12 new tables | [phase7/](phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md) |
| Gap Analysis | LaborPower coverage analysis against UnionCore schema | [phase7/](phase7/LABORPOWER_GAP_ANALYSIS.md) |

### Critical Schema Reminders

These findings from data analysis affect all Phase 7 development. Any new thread or Claude Code session working on Phase 7 **must** be aware of:

1. **APN = DECIMAL(10,2)**, NOT INTEGER — integer part is Excel serial date, decimal is secondary sort key
2. **Duplicate APNs exist** — unique constraint must be `UNIQUE(member_id, book_id, book_priority_number)`
3. **Member ≠ Student** — separate entities with distinct lifecycles and data models
4. **Book Name ≠ Contract Code** — STOCKMAN book maps to STOCKPERSON contract; 3 books have NO matching contract code
5. **RESIDENTIAL is the 8th contract code** — 259 employers, 80% overlap with WIREPERSON, 52 residential-only
6. **11 known books**, not the 8 originally documented — includes TERO APPR WIRE (compound book) and region-specific books
7. **14 business rules** from Referral Procedures (Oct 2024) govern dispatch logic, re-registration, check marks, exemptions

> Full detail in [Schema Guidance Vol. 1](phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE.md), [Vol. 2](phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE_VOL2.md), and [Consolidated Continuity Doc](phase7/UNIONCORE_CONTINUITY_DOCUMENT_CONSOLIDATED.md).

---

## Documentation Update Project Status

All project documentation is being systematically updated to reflect the current state and incorporate Phase 7 findings.

| Batch | Scope | Files | Status |
|-------|-------|-------|--------|
| Batch 1 | Core project files (CHANGELOG, README, CONTRIBUTING) | 3 | ✅ Complete |
| Batch 2 | Architecture docs (SYSTEM_OVERVIEW, AUTH, FILE_STORAGE, SCALABILITY) | 4 | ✅ Complete |
| Batch 3 | ADRs (README + ADR-001 through ADR-014) | 15 | ✅ Complete |
| Batch 4a | Phase 7 planning (GAP_ANALYSIS, IMPLEMENTATION_PLAN, REFERRAL_BOOKS, CONTINUITY_ADDENDUM) | 4 | ✅ Complete |
| Batch 4b | Phase 7 planning (REFERRAL_DISPATCH_PLAN, IMPL_PLAN_v2, REPORTS_INVENTORY, AUDIT_ARCHITECTURE) | 4 | ✅ Complete |
| Roadmap | IP2A_BACKEND_ROADMAP.md → v4.0 (Hub/Spoke migration) | 1 | ✅ Complete |
| Checklist | IP2A_MILESTONE_CHECKLIST.md → v2.0 (Hub/Spoke migration) | 1 | ✅ Complete |
| README | docs/README.md → hub_README_v1 (Hub/Spoke migration) | 1 | ✅ Complete |
| Batch 5 | Standards, Guides, References, Runbooks, Instructions | TBD | 🔜 Next |

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
| `registrations` | All actions *(Phase 7 — Spoke 2)* |
| `dispatches` | All actions *(Phase 7 — Spoke 2)* |
| `check_marks` | All actions *(Phase 7 — Spoke 2)* |

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

## 🔒 End-of-Session Documentation (MANDATORY)

**Before completing ANY development session:**

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

See [End-of-Session Documentation](standards/END_OF_SESSION_DOCUMENTATION.md) for full checklist.

---

### Version History

| Date | Version | Changes |
|------|---------|---------|
| February 4, 2026 | hub_README_v1 | Hub/Spoke project structure, cross-cutting concerns protocol, updated status to v0.9.6-alpha, Weeks 20-25 reflected, instruction weeks table with Spoke assignments, archived pre-Hub/Spoke READMEs to docs/historical/ |
| February 3, 2026 | docs_README_UPDATED | v0.9.4-alpha status, Phase 7 report priority table, instruction weeks through 19, Schema Guidance links |
| January 2026 | (original) | Initial feature-complete documentation structure |

---

*Last Updated: February 4, 2026*
*Hub/Spoke Model: Added February 2026*
