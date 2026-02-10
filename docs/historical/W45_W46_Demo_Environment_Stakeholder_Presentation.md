# Claude Code Instructions: Weeks 45–46 — Demo Environment & Stakeholder Presentation

**Spoke:** Spoke 2: Operations
**Created:** February 6, 2026
**Estimated Hours:** 5–8 (3–4 for W45, 2–4 for W46)
**Branch:** `develop`
**Starting Version:** v0.9.18-alpha (requires Week 44 completion)
**Target Version:** v0.9.20-alpha
**Dependency:** Weeks 43–44 MUST be complete. Test suite must be green. Phase 7 docs must be closed out.

---

## Context

This is the most strategically important sprint pair in the project. The stakeholder demo simultaneously:

1. **Unblocks 7a/7d** — The Access DB owner sees a working system and grants LaborPower data access
2. **Builds leadership support** — Union officers see the dispatch/referral system replacing daily LaborPower reports
3. **Neutralizes IT contractor concerns** — Docker isolation + Grafana monitoring = "I don't touch your stuff"
4. **Validates 85 reports** — Officers see real report output, confirm formats match their workflows

If this demo goes well, the project gets organizational buy-in and the remaining blocked sub-phases unlock. If it doesn't, we're stuck indefinitely. **Treat this sprint like a production deployment.**

---

## Pre-Flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git status  # Must be clean

# Verify Week 44 is complete
git log --oneline -5  # Should see Week 44 commit (v0.9.18-alpha)
grep "v0.9.18" CLAUDE.md  # Version must match

# Verify test baseline from Week 43
pytest -v --tb=short 2>&1 | tail -5
# Must show ≥98% pass rate — if not, STOP and fix first

# Verify Docker environment
docker --version
docker-compose --version
docker-compose up -d
docker-compose ps  # All services must be running

# Verify WeasyPrint (for PDF reports in demo)
python -c "import weasyprint; print('WeasyPrint OK')"
```

> ⚠️ **HARD STOP:** If tests aren't green or Docker isn't working, fix those issues first. Do not proceed to demo seed data on a broken foundation.

---

## WEEK 45: Demo Environment & Seed Data

### Objective

Build a realistic demo environment with seed data that tells a compelling story. The data must be realistic enough that dispatchers and officers recognize their daily workflows.

---

### Task 1: Create Demo Seed Script

**New File:** `src/db/demo_seed.py`

This script must be **idempotent** — safe to run multiple times without creating duplicates. Use `get_or_create` patterns.

```python
"""
Demo seed data for UnionCore stakeholder presentation.

Usage:
    python -m src.db.demo_seed

Creates realistic dispatch/referral data for demo purposes.
Idempotent — safe to run multiple times.
"""
```

#### Required Demo Data

**Referral Books (5 books minimum):**

| Book | Region | Contract Code | Registration Count | Notes |
|------|--------|---------------|-------------------|-------|
| WIRE SEATTLE | Seattle | WIREPERSON | 15–20 registrants | Largest book, most activity |
| WIRE BREMERTON | Bremerton | WIREPERSON | 10–15 registrants | Show cross-regional |
| TECHNICIAN | Jurisdiction-wide | SOUND & COMM | 8–10 registrants | Show inverted tier distribution |
| STOCKMAN | Jurisdiction-wide | STOCKPERSON | 5–8 registrants | Show book ≠ contract code |
| SOUND & COMM | Jurisdiction-wide | SOUND & COMM | 5–8 registrants | Additional classification |

**Members (20–30 active):**
- Use realistic-sounding names (e.g., "John Martinez", "Sarah Chen", "Mike O'Brien") — union electricians
- Varied classifications matching the books above
- Some members registered on MULTIPLE books (cross-regional Wire members)
- At least 2 members on 3+ books (demonstrates Rule 5 — one per classification, multiple classifications)
- Mix of Book 1, Book 2, and Book 3 tier registrants
- APNs must be DECIMAL(10,2) with realistic Excel serial date encoding (e.g., 45880.23, 45881.41)

**Employers (5–8):**
- Mix of contractor types:
  - 2 large general contractors (WIREPERSON + RESIDENTIAL contracts)
  - 1 Sound & Communications specialist (SOUND & COMM only)
  - 1 stockperson shop (STOCKPERSON)
  - 1 multi-contract employer (3+ contract codes — shows employer versatility)
  - 1 residential-only (RESIDENTIAL — demonstrates 8th contract code discovery)
- Include employer contact info, signatory status

**Dispatch Records (15–20):**
- Full lifecycle representation:
  - 5+ COMPLETED dispatches (member dispatched → worked → returned to book)
  - 3+ ACTIVE dispatches (currently working)
  - 2+ SHORT CALL dispatches (≤10 days, Rule 9)
  - 1 QUIT dispatch (Rule 12 — shows cascade roll-off from all books)
  - 1 BY-NAME request (Rule 13 — foreperson by-name)
  - 1+ CANCELLED labor request (employer withdrew)
- Timestamps spanning 90+ days back (needed for P3 forecast reports)
- Include varied shift times, job locations

**Check Marks (3–5 records, Rule 10):**
- 2 members with 1 check mark each (still active)
- 1 member with 2 check marks (at the limit — next one rolls off)
- Show check marks are per-area-book (member has mark on Wire Seattle, clean on Wire Bremerton)

**Exemptions (2–3 records, Rule 14):**
- 1 military exemption (with date range)
- 1 medical exemption
- 1 union business exemption (salting)

**Labor Requests (8–12):**
- Mix of statuses: OPEN, FILLED, CANCELLED, EXPIRED
- Include cutoff timestamps (Rule 3 — 3:00 PM cutoff)
- At least 1 request with specific skill requirements
- At least 1 PLA/CWA agreement type (Rule 4)

**Historical Depth:**
- Data should span at least 90 days back from current date
- Include some members who have re-signed (Rule 7 — 30-day cycle)
- Include at least 1 re-registration (Rule 6 — after short call)

#### Seed Script Architecture

```python
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def seed_demo_data(db: Session) -> dict:
    """
    Create complete demo dataset. Returns summary of created records.
    Idempotent — checks for existing demo data before creating.
    """
    summary = {}

    # Phase 1: Books
    summary["books"] = _seed_referral_books(db)

    # Phase 2: Members (with varied classifications)
    summary["members"] = _seed_demo_members(db)

    # Phase 3: Employers (with contract associations)
    summary["employers"] = _seed_demo_employers(db)

    # Phase 4: Registrations (members on books with realistic APNs)
    summary["registrations"] = _seed_registrations(db)

    # Phase 5: Labor Requests
    summary["labor_requests"] = _seed_labor_requests(db)

    # Phase 6: Dispatches (full lifecycle)
    summary["dispatches"] = _seed_dispatches(db)

    # Phase 7: Check marks, exemptions, activities
    summary["check_marks"] = _seed_check_marks(db)
    summary["exemptions"] = _seed_exemptions(db)

    db.commit()
    return summary


def _seed_referral_books(db: Session) -> int:
    """Create referral books. Skip if already exist."""
    # Use book_name as natural key for idempotency
    ...

# ... (implement each phase)

if __name__ == "__main__":
    from src.database import SessionLocal
    db = SessionLocal()
    try:
        result = seed_demo_data(db)
        for entity, count in result.items():
            logger.info(f"  {entity}: {count} records")
    finally:
        db.close()
```

> ⚠️ **APN Values:** Must be DECIMAL(10,2). Use realistic Excel serial date encoding. Example: February 1, 2026 ≈ 46054. So APNs should look like `46054.23`, `46055.41`, `46030.67` (for members registered in early January). The integer part is the date, the decimal is the intra-day ordering.

---

### Task 2: Create Demo Docker Compose

**New File:** `deployment/docker-compose.demo.yml`

This is a self-contained demo compose file that:
- Starts PostgreSQL with demo data
- Starts the API server
- Optionally starts Grafana for the IT contractor audience
- Uses clearly labeled demo ports to avoid conflicts

```yaml
# deployment/docker-compose.demo.yml
# Self-contained demo environment for stakeholder presentations
# Usage: docker-compose -f deployment/docker-compose.demo.yml up -d

version: '3.8'

services:
  demo-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: unioncore_demo
      POSTGRES_USER: demo
      POSTGRES_PASSWORD: DemoPassword2026!
    ports:
      - "5433:5432"  # Non-standard port to avoid conflicts
    volumes:
      - demo-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U demo -d unioncore_demo"]
      interval: 5s
      timeout: 5s
      retries: 5

  demo-api:
    build:
      context: ..
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://demo:DemoPassword2026!@demo-db:5432/unioncore_demo
      SECRET_KEY: demo-secret-key-not-for-production
      ENV: demo
      DEMO_MODE: "true"
    ports:
      - "8080:8000"  # Non-standard port
    depends_on:
      demo-db:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             python -m src.db.demo_seed &&
             uvicorn src.main:app --host 0.0.0.0 --port 8000"

volumes:
  demo-db-data:
```

---

### Task 3: Create Demo User Accounts

Add to demo_seed.py or create separately. Three accounts with distinct roles:

| Username | Password | Role | Purpose |
|----------|----------|------|---------|
| `demo_dispatcher` | `Demo2026!` | Staff | Day-to-day dispatch operations |
| `demo_officer` | `Demo2026!` | Officer | Reports, approvals, analytics |
| `demo_admin` | `Demo2026!` | Admin | Full system access, audit logs |

Each account should have a realistic display name (e.g., "Demo Dispatcher", "Demo Officer").

---

### Task 4: Smoke Test

Run through this checklist manually after seed data is loaded:

```bash
# Start demo environment
cd deployment
docker-compose -f docker-compose.demo.yml up -d

# Wait for healthy
docker-compose -f docker-compose.demo.yml ps
# All services should show "healthy" or "Up"
```

**Smoke Test Checklist:**

- [ ] Login as `demo_dispatcher` → lands on dashboard
- [ ] Navigate to Dispatch Board → shows pending labor requests
- [ ] Navigate to Book Status → shows 5 books with registration counts
- [ ] Click a book → shows registrants sorted by APN
- [ ] Navigate to Active Dispatches → shows currently dispatched members
- [ ] Generate 1 P0 report (e.g., Morning Referral Sheet) → PDF downloads
- [ ] Generate 1 P1 report (e.g., Registration History) → Excel downloads
- [ ] Login as `demo_officer` → has Reports section visible
- [ ] Generate 1 P2/P3 report (e.g., Dispatch Forecast) → renders correctly
- [ ] Login as `demo_admin` → audit logs visible
- [ ] Check audit log shows seed data creation entries

> **If any smoke test fails:** Fix it before proceeding to Week 46. A broken demo is worse than no demo.

---

### Week 45 Acceptance Criteria

- [ ] `src/db/demo_seed.py` created and idempotent
- [ ] Seed data includes all required entities (books, members, employers, dispatches, check marks, exemptions)
- [ ] APNs use correct DECIMAL(10,2) encoding
- [ ] Historical data spans 90+ days
- [ ] `deployment/docker-compose.demo.yml` created and functional
- [ ] 3 demo accounts created (dispatcher, officer, admin)
- [ ] All smoke test items pass
- [ ] Demo environment starts clean from `docker-compose up -d`
- [ ] Demo environment tears down clean with `docker-compose down -v`

### Week 45 Git Commit

```bash
git add -A
git commit -m "feat(demo): Week 45 — demo environment and seed data

- Created src/db/demo_seed.py with realistic dispatch/referral data
  - 5 referral books, 20-30 members, 5-8 employers
  - 15-20 dispatch records with full lifecycle representation
  - Check marks, exemptions, labor requests
  - 90+ days historical depth for forecast reports
- Created deployment/docker-compose.demo.yml (self-contained)
- Created 3 demo accounts: dispatcher, officer, admin
- Smoke tested: login, dispatch board, book status, 3 report types

Version: v0.9.19-alpha
Spoke: Spoke 2 (Operations)"
git push origin develop
```

---

## WEEK 46: Demo Script & Stakeholder Talking Points

### Objective

Create the presentation script and audience-specific talking points. Dry-run the entire demo end-to-end.

---

### Task 1: Create Demo Script

**New File:** `docs/demo/DEMO_SCRIPT_v1.md`

Create directory first:
```bash
mkdir -p docs/demo
```

Structure the demo as a **5-act narrative** with timing:

```markdown
# UnionCore Demo Script v1

> **Total Runtime:** ~22 minutes
> **Presenter:** [Your name]
> **Audience:** Union leadership, Access DB owner, IT contractor
> **Environment:** Demo environment (docker-compose.demo.yml)
> **Pre-demo:** Start demo environment 10 minutes before. Verify smoke test. Open browser to login page.

---

## Act 1: "The Problem" (2 minutes)

**Logged in as:** Nobody (show login screen)

**Talking points:**
- "Today we manage dispatch with 3 separate systems that don't talk to each other"
- "LaborPower handles referral but it's aging and we can't customize it"
- "The Access database handles [X] but only one person can maintain it"
- "Dispatchers spend [X] minutes every morning manually cross-referencing"
- "What I'm going to show you is a single system that handles all of this"

**Action:** Pause. Let the problem sink in.

---

## Act 2: "The Daily Workflow" (10 minutes)

**Log in as:** `demo_dispatcher` / `Demo2026!`

### 2a. Morning Dispatch Board (3 min)
- Show the dispatch dashboard
- Point out: pending labor requests from yesterday (submitted before 3 PM cutoff)
- Show: morning processing order (Wire 8:30 → S&C/Marine/Stock 9:00 → Tradeshow 9:30)
- Click into a labor request → show employer details, skill requirements
- "This is what dispatchers see every morning at 8:30"

### 2b. Processing a Referral (3 min)
- Walk through dispatching a member to a labor request
- Show: member's position on the book (APN-sorted queue)
- Show: check mark status (this member has 1 of 2 allowed)
- Process the dispatch → show status change
- "One click. Audit trail automatic. No paper."

### 2c. Book Management (2 min)
- Navigate to Book Status page
- Show: WIRE SEATTLE with registration counts by tier
- Show: cross-regional registrations (same member on Seattle + Bremerton)
- Show: the STOCKMAN book → "Notice the contract code is STOCKPERSON, not STOCKMAN"
- "We found 8 contract codes, not 7. We found 11 books, not 8."

### 2d. Enforcement (2 min)
- Show check mark tracking
- Show a member with 2 check marks (at the limit)
- Show exemptions (military, medical)
- "The system enforces the rules from the Referral Procedures automatically"

---

## Act 3: "The Reports" (5 minutes)

**Log in as:** `demo_officer` / `Demo2026!`

### 3a. P0 Reports — Daily Operational (2 min)
- Generate Morning Referral Sheet (PDF)
- "This is what dispatchers print every morning"
- Generate Out-of-Work List for WIRE SEATTLE
- "This replaces the LaborPower printout"

### 3b. P1 Reports — Weekly/Monthly (1.5 min)
- Generate Employer Active List (Excel)
- "Officers get this monthly — who's hiring, who's not"

### 3c. P2/P3 Reports — Analytics (1.5 min)
- Show a dispatch trend report or forecast
- "85 reports total. 14 critical daily reports. All built."
- "Historical data going back [X] days for forecasting"

---

## Act 4: "Under the Hood" (3 minutes)

**Target audience:** IT contractor

- Show Docker compose file: "It's 30 lines. All self-contained."
- Show Grafana dashboard (if set up): "Monitoring built in."
- "You don't maintain this. I do. Your systems are untouched."
- "It runs in its own container — isolated from everything else."
- Show audit log: "Every action is logged. 7-year retention. NLRA compliant."

---

## Act 5: "What's Next" (2 minutes)

**Talking points:**
- "Right now this runs on demo data. To go live, we need the LaborPower data export."
- "[Access DB owner name], your expertise would be invaluable for validating the data migration."
- "Next phase: online dues payment through Square. Members pay from their phone."
- "Everything I've shown you was built in [X] weeks of part-time development."
- "Questions?"

---

## Contingency Plans

| Problem | Recovery |
|---------|----------|
| Docker won't start | Fall back to local uvicorn: `uvicorn src.main:app --port 8000` |
| PDF report fails | Show the web version of the report instead |
| Login fails | Use demo_admin as fallback; all roles visible |
| Projector issues | Have screenshots in docs/demo/screenshots/ as backup |
| Tough question you can't answer | "Great question. Let me look into that and follow up." |
```

---

### Task 2: Create Stakeholder Talking Points

**New File:** `docs/demo/STAKEHOLDER_TALKING_POINTS.md`

```markdown
# Stakeholder-Specific Talking Points

## Access DB Owner

**Goal:** Get them excited about collaboration, not threatened by replacement.

- "This system complements yours — it handles dispatch, which your database wasn't designed for."
- "Your data stays in your database. We'd love your help validating when we import the LaborPower data."
- "You understand the business rules better than anyone. We need that expertise."
- "Think of it as: your system handles [what it handles], UnionCore handles dispatch and referral."
- ⚠️ **Do NOT say:** "replace", "migrate away from", "sunset"
- ✅ **Do say:** "complement", "work alongside", "your expertise"

## IT Contractor

**Goal:** Assure them this is contained and doesn't create work for them.

- "Everything runs in Docker containers — completely isolated from your network."
- "I handle all updates and maintenance. You don't need to touch this."
- "Here's the Grafana dashboard — you can monitor it if you want, but you don't have to."
- "The database is PostgreSQL — industry standard, not some custom thing."
- "Backups are automated. Disaster recovery is documented."
- ⚠️ **Do NOT say:** "I need access to your servers", "can you install this"
- ✅ **Do say:** "self-contained", "isolated", "I maintain it"

## Union Leadership (Business Manager, Officers)

**Goal:** Show business value. Reports they recognize. Daily time savings.

- "This replaces the daily LaborPower printouts your dispatchers use every morning."
- "85 reports — 14 of them are the critical daily operational reports."
- "Members will be able to check their book status and bid on jobs from their phone."
- "Online dues payment is the next phase — members pay from their phone via Square."
- "Every action is logged with a 7-year audit trail — NLRA compliant."
- "Built-in check mark tracking, exemption management, 30-day re-sign enforcement."
- ⚠️ **Frame as:** "time savings", "member service", "compliance", "modernization"
- ✅ **Key stat:** "Built in [X] weeks of part-time development. Feature parity with LaborPower for dispatch."
```

---

### Task 3: Dry Run

Execute the full demo script end-to-end. Note timing and fix any issues.

```bash
# Start fresh demo environment
cd deployment
docker-compose -f docker-compose.demo.yml down -v
docker-compose -f docker-compose.demo.yml up -d

# Wait for healthy
sleep 15
docker-compose -f docker-compose.demo.yml ps
```

**Dry Run Checklist:**

- [ ] Act 1: Login page loads cleanly
- [ ] Act 2a: Dispatch dashboard shows pending requests
- [ ] Act 2b: Can process a referral (dispatch a member)
- [ ] Act 2c: Book status shows 5 books with correct counts
- [ ] Act 2d: Check mark and exemption pages work
- [ ] Act 3a: P0 report generates as PDF
- [ ] Act 3b: P1 report generates as Excel
- [ ] Act 3c: P2/P3 report renders correctly
- [ ] Act 4: Docker compose file accessible, audit log shows entries
- [ ] Total runtime: ≤25 minutes (with buffer)
- [ ] No errors, no loading spinners, no broken pages

**If issues found during dry run:**
- Fix immediately if <15 min
- Document as "demo blocker" and fix before demo date if >15 min
- Create fallback plan (screenshots, alternative workflow)

---

### Task 4: Create Screenshots Directory (Optional but Recommended)

```bash
mkdir -p docs/demo/screenshots
```

Take screenshots of key demo moments as backup:
- Login page
- Dispatch dashboard
- Book status page
- Morning referral processing
- A generated PDF report
- Audit log page

These serve as fallback if demo environment has issues during the actual presentation.

---

### Week 46 Acceptance Criteria

- [ ] `docs/demo/` directory created
- [ ] `docs/demo/DEMO_SCRIPT_v1.md` created with 5-act structure and timing
- [ ] `docs/demo/STAKEHOLDER_TALKING_POINTS.md` created for all 3 audiences
- [ ] Dry run completed successfully — all acts work
- [ ] Total demo runtime ≤25 minutes
- [ ] Contingency plans documented
- [ ] No demo-blocking issues remaining
- [ ] Screenshots captured (if done)

### Week 46 Git Commit

```bash
git add -A
git commit -m "docs(demo): Week 46 — demo script and stakeholder talking points

- Created docs/demo/DEMO_SCRIPT_v1.md (5-act, 22-min demo)
  - Act 1: Problem statement
  - Act 2: Daily dispatch workflow (dispatcher role)
  - Act 3: Reports showcase (officer role)
  - Act 4: Infrastructure overview (IT audience)
  - Act 5: Next steps and ask
- Created docs/demo/STAKEHOLDER_TALKING_POINTS.md
  - Access DB owner: collaboration framing
  - IT contractor: containment assurance
  - Union leadership: business value
- Dry run completed: [results]
- Contingency plans documented

Version: v0.9.20-alpha
Spoke: Spoke 2 (Operations)"
git push origin develop
```

---

## Anti-Patterns (DO NOT)

- ❌ Do NOT use production data in demo seed — all demo data must be fictional
- ❌ Do NOT hardcode demo passwords in source code (use environment variables or seed script)
- ❌ Do NOT skip the dry run — untested demos fail publicly
- ❌ Do NOT make the demo too technical for leadership — dispatchers care about workflow, not architecture
- ❌ Do NOT use "replace" language with the Access DB owner — use "complement"
- ❌ Do NOT promise timelines during the demo — say "I'll follow up with a timeline"
- ❌ Do NOT leave the demo environment running on the develop branch — demo data stays isolated

## Files Created / Modified

### Week 45 — Created
- `src/db/demo_seed.py` (NEW)
- `deployment/docker-compose.demo.yml` (NEW)

### Week 45 — Modified
- `CLAUDE.md` (version bump to v0.9.19-alpha)
- `CHANGELOG.md` (Week 45 entry)

### Week 46 — Created
- `docs/demo/DEMO_SCRIPT_v1.md` (NEW)
- `docs/demo/STAKEHOLDER_TALKING_POINTS.md` (NEW)
- `docs/demo/screenshots/` (NEW directory, optional)

### Week 46 — Modified
- `CLAUDE.md` (version bump to v0.9.20-alpha)
- `CHANGELOG.md` (Week 46 entry)

---

## Documentation Mandate

> Make sure to update *ANY* & *ALL* documents to track our progress and for the historical record located in the directory /app/* OR /app/docs/* as necessary. Including ADR's, bug log, etc.

---

## Session Summary Template

```markdown
## Session: Weeks 45–46 — Demo Environment & Stakeholder Presentation
**Date:** [DATE]
**Duration:** [X] hours
**Spoke:** Spoke 2 (Operations)
**Starting Version:** v0.9.18-alpha
**Ending Version:** v0.9.20-alpha

### Week 45 Results
- Demo seed data: [X] books, [X] members, [X] employers, [X] dispatches
- Docker compose: [working/issues]
- Demo accounts: 3 created (dispatcher, officer, admin)
- Smoke test: [all pass / issues found]

### Week 46 Results
- Demo script: 5 acts, [X] minutes total
- Talking points: 3 audiences covered
- Dry run: [pass / issues found and fixed]
- Screenshots: [captured / skipped]

### Cross-Cutting Changes
- [List any changes to shared files]
- Hub handoff needed: [yes/no]

### Demo Readiness
- [ ] Environment starts cleanly
- [ ] All 5 acts execute without errors
- [ ] Reports generate correctly
- [ ] Stakeholder talking points reviewed
- [ ] Contingency plans in place

### Post-Demo Actions (for after the presentation)
- [ ] Capture feedback from each stakeholder
- [ ] Document access granted / blocked
- [ ] Update roadmap based on feedback
- [ ] Create Hub handoff with demo outcomes
```

---

## What Happens After Week 46

```
Week 46 complete → STAKEHOLDER DEMO EVENT
                    │
                    ├── Access DB owner grants access → Unblocks 7a → 7d
                    ├── Leadership approves → Project continues with support
                    ├── IT contractor satisfied → No blockers from IT
                    │
                    └── Hub reviews Spoke 1 Onboarding Doc (from Week 44)
                         └── Week 47: Spoke 1 begins Phase 8A (Square)
```

The demo is the inflection point. Everything before it builds toward this moment. Everything after flows from its outcome.

---

*Spoke 2: Operations — Weeks 45–46 Instruction Document*
*Generated: February 6, 2026*
