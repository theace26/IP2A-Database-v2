# IP2A Documentation

Welcome to the IP2A Database documentation. This index helps you find what you need.

## Quick Links

| I want to... | Go to... |
|--------------|----------|
| Understand the system | [System Overview](architecture/SYSTEM_OVERVIEW.md) |
| Set up development | [Getting Started](guides/getting-started.md) |
| See current progress | [Milestone Checklist](IP2A_MILESTONE_CHECKLIST.md) |
| Use the CLI tools | [ip2adb Reference](reference/ip2adb-cli.md) |
| Track member dues | [Dues Tracking Guide](guides/dues-tracking.md) |
| **Implement audit logging** | **[Audit Logging Guide](guides/audit-logging.md)** |
| **Understand audit architecture** | **[ADR-008: Audit Logging](decisions/ADR-008-audit-logging.md)** |
| **Phase 7: Referral & Dispatch** | **[Phase 7 Plan](phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md)** |
| **LaborPower report inventory** | **[Reports Inventory](phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md)** |
| **End-of-session docs rules** | **[Documentation Mandate](standards/END_OF_SESSION_DOCUMENTATION.md)** |
| Understand a decision | [Architecture Decisions](decisions/README.md) |
| See what changed | [CHANGELOG](../CHANGELOG.md) |
| Contribute | [Contributing Guide](../CONTRIBUTING.md) |

## Documentation Structure

### `/architecture`
Technical architecture documents describing how the system is built.
- [System Overview](architecture/SYSTEM_OVERVIEW.md) - High-level architecture
- [Authentication Architecture](architecture/AUTHENTICATION_ARCHITECTURE.md) - Auth system design
- [File Storage Architecture](architecture/FILE_STORAGE_ARCHITECTURE.md) - File handling
- [Scalability Architecture](architecture/SCALABILITY_ARCHITECTURE.md) - Scaling to 4,000+ users
- **[Audit Architecture](architecture/AUDIT_ARCHITECTURE.md) - Compliance and audit trail design**
- [Diagrams](architecture/diagrams/) - Mermaid diagrams

### `/decisions`
Architecture Decision Records (ADRs) explaining WHY we made specific choices.
- [ADR Index](decisions/README.md) - All decision records
- **[ADR-008: Audit Logging](decisions/ADR-008-audit-logging.md) - NLRA compliance, role-based access**

### `/guides`
How-to guides for common tasks and workflows.
- **[Audit Logging Guide](guides/audit-logging.md) - Implement audit trails (CRITICAL)**
- [Dues Tracking Guide](guides/dues-tracking.md) - Member dues management
- [Project Strategy](guides/project-strategy.md) - Overall project approach
- [Testing Strategy](guides/testing-strategy.md) - Testing philosophy

### `/reference`
Quick reference for CLI tools and commands.
- [ip2adb CLI](reference/ip2adb-cli.md) - Database management tool
- [Dues API Reference](reference/dues-api.md) - Dues tracking endpoints
- **[Audit API Reference](reference/audit-api.md) - Audit log endpoints**
- [Phase 2 Quick Reference](reference/phase2-quick-reference.md) - Union operations models and endpoints
- [Integrity Check](reference/integrity-check.md) - Data quality checks

### `/reports`
Generated reports from testing, assessments, and sessions.
- [Phase 2.1 Summary](reports/phase-2.1-summary.md) - Auto-healing implementation
- [Scaling Readiness](reports/scaling-readiness.md) - Production capacity assessment
- [Stress Test Analytics](reports/stress-test-analytics.md) - Performance benchmarks
- [Session Logs](reports/session-logs/) - Development session summaries

### `/runbooks`
Operational procedures for deployment and maintenance.
- [Deployment](runbooks/deployment.md) - Deploy new versions
- [Backup & Restore](runbooks/backup-restore.md) - Database backups
- [Disaster Recovery](runbooks/disaster-recovery.md) - Emergency procedures
- **[Audit Log Maintenance](runbooks/audit-maintenance.md) - Archive and retention procedures**

### `/standards`
Coding standards and conventions for contributors.
- **[End-of-Session Documentation](standards/END_OF_SESSION_DOCUMENTATION.md) - MANDATORY session close procedure**
- **[Audit Logging Standards](standards/audit-logging.md) - Compliance requirements (MUST READ)**
- [Coding Standards](standards/coding-standards.md) - Code style guide
- [Naming Conventions](standards/naming-conventions.md) - Naming patterns

### `/phase7`
Phase 7: Referral & Dispatch System documentation.
- **[Phase 7 Plan](phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md) - Full implementation plan**
- **[Implementation Plan v2](phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md) - Technical details**
- **[LaborPower Reports Inventory](phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md) - 78+ reports to build**
- [Local 46 Referral Books](phase7/LOCAL46_REFERRAL_BOOKS.md) - Seed data
- [LaborPower Gap Analysis](phase7/LABORPOWER_GAP_ANALYSIS.md) - Gap analysis
- [Phase 7 Continuity Document](phase7/PHASE7_CONTINUITY_DOC.md) - Session handoff doc

### `/instructions`
Claude Code instruction documents for development sessions.
- **[Week 11 Instructions](instructions/week11_instructions/) - Audit Trail & History UI (NEXT)**
- [Week 10 Instructions](instructions/dues_ui_session_a.md) - Dues UI (Current)
- [Week 9 Instructions](instructions/week9_instructions/) - Documents Frontend
- [Week 8 Instructions](instructions/week8_instructions/) - Reports & Export
- [Earlier weeks...](instructions/)

---

## Current Status

**Version:** v0.7.8 (Phase 6 Week 10 Session A Complete)

| Component | Status | Tests |
|-----------|--------|-------|
| Backend API | ✅ Complete | 165 |
| Frontend UI | 🟡 In Progress | 149 |
| **Audit Trail** | **🟡 Infrastructure done, UI pending** | **Integrated** |
| **Total** | **In Progress** | **312** |

### Upcoming: Week 11 - Audit Trail Completeness

**CRITICAL COMPLIANCE WORK** - All member information changes must be audited for NLRA (7-year retention).

| Task | Priority |
|------|----------|
| Add immutability trigger to `audit_logs` | 🔴 Critical |
| Create `member_notes` table | 🔴 Critical |
| Audit log viewer UI with role filtering | 🟡 High |
| Inline history on member detail page | 🟡 High |
| Export for compliance officers | 🟢 Medium |

See [Milestone Checklist](IP2A_MILESTONE_CHECKLIST.md) for detailed progress.

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
- **Immutability:** Audit logs cannot be modified or deleted
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

> Update *ANY* and *ALL* relevant documents to capture progress made this session.
> Scan `/docs/*` and make or create any relevant updates/documents to keep a
> historical record as the project progresses. Do not forget about ADRs —
> update as necessary.

See [End-of-Session Documentation](standards/END_OF_SESSION_DOCUMENTATION.md) for full checklist.

---

*Last Updated: February 2, 2026*
