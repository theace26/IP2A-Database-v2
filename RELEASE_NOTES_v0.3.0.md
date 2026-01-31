# Release Notes - v0.3.0

**Release Date:** January 28, 2026
**Tag:** v0.3.0
**Branch:** main

---

## 🎉 Phase 2 Complete: Union Operations

IP2A Database v0.3.0 marks the completion of **Phase 2: Union Operations**, expanding the platform from pre-apprenticeship program management to comprehensive union member services.

---

## ✨ What's New

### Union Operations Models

Five new database models for core union operations:

1. **SALTing Activities** - Track organizing campaigns at non-union employers
   - 8 activity types (outreach, site visits, meetings, card signing, etc.)
   - Worker engagement metrics (contacts, cards signed)
   - Outcome tracking and campaign notes

2. **Benevolence Fund** - Financial assistance for members in need
   - 5 assistance categories (medical, death in family, disaster, hardship, other)
   - Multi-level approval workflow (VP → Admin → Manager → President)
   - Amount tracking ($100-$7,500 range)
   - Payment status and history

3. **Grievance System** - Formal complaint tracking through arbitration
   - Unique grievance numbering (GR-YYYY-NNNN)
   - 10 common violation types (overtime, safety, termination, wages, etc.)
   - Step-by-step progression tracking (Steps 1-4 + arbitration)
   - Contract article references and settlement amounts

### API Endpoints

**27 new REST API endpoints:**

**SALTing Activities:**
- `POST /salting-activities/` - Create activity
- `GET /salting-activities/` - List all activities
- `GET /salting-activities/{id}` - Get specific activity
- `PUT /salting-activities/{id}` - Update activity
- `DELETE /salting-activities/{id}` - Delete activity

**Benevolence Applications:**
- `POST /benevolence-applications/` - Submit application
- `GET /benevolence-applications/` - List all applications
- `GET /benevolence-applications/{id}` - Get specific application
- `PUT /benevolence-applications/{id}` - Update application
- `DELETE /benevolence-applications/{id}` - Delete application

**Benevolence Reviews:**
- `POST /benevolence-reviews/` - Add review
- `GET /benevolence-reviews/` - List all reviews
- `GET /benevolence-reviews/{id}` - Get specific review
- `GET /benevolence-reviews/application/{application_id}` - Get reviews by application
- `PUT /benevolence-reviews/{id}` - Update review
- `DELETE /benevolence-reviews/{id}` - Delete review

**Grievances:**
- `POST /grievances/` - File grievance
- `GET /grievances/` - List all grievances
- `GET /grievances/{id}` - Get specific grievance
- `GET /grievances/number/{grievance_number}` - Get by grievance number
- `POST /grievances/{id}/steps` - Add step record
- `GET /grievances/{id}/steps` - Get grievance steps
- `PUT /grievances/{id}` - Update grievance
- `DELETE /grievances/{id}` - Delete grievance

### Comprehensive Seed Data

**New seed data generator** ([src/seed/phase2_seed.py](src/seed/phase2_seed.py)) provides realistic test data:

- **30 SALTing Activities** - Organizing campaigns at 13 employers
- **25 Benevolence Applications** - Financial assistance requests
- **47 Benevolence Reviews** - Multi-level approval workflow
- **20 Grievances** - Formal complaints with contract violations
- **31 Grievance Step Records** - Step-by-step progression tracking

**Total: 153 Phase 2 records**

**Standalone execution:**
```bash
python -m src.seed.phase2_seed
```

**Integrated with main seed:**
```bash
python -m src.seed.run_seed
```

### Documentation Improvements

**Reorganized documentation structure:**
- `/docs/architecture/` - System design documents
- `/docs/decisions/` - Architecture Decision Records (ADRs)
- `/docs/guides/` - How-to guides
- `/docs/reference/` - CLI and API reference
- `/docs/reports/` - Test reports and assessments
- `/docs/runbooks/` - Operational procedures
- `/docs/standards/` - Coding standards

**New documentation:**
- 7 Architecture Decision Records (ADRs)
- Getting Started Guide
- Coding Standards
- Naming Conventions
- Session Summary (2026-01-28)
- CONTRIBUTING.md
- CHANGELOG.md

---

## 🔧 Technical Details

### Database Schema

**New tables:**
- `salting_activities` - Organizing campaign tracking
- `benevolence_applications` - Financial assistance requests
- `benevolence_reviews` - Approval workflow
- `grievances` - Formal complaints
- `grievance_step_records` - Grievance progression

**New enums:**
- `SALTingActivityType` (8 values)
- `SALTingOutcome` (4 values)
- `BenevolenceReason` (5 values)
- `BenevolenceStatus` (6 values)
- `BenevolenceReviewLevel` (4 values)
- `BenevolenceReviewDecision` (4 values)
- `GrievanceStatus` (7 values)
- `GrievanceStep` (4 values)
- `GrievanceStepOutcome` (3 values)

**Migrations:**
- `bc1f99c730dc` - Add Phase 2 union operations models
- `6f77d764d2c3` - Add file_category to file_attachments

### Testing

**31 passing tests** for Phase 2 endpoints:
- 5 SALTing Activity tests
- 7 Benevolence Application tests
- 7 Benevolence Review tests
- 7 Grievance tests
- 5 Grievance Step tests

**Total project tests: 82** (79 passing, 3 pre-existing schema issues)

### Code Metrics

- **853 lines** of seed data code
- **17 functions** (11 main + 6 helpers)
- **72 activity descriptions** across 8 activity types
- **25 benevolence descriptions** across 5 reasons
- **30 grievance templates** (10 violation types)

---

## 📦 Installation & Upgrade

### For New Installations

```bash
# Clone repository
git clone https://github.com/theace26/IP2A-Database-v2.git
cd IP2A-Database-v2

# Checkout v0.3.0
git checkout v0.3.0

# Setup environment
cp .env.compose.example .env.compose
docker-compose up -d

# Run migrations
docker exec -it ip2a-api alembic upgrade head

# Seed database (includes Phase 2)
docker exec -it ip2a-api python -m src.seed.run_seed
```

### For Existing Installations

```bash
# Pull latest changes
git fetch origin
git checkout v0.3.0

# Apply migrations
docker exec -it ip2a-api alembic upgrade head

# Seed Phase 2 data (optional)
docker exec -it ip2a-api python -m src.seed.phase2_seed
```

---

## 📚 Documentation

**Key Documentation:**
- [System Overview](docs/architecture/SYSTEM_OVERVIEW.md) - Architecture overview
- [Getting Started](docs/guides/getting-started.md) - Setup guide
- [Session Summary](docs/reports/session-logs/2026-01-28.md) - Implementation details
- [CHANGELOG](CHANGELOG.md) - Complete change history
- [CONTRIBUTING](CONTRIBUTING.md) - Contribution guidelines

**ADRs (Architecture Decision Records):**
- [ADR-001](docs/decisions/ADR-001-database-choice.md) - PostgreSQL
- [ADR-002](docs/decisions/ADR-002-frontend-framework.md) - HTMX + Alpine.js
- [ADR-003](docs/decisions/ADR-003-authentication-strategy.md) - JWT
- [ADR-004](docs/decisions/ADR-004-file-storage-strategy.md) - Object Storage
- [ADR-005](docs/decisions/ADR-005-css-framework.md) - Tailwind CSS
- [ADR-006](docs/decisions/ADR-006-background-jobs.md) - TaskService
- [ADR-007](docs/decisions/ADR-007-observability.md) - Grafana + Loki

---

## 🎯 What's Next

### Immediate Next Steps

1. **Authentication System** - JWT implementation with RBAC
2. **Phase 3: Document Management** - S3 integration for file storage
3. **API Documentation** - OpenAPI/Swagger docs

### Future Phases

- **Phase 4:** Dues tracking and financial management
- **Phase 5:** TradeSchool integration
- **Phase 6:** Web portal and production deployment

---

## 🐛 Known Issues

- 3 pre-existing audit_log schema test failures (not blocking)
- Documentation dates need updating in some ADRs (marked as 2025-XX-XX)

---

## 👥 Contributors

- **Xerxes** - Project Owner
- **Claude Sonnet 4.5** - AI Development Assistant

---

## 📝 Commits in This Release

**From v0.2.0 to v0.3.0:**

```
712ff6a docs: Document Phase 2 seed data implementation
ec5bfee feat: Add Phase 2 seed data for union operations
b4dabda Merge docs/reorganization: Complete documentation restructuring
ebf8484 docs: add getting-started guide, coding standards, and additional ADRs
0a961d5 Fix internal documentation links
beb3b6d Phase 5: Create runbook templates
f3e5819 Phase 4: Update CLAUDE.md with new documentation structure
3d76ff4 Phase 3: Create new required files
cba947b Phase 2: Move and consolidate documentation files
464e643 Phase 1: Create new directory structure and rename to lowercase
```

**Total:** 10 commits, 857+ lines added

---

## 🔗 Links

- **Repository:** https://github.com/theace26/IP2A-Database-v2
- **v0.3.0 Tag:** https://github.com/theace26/IP2A-Database-v2/releases/tag/v0.3.0
- **Issues:** https://github.com/theace26/IP2A-Database-v2/issues
- **Compare Changes:** https://github.com/theace26/IP2A-Database-v2/compare/v0.2.0...v0.3.0

---

## 📄 License

[Include your license here]

---

**Thank you for using IP2A Database!**

For questions or issues, please open an issue on GitHub.
