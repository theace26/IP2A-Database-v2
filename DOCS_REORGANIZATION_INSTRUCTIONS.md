# Documentation Reorganization Instructions for Claude Code

> **Purpose:** This document provides step-by-step instructions for Claude Code to reorganize the IP2A-Database-v2 documentation structure.
> 
> **Created:** January 27, 2026
> **Author:** Planning session with Claude.ai

---

## Overview

The current `docs/` folder has grown organically and needs reorganization for:
1. Easier navigation
2. Reduced duplication
3. Industry-standard structure
4. Better separation of concerns

---

## Target Directory Structure

```
IP2A-Database-v2/
├── CLAUDE.md                    # AI assistant context (stays in root)
├── README.md                    # Project overview (stays in root)
├── CHANGELOG.md                 # NEW: Version history (stays in root)
├── CONTRIBUTING.md              # NEW: Contribution guidelines (stays in root)
├── docs/
│   ├── README.md                # NEW: Documentation index/navigation
│   │
│   ├── architecture/            # Lowercase for consistency
│   │   ├── AUTHENTICATION_ARCHITECTURE.md
│   │   ├── FILE_STORAGE_ARCHITECTURE.md
│   │   ├── SCALABILITY_ARCHITECTURE.md
│   │   ├── SYSTEM_OVERVIEW.md   # RENAME from ARCHITECTURE.md
│   │   └── diagrams/            # RENAME from graphs/
│   │       ├── migrations.mmd
│   │       ├── models_fk.mmd
│   │       └── seeds.mmd
│   │
│   ├── decisions/               # NEW: Architecture Decision Records
│   │   ├── README.md            # NEW: ADR index
│   │   ├── ADR-001-database-choice.md
│   │   ├── ADR-002-frontend-framework.md
│   │   ├── ADR-003-authentication-strategy.md
│   │   └── ADR-004-file-storage-strategy.md
│   │
│   ├── guides/                  # Lowercase
│   │   ├── audit-logging.md     # RENAME: consistent naming
│   │   ├── getting-started.md   # NEW: Quick start guide
│   │   └── project-strategy.md  # MOVE from root, RENAME
│   │
│   ├── reference/               # NEW: Quick reference docs
│   │   ├── ip2adb-cli.md        # CONSOLIDATE: IP2ADB.md + IP2ADB_QUICK_REF.md
│   │   ├── integrity-check.md   # CONSOLIDATE: INTEGRITY_CHECK*.md files
│   │   ├── load-testing.md      # CONSOLIDATE: LOAD_TEST*.md files
│   │   └── stress-testing.md    # MOVE: STRESS_TEST.md
│   │
│   ├── reports/                 # Lowercase
│   │   ├── phase-2.1-summary.md
│   │   ├── scaling-readiness.md
│   │   ├── stress-test-analytics.md
│   │   └── session-logs/        # NEW: Subfolder for session summaries
│   │       └── 2026-01-27.md
│   │
│   ├── standards/               # Lowercase
│   │   ├── audit-logging.md
│   │   ├── coding-standards.md  # NEW: Code style guide
│   │   └── naming-conventions.md # NEW: Naming patterns
│   │
│   └── runbooks/                # NEW: Operational procedures
│       ├── deployment.md        # NEW: How to deploy
│       ├── backup-restore.md    # NEW: Backup procedures
│       └── disaster-recovery.md # NEW: Emergency procedures
```

---

## Step-by-Step Instructions

### Phase 1: Create New Structure (Non-Destructive)

```bash
# Navigate to project root
cd ~/Projects/IP2A-Database-v2

# Create new directories
mkdir -p docs/decisions
mkdir -p docs/reference
mkdir -p docs/runbooks
mkdir -p docs/reports/session-logs

# Rename directories to lowercase (if not already)
# Note: Git on Mac/Windows may not detect case-only renames
# Use git mv for safety
git mv docs/Architecture docs/architecture 2>/dev/null || true
git mv docs/Guides docs/guides 2>/dev/null || true
git mv docs/Reports docs/reports 2>/dev/null || true
git mv docs/Standards docs/standards 2>/dev/null || true
git mv docs/architecture/graphs docs/architecture/diagrams 2>/dev/null || true
```

### Phase 2: Move and Consolidate Files

#### 2.1 Handle Root-Level docs/ Files

```bash
# Move project strategy (remove duplicate)
# Keep the one in guides/, delete root copy if identical
diff docs/Guides/IP2A_PROJECT_STRATEGY.md docs/IP2A_PROJECT_STRATEGY.md
# If identical, remove root copy:
rm docs/IP2A_PROJECT_STRATEGY.md
git mv docs/guides/IP2A_PROJECT_STRATEGY.md docs/guides/project-strategy.md

# Move ARCHITECTURE.md to architecture folder with new name
git mv docs/ARCHITECTURE.md docs/architecture/SYSTEM_OVERVIEW.md

# Move EXECUTIVE_SUMMARY.md to root (it's high-level)
git mv docs/EXECUTIVE_SUMMARY.md ./EXECUTIVE_SUMMARY.md

# Move ROADMAP.md to root (it's project-level)
git mv docs/ROADMAP.md ./ROADMAP.md

# Move TESTING_STRATEGY.md to guides
git mv docs/TESTING_STRATEGY.md docs/guides/testing-strategy.md
```

#### 2.2 Consolidate Reference Documents

```bash
# Consolidate IP2ADB docs
# Manually merge IP2ADB.md and IP2ADB_QUICK_REF.md into one file
# Create: docs/reference/ip2adb-cli.md
# Then remove originals:
rm docs/IP2ADB.md docs/IP2ADB_QUICK_REF.md

# Consolidate Integrity Check docs
# Merge INTEGRITY_CHECK*.md and INTEGRITY_QUICK_REF.md
# Create: docs/reference/integrity-check.md
# Then remove originals

# Consolidate Load Test docs
# Merge LOAD_TEST.md and LOAD_TEST_QUICK_REF.md
# Create: docs/reference/load-testing.md
# Then remove originals

# Move Stress Test
git mv docs/STRESS_TEST.md docs/reference/stress-testing.md
```

#### 2.3 Organize Reports

```bash
# Rename report files to kebab-case
git mv "docs/reports/PHASE_2.1_SUMMARY.md" docs/reports/phase-2.1-summary.md
git mv docs/reports/SCALING_READINESS_ASSESSMENT.md docs/reports/scaling-readiness.md
git mv docs/reports/STRESS_TEST_ANALYTICS_REPORT.md docs/reports/stress-test-analytics.md

# Move session logs to subfolder
git mv docs/reports/SESSION_SUMMARY_2026-01-27.md docs/reports/session-logs/2026-01-27.md
```

#### 2.4 Organize Standards and Guides

```bash
# Rename to kebab-case
git mv docs/standards/AUDIT_LOGGING_STANDARDS.md docs/standards/audit-logging.md
git mv docs/guides/AUDIT_LOGGING_GUIDE.md docs/guides/audit-logging.md
```

### Phase 3: Create New Required Files

#### 3.1 Create CHANGELOG.md in Project Root

```markdown
# Changelog

All notable changes to IP2A-Database-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation reorganization
- Architecture Decision Records

## [0.2.0] - 2026-XX-XX

### Added
- Phase 1 Services Layer complete
- Organization, OrgContact, Member, MemberEmployment, AuditLog services
- 51 passing tests
- Database management CLI (ip2adb)
- Stress testing system
- Integrity check system
- Load testing system

### Changed
- Consolidated enums to src/db/enums/
- Updated documentation structure

## [0.1.1] - 2026-XX-XX

### Fixed
- Stabilized src layout and project structure

## [0.1.0] - 2026-XX-XX

### Added
- Initial backend stabilization
- PostgreSQL 16 database setup
- Docker development environment
- Base models and migrations
```

#### 3.2 Create docs/README.md (Documentation Index)

```markdown
# IP2A Documentation

Welcome to the IP2A Database documentation. This index helps you find what you need.

## Quick Links

| I want to... | Go to... |
|--------------|----------|
| Understand the system | [System Overview](architecture/SYSTEM_OVERVIEW.md) |
| Set up development | [Getting Started](guides/getting-started.md) |
| Use the CLI tools | [ip2adb Reference](reference/ip2adb-cli.md) |
| Understand a decision | [Architecture Decisions](decisions/README.md) |
| See what changed | [CHANGELOG](../CHANGELOG.md) |

## Documentation Structure

### `/architecture`
Technical architecture documents describing how the system is built.
- Authentication, file storage, scalability designs
- System diagrams

### `/decisions`
Architecture Decision Records (ADRs) explaining WHY we made specific choices.

### `/guides`
How-to guides for common tasks and workflows.

### `/reference`
Quick reference for CLI tools and commands.

### `/reports`
Generated reports from testing, assessments, and sessions.

### `/runbooks`
Operational procedures for deployment and maintenance.

### `/standards`
Coding standards and conventions for contributors.
```

#### 3.3 Create docs/decisions/README.md

```markdown
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

## ADR Template

When creating a new ADR, use this template:

```markdown
# ADR-XXX: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?
```
```

#### 3.4 Create ADR-002 (Frontend Framework Decision)

```markdown
# ADR-002: Frontend Framework Choice

## Status
Accepted

## Date
2026-01-27

## Context

We need to choose a frontend technology for the IP2A staff interface. Constraints:

1. **Developer Experience:** Primary developer has no React/Vue/Svelte experience
2. **Time:** 5-10 hours/week available for development
3. **Maintainability:** Must be maintainable by volunteer union tech folks
4. **Longevity:** 10+ year horizon - must survive framework churn
5. **Features Required:**
   - Forms and CRUD operations
   - Data tables with search/filter
   - Data visualization (charts)
   - Keyboard shortcuts (like Google Docs)
   - Integration with backend services (QuickBooks, Stripe)

## Options Considered

### Option A: React
- Industry standard (~40% market share)
- Large ecosystem
- Steep learning curve
- Requires separate build process and deployment
- Subject to ecosystem churn

### Option B: Vue.js
- Gentler learning curve than React
- Still requires JavaScript expertise
- Still requires separate deployment

### Option C: Server-Side Rendering (Jinja2 + HTMX + Alpine.js)
- Minimal JavaScript required
- Single deployment (FastAPI serves everything)
- HTML/CSS are the most stable web technologies
- HTMX provides dynamic updates via HTML attributes
- Alpine.js handles keyboard shortcuts and micro-interactions
- Can add React later for member portal if needed

## Decision

We will use **Server-Side Rendering with HTMX and Alpine.js** for the staff interface.

Tech stack:
- **Jinja2:** HTML templating (built into FastAPI)
- **HTMX:** Dynamic updates without JavaScript
- **Alpine.js:** Keyboard shortcuts and small interactions
- **Chart.js:** Data visualization
- **Tailwind CSS:** Styling (optional, can use plain CSS)

## Consequences

### Positive
- Single codebase, single deployment
- No build step required
- HTML attributes are stable (won't break in 10 years)
- Lower learning curve for primary developer
- Easier onboarding for future contributors
- Backend integrations (QuickBooks, Stripe) unaffected

### Negative
- Less "modern" feel than SPA
- Complex real-time features (if needed) require more work
- Fewer pre-built component libraries
- May need React for member portal in Phase 4+

### Risks
- HTMX is newer (less proven than React)
- Mitigation: HTMX degrades gracefully to standard HTML forms
- Mitigation: Core functionality works without JavaScript

## References
- [HTMX Documentation](https://htmx.org/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [Why I Use HTMX](https://htmx.org/essays/)
```

#### 3.5 Create ADR-001 (Database Choice)

```markdown
# ADR-001: Database Choice

## Status
Accepted

## Date
2025-XX-XX (Backfill with original decision date)

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

## Consequences

### Positive
- Full ACID compliance protects financial/dues data
- JSONB allows flexible metadata storage
- Array types useful for multi-value fields
- Excellent SQLAlchemy support
- Large community for troubleshooting

### Negative
- Slightly more complex setup than SQLite
- Requires running database server

### Risks
- PostgreSQL major version upgrades can require migration
- Mitigation: Stay on LTS versions, test upgrades in dev first
```

#### 3.6 Create ADR-003 (Authentication Strategy)

```markdown
# ADR-003: Authentication Strategy

## Status
Accepted

## Date
2025-XX-XX

## Context

We need authentication for the IP2A staff interface and future member portal. Requirements:
- Support internal users (staff, officers, admins)
- Support external users (members, stewards)
- Audit trail of who performed actions
- Session management
- Role-based access control

## Options Considered

### Option A: Session-based Authentication (Traditional)
- Server stores session in database/Redis
- Cookie-based identification
- Simple to implement
- Requires session storage infrastructure

### Option B: JWT (JSON Web Tokens)
- Stateless authentication
- Token contains user identity and roles
- No server-side session storage required
- Industry standard for APIs

### Option C: OAuth2 with External Provider
- Delegate auth to Google/Microsoft
- Less password management
- Dependency on external service
- May not suit all union members

## Decision

We will use **JWT-based authentication** with:
- Access tokens (15 minute expiry)
- Refresh tokens (7 day expiry, stored in database)
- Bcrypt password hashing
- Role-based middleware

## Consequences

### Positive
- Stateless API (easier to scale)
- Standard approach, well-documented
- Works with future mobile apps
- No session storage infrastructure needed

### Negative
- Token revocation requires refresh token tracking
- Slightly more complex than session cookies

### Risks
- JWT secret key compromise = full breach
- Mitigation: Rotate keys, use strong secrets, monitor for anomalies

## References
- See: docs/architecture/AUTHENTICATION_ARCHITECTURE.md
```

#### 3.7 Create ADR-004 (File Storage Strategy)

```markdown
# ADR-004: File Storage Strategy

## Status
Accepted

## Date
2025-XX-XX

## Context

IP2A needs to store files:
- Member certifications (images, PDFs)
- Grievance evidence documents
- Grant reports
- Training materials

Requirements:
- Files must be associated with database records
- Access control (only authorized users see files)
- Reasonable storage costs at scale
- Backup strategy
- 10+ year retention for some documents

## Options Considered

### Option A: Store Files in Database (BLOB)
- Simple: everything in one place
- Backups include files automatically
- Database bloat (slow backups, expensive storage)
- Not recommended for files > 1MB

### Option B: Local Filesystem
- Simple implementation
- No additional services
- Difficult to scale
- No built-in redundancy
- Backup complexity

### Option C: Object Storage (S3-compatible)
- Industry standard for file storage
- Lifecycle policies (hot → cold storage)
- Built-in redundancy
- Scales independently from database
- Cost-effective for large volumes

## Decision

We will use **Object Storage** with:
- **Development:** MinIO (S3-compatible, runs in Docker)
- **Production:** Backblaze B2 or AWS S3
- **Database stores:** Metadata only (path, size, type, owner)
- **Lifecycle tiers:** Hot (30 days) → Warm (1 year) → Cold (archive)

## Consequences

### Positive
- Database stays small (fast backups)
- Storage scales independently
- Lifecycle policies reduce costs 70%+
- Industry-standard pattern

### Negative
- Additional service to manage
- Two backup strategies needed (DB + files)

### Risks
- Object storage provider outage
- Mitigation: Keep local copies of critical files, consider multi-region

## References
- See: docs/architecture/FILE_STORAGE_ARCHITECTURE.md
```

#### 3.8 Create CONTRIBUTING.md in Project Root

```markdown
# Contributing to IP2A Database

Thank you for your interest in contributing to IP2A! This document provides guidelines for contributing.

## Getting Started

1. Clone the repository
2. Copy `.env.compose.example` to `.env.compose`
3. Run `docker-compose up -d`
4. Open in VS Code with Dev Containers extension

See [Getting Started Guide](docs/guides/getting-started.md) for detailed setup.

## Development Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation only

### Commit Messages
Use conventional commits:
- `feat: add member search endpoint`
- `fix: correct date validation in enrollment`
- `docs: update API reference`
- `test: add integration tests for members`
- `refactor: simplify organization service`

### Pull Request Process
1. Create feature branch from `main`
2. Make changes with tests
3. Run `pytest -v` (all tests must pass)
4. Run `ruff check . --fix && ruff format .`
5. Update documentation if needed
6. Submit PR with description of changes

## Code Standards

See [Coding Standards](docs/standards/coding-standards.md) for:
- Naming conventions
- File organization
- Service/Router patterns

## Testing

All PRs must include tests. See [Testing Strategy](docs/guides/testing-strategy.md).

## Questions?

Open an issue or contact the project maintainer.
```

### Phase 4: Update CLAUDE.md

Add this section to CLAUDE.md:

```markdown
---

## Documentation Structure

```
docs/
├── architecture/     # System design documents
├── decisions/        # Architecture Decision Records (ADRs)
├── guides/           # How-to guides
├── reference/        # CLI and API reference
├── reports/          # Test reports, assessments
├── runbooks/         # Operational procedures
└── standards/        # Coding standards
```

### Documentation Principles
- Architecture docs describe HOW the system works
- ADRs explain WHY decisions were made
- Guides explain HOW TO do things
- Reference docs are for quick lookup
- Runbooks are step-by-step procedures

### When to Update Documentation
- New feature → Update relevant guide or create new one
- Major decision → Create ADR
- API change → Update reference
- Bug fix with lessons learned → Consider ADR or guide update
```

---

### Phase 5: Create Runbook Templates

#### 5.1 Create docs/runbooks/README.md

```markdown
# Runbooks

Operational procedures for IP2A Database system administration.

## What is a Runbook?

A runbook is a step-by-step procedure for performing operational tasks. They are written so that someone unfamiliar with the system can follow them during an emergency.

## Available Runbooks

| Runbook | Purpose | Last Updated |
|---------|---------|--------------|
| [deployment.md](deployment.md) | Deploy new version | TBD |
| [backup-restore.md](backup-restore.md) | Backup and restore database | TBD |
| [disaster-recovery.md](disaster-recovery.md) | Recover from system failure | TBD |

## Runbook Template

When creating a new runbook, include:
1. Overview and estimated time
2. Prerequisites
3. Step-by-step procedure with exact commands
4. Verification steps
5. Troubleshooting section
6. Rollback procedure
7. Emergency contacts
```

#### 5.2 Create docs/runbooks/backup-restore.md (Template)

```markdown
# Runbook: Database Backup and Restore

## Overview
Procedures for backing up and restoring the IP2A PostgreSQL database.

**Estimated time:** 
- Backup: 5 minutes
- Restore: 15-30 minutes

## Prerequisites
- SSH access to server
- Docker access
- Backup storage location access

---

## BACKUP PROCEDURE

### Step 1: Connect to Server
```bash
ssh user@ip2a-server
cd ~/Projects/IP2A-Database-v2
```

### Step 2: Create Backup
```bash
docker exec ip2a-db pg_dump -U postgres ip2a_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 3: Verify Backup
```bash
ls -lh backup_*.sql | tail -1
```
File should be > 1MB.

### Step 4: Copy to Safe Location
```bash
cp backup_*.sql /path/to/backup/location/
```

---

## RESTORE PROCEDURE

⚠️ **WARNING: This OVERWRITES the current database!**

### Step 1: Stop Application
```bash
docker-compose stop api
```

### Step 2: Restore Database
```bash
docker exec -i ip2a-db psql -U postgres -c "DROP DATABASE IF EXISTS ip2a_db;"
docker exec -i ip2a-db psql -U postgres -c "CREATE DATABASE ip2a_db;"
docker exec -i ip2a-db psql -U postgres ip2a_db < /path/to/backup_file.sql
```

### Step 3: Restart Application
```bash
docker-compose start api
```

### Step 4: Verify
```bash
curl http://localhost:8000/health
```

---

## Troubleshooting

### Problem: "database is being accessed by other users"
**Solution:** `docker-compose down` then `docker-compose up -d db`, wait 10 seconds, retry.

---

## Contacts
- Primary: [TODO: Add contact]
- Backup: [TODO: Add contact]
```

#### 5.3 Create docs/runbooks/deployment.md (Template)

```markdown
# Runbook: Deployment

## Overview
Deploy a new version of IP2A Database to production.

**Estimated time:** 15-30 minutes

## Prerequisites
- Git access to repository
- SSH access to server
- Docker access

---

## PRE-DEPLOYMENT

### Step 1: Backup Database
Follow [backup-restore.md](backup-restore.md) backup procedure first!

### Step 2: Review Changes
```bash
git log main..HEAD --oneline
```

---

## DEPLOYMENT

### Step 1: Connect to Server
```bash
ssh user@ip2a-server
cd ~/Projects/IP2A-Database-v2
```

### Step 2: Pull Latest Code
```bash
git fetch origin
git checkout main
git pull origin main
```

### Step 3: Rebuild and Restart
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Step 4: Run Migrations
```bash
docker exec ip2a-api alembic upgrade head
```

---

## VERIFICATION

### Step 1: Check Services Running
```bash
docker-compose ps
```
All services should show "Up".

### Step 2: Check API Health
```bash
curl http://localhost:8000/health
```

### Step 3: Check Logs for Errors
```bash
docker-compose logs --tail=50 api
```

---

## ROLLBACK

If deployment fails:

### Step 1: Revert to Previous Version
```bash
git checkout HEAD~1
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Step 2: Restore Database if Needed
Follow [backup-restore.md](backup-restore.md) restore procedure.

---

## Contacts
- Primary: [TODO: Add contact]
- Backup: [TODO: Add contact]
```

#### 5.4 Create docs/runbooks/disaster-recovery.md (Template)

```markdown
# Runbook: Disaster Recovery

## Overview
Recover IP2A Database from complete system failure.

**Estimated time:** 1-2 hours

## Prerequisites
- Access to backup files
- Access to new/rebuilt server
- Docker installation capability

---

## SCENARIOS

### Scenario A: Application Container Crashed

**Symptoms:** API not responding, database still running

**Recovery:**
```bash
docker-compose restart api
docker-compose logs --tail=50 api
```

### Scenario B: Database Container Crashed

**Symptoms:** API shows database connection errors

**Recovery:**
```bash
docker-compose restart db
# Wait 30 seconds
docker-compose restart api
```

### Scenario C: Server Unreachable

**Symptoms:** Cannot SSH to server

**Recovery:**
1. Contact hosting provider / check hardware
2. If server is lost, proceed to Scenario D

### Scenario D: Complete Data Loss (Rebuild from Backup)

**Recovery:**

1. **Set up new server** with Docker and Docker Compose

2. **Clone repository**
   ```bash
   git clone https://github.com/theace26/IP2A-Database-v2.git
   cd IP2A-Database-v2
   ```

3. **Copy environment file**
   ```bash
   cp .env.compose.example .env.compose
   # Edit with correct credentials
   ```

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Restore database from backup**
   Follow [backup-restore.md](backup-restore.md) restore procedure.

6. **Verify system**
   ```bash
   curl http://localhost:8000/health
   ```

---

## BACKUP LOCATIONS

| Backup Type | Location | Retention |
|-------------|----------|-----------|
| Database dumps | [TODO: Add path] | 30 days |
| File attachments | [TODO: Add path] | Indefinite |

---

## Contacts

### Primary
- Name: [TODO]
- Phone: [TODO]
- Email: [TODO]

### Backup
- Name: [TODO]
- Phone: [TODO]

### Hosting Provider
- Support: [TODO]
- Account: [TODO]
```

---

## Verification Checklist

After reorganization, verify:

- [ ] No duplicate files remain
- [ ] All internal links in documents still work
- [ ] CLAUDE.md reflects new structure
- [ ] `git status` shows all moves tracked
- [ ] No orphaned files in `docs/` root (except README.md)

## Files to Delete After Consolidation

These files should be removed AFTER their content is merged:

```
docs/IP2A_PROJECT_STRATEGY.md (duplicate)
docs/IP2ADB.md (merged into reference/)
docs/IP2ADB_QUICK_REF.md (merged into reference/)
docs/INTEGRITY_CHECK*.md (merged into reference/)
docs/INTEGRITY_QUICK_REF.md (merged into reference/)
docs/LOAD_TEST.md (merged into reference/)
docs/LOAD_TEST_QUICK_REF.md (merged into reference/)
```

---

## Notes for Claude Code

1. **Do this in a feature branch:** `git checkout -b docs/reorganization`
2. **Use `git mv` for all moves** to preserve history
3. **Check for internal links** in moved files and update them
4. **Run verification checklist** before committing
5. **Commit in phases** (one commit per phase)

---

*Document created: January 27, 2026*
*For use with: Claude Code*
