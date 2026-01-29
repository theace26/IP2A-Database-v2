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
- [Diagrams](architecture/diagrams/) - Mermaid diagrams

### `/decisions`
Architecture Decision Records (ADRs) explaining WHY we made specific choices.
- [ADR Index](decisions/README.md) - All decision records

### `/guides`
How-to guides for common tasks and workflows.
- [Audit Logging Guide](guides/audit-logging.md) - Implement audit trails
- [Dues Tracking Guide](guides/dues-tracking.md) - Member dues management (Phase 4)
- [Project Strategy](guides/project-strategy.md) - Overall project approach
- [Testing Strategy](guides/testing-strategy.md) - Testing philosophy

### `/reference`
Quick reference for CLI tools and commands.
- [ip2adb CLI](reference/ip2adb-cli.md) - Database management tool
- [Dues API Reference](reference/dues-api.md) - Dues tracking endpoints (Phase 4)
- [Phase 2 Quick Reference](reference/phase2-quick-reference.md) - Union operations models and endpoints
- [Integrity Check](reference/integrity-check.md) - Data quality checks
- [Load Testing](reference/load-testing.md) - Performance testing
- [Stress Testing](reference/stress-testing.md) - Large-scale testing

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

### `/standards`
Coding standards and conventions for contributors.
- [Audit Logging Standards](standards/audit-logging.md) - Compliance requirements
- [Coding Standards](standards/coding-standards.md) - Code style guide
- [Naming Conventions](standards/naming-conventions.md) - Naming patterns

### `/instructions`
Claude Code instruction documents for development sessions.
- [Week 10 Instructions](instructions/dues_ui_session_a.md) - Dues UI (Current)
- [Week 9 Instructions](instructions/week9_instructions/) - Documents Frontend
- [Week 8 Instructions](instructions/week8_instructions/) - Reports & Export
- [Week 7 Instructions](instructions/week7_instructions/) - Dues (Skipped)
- [Week 6 Instructions](instructions/week6_instructions/) - Union Operations
- [Week 5 Instructions](instructions/week5_instructions/) - Members Landing
- [Week 4 Instructions](instructions/week4_instructions/) - Training Landing
- [Week 3 Instructions](instructions/week3_instructions/) - Staff Management
- [Week 2 Instructions](instructions/week2_instructions/) - Auth cookies + Dashboard
- [Week 1 Instructions](instructions/) - Frontend setup + Login

---

## Current Status

**Version:** v0.7.8 (Phase 6 Week 10 Session A Complete)

| Component | Status | Tests |
|-----------|--------|-------|
| Backend API | Complete | 165 |
| Frontend (Auth + Dashboard + Staff + Training + Members + Operations + Reports + Documents + Dues) | In Progress | 149 |
| **Total** | **In Progress** | **312** |

See [Milestone Checklist](IP2A_MILESTONE_CHECKLIST.md) for detailed progress.

---

## Getting Help

- **GitHub Issues**: https://github.com/theace26/IP2A-Database-v2/issues
- **Documentation Updates**: Submit PRs to improve these docs
- **Questions**: Open a discussion or issue

---

*Last Updated: January 29, 2026*
