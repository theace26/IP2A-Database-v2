# SUB-PHASE 7a: DATA COLLECTION

**Status:** ⛔ BLOCKED — Awaiting LaborPower system access
**Estimated Effort:** 3-5 hours
**Prerequisites:** LaborPower login credentials or delegation to someone with access
**Spoke:** Spoke 2 (Operations)
**Parent:** [Phase 7 Framework](Phase_7_Subphase_Instruction_Framework.md)

---

## Objective

Obtain 3 Priority 1 data exports from LaborPower's Custom Reports module. These exports are BLOCKING for schema finalization.

## Required Exports

| # | Report Name | What We Need | Why Blocking |
|---|-------------|-------------|--------------|
| 1 | REGLIST (with member identifiers) | Full registration list: member_id/card_number + APN + book + tier | Cannot resolve APN-to-member mapping when duplicates exist |
| 2 | RAW DISPATCH DATA | Complete dispatch history CSV with all column headers | Need to know every field LaborPower stores per dispatch |
| 3 | EMPLOYCONTRACT | Employer-to-contract-code mappings with dates | Need to explain 196 duplicate employer entries |

## Execution Steps

1. Log into LaborPower (or have dispatch staff run the reports)
2. Navigate to Custom Reports module
3. Run each report with ALL fields selected, ALL date ranges
4. Export as CSV (preferred) or PDF
5. Save exports to `docs/phase7/data/` (create directory if needed)

## Output

- 3 CSV/PDF files in `docs/phase7/data/`
- Brief analysis notes for each export (column headers, row counts, any surprises)
- Updated gap analysis: which Priority 1 gaps are now resolved?

## Acceptance Criteria

- [ ] All 3 exports obtained
- [ ] Column headers documented
- [ ] Row counts recorded
- [ ] Files committed to repo (in `docs/phase7/data/` — .gitignore if sensitive)
- [ ] Gap analysis updated

## ⚠️ NOT YET READY — Blocked on stakeholder approval for LaborPower access

---

*Created: February 5, 2026 — Spoke 2*
