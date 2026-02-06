# SUB-PHASE 7b: SCHEMA FINALIZATION

**Status:** READY WHEN 7a completes
**Estimated Effort:** 10-15 hours
**Prerequisites:** 7a complete — Priority 1 data exports analyzed
**Spoke:** Spoke 2 (Operations)
**Parent:** [Phase 7 Framework](Phase_7_Subphase_Instruction_Framework.md)

---

## Objective

Lock the Phase 7 database schema. Create Alembic migrations for all Phase 7 tables. Seed referral books and contract codes. Validate against all 14 business rules.

## Important: Existing Models

Weeks 20-21 already created 6 models with 19 enums. This sub-phase REFINES those models based on Priority 1 data from 7a, creates proper Alembic migrations (replacing any development-time auto-generated ones), and adds any missing tables discovered during data analysis.

### Currently Implemented (from Weeks 20-21)

| Model | File | Status |
|-------|------|--------|
| ReferralBook | `src/models/referral_book.py` | ✅ Exists — may need refinement |
| BookRegistration | `src/models/book_registration.py` | ✅ Exists — may need refinement |
| RegistrationActivity | `src/models/registration_activity.py` | ✅ Exists — may need refinement |
| LaborRequest | `src/models/labor_request.py` | ✅ Exists — may need refinement |
| JobBid | `src/models/job_bid.py` | ✅ Exists — may need refinement |
| Dispatch | `src/models/dispatch.py` | ✅ Exists — has known Dispatch.bid bug |

### Potentially Needed (from original 12-table design — assess during 7b)

| Table | Purpose | Status |
|-------|---------|--------|
| employer_contracts | Employer-to-contract-code mappings | Assess: may be handled differently |
| job_requirements | Per-request skill/cert requirements | Assess: may be columns on labor_requests |
| web_bids | Internet bidding records | Assess: may be subset of job_bids |
| check_marks | Penalty tracking | Assess: may be in registration_activities |
| member_exemptions | No-check-mark exceptions | Assess: needed for Rule 11, 14 |
| bidding_infractions | Internet bidding privilege revocation | Assess: needed for Rule 8 |
| worksites | Physical job locations | Assess: may be columns on labor_requests |
| blackout_periods | Foreperson restrictions | Assess: needed for Rule 12, 13 |

---

## Execution Steps

### Step 1: Analyze Priority 1 Data (2-3 hours)

With the 3 exports from 7a in hand:

1. **REGLIST analysis:**
   - Map every column to the `book_registrations` model
   - Confirm APN decimal encoding matches DECIMAL(10,2)
   - Resolve member_id mapping (card_number → members.card_number FK?)
   - Document any columns not in current schema

2. **RAW DISPATCH DATA analysis:**
   - Map every column to the `dispatches` model
   - Identify any fields we don't have (→ new columns or tables)
   - Document the dispatch lifecycle (status transitions)
   - Note any surprise fields (e.g., foreman tracking, blackout references)

3. **EMPLOYCONTRACT analysis:**
   - Confirm 8 contract codes (including RESIDENTIAL)
   - Map employer-to-contract relationships
   - Resolve the 196 duplicate employer entries
   - Decide: separate `employer_contracts` table or columns on `organizations`?

### Step 2: Schema Refinement (2-3 hours)

Based on analysis, update the 6 existing models:

```bash
# Files to potentially modify:
src/models/referral_book.py
src/models/book_registration.py
src/models/registration_activity.py
src/models/labor_request.py
src/models/job_bid.py
src/models/dispatch.py
src/db/enums/phase7_enums.py
```

**For each model:**
1. Compare current columns against data export columns
2. Add missing columns
3. Fix data types (especially APN — MUST be DECIMAL(10,2))
4. Update enum values if new values discovered in data
5. Fix the Dispatch.bid relationship bug (add `foreign_keys=[bid_id]`)

**Schema corrections checklist (must be verified):**

| Correction | Current State | Action |
|------------|--------------|--------|
| APN = DECIMAL(10,2) | ✅ Already correct | Verify |
| APN field = applicant_priority_number | ✅ Already correct | Verify |
| Unique = (member_id, book_id, book_priority_number) | ✅ Already correct | Verify |
| contract_code NULLABLE | ✅ Already correct | Verify |
| agreement_type column | ✅ Already exists | Verify values |
| work_level column | ✅ Already exists | Verify values |
| book_type column | ✅ Already exists | Verify values |
| 8 contract codes | Check enum | Update if needed |
| Dispatch.bid foreign_keys | ❌ BUG | **FIX THIS** |

### Step 3: Create New Tables (if needed) (2-3 hours)

Based on data analysis, decide which of the 6 "potentially needed" tables to create:

For each new table:
1. Write the SQLAlchemy model in `src/models/`
2. Add enums to `src/db/enums/phase7_enums.py`
3. Add the model import to `src/models/__init__.py`
4. Create Pydantic schemas in `src/schemas/`

**Naming conventions:**
- Tables: `snake_case`, plural (`check_marks`, `member_exemptions`)
- Models: `PascalCase`, singular (`CheckMark`, `MemberExemption`)
- Enums: `PascalCase` + descriptive suffix (`ExemptionType`, `InfractionSeverity`)

### Step 4: Alembic Migration (1-2 hours)

```bash
# Generate migration
alembic revision --autogenerate -m "phase7_schema_finalization"

# Review the generated migration BEFORE applying
cat alembic/versions/[latest].py

# Verify:
# - All new tables present
# - All column modifications present
# - Enum types created BEFORE table creation
# - Foreign keys reference correct tables
# - No DROP statements for existing tables

# Apply
alembic upgrade head
```

**Migration safety rules:**
- Enum types must be created before they're used in column definitions
- Foreign keys must reference existing tables
- Never auto-drop tables or columns — review every DROP statement
- Test rollback: `alembic downgrade -1` then `alembic upgrade head`

### Step 5: Seed Data (1 hour)

Create or update `src/db/seed_phase7.py`:

```python
# Seed the 11 known referral books
REFERRAL_BOOKS = [
    {"book_name": "WIRE SEATTLE", "classification": "Wire", "region": "Seattle",
     "contract_code": "WIREPERSON", "agreement_type": "STANDARD",
     "work_level": "JOURNEYMAN", "book_type": "PRIMARY",
     "morning_sort_order": 1, "processing_time": "08:30"},
    {"book_name": "WIRE BREMERTON", "classification": "Wire", "region": "Bremerton",
     "contract_code": "WIREPERSON", "agreement_type": "STANDARD",
     "work_level": "JOURNEYMAN", "book_type": "PRIMARY",
     "morning_sort_order": 1, "processing_time": "08:30"},
    # ... all 11 books from the catalog
]

# Seed the 8 contract codes
CONTRACT_CODES = [
    "WIREPERSON", "SOUND & COMM", "STOCKPERSON", "LT FXT MAINT",
    "GROUP MARINE", "GROUP TV & APPL", "MARKET RECOVERY", "RESIDENTIAL"
]
```

### Step 6: Validate Against Business Rules (1 hour)

For each of the 14 business rules, verify the schema can support it:

| Rule | Schema Support | Verified? |
|------|---------------|-----------|
| 1. Office Hours & Regions | Region field on referral_books | [ ] |
| 2. Morning Processing Order | morning_sort_order + processing_time fields | [ ] |
| 3. Labor Request Cutoff | Timestamp fields on labor_requests | [ ] |
| 4. Agreement Types | agreement_type enum on referral_books + labor_requests | [ ] |
| 5. Registration Rules | Unique constraint on registrations | [ ] |
| 6. Re-Registration Triggers | re_registration_reason enum, activity log | [ ] |
| 7. Re-Sign 30-Day | last_re_sign_date on registrations, activity log | [ ] |
| 8. Internet Bidding | job_bids with time gates, bidding_infractions table | [ ] |
| 9. Short Calls | Duration fields on dispatches, short_call_count tracking | [ ] |
| 10. Check Marks | check_marks table or registration_activities | [ ] |
| 11. No Check Mark Exceptions | member_exemptions table, exemption_type enum | [ ] |
| 12. Quit/Discharge | Cascade deregistration logic, blackout_periods | [ ] |
| 13. Foreperson By Name | by_name_request flag, anti-collusion audit | [ ] |
| 14. Exempt Status | member_exemptions with date ranges | [ ] |

### Step 7: Add to AUDITED_TABLES (15 minutes)

In `src/services/audit_service.py`, add Phase 7 tables to `AUDITED_TABLES`:

```python
AUDITED_TABLES = [
    # ... existing tables ...
    "book_registrations",    # Phase 7
    "dispatches",            # Phase 7
    "check_marks",           # Phase 7 (if created as separate table)
    "member_exemptions",     # Phase 7 (if created)
    "bidding_infractions",   # Phase 7 (if created)
]
```

### Step 8: Tests (2 hours)

Create `src/tests/test_phase7_schema.py`:

```python
"""Phase 7 schema validation tests.

Validates that all Phase 7 tables, columns, constraints, and enums
match the corrected schema from data analysis (Volumes 1 & 2).
"""

def test_referral_books_table_exists(db_session):
    """referral_books table has all required columns."""
    pass

def test_apn_is_decimal(db_session):
    """book_registrations.applicant_priority_number is DECIMAL(10,2)."""
    pass

def test_apn_duplicate_allowed(db_session):
    """Two registrations can have the same APN on different books."""
    pass

def test_apn_unique_constraint(db_session):
    """UNIQUE(member_id, book_id, book_priority_number) is enforced."""
    pass

def test_contract_code_nullable(db_session):
    """referral_books.contract_code allows NULL (Tradeshow, TERO)."""
    pass

def test_eleven_books_seeded(db_session):
    """All 11 known referral books are present after seeding."""
    pass

def test_eight_contract_codes(db_session):
    """All 8 contract codes are valid enum values."""
    pass

def test_dispatch_bid_relationship(db_session):
    """Dispatch.bid relationship resolves correctly (Bug fix)."""
    pass

def test_audit_tables_registered(db_session):
    """Phase 7 tables are in AUDITED_TABLES."""
    pass
```

---

## Acceptance Criteria

- [ ] All 6 existing models reviewed and updated if needed
- [ ] Any new tables created with proper models, schemas, enums
- [ ] Dispatch.bid relationship bug fixed
- [ ] Alembic migration created and applied cleanly
- [ ] Migration rollback tested
- [ ] Seed data for 11 books and 8 contract codes
- [ ] All 14 business rules validated against schema
- [ ] Phase 7 tables added to AUDITED_TABLES
- [ ] Schema validation tests written and passing
- [ ] CLAUDE.md updated
- [ ] CHANGELOG.md updated
- [ ] ADR-015 updated if schema changed significantly
- [ ] Committed to develop branch

## ⚠️ READY WHEN Sub-Phase 7a completes (Priority 1 data exports analyzed)

---

*Created: February 5, 2026 — Spoke 2*
