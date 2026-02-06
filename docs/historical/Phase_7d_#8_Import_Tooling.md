# SUB-PHASE 7d: IMPORT TOOLING

**Status:** Stub — Waiting on 7b (can run parallel with 7c)
**Estimated Effort:** 15-20 hours
**Prerequisites:** 7b complete — Schema locked, migrations applied
**Spoke:** Spoke 2 (Operations)
**Parent:** [Phase 7 Framework](Phase_7_Subphase_Instruction_Framework.md)

---

## Objective

Build CSV import pipeline to migrate production data from LaborPower into UnionCore. Import order matters due to foreign key dependencies.

## Import Order (FK-safe)

```
1. employers (organizations table)    — No FK dependencies
2. employer_contracts                  — FK → organizations
3. referral_books                      — Seed data (already done in 7b)
4. book_registrations                  — FK → members, referral_books
5. dispatches (historical)             — FK → members, labor_requests, book_registrations
```

## Pipeline Architecture

```
CSV File → Validation → Staging Table → Reconciliation → Production Insert
                ↓              ↓                ↓
           Reject Log    Duplicate Check    Audit Log Entry
```

## Key Challenges

| Challenge | Solution |
|-----------|----------|
| Duplicate employers (196 known) | Fuzzy matching + manual review queue |
| APN decimal preservation | Parse as Decimal, never float |
| Member ID resolution | Match on card_number or name+DOB composite |
| Historical dispatch dates | Preserve original timestamps, don't auto-generate |

## Expected Output

- Import scripts in `scripts/import/`
- Validation reports for each import step
- Rejected rows log with reasons
- Import test suite
- Runbook: `docs/runbooks/data-import.md`

## Acceptance Criteria

- [ ] Employer import handles duplicates gracefully
- [ ] APN decimal values preserved through entire pipeline
- [ ] Foreign key relationships maintained
- [ ] Audit trail for all imported records
- [ ] Validation reports generated
- [ ] Rejected rows documented with reasons
- [ ] Runbook created for production import

## ⚠️ NOT YET READY — Waiting on 7b. Can start in parallel with 7c once schema is locked.

---

*Created: February 5, 2026 — Spoke 2*
