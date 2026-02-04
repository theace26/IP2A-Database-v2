# IP2A Milestone Checklist (Quick Reference)

> **Document Created:** January 27, 2026
> **Last Updated:** February 4, 2026
> **Version:** v0.9.5-alpha — Phase 7 Weeks 20-22 Complete
> **Status:** Phase 7 IN PROGRESS — Models, Enums, Schemas, Services Complete
> **Print this or keep it open during sessions**

---

## Current Focus: Phase 7 — Referral & Dispatch System (Implementation)

### Legend: Done | In Progress | Pending

---

## Backend Phases: ALL COMPLETE + Phase 7 In Progress

| Phase | Description | Models | Endpoints | Tests | Status |
|-------|-------------|--------|-----------|-------|--------|
| Phase 0 | Documentation & Structure | - | - | - | Done |
| Phase 1 | Auth (JWT, RBAC, Registration) | 4 | 13 | 52 | Done |
| Phase 2a | Union Ops (SALT, Benevolence, Grievance) | 5 | 27 | 31 | Done |
| Phase 2b | Training (Students, Courses, Grades) | 7 | ~35 | 33 | Done |
| Phase 3 | Documents (S3/MinIO) | 1 | 8 | 11 | Done |
| Phase 4 | Dues Tracking | 4 | ~35 | 21 | Done |
| **Phase 7** | **Referral & Dispatch (foundation)** | **6** | **—** | **20+** | **WIP** |
| **Total** | **Including Phase 7 foundation** | **31** | **~120** | **185+** | **WIP** |

---

## Phase 6: Frontend Build — COMPLETE

### Week 1: Setup + Login (COMPLETE)

| Task | Status |
|------|--------|
| Base templates (DaisyUI + Tailwind + HTMX + Alpine.js) | Done |
| Component templates (navbar, sidebar, flash, modal) | Done |
| Login page with HTMX form | Done |
| Forgot password page | Done |
| Dashboard placeholder | Done |
| Error pages (404, 500) | Done |
| Frontend router | Done |
| 12 frontend tests | Done |

**Commit:** `1274c12` - v0.7.0 (Week 1 Complete)

### Week 2: Auth Cookies + Dashboard (COMPLETE)

| Task | Status |
|------|--------|
| Cookie-based authentication (auth_cookie.py) | Done |
| HTTP-only cookies on login/logout | Done |
| Protected routes redirect to login | Done |
| Dashboard service with real stats | Done |
| Activity feed from audit log | Done |
| HTMX refresh for dashboard | Done |
| Flash message support | Done |
| 10 new auth tests (22 total) | Done |

**Commit:** `b997022` - v0.7.1 (Week 2 Complete)

### Week 3: Staff Management (COMPLETE)

| Task | Status |
|------|--------|
| StaffService with search/filter/paginate | Done |
| User list page with table and stats | Done |
| HTMX live search (300ms debounce) | Done |
| Filter by role and status | Done |
| Pagination component | Done |
| Quick edit modal with role checkboxes | Done |
| Account status toggle (active/locked) | Done |
| Full detail page with edit form | Done |
| Account actions (lock, unlock, reset password, delete) | Done |
| 403 error page | Done |
| 18 new staff tests (40 frontend total) | Done |

**Commits:**
- `4d80365` - Session A: User list with search
- `85ada48` - Session B: Quick edit modal
- `89a045c` - Session C: Actions and detail page

**Version:** v0.7.2 (Week 3 Complete)

### Week 4: Training Landing (COMPLETE)

| Task | Status |
|------|--------|
| TrainingFrontendService with stats queries | Done |
| Training landing page with stats dashboard | Done |
| Stats: students, completed, courses, completion rate | Done |
| Recent students table | Done |
| Student list with HTMX search (300ms debounce) | Done |
| Filter by status and cohort | Done |
| Status badges with color coding | Done |
| Pagination component | Done |
| Student detail page with enrollments | Done |
| Course list with card layout | Done |
| Course detail page with enrolled students | Done |
| 19 new training tests (59 frontend total) | Done |

**Commits:**
- `ef77cb8` - Session A: Training landing page
- `db19cac` - Session B: Student list enhancements
- `bbcd7ca` - Session C: Course detail and tests

**Version:** v0.7.3 (Week 4 Complete)

### Week 5: Members Landing (COMPLETE)

| Task | Status |
|------|--------|
| MemberFrontendService with stats queries | Done |
| Members landing page with stats dashboard | Done |
| Stats: total, active, inactive/suspended, dues % | Done |
| Classification breakdown with badges | Done |
| Member list with HTMX search (300ms debounce) | Done |
| Filter by status and classification | Done |
| Status and classification badges | Done |
| Current employer display | Done |
| Quick edit modal | Done |
| Pagination component | Done |
| Member detail page with contact info | Done |
| Employment history timeline (HTMX loaded) | Done |
| Dues summary section (HTMX loaded) | Done |
| 15 new member tests (73 frontend total) | Done |

**Commit:**
- `d6f7132` - Phase 6 Week 5 Complete - Members Landing Page

**Version:** v0.7.4 (Week 5 Complete)

### Week 6: Union Operations (COMPLETE)

| Task | Status |
|------|--------|
| OperationsFrontendService with stats queries | Done |
| Operations landing page with module cards | Done |
| SALTing activities list with type/outcome badges | Done |
| SALTing detail with organizer and employer info | Done |
| Benevolence applications list with status workflow | Done |
| Benevolence detail with payment history | Done |
| Grievances list with step progress indicators | Done |
| Grievance detail with step timeline | Done |
| 21 new operations tests (94 frontend total) | Done |

**Commits:**
- `78efab7` - Phase 6 Week 6 Session D - Tests + Documentation

**Version:** v0.7.5 (Week 6 Complete)

### Week 8: Reports & Export (COMPLETE)

| Task | Status |
|------|--------|
| ReportService with PDF/Excel generation | Done |
| Reports landing page with categorized reports | Done |
| Member roster report (PDF/Excel) | Done |
| Dues summary report (PDF/Excel) | Done |
| Overdue members report (PDF/Excel) | Done |
| Training enrollment report (Excel) | Done |
| Grievance summary report (PDF) | Done |
| SALTing activities report (Excel) | Done |
| 30 new report tests (124 frontend total) | Done |

**Commit:** `d031451` - Phase 6 Week 8 - Reports & Export

**Version:** v0.7.6 (Week 8 Complete)

### Week 9: Documents Frontend (COMPLETE)

| Task | Status |
|------|--------|
| Documents landing page with storage stats | Done |
| Upload page with Alpine.js drag-drop zone | Done |
| Browse page with entity type filtering | Done |
| Download redirect endpoint (presigned URLs) | Done |
| Delete endpoint with HTMX confirmation | Done |
| HTMX partials for success/error states | Done |
| 6 new document tests (130 frontend total) | Done |

**Commit:** `79cb86e` - Phase 6 Week 9 - Documents Frontend

**Version:** v0.7.7 (Week 9 Complete)

### Week 10: Dues UI (COMPLETE)

| Task | Status |
|------|--------|
| DuesFrontendService with stats and badge helpers | Done |
| Dues landing page with current period display | Done |
| Stats cards (MTD, YTD, overdue, pending) | Done |
| Quick action cards for rates/periods/payments/adjustments | Done |
| Rates list page with HTMX filtering | Done |
| Rates table partial with status badges | Done |
| Sidebar navigation with Dues dropdown | Done |
| Periods management page | Done |
| Generate year modal | Done |
| Period detail with payment summary | Done |
| Close period workflow | Done |
| Payments list with search and filters | Done |
| Record payment modal | Done |
| Member payment history page | Done |
| Adjustments list with status/type filters | Done |
| Adjustment detail with approve/deny | Done |
| 37 new dues frontend tests | Done |
| ADR-011: Dues Frontend Patterns | Done |

**Version:** v0.7.9 (Week 10 Complete)

### Week 11: Audit Infrastructure + Stripe (COMPLETE)

| Task | Status |
|------|--------|
| Stripe Phase 1: PaymentService, webhook handler | Done |
| Stripe Phase 2: Database migrations (stripe_customer_id) | Done |
| Stripe Phase 3: Frontend payment flow (Pay Now button) | Done |
| Success/cancel pages for Stripe payments | Done |
| Audit log immutability (PostgreSQL triggers) | Done |
| MemberNote model with visibility levels | Done |
| MemberNoteService with role-based filtering | Done |
| Member notes API endpoints | Done |
| Audit UI with role-based permissions | Done |
| Sensitive field redaction for non-admins | Done |
| HTMX filtering for audit logs | Done |
| CSV export (admin only) | Done |
| Inline audit history on member detail pages | Done |
| Notes UI with add/view/delete | Done |
| ADR-012: Audit Logging, ADR-013: Stripe Integration | Done |

**Version:** v0.8.0-alpha1 (Week 11 Complete)

### Week 12: User Profile & Settings (COMPLETE)

| Task | Status |
|------|--------|
| ProfileService with password change validation | Done |
| User activity summary from audit logs | Done |
| Profile view page with account info | Done |
| Password change form with validation | Done |
| Password changes logged via audit system | Done |

**Version:** v0.8.1-alpha (Week 12 Complete)

### Week 13: IP2A Entity Completion Audit (COMPLETE)

| Task | Status |
|------|--------|
| Audit existing models vs IP2A design requirements | Done |
| Location model verification (full address, capacity, contacts) | Done |
| InstructorHours model verification (hours tracking, payroll) | Done |
| ToolsIssued model verification (checkout/return, condition) | Done |
| Expense model verification (grant_id FK exists) | Done |
| **No new models required** - all entities already exist | Done |

**Version:** v0.8.2-alpha (Week 13 Complete)

### Week 14: Grant Compliance Reporting (COMPLETE)

| Task | Status |
|------|--------|
| GrantStatus, GrantEnrollmentStatus, GrantOutcome enums | Done |
| Grant model enhancements (status, targets) | Done |
| GrantEnrollment model (student-grant association) | Done |
| Outcome tracking (credential, apprenticeship, employment) | Done |
| Placement tracking (employer, wage, job title) | Done |
| GrantMetricsService for compliance metrics | Done |
| GrantReportService (summary, detailed, funder reports) | Done |
| Excel export with openpyxl | Done |
| Grant frontend routes (list, detail, enrollments, expenses) | Done |
| Reports page with generation options | Done |
| Grants link added to sidebar | Done |
| ADR-014: Grant Compliance Reporting System | Done |

**Version:** v0.9.0-alpha (Week 14 Complete)

### Week 16: Production Hardening (COMPLETE)

| Task | Status |
|------|--------|
| SecurityHeadersMiddleware (X-Frame-Options, CSP, etc.) | Done |
| Enhanced health check endpoints (/health/live, /health/ready, /health/metrics) | Done |
| Sentry integration for error tracking (src/core/monitoring.py) | Done |
| Structured JSON logging for production (src/core/logging_config.py) | Done |
| Database connection pooling configuration | Done |
| Rate limiting middleware (already existed) | Done |
| Performance indexes migration (already existed) | Done |
| 32 new tests (security headers, health checks, rate limiting) | Done |

**Version:** v0.9.1-alpha (Week 16 Complete)

### Week 17: Post-Launch Operations (COMPLETE)

| Task | Status |
|------|--------|
| Backup scripts (backup_database.sh, verify_backup.sh) | Done |
| Audit log archival script (archive_audit_logs.sh) | Done |
| Session cleanup script (cleanup_sessions.sh) | Done |
| Crontab example for scheduled tasks | Done |
| Admin metrics dashboard (/admin/metrics) | Done |
| Admin metrics template | Done |
| Incident response runbook | Done |
| Updated runbooks README | Done |
| 13 new tests | Done |

**Version:** v0.9.2-alpha (Week 17 Complete)

### Week 18: Mobile Optimization & PWA (COMPLETE)

| Task | Status |
|------|--------|
| Mobile CSS with touch-friendly styles (mobile.css) | Done |
| PWA manifest (manifest.json) | Done |
| Service worker for offline support (sw.js) | Done |
| Offline page (offline.html) | Done |
| Mobile drawer component | Done |
| Bottom navigation component | Done |
| Base template PWA meta tags | Done |
| Service worker registration | Done |
| Offline route | Done |
| 14 new tests | Done |

**Version:** v0.9.3-alpha (Week 18 Complete)

### Week 19: Analytics Dashboard & Report Builder (COMPLETE)

| Task | Status |
|------|--------|
| AnalyticsService with membership, dues, training, activity metrics | Done |
| ReportBuilderService for custom report generation | Done |
| Executive dashboard with key metrics and Chart.js charts | Done |
| Membership analytics page with 24-month trend chart | Done |
| Dues analytics page with collection stats and delinquency | Done |
| Custom report builder with field selection | Done |
| CSV/Excel export for reports | Done |
| Officer-level role checking for analytics access | Done |
| 19 new tests | Done |

**Version:** v0.9.4-alpha (Week 19 Complete)

### Weeks 20-22: Phase 7 Foundation (COMPLETE)

| Task | Status |
|------|--------|
| **Week 20A:** Schema reconciliation & Phase 7 enums (19 enums) | Done |
| **Week 20B:** ReferralBook model & 11 book seeds | Done |
| **Week 20C:** BookRegistration model with DECIMAL APN | Done |
| **Week 21A:** LaborRequest & JobBid models | Done |
| **Week 21B:** Dispatch model | Done |
| **Week 21C:** RegistrationActivity model (append-only audit) | Done |
| **Week 22A:** ReferralBookService (CRUD, stats, settings) | Done |
| **Week 22B:** BookRegistrationService core (register, re-sign, queue) | Done |
| **Week 22C:** Check mark logic & roll-off rules | Done |
| 20+ model tests | Done |
| Schema decisions documented (PHASE7_SCHEMA_DECISIONS.md) | Done |

**Version:** v0.9.5-alpha (Weeks 20-22 Complete)

---

## Phase 7: Referral & Dispatch System

**Goal:** Build complete out-of-work referral and dispatch system to replace LaborPower.

**Effort Estimate:** 100-150 hours across sub-phases 7a-7g

**Planning Documents:** `docs/phase7/` — see §7.9 Key Documents below

**Dependency Chain:** 7a → 7b → 7c/7d (parallel) → 7e → 7f → 7g

**Audit Scope:** Phase 7 tables `registrations`, `dispatches`, and `check_marks` require full audit trail logging (7-year NLRA compliance). Add to `AUDITED_TABLES` during 7c.

**Pre-Deployment:** Merge `develop → main` for v0.9.4-alpha production deployment before starting Phase 7 development.

---

### §7.0 LaborPower Data Analysis (COMPLETE)

| Task | Status |
|------|--------|
| Batch 1: 12 production data exports analyzed | Done |
| Batch 2: 12 additional exports analyzed | Done |
| 78 de-duplicated reports cataloged (91 raw) | Done |
| Schema Guidance Vol. 1 (Word doc) | Done |
| Schema Guidance Vol. 2 (Word doc) | Done |
| Consolidated Continuity Document (Markdown) | Done |
| Roadmap v3.0 updated with all findings | Done |

**Key Documents Produced:**
- `LaborPower_Data_Analysis_Schema_Guidance.docx` (Vol. 1)
- `LaborPower_Data_Analysis_Schema_Guidance_Vol2.docx` (Vol. 2)
- `UnionCore_Continuity_Document_Consolidated.md`

---

### §7.1 Quick Reference: Critical Schema Findings (8)

| # | Finding | Severity | Impact |
|---|---------|----------|--------|
| 1 | APN = DECIMAL(10,2), NOT INTEGER — integer part is Excel serial date | Critical | Wrong data type loses secondary sort key |
| 2 | Duplicate APNs — cannot use as unique key | Critical | Unique constraint must be (member_id, book_id, book_priority_number) |
| 3 | RESIDENTIAL = 8th contract code (259 employers) | High | Missing from all prior documentation |
| 4 | Book Name ≠ Contract Code (e.g. STOCKMAN → STOCKPERSON) | High | 3 books have NO matching contract code |
| 5 | TERO APPR WIRE = compound book (agreement_type + work_level + classification) | Medium | Requires additional columns on referral_books |
| 6 | Cross-regional registration — 87% on ALL THREE regional books | Medium | Validates many-to-many model |
| 7 | APN 45880.41 on FOUR books | Medium | Confirms member can be on multiple books simultaneously |
| 8 | Inverted tier distributions — STOCKMAN B3 = 8.6× B1 | Low | Strengthens "Book 3 = Travelers" hypothesis |

---

### §7.2 Quick Reference: Known Books (11)

| Book Name | Total Records | Tier Pattern | Contract Code |
|-----------|---------------|--------------|---------------|
| WIRE SEATTLE | 1,186 | Normal | WIREPERSON |
| WIRE BREMERTON | 1,115 | Normal | WIREPERSON |
| WIRE PT ANGELES | 1,100 | Normal | WIREPERSON |
| TRADESHOW | 315 | Normal (94.6% B1) | NONE |
| TECHNICIAN | 260 | Inverted (B3 > B1) | SOUND & COMM |
| STOCKMAN | 54 | Inverted (B3 = 8.6× B1) | STOCKPERSON |
| TERO APPR WIRE | 2 | Single tier | NONE |
| UTILITY WORKER | 1 | Single tier | NONE |
| LT FXT MAINT | — | Inferred from employer data | LT FXT MAINT |
| GROUP MARINE | — | Inferred from employer data | GROUP MARINE |
| RESIDENTIAL | — | Inferred from employer data | RESIDENTIAL |

> **SESSION REMINDER:** Member ≠ Student. Members are IBEW union members in the referral system. Students are pre-apprenticeship program participants. Do NOT conflate these entities.

> **SESSION REMINDER:** Book ≠ Contract. Books are out-of-work registration lists. Contracts are collective bargaining agreements with employers. The mapping between them is NOT 1:1.

> **SESSION REMINDER:** APN is DECIMAL(10,2). Integer part = Excel serial date (registration date). Decimal part = secondary sort key. Never truncate to INTEGER.

---

### §7.3 Quick Reference: Business Rules (14)

| # | Rule | System Impact |
|---|------|---------------|
| 1 | Office Hours & Regions | Region enum, operating hours config |
| 2 | Morning Referral Processing Order (Wire 8:30 → S&C/Marine/Stock/LFM/Residential 9:00 → Tradeshow 9:30) | Processing queue with time windows |
| 3 | Labor Request Cutoff (3 PM next-day; web bids after 5:30 PM) | Deadline enforcement, web bid time gates |
| 4 | Agreement Types (PLA/CWA/TERO) | agreement_type enum on referral_books |
| 5 | Registration Rules (one per classification) | Validation: one active registration per book per member |
| 6 | Re-Registration Triggers (short call, under scale, 90-day, turnarounds) | re_registration_reason enum, auto-relist logic |
| 7 | Re-Sign 30-Day Cycle | Scheduled job or manual trigger, notification |
| 8 | Internet/Email Bidding (5:30 PM–7 AM; 2nd rejection = 1 year loss) | Time-gated bidding, rejection counter, penalty enforcement |
| 9 | Short Calls (≤10 days, max 2 per cycle, ≤3 days don't count) | Duration tracking, cycle counter, exemption logic |
| 10 | Check Marks (2 allowed, 3rd = rolled off; separate per area book) | check_marks table with per-book tracking |
| 11 | No Check Mark Exceptions (specialty, MOU, early start, under scale, etc.) | member_exemptions table, exemption_type enum |
| 12 | Quit/Discharge (rolled off ALL books; 2-week foreperson blackout) | Cascade deregistration, blackout_periods table |
| 13 | Foreperson By Name (anti-collusion) | by_name_request flag on dispatches |
| 14 | Exempt Status (military, union business, salting, medical, jury duty) | member_exemptions with date ranges and reason types |

---

### §7.4 Quick Reference: Schema Corrections (9)

| Item | Original Assumption | Corrected To |
|------|---------------------|--------------|
| APN data type | INTEGER | DECIMAL(10,2) |
| APN field name | position_number | applicant_priority_number |
| Unique constraint | (member_id, book_id) | (member_id, book_id, book_priority_number) |
| Book tier field | Not explicit | book_priority_number INTEGER (1–4) |
| referral_books.contract_code | NOT NULL | NULLABLE (Tradeshow, TERO have no contract) |
| referral_books.agreement_type | Not proposed | NEW: VARCHAR(20) DEFAULT 'STANDARD' |
| referral_books.work_level | Not proposed | NEW: VARCHAR(20) DEFAULT 'JOURNEYMAN' |
| referral_books.book_type | Not proposed | NEW: VARCHAR(20) DEFAULT 'PRIMARY' |
| employer_contracts domain | 7 contract codes | 8 codes (+ RESIDENTIAL) |

---

### §7.5 Quick Reference: New Tables (12)

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| referral_books | Book definitions (name, contract, agreement type, region) | → employer_contracts |
| registrations | Member out-of-work list entries with APN | → members, → referral_books |
| employer_contracts | Employer-contract associations with status | → employers (existing or new) |
| job_requests | Employer labor requests with requirements | → employer_contracts |
| job_requirements | Per-request skill/cert requirements | → job_requests |
| dispatches | Member dispatch records with outcomes | → members, → job_requests |
| web_bids | Internet bidding entries with timestamps | → members, → job_requests |
| check_marks | Penalty tracking (2 allowed, 3rd = roll-off) | → members, → referral_books |
| member_exemptions | Exempt status with reason and date range | → members |
| bidding_infractions | Internet bidding violations and penalties | → members |
| worksites | Physical job locations for dispatch | → employer_contracts |
| blackout_periods | Foreperson/employer blackout windows | → members or employers |

---

### §7.6 Quick Reference: Data Gaps (16 items)

#### Priority 1 — BLOCKING (3)

These must be resolved before schema finalization (Sub-Phase 7b).

| # | Gap | What We Need | How to Get It |
|---|-----|-------------|---------------|
| 1 | REGLIST with member identifiers | Full registration list showing member_id/name alongside APN and book | LaborPower Custom Report: REGLIST |
| 2 | RAW DISPATCH DATA | Complete dispatch history with all columns | LaborPower Custom Report: RAW DISPATCH DATA |
| 3 | EMPLOYCONTRACT report | Employer-to-contract mapping with all fields | LaborPower Custom Report: EMPLOYCONTRACT |

#### Priority 2 — IMPORTANT (6)

Required during Sub-Phase 7b-7c for complete implementation.

| # | Gap | Purpose |
|---|-----|---------|
| 4 | Complete book catalog confirmation | Verify all 11 books + any hidden books |
| 5 | Book-to-contract mapping (official) | Confirm which books map to which contracts |
| 6 | Sample registration detail (single member) | Validate data model with real member journey |
| 7 | Sample dispatch history (single member) | Validate dispatch workflow end-to-end |
| 8 | TERO/PLA/CWA catalog | Complete list of special agreement types |
| 9 | Duplicate employer resolution strategy | How LaborPower handles employer name variations |

#### Priority 3 — CLARIFICATION (7)

Can be resolved during implementation without blocking.

| # | Gap | Question |
|---|-----|----------|
| 10 | 90-day rule details | Exact triggering conditions for re-registration |
| 11 | "Too many days" threshold | What count triggers an automatic roll-off? |
| 12 | Region count | Currently 3 regions (Seattle, Bremerton, Pt Angeles) — are there more? |
| 13 | Tier semantics | Is Book 3 = Travelers confirmed? What is Book 4? |
| 14 | TRADESHOW specific rules | Any special dispatch logic beyond 9:30 AM processing? |
| 15 | Apprentice books | Do apprentices use the same referral system or separate? |
| 16 | RESIDENTIAL vs WIREPERSON | Are these truly separate dispatch workflows or shared? |

---

### Sub-Phase 7a: Data Collection (3-5 hrs) — BLOCKED by LaborPower access

| Task | Est. | Status |
|------|------|--------|
| Request REGLIST custom report with member identifiers | 1 hr | Pending |
| Request RAW DISPATCH DATA custom report | 1 hr | Pending |
| Request EMPLOYCONTRACT custom report | 1 hr | Pending |
| Analyze exports and resolve Priority 1 gaps | 1-2 hrs | Pending |

**Blocker:** Requires LaborPower system access to run Custom Reports.

---

### Sub-Phase 7b: Schema Finalization (10-15 hrs) — BLOCKED by 7a

| Task | Est. | Status |
|------|------|--------|
| Finalize referral_books table DDL with all corrected columns | 1 hr | Pending |
| Finalize registrations table DDL with DECIMAL(10,2) APN | 1 hr | Pending |
| Finalize employer_contracts with 8 contract codes | 1 hr | Pending |
| Create DDL for remaining 9 tables (jobs, dispatches, bids, etc.) | 3 hrs | Pending |
| Create Alembic migration for all 12 tables | 2 hrs | Pending |
| Create enums (contract_code, agreement_type, dispatch_status, etc.) | 1 hr | Pending |
| Create SQLAlchemy ORM models for all 12 tables | 2 hrs | Pending |
| Seed referral_books with 11 known books | 30 min | Pending |
| Seed contract codes with 8 known codes | 30 min | Pending |
| Validate schema against all 14 business rules | 1 hr | Pending |
| Update AUDITED_TABLES with registrations, dispatches, check_marks | 15 min | Pending |

---

### Sub-Phase 7c: Core Services + API (25-35 hrs) — BLOCKED by 7b

| Task | Est. | Status |
|------|------|--------|
| ReferralBookService (CRUD + book catalog queries) | 2 hrs | Pending |
| RegistrationService (register, deregister, re-register, APN management) | 4 hrs | Pending |
| EmployerContractService (CRUD + contract code management) | 2 hrs | Pending |
| JobRequestService (create, fill, cancel, deadline enforcement) | 3 hrs | Pending |
| DispatchService (dispatch, accept, reject, short call tracking) | 5 hrs | Pending |
| WebBidService (time-gated bidding, rejection counting, penalty logic) | 3 hrs | Pending |
| CheckMarkService (track marks, enforce 3rd-mark roll-off, per-book) | 2 hrs | Pending |
| ExemptionService (military, medical, union business, salting) | 2 hrs | Pending |
| Re-registration logic (short call, under scale, 90-day, turnaround) | 2 hrs | Pending |
| Quit/discharge cascade (roll off ALL books, foreperson blackout) | 1 hr | Pending |
| API routers for all services | 3 hrs | Pending |
| Unit + integration tests (target: 50+) | 5 hrs | Pending |

---

### Sub-Phase 7d: Import Tooling (15-20 hrs) — BLOCKED by 7b, parallel with 7c

| Task | Est. | Status |
|------|------|--------|
| CSV import pipeline architecture (validation → staging → commit) | 2 hrs | Pending |
| Employer import script (deduplicate, normalize names) | 3 hrs | Pending |
| Employer-contract association import | 2 hrs | Pending |
| Registration import (APN decimal handling, tier mapping) | 4 hrs | Pending |
| Dispatch history import (if historical data available) | 3 hrs | Pending |
| Import validation reports (rejected rows, duplicate detection) | 2 hrs | Pending |
| Import tests | 2 hrs | Pending |

**Import Order:** employers → employer_contracts → registrations → dispatch history

---

### Sub-Phase 7e: Frontend UI (20-30 hrs) — BLOCKED by 7c

| Task | Est. | Status |
|------|------|--------|
| Referral landing page with book status overview | 2 hrs | Pending |
| Book list page with registration counts per tier | 2 hrs | Pending |
| Book detail page with registrant list | 3 hrs | Pending |
| Registration management (add/remove members from books) | 3 hrs | Pending |
| Dispatch board (pending requests, available members, drag-assign) | 5 hrs | Pending |
| Job request creation form (employer, requirements, dates) | 2 hrs | Pending |
| Web bidding interface (time-gated, member-facing) | 3 hrs | Pending |
| Check mark tracking UI | 2 hrs | Pending |
| Exemption management UI | 2 hrs | Pending |
| Sidebar navigation update (Referral & Dispatch section) | 1 hr | Pending |
| Frontend tests (target: 30+) | 3 hrs | Pending |

---

### Sub-Phase 7f: Reports P0 + P1 (20-30 hrs) — BLOCKED by 7c

| Priority | Count | Examples | Status |
|----------|-------|----------|--------|
| P0 (Critical) | 16 | Out-of-work lists, dispatch logs, employer active list | Pending |
| P1 (High) | 33 | Registration history, dispatch summaries, check mark reports | Pending |

| Task | Est. | Status |
|------|------|--------|
| P0 report templates (WeasyPrint PDF + Excel) | 10 hrs | Pending |
| P1 report templates (WeasyPrint PDF + Excel) | 12 hrs | Pending |
| Report generation service with async support | 3 hrs | Pending |
| Report scheduling (if needed) | 2 hrs | Pending |
| Report UI integration (generate, download, preview) | 3 hrs | Pending |

---

### Sub-Phase 7g: Reports P2 + P3 (10-15 hrs) — BLOCKED by 7f

| Priority | Count | Examples | Status |
|----------|-------|----------|--------|
| P2 (Medium) | 22 | Analytics, trend reports, employer utilization | Pending |
| P3 (Low) | 7 | Projections, ad-hoc queries | Pending |

| Task | Est. | Status |
|------|------|--------|
| P2 report templates | 5 hrs | Pending |
| P3 report templates | 3 hrs | Pending |
| Chart.js analytics integration for referral data | 3 hrs | Pending |
| Custom report builder extension for referral entities | 2 hrs | Pending |

---

### §7.7 Report Inventory Summary

| Priority | Reports | Description | Status |
|----------|---------|-------------|--------|
| P0 (Critical) | 16 | Core operational reports needed daily | Pending |
| P1 (High) | 33 | Important reports needed weekly/monthly | Pending |
| P2 (Medium) | 22 | Analytics and trend reports | Pending |
| P3 (Low) | 7 | Nice-to-have projections and ad-hoc | Pending |
| **Total** | **78** | **De-duplicated from 91 raw reports** | **Pending** |

Full report inventory in `docs/phase7/LABORPOWER_REPORTS_INVENTORY.md`

---

### §7.8 Immediate Next Steps (Pre-7a)

| # | Task | Status |
|---|------|--------|
| 1 | Merge `develop → main` for v0.9.4-alpha production deployment | Pending |
| 2 | Set production Stripe keys and S3 storage | Pending |
| 3 | Obtain Priority 1 blocking data exports from LaborPower (3 reports) | Pending |
| 4 | Resolve Priority 2 data gaps as exports become available | Pending |

---

### §7.9 Key Planning Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Roadmap v3.0 | `IP2A_BACKEND_ROADMAP.md` | Master plan with Phase 7 detail |
| Schema Guidance Vol. 1 | `docs/phase7/LaborPower_Schema_Guidance_Vol1.docx` | APN analysis, cross-registration findings |
| Schema Guidance Vol. 2 | `docs/phase7/LaborPower_Schema_Guidance_Vol2.docx` | Batch 2 analysis, RESIDENTIAL discovery |
| Continuity Document | `docs/phase7/UnionCore_Continuity_Document_Consolidated.md` | Full context for new chat threads |
| Gap Analysis | `docs/phase7/IP2A_GAP_ANALYSIS.md` | Data gap tracking with priorities |
| Implementation Plan v2 | `docs/phase7/IP2A_IMPLEMENTATION_PLAN_v2.md` | Detailed sub-phase breakdown |
| Referral Books Schema | `docs/phase7/IP2A_REFERRAL_BOOKS_SCHEMA.md` | DDL and model specifications |
| Dispatch Plan | `docs/phase7/IP2A_REFERRAL_DISPATCH_PLAN.md` | Dispatch workflow and business logic |
| Reports Inventory | `docs/phase7/LABORPOWER_REPORTS_INVENTORY.md` | 78 reports by priority with field mapping |

---

## Quick Stats

| Metric | Current |
|--------|---------|
| Total Tests | ~490+ |
| Backend Tests | 185+ |
| Frontend Tests | 200+ |
| Production Tests | 78 |
| Stripe Tests | 25 |
| API Endpoints | ~150 |
| ORM Models | 32 (26 existing + 6 Phase 7) |
| ADRs | 14 |
| Version | v0.9.5-alpha |
| Phase 7 Models Complete | 6 |
| Phase 7 Services Complete | 2 |
| Phase 7 Reports | 78 (de-duplicated, pending) |
| Phase 7 Effort Remaining | ~80-100 hrs |

---

## Version History

| Version | Date | Milestone |
|---------|------|-----------|
| v0.9.5-alpha | 2026-02-04 | Phase 7 Weeks 20-22 - Models, Enums, Schemas, Services |
| v0.9.4-alpha | 2026-02-03 | Phase 7 planning integrated into checklist |
| v0.9.4-alpha | 2026-02-02 | Week 19 - Analytics Dashboard |
| v0.9.3-alpha | 2026-02-02 | Week 18 - Mobile PWA |
| v0.9.2-alpha | 2026-02-02 | Week 17 - Post-Launch Operations |
| v0.9.1-alpha | 2026-02-02 | Week 16 - Production Hardening |
| v0.9.0-alpha | 2026-02-02 | Phase 6 Week 14 - Grant Compliance (FEATURE COMPLETE) |
| v0.8.2-alpha | 2026-02-02 | Phase 6 Week 13 - Entity Completion Audit |
| v0.8.1-alpha | 2026-01-31 | Phase 6 Week 12 - User Profile & Settings |
| v0.8.0-alpha1 | 2026-01-30 | Phase 6 Week 11 - Audit Infrastructure + Stripe |
| v0.7.9 | 2026-01-30 | Phase 6 Week 10 - Dues UI (Complete) |
| v0.7.8 | 2026-01-29 | Phase 6 Week 10 - Dues UI (Session A) |
| v0.7.7 | 2026-01-29 | Phase 6 Week 9 - Documents Frontend |
| v0.7.6 | 2026-01-29 | Phase 6 Week 8 - Reports & Export |
| v0.7.5 | 2026-01-29 | Phase 6 Week 6 - Union Operations |
| v0.7.4 | 2026-01-29 | Phase 6 Week 5 - Members Landing |
| v0.7.3 | 2026-01-29 | Phase 6 Week 4 - Training Landing |
| v0.7.2 | 2026-01-29 | Phase 6 Week 3 - Staff Management |
| v0.7.1 | 2026-01-29 | Phase 6 Week 2 - Auth cookies + Dashboard |
| v0.7.0 | 2026-01-28 | Phase 4 Complete (Backend milestone) |
| v0.6.0 | 2026-01-28 | Phase 3 + Auth + Training |
| v0.2.0 | 2026-01-27 | Phase 1 Services Layer |
| v0.1.0 | 2026-01-XX | Initial backend stabilization |

---

## Commands Cheat Sheet

```bash
# Start dev environment
docker-compose up -d

# Run tests
pytest -v

# Run frontend tests only
pytest src/tests/test_frontend.py -v

# Run staff tests only
pytest src/tests/test_staff.py -v

# Run training tests only
pytest src/tests/test_training_frontend.py -v

# Run member tests only
pytest src/tests/test_member_frontend.py -v

# Run dues frontend tests only
pytest src/tests/test_dues_frontend.py -v

# Run referral/dispatch tests (Phase 7)
pytest src/tests/test_referral*.py src/tests/test_dispatch*.py -v

# Check code quality
ruff check . --fix && ruff format .

# Database migration
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run API server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# View logs
docker-compose logs -f api

# Access MinIO console (file storage)
open http://localhost:9001
```

---

## Session Workflow

### Starting a Session
1. `git checkout develop` (ALWAYS work on develop branch)
2. `git pull origin develop`
3. `docker-compose up -d`
4. `pytest -v --tb=short` (verify green)
5. Check CLAUDE.md for current tasks

### Ending a Session
1. `pytest -v` (verify green)
2. `git status` (check for uncommitted changes)
3. Commit with conventional commit message
4. `git push origin develop` (push to develop, NOT main)
5. Update CLAUDE.md with session summary

### Merging to Main (for deployment)
1. `git checkout main`
2. `git pull origin main`
3. `git merge develop`
4. `git push origin main` (triggers Railway auto-deploy)

### Phase 7 Session Reminders

> **Member ≠ Student.** Members are IBEW union members in the referral system. Students are pre-apprenticeship program participants. Never conflate these entities in code, models, or UI.

> **Book ≠ Contract.** Books are out-of-work registration lists. Contracts are collective bargaining agreements. The mapping is NOT 1:1 — some books have no contract code (Tradeshow, TERO, Utility Worker).

> **APN = DECIMAL(10,2).** Integer part is Excel serial date encoding the registration date. Decimal part is the secondary sort key. Truncating to INTEGER destroys data fidelity.

### 📝 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.
> Scan `/docs/*` and make or create any relevant updates/documents to keep a
> historical record as the project progresses. Do not forget about ADRs —
> update as necessary.

See `docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

## Previous Version Notes

**v0.9.4-alpha Checklist (Feb 2, 2026):** Phase 7 section contained only report priority summary (17 lines). Updated Feb 3 to incorporate all LaborPower data analysis findings from Roadmap v3.0 including 8 schema findings, 11-book catalog, 14 business rules, 9 schema corrections, 12 new tables, 16 data gaps, and 7a-7g implementation sub-phases.

---

*Keep this checklist updated during each session!*
