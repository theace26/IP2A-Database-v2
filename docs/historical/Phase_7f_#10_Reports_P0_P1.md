# SUB-PHASE 7f: REPORTS P0 + P1

**Status:** Stub — Waiting on 7c
**Estimated Effort:** 20-30 hours
**Prerequisites:** 7c complete — Services available for data queries
**Spoke:** Spoke 2 or Spoke 3 (Reports may move to Infrastructure spoke)
**Parent:** [Phase 7 Framework](Phase_7_Subphase_Instruction_Framework.md)

---

## Objective

Build the 49 highest-priority reports (16 P0 + 33 P1) to achieve operational parity with LaborPower's reporting capabilities.

## Report Technology

- **PDF generation:** WeasyPrint (already used in Week 8 report module)
- **Excel generation:** openpyxl (already used in grant compliance reports)
- **Charts:** Chart.js (already used in Week 19 analytics dashboard)
- **Templating:** Jinja2 templates for report layouts

## P0 Reports (16 — Daily Operations)

These are the reports dispatch staff use every day. Full list in `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md`.

Examples: Out-of-work book lists, daily dispatch logs, employer active lists, morning referral queues.

## P1 Reports (33 — Weekly/Monthly)

Employment tracking, contractor workforce summaries, registration history, check mark reports.

## Expected Output

- Report service: `src/services/referral_report_service.py`
- Report templates in `src/templates/reports/referral/`
- API endpoints for report generation + download
- PDF and Excel output for each report
- Tests for report generation

## Acceptance Criteria

- [ ] All 16 P0 reports generate correctly
- [ ] All 33 P1 reports generate correctly
- [ ] PDF and Excel output for each
- [ ] Report data validated against service queries
- [ ] Existing report module patterns followed (Week 8)
- [ ] Tests for each report
- [ ] CLAUDE.md, CHANGELOG.md updated

## ⚠️ NOT YET READY — Waiting on 7c (services must be stable for report queries)

---

*Created: February 5, 2026 — Spoke 2*
