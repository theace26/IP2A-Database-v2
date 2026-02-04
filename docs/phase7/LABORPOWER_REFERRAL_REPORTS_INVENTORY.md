# LaborPower Referral Reports Inventory

> **Document Created:** February 2, 2026
> **Last Updated:** February 3, 2026 (Batch 4b documentation update)
> **Version:** 2.0
> **Status:** Reference — Feature Parity Target for Phase 7
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1-19)

---

## Purpose

Complete inventory of all reports available in LaborPower's Referral module. These reports represent the feature parity target for IP2A Phase 7 (Referral & Dispatch System).

**Source:** Screenshots of LaborPower Report Preparation window, captured February 2, 2026

---

## Related Documents

| Document | Location | Relationship |
|----------|----------|-------------|
| Phase 7 Implementation Plan v2 | `docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` | Week-by-week build plan; report sprints in Weeks 29-32+ |
| Phase 7 Referral & Dispatch Plan | `docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` | Schema and business rules powering report data |
| LaborPower Gap Analysis | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` | Maps IP2A needs vs. LaborPower features |
| LaborPower Implementation Plan | `docs/phase7/LABORPOWER_IMPLEMENTATION_PLAN.md` | Authoritative build schedule (Weeks 20-32) |
| Phase 7 Continuity Doc Addendum | `docs/phase7/PHASE7_CONTINUITY_DOC_ADDENDUM.md` | Report sprint schedule overlap notes |
| ADR-014 Grant Compliance Reporting | `docs/decisions/ADR-014-grant-compliance-reporting.md` | WeasyPrint PDF + openpyxl Excel export (shipped Week 14) |
| ADR-002 Frontend Framework | `docs/decisions/ADR-002-frontend-framework.md` | Jinja2 + HTMX + Alpine.js render strategy |
| ADR-010 Operations Frontend Patterns | `docs/decisions/ADR-010-operations-frontend-patterns.md` | List/detail/form patterns for report UIs |
| ADR-012 Audit Logging | `docs/decisions/ADR-012-audit-logging.md` | Immutable audit trail powering historical reports |

---

## What IP2A Already Has (v0.9.4-alpha Baseline)

Phase 7 reports do NOT start from zero. Weeks 1-19 delivered infrastructure that directly supports report generation:

| Capability | Shipped In | Relevance to Reports |
|-----------|-----------|---------------------|
| **WeasyPrint PDF generation** | Week 14 (ADR-014) | PDF export for all reports — tested and deployed |
| **openpyxl Excel/CSV export** | Week 14 (ADR-014) | CSV/Excel export — reuse for data analysis reports |
| **Chart.js analytics dashboard** | Week 19 | Visualization layer for summary/trend reports |
| **Custom report builder** | Week 19 | User-configurable report parameters — extend for referral filters |
| **Member model** | Week 5 | Core entity for all member-facing reports |
| **Organization model** | Week 6 | Employer data for contractor/employer reports |
| **DuesPayment model** | Week 10 (ADR-008) | Transaction data for financial crossover reports |
| **Stripe integration** | Week 11 (ADR-013) | Payment source data for transaction reports |
| **Audit logging** | Week 11 (ADR-012) | Immutable audit trail — powers historical/compliance reports |
| **PWA + offline** | Week 18 | Mobile-responsive report viewing at the dispatch window |
| **Sentry + structured logging** | Week 16 (ADR-007) | Error tracking for report generation failures |

> **⚠️ Key Architecture Reminder:** **Member is SEPARATE from Student** (linked via FK on Student). Skills/qualifications reports (A-16, C-37) track dispatch certifications, NOT JATC training records. Keep these concerns separated when building report queries.

---

## Overview

LaborPower's Referral module includes **4 report categories** with a total of **91 reports listed** across Basic (operational daily-use), Advanced (filtered analysis), Applicant (individual member), and Custom (Local 46-specific) tabs. After accounting for overlap between tabs (e.g., Registration List in Basic vs. REGLIST in Custom), the effective unique report count is approximately **~78 reports**.

### Priority Legend

| Priority | Meaning |
|----------|---------|
| 🔴 P0 - Critical | Core daily hall operations — must have for launch |
| 🟡 P1 - High | Important operational reports — needed within first month |
| 🟢 P2 - Medium | Nice-to-have analytics and compliance reports |
| 🔵 P3 - Low | Custom/legacy reports — evaluate need before building |

### Status Legend

| Status | Meaning |
|--------|---------|
| ⬜ Not Started | Not yet implemented |
| 🟡 In Progress | Partially implemented |
| ✅ Done | Implemented and tested |
| ❌ Deferred | Intentionally skipped (document reason) |

---

## 1. Basic Tab — Daily Operational Reports

These are the bread-and-butter reports used daily in the dispatch hall.

| # | Report Name | Priority | IP2A Status | Notes |
|---|-------------|----------|-------------|-------|
| B-01 | Registration List | 🔴 P0 | ⬜ | Current out-of-work list by book. **Core dispatch function.** Likely overlaps C-34 (REGLIST). |
| B-02 | Dropped Due to Re-Sign | 🔴 P0 | ⬜ | Members who missed 30-day re-sign deadline |
| B-03 | Dropped Due to Checkmarks | 🔴 P0 | ⬜ | Members rolled off (3 check marks) |
| B-04 | Dropped Due to ShortCall | 🟡 P1 | ⬜ | Members dropped for short call rule violations |
| B-05 | Open Requests | 🔴 P0 | ⬜ | Active labor requests needing dispatch. **Core dispatch function.** |
| B-06 | Dispatch Report (Day Book) | 🔴 P0 | ⬜ | Daily dispatch log. **THE primary operational document.** |
| B-07 | Offer Report | 🟡 P1 | ⬜ | Job offers extended to members |
| B-08 | Request Activity | 🟡 P1 | ⬜ | Activity log for labor requests (currently selected in LP screenshot) |
| B-09 | Overdue Short Call Dispatches | 🟡 P1 | ⬜ | Short call members past expected return date |
| B-10 | Employers by Contract | 🟢 P2 | ⬜ | Employer list filtered by contract type |
| B-11 | X-Out List Call List | 🟡 P1 | ⬜ | Members marked as X-out (removed from referral) |
| B-12 | Monthly Referral Summary | 🟡 P1 | ⬜ | Monthly aggregate dispatch/referral statistics |
| B-13 | Daily Referral Summary | 🔴 P0 | ⬜ | Daily aggregate — needed for end-of-day reporting |
| B-14 | Active Contractors | 🟢 P2 | ⬜ | Currently active signatory contractors |
| B-15 | Current Worksites | 🟢 P2 | ⬜ | Active job sites with dispatched members |
| B-16 | Cope Checkoff (by employer) | 🟢 P2 | ⬜ | COPE political fund contributions by employer |
| B-17 | Historical Registration List | 🟡 P1 | ⬜ | Past registrations (audit/compliance). Powered by RegistrationActivity audit trail. |
| B-18 | Job Bids | 🔴 P0 | ⬜ | Internet/email bid tracking. **Core for online bidding.** |
| B-19 | Dropped & Re-Registered (Rolled) | 🟡 P1 | ⬜ | Members who were dropped and re-registered |
| B-20 | Dispatch Details by Job Request | 🟡 P1 | ⬜ | Detailed view of who was dispatched per request |

**Filter Options (Basic Tab):**
- Date range (from/to)
- All Books / One Book selector

**Tab totals:** 20 reports (P0: 7 | P1: 9 | P2: 4 | P3: 0)

---

## 2. Advanced Tab — Filtered Analysis Reports

These provide deeper analysis with multi-dimensional filtering.

| # | Report Name | Priority | IP2A Status | Notes |
|---|-------------|----------|-------------|-------|
| A-01 | Current Employee Report | 🔴 P0 | ⬜ | Active dispatched members by employer. **Core operational.** |
| A-02 | Historical Employee Report | 🟡 P1 | ⬜ | Past employment records |
| A-03 | Request Report | 🟡 P1 | ⬜ | Summary of labor requests |
| A-04 | Request Detail Report | 🟡 P1 | ⬜ | Detailed labor request info |
| A-05 | Termination Report | 🟡 P1 | ⬜ | RIF, quit, and discharge records |
| A-06 | Travelers Report | 🟡 P1 | ⬜ | Members traveling from other locals |
| A-07 | Steward Report | 🟢 P2 | ⬜ | Job steward assignments |
| A-08 | Applicant Report | 🟢 P2 | ⬜ | General applicant information. Likely overlaps AP-01. |
| A-09 | EEOC Report | 🟢 P2 | ⬜ | Equal Employment Opportunity compliance data. **PII handling required.** |
| A-10 | Employer-Requested By Name Report | 🟡 P1 | ⬜ | Foreperson-by-name request tracking |
| A-11 | Dispatch History Report | 🟡 P1 | ⬜ | Complete dispatch history. Powered by audit trail (ADR-012). |
| A-12 | Current Travelers Report | 🟡 P1 | ⬜ | Currently traveling members |
| A-13 | Working Time Limit Report | 🟢 P2 | ⬜ | Members approaching time limits |
| A-14 | Job Request History | 🟡 P1 | ⬜ | Historical labor request data |
| A-15 | Jobs Available For Member | 🔴 P0 | ⬜ | Open jobs a specific member qualifies for. **Member-facing.** |
| A-16 | Applicant Skills Report | 🟢 P2 | ⬜ | Skills/certifications by applicant. **⚠️ Dispatch skills only, NOT JATC training certs (Member ≠ Student).** |
| A-17 | Applicant Photo ID's | 🔵 P3 | ⬜ | Photo identification records |

**Filter Options (Advanced Tab):**
- Employer: All / Selected
- Books: All / Selected
- Book #s: All / Selected
- Working As: All / Selected
- Worksites: All / Selected
- Skills: All / Selected
- Status: All / Selected
- Ages: All / Selected
- Race: All / Selected
- Gender: All / Male / Female
- Job Class: All / Selected
- Report Format: Detail / Summary

**Tab totals:** 17 reports (P0: 2 | P1: 9 | P2: 5 | P3: 1)

---

## 3. Applicant Tab — Individual Member Reports

Per-member reports, often used at the dispatch window or for member inquiries.

| # | Report Name | Priority | IP2A Status | Notes |
|---|-------------|----------|-------------|-------|
| AP-01 | Basic Information Report | 🔴 P0 | ⬜ | Member demographics and contact info |
| AP-02 | Registration History Report | 🔴 P0 | ⬜ | Full book sign-on/off history for a member. Powered by RegistrationActivity. |
| AP-03 | Employment History | 🔴 P0 | ⬜ | Complete dispatch/employment record |
| AP-04 | Current Registrations | 🔴 P0 | ⬜ | What books a member is currently signed on |
| AP-05 | Travel Report | 🟡 P1 | ⬜ | Travel card history |
| AP-06 | Travel Letter | 🟡 P1 | ⬜ | Generated travel letter document. PDF via WeasyPrint (Week 14). |
| AP-07 | Letter of Introduction | 🟢 P2 | ⬜ | Formal letter for member. PDF via WeasyPrint. |
| AP-08 | Internet Bids | 🟡 P1 | ⬜ | Member's online bidding history |

**Filter Options (Applicant Tab):**
- Same multi-dimensional filters as Advanced tab (Employer, Books, Worksites, Skills, Status, etc.)
- Report Format: Detail / Summary

**Tab totals:** 8 reports (P0: 4 | P1: 3 | P2: 1 | P3: 0)

---

## 4. Custom Tab — Local 46-Specific Reports

These are custom reports built specifically for IBEW Local 46 operations. Many are legacy reports that may overlap with Basic/Advanced reports but provide Local 46-specific formatting or data.

| # | Report Name | Priority | IP2A Status | Notes |
|---|-------------|----------|-------------|-------|
| C-01 | 180 DAYS FOLLOW-UP | 🟡 P1 | ⬜ | Members dispatched 180 days ago — follow-up tracking |
| C-02 | 30 DAYS FOLLOW-UP | 🟡 P1 | ⬜ | 30-day dispatch follow-up |
| C-03 | 365 DAYS FOLLOW-UP | 🟢 P2 | ⬜ | Annual dispatch follow-up |
| C-04 | ACTIVE MEMBERS CLASSIFICATIONS | 🟡 P1 | ⬜ | Members by classification breakdown |
| C-05 | ACTIVE.CONTRACTORS.(LJ)2017_MLF | 🔵 P3 | ⬜ | Legacy contractor list — evaluate if still needed |
| C-06 | AGE BREAKDOWN BY DATE | 🟢 P2 | ⬜ | Demographics: age distribution |
| C-07 | ALL MEMBERS REFERRAL STATUS | 🟡 P1 | ⬜ | Every member's current referral status |
| C-08 | ALL_FOREMANLJ_LIST | 🟡 P1 | ⬜ | Foreman/foreperson by-name request list |
| C-09 | CLASS BREAKDOWN BY DATE | 🟢 P2 | ⬜ | Classification distribution over time |
| C-10 | CLASS GENDER BREAKDOWN BY DATE | 🟢 P2 | ⬜ | Classification × Gender demographics |
| C-11 | Dispatched without 401K statement | 🟢 P2 | ⬜ | Compliance: members dispatched missing 401K info |
| C-12 | EMPLOYCONTRACT | 🟢 P2 | ⬜ | Employment contract details |
| C-13 | Employee Count By Employer | 🟡 P1 | ⬜ | Headcount per contractor |
| C-14 | EMPLOYMENT HISTORY BY PERIOD | 🟡 P1 | ⬜ | Employment records filtered by date range |
| C-15 | ETHNIC BREAKDOWN BY DATE | 🟢 P2 | ⬜ | Demographics: ethnicity distribution. **PII/EEOC compliance required.** |
| C-16 | GENDER BREAKDOWN BY DATE | 🟢 P2 | ⬜ | Demographics: gender distribution |
| C-17 | GENDER ETHNICITY BREAKDOWN BY DATE | 🟢 P2 | ⬜ | Demographics: gender × ethnicity |
| C-18 | GENDER_ETHNIC | 🟢 P2 | ⬜ | Demographics cross-tab. Likely overlaps C-17. |
| C-19 | INSTALLER AND TECH EMAIL EXPORT | 🔵 P3 | ⬜ | Email list export for installers/techs |
| C-20 | JOB COUNT BY CATEGORY - NO EMPLOYER | 🟡 P1 | ⬜ | Job request counts by category (unfilled) |
| C-21 | JOB COUNT BY CATEGORY - WITH EMPLOYER | 🟡 P1 | ⬜ | Job request counts by category (filled) |
| C-22 | JOURNEYMAN COUNTS BY SECTOR | 🟡 P1 | ⬜ | JW distribution across sectors |
| C-23 | JRNY TECH SUMMARY | 🟡 P1 | ⬜ | Journeyman/technician summary stats |
| C-24 | L_FIX_MAINT_EMAIL_EXPORT | 🔵 P3 | ⬜ | Legacy maintenance email export |
| C-25 | MAILINGLIST46 | 🔵 P3 | ⬜ | Mailing list generation |
| C-26 | Member Contact By Contractor and Worksite | 🟡 P1 | ⬜ | Member contact info grouped by employer/site |
| C-27 | Member Contact By Contractor By Dispatch Date | 🟡 P1 | ⬜ | Contact info sorted by dispatch date |
| C-28 | Member Contact By Dispatch Date All Contractors | 🟡 P1 | ⬜ | Contact info across all contractors |
| C-29 | MEMBERS WITHOUT EMAIL | 🟢 P2 | ⬜ | Data quality: members missing email addresses |
| C-30 | One Day Dropped Due To Too Many Days | 🟢 P2 | ⬜ | Single-day drop tracking |
| C-31 | ORGANIZED | 🟢 P2 | ⬜ | Organized (newly organized) member tracking |
| C-32 | RAW DISPATCH DATA | 🟡 P1 | ⬜ | Raw dispatch data export (for analysis). CSV via openpyxl (Week 14). |
| C-33 | RE-SIGN DUE REPORT | 🔴 P0 | ⬜ | Members approaching re-sign deadline. **Critical for hall ops.** |
| C-34 | REGLIST | 🔴 P0 | ⬜ | Registration list (simplified format). Likely overlaps B-01. |
| C-35 | SHORT CALL DROPPED SINCE 90-DAY RULE | 🟡 P1 | ⬜ | Short call rule enforcement tracking |
| C-36 | SPARKS MAILING LABELS | 🔵 P3 | ⬜ | Physical mailing label generation |
| C-37 | SPECIAL SKILLS - ACTIVE MEMBERS | 🟢 P2 | ⬜ | Members with special certifications/skills. **⚠️ Dispatch skills only, NOT JATC training (Member ≠ Student).** |
| C-38 | Total Dropped Due To Too Many Days | 🟢 P2 | ⬜ | Aggregate drop statistics |
| C-39 | Total JW COUNT | 🟡 P1 | ⬜ | Total journeyman count |
| C-40 | UNEMPLOYED COUNTS BY BOOK | 🔴 P0 | ⬜ | Out-of-work counts per book. **Key dashboard metric.** Extend Chart.js dashboard (Week 19). |
| C-41 | UNEMPLOYED MEMBERS | 🔴 P0 | ⬜ | Full unemployed member list |
| C-42 | WEB BID HISTORY BY MEMBER/DATE | 🟡 P1 | ⬜ | Online bidding audit trail |
| C-43 | WEBBID_WIRE | 🟡 P1 | ⬜ | Wire book web bidding data |
| C-44 | WEBBID_WIRE SEATTLE | 🟡 P1 | ⬜ | Seattle wire book web bidding data. Likely overlaps C-43 with region filter. |
| C-45 | WIREMAN EMAIL EXPORT | 🔵 P3 | ⬜ | Wireman email list export |
| C-46 | WIREMAN LIST WITH PHONE (6/21) | 🟢 P2 | ⬜ | Wireman contact list with phone numbers |

**Tab totals:** 46 reports (P0: 4 | P1: 20 | P2: 16 | P3: 6)

---

## Summary by Priority

### Raw Counts (All Tabs)

| Tab | Total | P0 | P1 | P2 | P3 |
|-----|-------|----|----|----|----|
| Basic (daily ops) | 20 | 7 | 9 | 4 | 0 |
| Advanced (filtered) | 17 | 2 | 9 | 5 | 1 |
| Applicant (per-member) | 8 | 4 | 3 | 1 | 0 |
| Custom (Local 46) | 46 | 4 | 20 | 16 | 6 |
| **Raw Total** | **91** | **17** | **41** | **26** | **7** |

### Working Estimate (After De-Duplication)

Several Custom tab reports overlap with Basic/Advanced reports in different formats (e.g., B-01 Registration List ≈ C-34 REGLIST, C-43/C-44 overlap with region filter, C-17/C-18 are likely the same report). After accounting for ~13 overlapping reports, the effective unique count is:

| Priority | Est. Unique | Description |
|----------|-------------|-------------|
| 🔴 P0 - Critical | **~16** | Must have for launch — daily hall operations |
| 🟡 P1 - High | **~33** | Important operational — needed within first month |
| 🟢 P2 - Medium | **~22** | Analytics, compliance, demographics |
| 🔵 P3 - Low | **~7** | Legacy/mailing — evaluate need |
| **Total** | **~78** | Unique reports after de-duplication |

> **⚠️ Verification needed:** The de-duplicated estimates (~78 total) are used throughout Phase 7 planning documents. Exact overlap should be confirmed during implementation planning (Session 20A). Overlap candidates are annotated in the report tables above.

> **⚠️ Addendum count correction:** The per-tab breakdown in `PHASE7_CONTINUITY_DOC_ADDENDUM.md` shows Advanced P2=4 (actual: 5) and Custom P0=3/P1=18/P2=17 (actual: P0=4/P1=20/P2=16). The ~78 de-duplicated total and the per-priority working estimates are unaffected by this correction since they represent de-duplicated counts, not raw tab counts.

---

## Implementation Approach

### Phase 7 Report Implementation Plan

> **Cross-reference:** The report sprints below overlap with `PHASE7_IMPLEMENTATION_PLAN_v2.md` Weeks 29-32+ and with `LABORPOWER_IMPLEMENTATION_PLAN.md` Phases 5-6. See `PHASE7_CONTINUITY_DOC_ADDENDUM.md` for schedule reconciliation.

**Sprint 1 (Weeks 29-30): P0 Critical Reports (~16 reports)**
Build the critical reports that dispatchers need daily:
- Registration List (B-01)
- Dispatch Report / Day Book (B-06)
- Open Requests (B-05)
- Daily Referral Summary (B-13)
- Job Bids (B-18)
- Dropped reports (B-02, B-03)
- Current Employee Report (A-01)
- Jobs Available For Member (A-15)
- Applicant reports (AP-01 through AP-04)
- Re-Sign Due Report (C-33)
- Unemployed Counts/Members (C-40, C-41)
- REGLIST (C-34) — evaluate if separate from B-01 or same with different format

**Sprint 2 (Weeks 30-31): P1 High Priority Reports (~33 reports)**
Build the high-priority reports needed for full operations.

**Sprint 3 (Week 32+): P2/P3 Reports (~29 reports)**
Build remaining analytics, demographics, and custom reports as time allows.

### Report Architecture

Each report should support:
- **Web view** (HTML via Jinja2 + HTMX, paginated, filterable — per ADR-002)
- **PDF export** (WeasyPrint — already deployed for grant compliance, Week 14/ADR-014)
- **CSV/Excel export** (openpyxl — already available from Week 14)
- **Print-optimized** CSS
- **Chart visualization** where applicable (Chart.js — deployed Week 19)

### Filter Framework

Build a reusable filter component supporting the LaborPower filter dimensions. This builds on the existing report builder (Week 19) and should follow frontend patterns from ADR-010:

- Date range (from/to)
- Book / All Books
- Employer / All Employers
- Job Class / All Classes
- Region (Seattle, Bremerton, Pt. Angeles)
- Status filters
- Demographics (for compliance reports only — **PII handling required**)
- Report Format: Detail / Summary toggle

### IP2A Improvements Over LaborPower

| LaborPower Limitation | IP2A Improvement |
|----------------------|------------------|
| Desktop-only application | Web-accessible from anywhere (PWA — Week 18) |
| Print/PDF only | Web view + PDF + CSV/Excel + Email |
| Fixed report parameters | Dynamic filters with saved presets (builds on Week 19 report builder) |
| No mobile access | Mobile-responsive design (PWA — Week 18) |
| Separate Basic/Advanced/Applicant tabs | Unified search with smart categorization |
| Static custom reports | User-configurable report builder (Week 19 foundation) |
| No scheduling | Scheduled report delivery via email (future) |
| No API access | REST API for programmatic report generation |
| No audit trail | Immutable audit logging (Week 11/ADR-012) for all report data |

---

## Cross-Reference to Phase 7 Implementation Weeks

> **Note:** Two schedule sources exist for Phase 7 with slightly different week assignments. See `PHASE7_CONTINUITY_DOC_ADDENDUM.md` for the schedule reconciliation table.

| Week | Focus | Reports Addressed |
|------|-------|-------------------|
| 20-21 | Core Models | Schema foundation for all reports |
| 22-23 | Services | Business logic for report queries |
| 24 | Queue Management | Registration List, Dropped reports |
| 25 | API Endpoints | Report data endpoints |
| 26 | Frontend - Books | Registration List, Unemployed Counts |
| 27 | Frontend - Requests | Open Requests, Request Activity |
| 28 | Frontend - Dispatch | Day Book, Dispatch History |
| 29-30 | Reports Sprint 1 | P0 Critical reports (~16 reports) |
| 30-31 | Reports Sprint 2 | P1 High Priority reports (~33 reports) |
| 32+ | Reports Sprint 3 | P2/P3 remaining reports (~29 reports) |

---

## Notes

- Custom tab reports (C-xx) may overlap significantly with Basic/Advanced reports — evaluate during implementation whether they need separate implementations or are just pre-configured filters on the same query (overlap candidates annotated in tables above)
- EEOC and demographics reports (A-09, C-15, C-16, C-17) require careful handling of PII and compliance with reporting standards
- Some legacy reports (marked P3) may no longer be needed — confirm with dispatchers before building
- The filter options visible in LaborPower's Advanced and Applicant tabs should inform the reusable filter component design
- Export formats: LaborPower supports Preview, Print, CSV, and PDF — IP2A should match or exceed this using existing WeasyPrint + openpyxl infrastructure
- Historical reports (B-17, A-11, AP-02) are powered by the RegistrationActivity audit trail — ensure RegistrationActivity model captures sufficient detail during Phase 7 model implementation
- Summary/dashboard reports (C-40, B-12, B-13) should integrate with the Chart.js analytics dashboard (Week 19) where appropriate

---

## 📝 End-of-Session Documentation (MANDATORY)

**Before completing ANY session:**

> Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (February 2, 2026 — Initial inventory from LaborPower screenshots)
