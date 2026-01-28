# Claude Code Instructions: Finalize Phase 4 & Tag v0.7.0

**Document Version:** 1.0
**Created:** January 28, 2026
**Estimated Time:** 30-45 minutes
**Priority:** High (milestone release)

---

## Objective

Finalize Phase 4 (Dues Tracking), create release documentation, and tag v0.7.0.

---

## Pre-Flight Checklist

Before starting, verify the current state:

```bash
cd ~/Projects/IP2A-Database-v2
git status                    # Should be clean
git branch --show-current     # Should be main
pytest -v                     # Should show 165 passing
```

---

## Step-by-Step Instructions

### Step 1: Verify All Phase 4 Components Exist

Run these checks to confirm Phase 4 is complete:

```bash
# Check core files exist
ls -la src/db/enums/dues_enums.py
ls -la src/models/dues_rate.py
ls -la src/models/dues_period.py
ls -la src/models/dues_payment.py
ls -la src/models/dues_adjustment.py
ls -la src/services/dues_rate_service.py
ls -la src/services/dues_period_service.py
ls -la src/services/dues_payment_service.py
ls -la src/services/dues_adjustment_service.py
ls -la src/routers/dues_rates.py
ls -la src/routers/dues_periods.py
ls -la src/routers/dues_payments.py
ls -la src/routers/dues_adjustments.py
ls -la src/tests/test_dues.py

# Verify routers are registered
grep "dues" src/main.py

# Check documentation exists
ls -la docs/decisions/ADR-008-dues-tracking-system.md
ls -la docs/guides/dues-tracking.md
ls -la docs/reference/dues-api.md
```

### Step 2: Run Full Test Suite

```bash
# Run all tests with verbose output
pytest -v

# Expected: 165 tests passing
# If any failures, fix before proceeding
```

### Step 3: Update CHANGELOG.md

Move Phase 4 from [Unreleased] to [0.7.0]. Edit `CHANGELOG.md`:

```markdown
## [0.7.0] - 2026-01-28

### Added
- **Phase 4: Dues Tracking System**
  * 4 new models: DuesRate, DuesPeriod, DuesPayment, DuesAdjustment
  * 4 new enums: DuesPaymentStatus, DuesPaymentMethod, DuesAdjustmentType, AdjustmentStatus
  * Complete dues lifecycle: rate management, period tracking, payments, adjustments
  * Member classification-based rate lookup (apprentice 1-5, journeyman, foreman, retiree, honorary)
  * Approval workflow for dues adjustments (pending/approved/denied)
  * Period management with close functionality
  * Overdue payment tracking
  * ~35 API endpoints across 4 routers
  * Dues seed data with rates for all 9 member classifications
  * 21 new tests (165 total passing)
  * ADR-008: Dues Tracking System Design
  * Comprehensive documentation (guide + API reference)
```

### Step 4: Create Release Notes

Create `docs/releases/RELEASE_NOTES_v0.7.0.md`:

```bash
mkdir -p docs/releases
```

Then create the file with this content:

```markdown
# Release Notes - v0.7.0

**Release Date:** January 28, 2026
**Tag:** v0.7.0
**Branch:** main

---

## 🎉 Phase 4 Complete: Dues Tracking System

v0.7.0 delivers a comprehensive dues tracking system for managing member financial obligations.

---

## ✨ What's New

### Dues Tracking Models (4)

| Model | Purpose |
|-------|---------|
| **DuesRate** | Classification-based dues amounts with effective dates |
| **DuesPeriod** | Monthly billing periods with grace periods |
| **DuesPayment** | Payment records with status tracking |
| **DuesAdjustment** | Waivers, credits with approval workflow |

### Member Classifications & Rates

| Classification | Default Rate |
|---------------|--------------|
| apprentice_1 | $35.00 |
| apprentice_2 | $40.00 |
| apprentice_3 | $45.00 |
| apprentice_4 | $50.00 |
| apprentice_5 | $55.00 |
| journeyman | $75.00 |
| foreman | $85.00 |
| retiree | $25.00 |
| honorary | $0.00 |

### API Endpoints (~35 new)

**Dues Rates:**
- `GET/POST /dues-rates/` - List, create rates
- `GET /dues-rates/current/{classification}` - Current active rate
- `GET /dues-rates/for-date/{classification}` - Rate for specific date

**Dues Periods:**
- `GET/POST /dues-periods/` - List, create periods
- `POST /dues-periods/generate/{year}` - Generate 12 monthly periods
- `POST /dues-periods/{id}/close` - Close a billing period

**Dues Payments:**
- `GET/POST /dues-payments/` - List, create payment records
- `POST /dues-payments/{id}/record` - Record actual payment
- `GET /dues-payments/member/{id}/summary` - Member dues summary
- `POST /dues-payments/update-overdue` - Batch update overdue status

**Dues Adjustments:**
- `GET/POST /dues-adjustments/` - List, create adjustments
- `GET /dues-adjustments/pending` - Pending approvals
- `POST /dues-adjustments/{id}/approve` - Approve or deny

### Key Features

- **Classification-based rates** - Different member types pay different amounts
- **Effective date tracking** - Historical rate changes preserved
- **Multiple payment methods** - Cash, check, card, ACH, payroll deduction
- **Payment status workflow** - Pending → Paid/Partial/Overdue/Waived
- **Adjustment approval** - Pending → Approved/Denied with audit trail
- **Period management** - Generate entire year, close completed periods
- **Overdue tracking** - Automatic status update after grace period

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| Total Tests | 165 passing |
| API Endpoints | ~120 total |
| Database Tables | 25+ |
| ADRs | 8 documented |

### Test Breakdown
- Core Models: 17 tests
- Auth System: 52 tests
- Union Operations: 31 tests
- Training System: 33 tests
- Document Management: 11 tests
- Dues Tracking: 21 tests

---

## 📦 Installation & Upgrade

### New Installation

```bash
git clone https://github.com/theace26/IP2A-Database-v2.git
cd IP2A-Database-v2
git checkout v0.7.0
cp .env.compose.example .env.compose
docker-compose up -d
docker exec -it ip2a-api alembic upgrade head
docker exec -it ip2a-api python -m src.seed.run_seed
```

### Upgrade from v0.6.0

```bash
git fetch origin
git checkout v0.7.0
docker exec -it ip2a-api alembic upgrade head
docker exec -it ip2a-api python -m src.seed.dues_seed  # Optional: seed dues data
```

---

## 📚 Documentation

- [ADR-008: Dues Tracking System Design](docs/decisions/ADR-008-dues-tracking-system.md)
- [Dues Tracking Guide](docs/guides/dues-tracking.md)
- [Dues API Reference](docs/reference/dues-api.md)
- [Session Log](docs/reports/session-logs/2026-01-28-phase-4.md)

---

## 🎯 What's Next

### Phase 5: TradeSchool Integration
- External system connectivity
- Data synchronization

### Phase 6: Frontend
- Jinja2 + HTMX + Alpine.js
- Dashboard and CRUD interfaces
- Mobile-responsive design

### Phase 7: Deployment
- Railway/Render hosting
- Production configuration

---

## 🔗 Links

- **Repository:** https://github.com/theace26/IP2A-Database-v2
- **v0.7.0 Tag:** https://github.com/theace26/IP2A-Database-v2/releases/tag/v0.7.0

---

*Released: January 28, 2026*
```

### Step 5: Update CLAUDE.md Current State

Update the "Current State" section in CLAUDE.md:

```markdown
### 📊 Current State
- **Branch:** main
- **Tag:** v0.7.0 (Phase 4 Dues Tracking)
- **Tests:** 165 total (all passing) ✅
```

And update the "Next Task" line:
```markdown
*Next Task: Phase 5 TradeSchool or Phase 6 Frontend*
```

### Step 6: Add Changelog Entry to CLAUDE.md

Add to the changelog table:

```markdown
| 2026-01-28 XX:XX UTC | Claude Code | v0.7.0 Tagged: Phase 4 Dues Tracking complete. 4 models, ~35 endpoints, 21 tests. ADR-008 documented. Ready for Phase 5/6. |
```

### Step 7: Commit All Changes

```bash
git add -A
git status  # Review changes

git commit -m "docs: Finalize Phase 4, prepare v0.7.0 release

- Update CHANGELOG.md with v0.7.0 release notes
- Create docs/releases/RELEASE_NOTES_v0.7.0.md
- Update CLAUDE.md current state
- Dues Tracking System complete:
  * 4 models (DuesRate, DuesPeriod, DuesPayment, DuesAdjustment)
  * ~35 API endpoints
  * Classification-based rates
  * Approval workflow
  * 21 tests passing
- ADR-008 documented"
```

### Step 8: Create Git Tag

```bash
# Create annotated tag
git tag -a v0.7.0 -m "v0.7.0 - Phase 4: Dues Tracking System

Features:
- 4 dues models with classification-based rates
- ~35 API endpoints across 4 routers
- 9 member classifications (apprentice 1-5, journeyman, foreman, retiree, honorary)
- Payment status workflow (pending/paid/partial/overdue/waived)
- Adjustment approval workflow (pending/approved/denied)
- Period management with close functionality
- Overdue tracking after grace period

Stats:
- 165 tests passing
- ~120 API endpoints total
- 8 ADRs documented

Next: Phase 5 TradeSchool or Phase 6 Frontend"

# Verify tag
git tag -l -n1 v0.7.0
```

### Step 9: Push to Remote

```bash
# Push commits
git push origin main

# Push tag
git push origin v0.7.0

# Verify on GitHub
echo "Check: https://github.com/theace26/IP2A-Database-v2/releases/tag/v0.7.0"
```

---

## Checklist

- [ ] Verify all Phase 4 files exist
- [ ] Run pytest - 165 tests passing
- [ ] Update CHANGELOG.md with v0.7.0 section
- [ ] Create docs/releases/RELEASE_NOTES_v0.7.0.md
- [ ] Update CLAUDE.md current state
- [ ] Add CLAUDE.md changelog entry
- [ ] Commit changes
- [ ] Create v0.7.0 tag
- [ ] Push commits and tag

---

## Expected Outcome

- ✅ v0.7.0 tag created and pushed
- ✅ Release notes documented
- ✅ CHANGELOG.md updated
- ✅ Ready for Phase 5 or Phase 6

---

*End of Instructions*
