# UnionCore Demo Environment

**Created:** February 7, 2026 (Week 45)
**Purpose:** Stakeholder demonstration of Phase 7 Referral & Dispatch system
**Version:** v0.9.19-alpha

---

## Quick Start

```bash
# From project root
cd deployment

# Start demo environment
docker-compose -f docker-compose.demo.yml up -d

# Wait 30-60 seconds for database migration and seed data
# Watch logs to see progress
docker-compose -f docker-compose.demo.yml logs -f demo-api

# When you see "📍 Demo available at: http://localhost:8080", it's ready
```

**Access the demo:**
- URL: http://localhost:8080
- Demo accounts created automatically (see below)

**Stop demo environment:**
```bash
docker-compose -f docker-compose.demo.yml down

# To completely reset (clear all data):
docker-compose -f docker-compose.demo.yml down -v
```

---

## Demo Accounts

Three accounts are created automatically with the demo seed data:

| Username | Password | Role | Purpose |
|----------|----------|------|---------|
| `demo_dispatcher@ibew46.demo` | `Demo2026!` | Staff | Day-to-day dispatch operations |
| `demo_officer@ibew46.demo` | `Demo2026!` | Officer | Reports, approvals, analytics |
| `demo_admin@ibew46.demo` | `Demo2026!` | Admin | Full system access, audit logs |

---

## Demo Data Summary

The demo seed creates realistic data for stakeholder presentations:

### Referral Books (5)
- **Wire Seattle** (15-20 registrants) — Largest book, most activity
- **Wire Bremerton** (10-15 registrants) — Cross-regional demonstration
- **Technician Seattle** (8-10 registrants) — Inverted tier distribution
- **Stockperson Seattle** (5-8 registrants) — Book ≠ contract code
- **Sound Seattle** (5-8 registrants) — Additional classification

### Members (30)
- Realistic union electrician names
- Varied classifications matching books above
- Cross-regional Wire members (same member on multiple books)
- Multiple classification registrations (2+ members on 3+ books)
- Mix of Book 1, Book 2, Book 3 tier registrants

### Employers (6)
- 2 large general contractors (WIREPERSON + RESIDENTIAL)
- 1 Sound & Communications specialist
- 1 stockperson shop
- 1 multi-contract employer (3+ contract codes)
- 1 residential-only contractor

### Dispatch Records (15-20)
- **COMPLETED** dispatches (worked and returned to book)
- **ACTIVE** dispatches (currently working)
- **SHORT CALL** dispatches (≤10 days, Rule 9)
- **QUIT** dispatch (Rule 12 — cascade roll-off demonstration)
- **BY-NAME** request (Rule 13 — foreperson by-name)
- **CANCELLED** labor request (employer withdrew)

### Business Rules Demonstrated
- **Check Marks** (Rule 10): 3 registrations with penalty tracking
  - 2 members with 1 check mark each (still active)
  - 1 member with 2 check marks (at the limit)
- **Exemptions** (Rule 14): 3 types
  - Military exemption (with date range)
  - Medical exemption
  - Union business exemption (salting)

### Historical Depth
- Data spans **90+ days** back from current date
- Supports P2/P3 forecast and trend reports
- Re-sign cycles demonstrated (Rule 7)
- Re-registration after short call (Rule 6)

---

## Smoke Test Checklist

After starting the demo environment, verify these key features:

### Login & Dashboard
- [ ] Login as `demo_dispatcher@ibew46.demo` → lands on dashboard
- [ ] Dashboard shows pending labor requests
- [ ] Dashboard shows active dispatches count

### Referral System
- [ ] Navigate to Referral > Book Status → shows 5 books
- [ ] Click "Wire Seattle" → shows registrants sorted by APN
- [ ] Verify APN format: `XXXXX.XX` (DECIMAL with 2 decimal places)
- [ ] Verify cross-regional registration (same member on Seattle + Bremerton)

### Dispatch Workflow
- [ ] Navigate to Dispatch > Dashboard → shows pending labor requests
- [ ] Navigate to Dispatch > Active Dispatches → shows currently dispatched members
- [ ] Navigate to Dispatch > Queue Management → shows queue positions by book

### Reports
- [ ] Login as `demo_officer@ibew46.demo`
- [ ] Generate P0 report: Morning Referral Sheet (PDF) → downloads
- [ ] Generate P1 report: Registration History (Excel) → downloads
- [ ] Generate P2/P3 report: Dispatch Forecast → renders correctly

### Audit & Admin
- [ ] Login as `demo_admin@ibew46.demo`
- [ ] Navigate to Admin > Audit Logs → shows seed data creation entries
- [ ] Verify demo seed operations logged

### Enforcement
- [ ] Navigate to Dispatch > Enforcement Dashboard
- [ ] Verify check mark tracking visible
- [ ] Verify exemption status shown

---

## Troubleshooting

### Demo environment won't start
```bash
# Check if port 5433 (database) or 8080 (API) are in use
lsof -i :5433
lsof -i :8080

# If occupied, stop conflicting services or edit docker-compose.demo.yml ports
```

### Database migration fails
```bash
# View logs
docker-compose -f docker-compose.demo.yml logs demo-api

# Reset and restart
docker-compose -f docker-compose.demo.yml down -v
docker-compose -f docker-compose.demo.yml up -d
```

### Demo seed creates duplicates
The demo seed is idempotent — safe to run multiple times. It uses `get_or_create` patterns to avoid duplicates. If you see duplicates:
1. Stop the environment
2. Reset volumes: `docker-compose -f docker-compose.demo.yml down -v`
3. Restart

### WeasyPrint PDF generation fails
WeasyPrint requires system libraries (libpango, libgdk-pixbuf). If PDF reports fail:
- Check Docker image includes WeasyPrint dependencies
- Fall back to web version of reports during demo
- See: Dockerfile for WeasyPrint setup

---

## Technical Notes

### Port Configuration
- **Database:** Port 5433 (non-standard to avoid dev database conflicts)
- **API Server:** Port 8080 (non-standard to avoid dev server conflicts)

### Environment Variables
Key demo-specific settings in `docker-compose.demo.yml`:
- `IP2A_ENV=demo` — Identifies demo environment
- `DEMO_MODE=true` — Enables demo-specific features
- `RUN_PRODUCTION_SEED=false` — Prevents production seed from running

### Database Isolation
The demo uses a separate database (`unioncore_demo`) and volume (`unioncore-demo-db-data`). This ensures:
- No conflicts with development database
- Clean reset with `down -v`
- Separate demo data from real data

### Idempotency
Running `python -m src.db.demo_seed` multiple times is safe:
- Checks for existing records before creating
- Uses natural keys (email, code, name) for lookups
- Skips creation if record already exists

---

## Next Steps

After verifying the demo environment works:

1. **Week 46: Create Demo Script** (`docs/demo/DEMO_SCRIPT_v1.md`)
   - 5-act narrative structure
   - ~22 minutes total runtime
   - Stakeholder-specific talking points

2. **Dry Run the Demo**
   - Walk through all 5 acts
   - Time each section
   - Identify any rough edges

3. **Prepare Fallbacks**
   - Screenshot key pages
   - Print sample PDF reports
   - Document contingency plans

---

## Demo Environment Status

✅ **Ready for Week 46 demo script creation**

- [x] Demo seed script created (idempotent)
- [x] Docker compose file created (self-contained)
- [x] 3 demo accounts created
- [x] 5 books, 30 members, 6 employers, 15-20 dispatches
- [x] 90+ days historical depth
- [x] All business rules demonstrated

**Smoke test:** Requires Docker environment (run locally)

---

*UnionCore Demo Environment — Week 45 (February 7, 2026)*
