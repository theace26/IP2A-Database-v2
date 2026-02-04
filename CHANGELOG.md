# Changelog

All notable changes to IP2A-Database-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> **v0.9.7-alpha — PHASE 7 Week 26 Complete**
> 564+ tests, ~200+ API endpoints, 32 models (26 + 6 Phase 7), 15 ADRs
> Railway deployed, Stripe live, Mobile PWA enabled
> Current: Phase 7 — Referral & Dispatch System (Backend + Week 26 Frontend UI Complete)

### Added
- **Phase 7 Week 26: Books & Registration UI** (February 4, 2026)
  * Created ReferralFrontendService for template data formatting and badge helpers
  * Created referral landing page with stats dashboard (active books, registered members, dispatched count)
  * Created books list page with HTMX filtering and search
  * Created book detail page with registered members table, stats cards, and queue display
  * Created registration list page with cross-book search and filtering
  * Created registration detail page with member info and registration history
  * Created 8 HTMX partials: stats cards, books overview/table, queue table, registrations table, register/re-sign/resign modals
  * Created referral_frontend router with 17 routes (5 main pages, 8 HTMX partials, 3 form submissions, 1 member search)
  * Added Referral & Dispatch section to sidebar navigation with Books and Registrations links
  * Added 22 new frontend tests (564 total)
  * Registered referral_frontend_router in main.py
  * Created API discovery document: docs/phase7/week26_api_discovery.md
- **Phase 7: Referral & Dispatch Implementation - Weeks 23-25** (February 4, 2026)
  * **Week 23A: LaborRequestService**
    - Created src/services/labor_request_service.py implementing Rules 2, 3, 4, 11
    - Rule 2: Morning referral processing order (Wire 8:30 AM, S&C 9:00 AM, Tradeshow 9:30 AM)
    - Rule 3: 3 PM cutoff enforcement for next-morning dispatch
    - Rule 4: Agreement type filtering (PLA/CWA/TERO)
    - Rule 11: Check mark determination (specialty skills, MOU sites, early starts)
    - Methods: create_request, update_request, cancel_request, expire_request, fulfill_request
  * **Week 23B: JobBidService**
    - Created src/services/job_bid_service.py implementing Rule 8
    - Rule 8: 5:30 PM – 7:00 AM bidding window validation
    - Bid operations: place_bid, withdraw_bid, accept_bid, reject_bid
    - Suspension tracking: 2 rejections in 12 months = 1-year suspension
    - Methods: get_pending_bids, get_member_bids, process_bids_for_request
  * **Week 23C: DispatchService**
    - Created src/services/dispatch_service.py implementing Rules 9, 12, 13
    - Rule 9: Short call handling (≤10 days, max 2 per cycle, position restoration)
    - Rule 12: Quit/discharge = all-books rolloff + 2-week blackout
    - Rule 13: By-name anti-collusion enforcement
    - Methods: dispatch_from_queue, dispatch_by_name, terminate_dispatch, restore_position
  * **Week 24A: QueueService Core**
    - Created src/services/queue_service.py for queue management
    - Queue snapshots with configurable depth and filters
    - Multi-book queue views with book priority ordering (Book 1→2→3)
    - Next-eligible selection (skips exempt, blackout, suspended)
    - Wait time estimation based on historical dispatch rates
    - Methods: get_queue_snapshot, get_member_queue_status, get_next_eligible
  * **Week 24B: EnforcementService**
    - Created src/services/enforcement_service.py for batch processing
    - daily_enforcement_run() with dry_run mode for admin preview
    - enforce_re_sign_deadlines() - 30-day cycle + grace period rolloffs
    - send_re_sign_reminders() - 7 days before deadline warnings
    - process_expired_requests/exemptions/bids() - cleanup routines
    - enforce_check_mark_limits() - batch verification
  * **Week 24C: Analytics & Integration**
    - get_pending_enforcements() for dashboard counts
    - get_enforcement_report() dry-run preview
    - run_specific_enforcement() for targeted execution
    - Queue utilization and dispatch rate metrics
  * **Week 25A: Book & Registration API**
    - Created src/routers/referral_books_api.py (~12 endpoints)
    - GET /api/v1/referral/books - list all books
    - GET /api/v1/referral/books/{id} - book detail
    - POST /api/v1/referral/books - create book (admin)
    - PUT /api/v1/referral/books/{id} - update book
    - GET /api/v1/referral/books/{id}/stats - book statistics
    - Created src/routers/registration_api.py (~12 endpoints)
    - POST /api/v1/referral/registrations - register member
    - POST /api/v1/referral/registrations/{id}/re-sign - re-sign
    - POST /api/v1/referral/registrations/{id}/resign - resign from book
    - GET /api/v1/referral/registrations/member/{id} - member's registrations
  * **Week 25B: LaborRequest & Bid API**
    - Created src/routers/labor_request_api.py (~12 endpoints)
    - CRUD for labor requests with status lifecycle
    - POST /api/v1/referral/requests/{id}/cancel
    - POST /api/v1/referral/requests/{id}/fulfill
    - GET /api/v1/referral/requests/open - active requests
    - Created src/routers/job_bid_api.py (~10 endpoints)
    - POST /api/v1/referral/bids - place bid (validates window)
    - DELETE /api/v1/referral/bids/{id} - withdraw bid
    - POST /api/v1/referral/bids/{id}/accept
    - POST /api/v1/referral/bids/{id}/reject
  * **Week 25C: Dispatch & Admin API**
    - Created src/routers/dispatch_api.py (~16 endpoints)
    - POST /api/v1/referral/dispatch/from-queue - dispatch next eligible
    - POST /api/v1/referral/dispatch/by-name - dispatch specific member
    - POST /api/v1/referral/dispatch/{id}/terminate - handle termination
    - GET /api/v1/referral/queue/{book_id} - queue snapshot
    - GET /api/v1/referral/queue/member/{id}/status - member queue status
    - POST /api/v1/referral/enforcement/run - trigger daily enforcement
    - GET /api/v1/referral/enforcement/report - dry-run preview
  * **main.py Updates**
    - Registered 5 Phase 7 API routers
    - Version bumped to v0.9.6-alpha
    - ~50 new endpoints for Phase 7
  * All 14 business rules now have service-layer implementations
- **Phase 7: Referral & Dispatch Implementation - Weeks 20-22** (February 4, 2026)
  * **Week 20A: Schema Reconciliation & Enums**
    - Created docs/phase7/PHASE7_SCHEMA_DECISIONS.md documenting 5 pre-implementation decisions
    - Decision 1: Separate JobBid model (cleaner audit trail, rejection tracking)
    - Decision 2: MemberTransaction independent of DuesPayment
    - Decision 3: Per-book exempt status on BookRegistration (not global on Member)
    - Decision 4: Field naming standardized (registration_number for APN, referral_start_time, etc.)
    - Decision 5: Dual audit pattern (RegistrationActivity + audit_logs for NLRA compliance)
    - Created src/db/enums/phase7_enums.py with 19 Phase 7 enums
    - Enums: BookClassification, BookRegion, RegistrationStatus, RegistrationAction, ExemptReason, RolloffReason, NoCheckMarkReason, LaborRequestStatus, BidStatus, DispatchMethod, DispatchStatus, DispatchType, TermReason, JobClass, MemberType, ReferralStatus, ActivityCode, PaymentSource, AgreementType
    - Updated src/db/enums/__init__.py to export all Phase 7 enums
  * **Week 20B: ReferralBook Model & Seeds**
    - Created src/models/referral_book.py with classification, region, referral_start_time, re_sign_days, max_check_marks, internet_bidding_enabled
    - Properties: full_name (e.g., "Wire Seattle Book 1"), is_wire_book
    - Created src/schemas/referral_book.py with ReferralBookBase, ReferralBookCreate, ReferralBookUpdate, ReferralBookRead, ReferralBookStats, ReferralBookSummary
    - Created src/seed/phase7_seed.py seeding 11 referral books (Wire Seattle/Bremerton/Port Angeles, Tradeshow, Sound & Comm, Marine, Stockperson, Light Fixture, Residential, Technician, Utility Worker)
  * **Week 20C: BookRegistration Model**
    - Created src/models/book_registration.py with registration_number as DECIMAL(10,2) for APN FIFO ordering
    - Fields: status, check_marks, exempt status (is_exempt, exempt_reason, exempt_start/end_date), rolloff tracking
    - Properties: is_active, is_rolled_off, can_be_dispatched, days_on_book, check_marks_remaining
    - Created src/schemas/book_registration.py with BookRegistrationBase, BookRegistrationCreate, BookRegistrationUpdate, BookRegistrationRead, BookRegistrationWithMember, QueuePosition, ReSignRequest, ExemptRequest, RolloffRequest
    - Updated src/models/member.py with book_registrations relationship
  * **Week 21A: LaborRequest & JobBid Models**
    - Created src/models/labor_request.py for employer job requests
    - Fields: workers_requested/dispatched, worksite info, short_call flags, check_mark rules, bidding windows
    - Properties: is_filled, workers_remaining, is_bidding_open
    - Created src/models/job_bid.py for member bid tracking (per Decision 1: separate model)
    - Tracks bid_status, rejection tracking for 1-year suspension rule
    - Properties: is_pending, was_accepted, counts_as_quit
    - Created src/schemas/labor_request.py and src/schemas/job_bid.py
  * **Week 21B: Dispatch Model**
    - Created src/models/dispatch.py linking member → job_request → employer
    - Tracks check-in, short call restoration, termination details
    - Properties: is_active, is_completed, was_quit_or_fired, should_restore_position
    - Created src/schemas/dispatch.py with DispatchBase, DispatchCreate, DispatchUpdate, DispatchCheckIn, DispatchTerminate, DispatchRead, DispatchWithDetails
  * **Week 21C: RegistrationActivity Model**
    - Created src/models/registration_activity.py as append-only audit trail (no updated_at column)
    - Tracks action, previous_status, new_status, positions, related dispatch/labor_request
    - Created src/schemas/registration_activity.py with RegistrationActivityBase, RegistrationActivityCreate, RegistrationActivityRead, RegistrationActivityWithDetails
    - Updated src/models/__init__.py to export all 6 Phase 7 models
    - Updated src/schemas/__init__.py to export all Phase 7 schemas
  * **Week 22A: ReferralBookService**
    - Created src/services/referral_book_service.py with full book management
    - Query methods: get_by_id, get_by_code, get_all_active, get_all, get_by_classification, get_by_region, get_by_classification_and_region
    - Stats: get_book_stats (registered, dispatched, avg_days_on_book, active_count), get_all_books_summary
    - CRUD: create_book, update_book
    - Admin: activate_book, deactivate_book, update_book_settings
  * **Week 22B: BookRegistrationService Core**
    - Created src/services/book_registration_service.py with core registration logic
    - Registration: register_member (with next APN calculation), re_sign_member
    - Status transitions: resign_member, roll_off_member, mark_dispatched
    - Query: get_by_id, get_book_queue (FIFO ordered by APN), get_member_registrations, get_member_position, get_registrations_expiring_soon
    - Validation: can_register (checks duplicate, status), can_re_sign (checks timing, status)
  * **Week 22C: Check Mark Logic & Roll-Off Rules**
    - Check marks: record_check_mark (increments, triggers rolloff at 3), record_missed_check_mark, restore_check_mark
    - Exempt status: grant_exempt_status (7 reason types), revoke_exempt_status
    - Roll-off: process_roll_offs (batch processing), get_re_sign_reminders (approaching 30-day deadline)
    - Protection: is_protected_from_rolloff (checks specialty_skill, mou_site, short_call, under_scale, early_start)
    - Business rules implemented: 30-day re-sign cycle, 3 check marks = rolloff, short call position restoration (max 2 per cycle)
  * **Tests**
    - Created src/tests/test_phase7_models.py with 20+ tests
    - Tests cover: ReferralBook, BookRegistration, RegistrationActivity models
    - Tests cover: BookClassification, BookRegion, RegistrationStatus enums
    - Tests verify: APN as DECIMAL(10,2), unique constraints, model properties, relationships
  * Version bumped to v0.9.5-alpha

- **Phase 7: Referral & Dispatch Planning** (February 2, 2026)
  * Created comprehensive Phase 7 planning documentation in docs/phase7/
  * PHASE7_REFERRAL_DISPATCH_PLAN.md — Full implementation plan
  * PHASE7_IMPLEMENTATION_PLAN_v2.md — Technical details and data models
  * PHASE7_CONTINUITY_DOC.md — Session handoff document
  * LOCAL46_REFERRAL_BOOKS.md — Referral book structure and seed data
  * LABORPOWER_GAP_ANALYSIS.md — Gap analysis vs LaborPower system
  * LABORPOWER_REFERRAL_REPORTS_INVENTORY.md — Inventory of ~78 reports to build (16 P0, 33 P1, 22 P2, 7 P3)

- **Week 19: Advanced Analytics Dashboard & Report Builder** (February 2, 2026)
  * Created AnalyticsService with membership stats, trends, dues analytics, training metrics, and activity tracking
  * Created ReportBuilderService for custom reports with CSV/Excel export
  * Created analytics router with executive dashboard, membership analytics, dues analytics, and report builder endpoints
  * Created dashboard template with Chart.js integration for membership trends and payment method charts
  * Created membership analytics page with 24-month trend chart and data table
  * Created dues analytics page with collection stats and delinquency report
  * Created custom report builder with dynamic field selection and status filtering
  * Officer-level role checking for analytics access
  * Created 19 new tests (test_analytics.py)
  * Version bumped to v0.9.4-alpha

- **Week 18: Mobile Optimization & Progressive Web App** (February 2, 2026)
  * Created mobile.css with touch-friendly styles (48x48px minimum touch targets)
  * Created PWA manifest.json with app icons and shortcuts
  * Created service worker (sw.js) for offline support and caching
  * Created offline.html page for when device has no internet connection
  * Created mobile drawer component (_mobile_drawer.html)
  * Created bottom navigation component (_bottom_nav.html)
  * Updated base.html with PWA meta tags and service worker registration
  * Added /offline route to frontend router
  * Created 14 new tests (test_mobile_pwa.py)
  * Version bumped to v0.9.3-alpha

- **Week 17: Post-Launch Operations & Maintenance** (February 2, 2026)
  * Created backup scripts (scripts/backup_database.sh, scripts/verify_backup.sh)
  * Created audit log archival script (scripts/archive_audit_logs.sh)
  * Created session cleanup script (scripts/cleanup_sessions.sh)
  * Created crontab example with scheduled tasks (scripts/crontab.example)
  * Created admin metrics dashboard router (src/routers/admin_metrics.py)
  * Created admin metrics template (src/templates/admin/metrics.html)
  * Created incident response runbook (docs/runbooks/incident-response.md)
  * Updated runbooks README with scheduled tasks documentation
  * Created 13 new tests (test_admin_metrics.py)
  * Version bumped to v0.9.2-alpha

- **Week 16: Production Hardening & Performance Optimization** (February 2, 2026)
  * Added SecurityHeadersMiddleware with X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Content-Security-Policy, Permissions-Policy headers
  * Created enhanced health check router with /health/live, /health/ready, /health/metrics endpoints
  * Added Sentry integration for error tracking and performance monitoring (src/core/monitoring.py)
  * Added structured JSON logging configuration for production (src/core/logging_config.py)
  * Updated database connection pooling with configurable settings (DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE)
  * Added new settings: SENTRY_DSN, APP_VERSION, ALLOWED_ORIGINS, JSON_LOGS
  * Added sentry-sdk[fastapi]>=1.40.0 to requirements.txt
  * Created 32 new tests (test_security_headers.py, test_health_checks.py, test_rate_limiting.py)
  * Version bumped to v0.9.1-alpha

- **Branching Strategy Established** (January 30, 2026)
  * Created `develop` branch for ongoing development
  * Frozen `main` branch at v0.8.0-alpha1 for Railway demo stability
  * All development now occurs on `develop` branch
  * `main` branch only updated when ready to deploy to Railway
  * Updated CLAUDE.md and CONTINUITY.md with branching workflow
  * Session workflow documentation updated to reflect new branch strategy

- **Stripe Payment Integration - Phase 1 Backend** (January 30, 2026)
  * Implemented PaymentService for creating Stripe Checkout Sessions
  * Created Stripe webhook handler at /webhooks/stripe endpoint
  * Webhook handles: checkout.session.completed, checkout.session.expired, payment_intent.succeeded, payment_intent.payment_failed, charge.refunded
  * Added Stripe configuration to src/config/settings.py (STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET)
  * Added stripe>=8.0.0 to requirements.txt
  * Updated .env.example with Stripe environment variables
  * Registered Stripe webhook router in src/main.py
  * Created src/services/payment_service.py with Checkout Session creation, session retrieval, customer ID management, webhook event verification
  * Created src/routers/webhooks/ directory structure
  * Created src/routers/webhooks/stripe_webhook.py with full webhook event handling
  * Webhook verifies signature for security (no authentication needed)
  * Payment records automatically created in DuesPayment table on successful payment
  * Supports credit/debit cards and ACH bank transfers via Stripe
  * Next phase: Database migrations (stripe_customer_id field), frontend integration, success/cancel pages

- **Documentation Standardization** (January 30, 2026)
  * Standardized "End-of-Session Documentation" reminder added to all 55 instruction documents
  * Updated 10 MASTER instruction files with mandatory documentation checklist
  * Updated 32 session-specific instruction files
  * Updated 6 Week 1 instruction files
  * Updated 6 deployment instruction files
  * Updated INSTRUCTION_TEMPLATE.md for future instruction documents
  * All instruction docs now include reminder to update CHANGELOG, ADRs, session logs, etc.
  * Ensures historical record-keeping and "bus factor" protection

- **Stripe Payment Integration Planning** (January 30, 2026)
  * ADR-013: Stripe Payment Integration architecture decision
  * Decision: Use Stripe Checkout Sessions for online dues payment
  * Payment methods: Credit/debit cards (2.9% + $0.30), ACH bank transfers (0.8%, $5 cap)
  * Webhook verification strategy for payment confirmation
  * Test mode setup documented (Stripe CLI, test cards, test bank accounts)

- **Stripe Payment Integration - Phase 2 Database** (January 30, 2026)
  * Created migration f1a2b3c4d5e6 to add stripe_customer_id to members table
  * Added stripe_customer_id column (VARCHAR(100), unique, indexed)
  * Updated Member model with stripe_customer_id field
  * Updated Member schema to include stripe_customer_id in read operations
  * Created migration g2b3c4d5e6f7 to add Stripe payment methods to DuesPaymentMethod enum
  * Added STRIPE_CARD, STRIPE_ACH, STRIPE_OTHER enum values
  * Fixed webhook handler bug: changed DuesPaymentStatus.COMPLETED to PAID
  * Created src/tests/test_stripe_integration.py with 11 integration tests
  * Tests cover PaymentService, webhook handling, model updates, enum validation
  * Database ready for Stripe customer tracking and payment method classification

- **Stripe Payment Integration - Phase 3 Frontend** (January 30, 2026)
  * Added payment initiation endpoint POST /dues/payments/initiate/{member_id}/{period_id}
  * Endpoint creates Stripe Checkout Session and redirects to Stripe hosted page
  * Added success page GET /dues/payments/success with optional session retrieval
  * Added cancel page GET /dues/payments/cancel for abandoned checkouts
  * Created src/templates/dues/payments/success.html with payment confirmation UI
  * Created src/templates/dues/payments/cancel.html with retry options
  * Added "Pay Now Online" button to member payment history page (when balance > 0)
  * Button triggers Stripe Checkout flow with member's current dues rate
  * Added get_rate_for_member() method to DuesFrontendService
  * Updated payment method display names to include "Stripe (Card)", "Stripe (ACH)", "Stripe (Other)"
  * Created src/tests/test_stripe_frontend.py with 14 frontend tests
  * Tests cover payment initiation, success/cancel pages, rate lookup, display formatting
  * Complete end-to-end payment flow: Member → Pay button → Stripe → Webhook → Database

- **Week 11 Session A: Audit Infrastructure** (January 30, 2026)
  * Created migration h3c4d5e6f7g8 to add immutability triggers to audit_logs table
  * Implemented prevent_audit_modification() PostgreSQL trigger function
  * Added BEFORE UPDATE and BEFORE DELETE triggers to audit_logs (NLRA compliance)
  * Triggers prevent any modification or deletion of audit records (7-year retention)
  * Created src/tests/test_audit_immutability.py with 4 tests verifying trigger enforcement
  * Created MemberNote model for staff documentation about members
  * Implemented NoteVisibility levels: staff_only, officers, all_authorized
  * Created migration i4d5e6f7g8h9 to add member_notes table
  * Table includes: id, member_id, created_by_id, note_text, visibility, category, soft delete fields
  * Created src/schemas/member_note.py with Pydantic schemas
  * Created src/services/member_note_service.py with full CRUD operations
  * Service implements role-based visibility filtering (Admin/Officer/Staff permissions)
  * All member note operations automatically logged via audit_service
  * Created src/routers/member_notes.py with REST API endpoints
  * Registered router at /api/v1/member-notes
  * Added member_notes to AUDITED_TABLES in audit_service.py
  * Updated Member model with notes relationship
  * Created src/tests/test_member_notes.py with 15 comprehensive tests
  * Tests cover model, service, API endpoints, visibility filtering, soft delete
  * Total new tests: 19 (4 immutability + 15 member notes)
  * Future phases planned: Subscriptions, payment plans, customer portal, QuickBooks sync
  * Updated docs/decisions/README.md with ADR-012 and ADR-013
  * Implementation components defined (PaymentService, webhook router, migrations)

- **Week 11 Session B: Audit UI & Role Permissions** (January 31, 2026)
  * Created src/core/permissions.py with AuditPermission enum and role-based permission mapping
  * Defined audit permissions: VIEW_OWN, VIEW_MEMBERS, VIEW_USERS, VIEW_ALL, EXPORT
  * Role mappings: staff (view own), officer (view members/users), admin (view all + export)
  * Implemented redact_sensitive_fields() for non-admin users (SSN, passwords, etc.)
  * Created src/services/audit_frontend_service.py with role-based audit log queries
  * Service determines user's primary role (highest privilege) for filtering
  * Filtering by table, action, date range, search query
  * Created src/routers/audit_frontend.py with audit log frontend routes
  * GET /admin/audit-logs - main audit viewer page with stats and filters
  * GET /admin/audit-logs/search - HTMX endpoint for filtered/paginated results
  * GET /admin/audit-logs/detail/{log_id} - detailed view with before/after comparison
  * GET /admin/audit-logs/export - CSV export (admin only)
  * GET /admin/audit-logs/entity/{table_name}/{record_id} - inline entity history
  * Created src/templates/admin/audit_logs.html - main audit page with stats cards and filters
  * Stats: total logs, logs this week, logs today
  * HTMX-powered filters with live search (300ms debounce)
  * Created src/templates/admin/audit_detail.html - log detail page with JSON diff view
  * Created src/templates/admin/partials/_audit_table.html - paginated table with action badges
  * Created src/templates/components/_audit_history.html - reusable timeline component
  * DaisyUI timeline-vertical layout with color-coded action indicators
  * Updated src/templates/components/_sidebar.html with Audit Logs link (admin/officer only)
  * Created src/tests/test_audit_frontend.py with 20 comprehensive tests
  * Tests cover role permissions, redaction, filtering, CSV export, inline history
  * Fixed import error in member_notes.py (get_current_active_user → get_current_user)
  * Added missing test fixtures to conftest.py (auth_headers, test_user, test_member)
  * Created get_current_user_model() dependency in auth_cookie.py for full User object access
  * Total new tests: 20 (audit frontend)

- **Week 11 Session C: Inline History & Member Notes UI** (January 31, 2026)
  * Created src/templates/members/partials/_notes_list.html - member notes display with visibility badges
  * Notes filtered by role: staff sees own, officers see all staff+officer, admin sees all
  * Visibility badges: staff_only (warning), officers (info), all_authorized (success)
  * Role-based delete button (creator or admin only)
  * Empty state with helpful message
  * Created src/templates/members/partials/_add_note_modal.html - modal for creating notes
  * Visibility selector: staff_only, officers, all_authorized
  * Category selector: contact, dues, grievance, referral, training, general
  * HTMX post with automatic refresh via custom event
  * Updated src/templates/members/detail.html with Notes and Audit History sections
  * Notes section with HTMX loading on page load and notes-updated event
  * Audit History section with DaisyUI timeline component
  * Add Note modal integrated into detail page
  * Updated src/templates/components/_audit_history.html to use DaisyUI timeline-vertical
  * Color-coded timeline entries: CREATE (success), UPDATE (warning), DELETE (error)
  * Shows changed fields and notes for each audit entry
  * Link to full audit log history for the entity
  * Added notes endpoints to src/routers/member_frontend.py
  * GET /members/{member_id}/notes-list - HTMX endpoint returning notes list
  * POST /members/{member_id}/notes - HTMX endpoint creating new note
  * Both endpoints use SyncSession for notes service compatibility
  * Format notes for template display (convert model to dict)
  * Handle RedirectResponse for expired sessions with HX-Redirect header
  * Total new functionality: Notes UI, inline audit timeline, enhanced member detail page

- **Week 13: IP2A Entity Completion Audit** (February 2, 2026)
  * Completed entity audit verifying existing IP2A-specific models
  * Confirmed Location model exists with full address, capacity, contacts, LocationType enum
  * Confirmed InstructorHours model exists with hours tracking, prep_hours, payroll support
  * Confirmed ToolsIssued model exists with checkout/return tracking, condition, value
  * Confirmed Expense model already has grant_id FK (acts as GrantExpense)
  * All Week 13 entities verified as fully implemented in current codebase
  * No new models required - original IP2A design already covered by existing infrastructure

- **Week 14: Grant Module Expansion** (February 2, 2026)
  * Created src/db/enums/grant_enums.py with GrantStatus, GrantEnrollmentStatus, GrantOutcome
  * GrantStatus: pending, active, completed, closed, suspended
  * GrantEnrollmentStatus: enrolled, active, completed, withdrawn, dropped
  * GrantOutcome: completed_program, obtained_credential, entered_apprenticeship, obtained_employment, continued_education, withdrawn, other
  * Enhanced Grant model with status field and target fields (target_enrollment, target_completion, target_placement)
  * Created src/models/grant_enrollment.py - links students to grants with outcome tracking
  * Tracks enrollment_date, status, completion_date, outcome, outcome_date
  * Includes placement tracking: employer, date, wage, job_title
  * Created migration j5e6f7g8h9i0 for grant_enrollments table and Grant enhancements
  * Created src/schemas/grant.py with GrantBase, GrantCreate, GrantUpdate, GrantRead, GrantSummary, GrantMetrics
  * Created src/schemas/grant_enrollment.py with full schema set including RecordOutcome
  * Created src/services/grant_metrics_service.py for calculating compliance metrics
  * Metrics: enrollment stats, financial stats, outcome stats, progress toward targets
  * Badge helper methods for status, enrollment status, and outcome colors
  * Created src/services/grant_report_service.py for compliance reporting
  * Report types: summary (executive), detailed (student-level), funder (formatted for submission)
  * Excel export with Summary, Enrollments, Expenses sheets (via openpyxl)
  * Created src/routers/grants_frontend.py with full grant management routes
  * Routes: landing, list, detail, enrollments, expenses, reports, report views, excel download
  * Created src/templates/grants/ with index.html, list.html, detail.html
  * Created enrollments.html, expenses.html, reports.html, report_summary.html
  * Created grants/partials/_enrollments_table.html for HTMX filtering
  * Added Grants link to sidebar navigation (Training section)
  * Registered grants_frontend_router in src/main.py
  * Created src/tests/test_grant_enrollment.py with enum, model, schema tests
  * Created src/tests/test_grant_services.py with service and router tests
  * Created ADR-014: Grant Compliance Reporting System
  * Updated reconciliation checklist with completion status

- **Week 12 Session A: User Profile & Settings** (January 31, 2026)
  * Created src/services/profile_service.py with ProfileService class
  * change_password() method with validation: current password verification, minimum 8 chars, different from old
  * Password changes trigger must_change_password = False
  * get_user_activity_summary() queries audit logs for past 7 days
  * Returns action counts and recent activity for profile display
  * Created src/routers/profile_frontend.py with profile management routes
  * GET /profile - user profile view page
  * GET /profile/change-password - change password form
  * POST /profile/change-password - process password change with validation
  * Uses get_current_user_model() dependency for full User object access
  * Flash messages for success/error feedback
  * Created src/templates/profile/index.html - profile information display
  * Account info card: email, name, roles
  * Account security card with password change link
  * Activity summary card showing actions this week from audit log
  * User roles display with badges
  * Created src/templates/profile/change_password.html - password change form
  * Three fields: current password, new password, confirm password
  * Password requirements alert (minimum 8 characters, must be different)
  * Error message display for validation failures
  * Form validation with minlength=8
  * Registered profile_frontend_router in src/main.py at /profile route
  * Password changes automatically logged via audit system
  * Total new functionality: User profile page, password change flow, activity tracking

- **Project Documentation Updates** (January 30, 2026)
  * Updated CLAUDE.md with documentation standardization and Stripe planning sections
  * Updated CONTINUITY.md with Recent Updates section and latest status
  * Updated CONTINUITY.md Last Updated date to 2026-01-30
  * Updated ADR count from 11 to 13 in CLAUDE.md status line
  * Created comprehensive session log: 2026-01-30-documentation-standardization.md

- **Production Database Seeding Expansion** (January 30, 2026)
  * Increased seed counts: 1000 members, 500 students, 100 organizations, 75 instructors
  * Added `seed_grants.py` - 10 grant/funding source records
  * Added `seed_expenses.py` - 200 expense records linked to grants
  * Added `seed_instructor_hours.py` - 20 entries per instructor
  * Added `truncate_all.py` - Safe database truncation in dependency order
  * Added `seed_tools_issued.py` integration (2 per student)
  * Added `seed_credentials.py` integration (2 per student)
  * Added `seed_jatc_applications.py` integration (1 per student)
  * Expanded seed to 18 steps (was 12)
  * Training seed now creates 200 student enrollments
  * Production seed now truncates and reseeds on each run (controlled by env var)

- **Documents "Feature Not Implemented" Page**
  * Friendly placeholder page when S3/MinIO is not configured
  * Shows setup instructions for production storage

- **Phase 6 Week 10: Dues UI** (Complete)
  * Dues landing page with current period display and days until due
  * Stats cards: MTD collected, YTD collected, overdue count, pending adjustments
  * Quick action cards linking to rates, periods, payments, adjustments
  * Rates list page with HTMX filtering by classification
  * Active only toggle for filtering current rates
  * Rates table partial with status badges (Active/Expired/Future)
  * Periods list page with year/status filters
  * Generate year modal for creating 12 monthly periods
  * Period detail page with payment summary and status breakdown
  * Close period workflow with confirmation modal
  * Payments list page with search, period filter, status filter
  * Record payment modal (amount, method, check number, notes)
  * Member payment history page with balance summary
  * Adjustments list page with status/type filters
  * Adjustment detail page with approve/deny modal workflow
  * DuesFrontendService with stats queries and badge color helpers
  * Currency formatting and period name formatting utilities
  * Sidebar navigation updated with Dues dropdown menu
  * 37 new dues frontend tests (167 frontend total)
  * ADR-011: Dues Frontend Patterns

- **Phase 6 Week 9: Documents Frontend** (Complete)
  * Documents landing page with storage stats and recent files
  * Upload page with Alpine.js drag-drop zone
  * Browse page with entity type filtering
  * Download redirect endpoint (presigned S3 URLs)
  * Delete endpoint with HTMX confirmation
  * HTMX partials for upload/delete success and error states
  * Entity type dropdown (Member, Student, Grievance, SALTing, Benevolence)
  * Documents link added to sidebar navigation
  * 6 new document frontend tests (130 frontend total)

- **Phase 6 Week 8: Reports & Export** (Complete)
  * Reports landing page with categorized report list
  * ReportService with PDF generation (WeasyPrint) and Excel generation (openpyxl)
  * Member roster report (PDF/Excel) with filtering by status
  * Dues summary report (PDF/Excel) with year parameter
  * Overdue members report (PDF/Excel) with balance calculation
  * Training enrollment report (Excel) with course enrollment counts
  * Grievance summary report (PDF) with status breakdown
  * SALTing activities report (Excel) with full activity details
  * PDF templates with professional styling and header/footer
  * Lazy loading for WeasyPrint to handle missing system dependencies
  * 30 new report tests (124 frontend total)
  * Updated requirements.txt with weasyprint and openpyxl

- **Infrastructure Phase 2: Migration Safety** (Complete)
  * Alembic wrapper for timestamped migrations (YYYYMMDD_HHMMSS_description.py)
  * FK dependency graph analyzer (scripts/migration_graph.py)
  * Destructive operation detector (scripts/migration_validator.py)
  * CLI commands: migrate new, validate, list, graph, check-destructive
  * Pre-commit hooks for migration naming and destructive checks
  * ADR-009: Migration Safety Strategy

- **Phase 6 Week 6: Union Operations Frontend** (Complete)
  * Union operations landing page with module cards
  * Overview stats: SALTing activities/month, benevolence pending/YTD, grievances open/total
  * SALTing activities list with type and outcome badges
  * SALTing detail with organizer and employer info
  * Filter SALTing by activity type and outcome
  * Benevolence applications list with status workflow badges
  * Benevolence detail with payment history and review timeline
  * Status workflow steps visualization (Draft -> Paid)
  * Filter benevolence by status and reason
  * Grievances list with step progress indicators
  * Grievance detail with step timeline
  * Step progress visualization (Steps 1-3 + Arbitration)
  * Filter grievances by status and step
  * OperationsFrontendService for all 3 modules
  * 21 new operations frontend tests (94 frontend total)
  * Updated sidebar navigation with Operations dropdown

- **Phase 6 Week 5: Members Landing Page** (Complete)
  * Members landing page with overview stats dashboard
  * Stats: total members, active, inactive/suspended, dues current %
  * Classification breakdown with color-coded badges
  * Member list page with HTMX search (300ms debounce)
  * Filter by status (active/inactive/suspended/retired) and classification
  * Status and classification badges with color coding
  * Current employer display in table
  * Quick edit modal for member info
  * Member detail page with contact info
  * Employment history timeline (HTMX loaded)
  * Dues summary section with payment history (HTMX loaded)
  * Current employer and quick actions sidebar
  * MemberFrontendService for stats and queries
  * 15 new member frontend tests (73 frontend total)

- **Phase 6 Week 4: Training Landing Page** (Complete)
  * Training landing page with overview stats dashboard
  * Stats: total students, active students, completed, completion rate
  * Recent students table with quick view
  * Quick action buttons for navigation
  * Student list page with HTMX search (300ms debounce)
  * Filter by status (enrolled/completed/dropped/etc) and cohort
  * Status badges with color coding
  * Student detail page with enrollments and program dates
  * Course list with card layout showing enrollment counts
  * Course detail page with enrolled students table
  * TrainingFrontendService for stats and queries
  * 19 new training frontend tests (59 frontend total)

- **Phase 6 Week 3: Staff Management** (Complete)
  * Staff list page with search, filter, and pagination
  * HTMX-powered live search (300ms debounce)
  * Filter by role and account status (active/locked/inactive)
  * Quick edit modal with role checkboxes and status toggle
  * Full detail page with user info and quick actions
  * Account actions: lock/unlock, reset password, soft delete
  * Prevent self-lock and self-delete
  * 403 error page for unauthorized access
  * StaffService with complete CRUD operations
  * 18 new staff management tests (205 total)

- **Phase 6 Week 2: Auth Cookies + Dashboard** (Complete)
  * Cookie-based authentication with HTTP-only cookies
  * `auth_cookie.py` dependency for JWT cookie validation
  * `dashboard_service.py` for real-time stats aggregation
  * Dashboard shows real data: active members, students, grievances, dues MTD
  * Activity feed from audit log with badges and time-ago formatting
  * HTMX refresh for dashboard stats and activity
  * Flash message support via URL parameters
  * Token expiry handling with redirect to login
  * Placeholder routes for future pages (members, dues, training, etc.)
  * 10 new auth tests (187 total)

- **Phase 6 Week 1: Frontend Foundation** (Complete)
  * Base templates with DaisyUI + Tailwind CSS + HTMX + Alpine.js (CDN)
  * Login page with HTMX form submission
  * Forgot password page
  * Dashboard placeholder with stats cards and quick actions
  * Responsive sidebar navigation with drawer component
  * Component templates (navbar, sidebar, flash messages, modal)
  * Custom CSS and JavaScript (toast notifications, HTMX handlers)
  * Error pages (404, 500) with hybrid HTML/JSON responses
  * Frontend router for HTML page serving
  * 12 frontend tests (177 total)
  * jinja2 added to requirements.txt

### Fixed
- **HTMX 401 Errors Not Handled Gracefully** (Bug #022) - January 30, 2026
  * Root cause: HTMX requests returning 401 showed generic "An error occurred" toast instead of redirecting to login
  * Added specific error handling for 401, 403, 404, 500+ status codes in `app.js`
  * Added `HX-Redirect` header to backend 401 responses for proper HTMX redirect
  * Users now see "Session expired. Redirecting to login..." and are automatically redirected
  * Files modified: `src/static/js/app.js`, `src/routers/operations_frontend.py`, `src/routers/member_frontend.py`, `src/routers/dues_frontend.py`

- **bcrypt 4.1.x Incompatibility with passlib** (Bug #023) - January 30, 2026
  * Root cause: bcrypt 4.1+ removed `__about__` attribute that passlib tries to access
  * Manifested as: `AttributeError: module 'bcrypt' has no attribute '__about__'`
  * Fix: Pinned bcrypt to `>=4.0.1` in requirements.txt
  * Files modified: `requirements.txt`

- **Reports Router Async/Sync Session Mismatch** (Bug #024) - January 30, 2026
  * Root cause: `reports.py` used `await db.execute()` with `AsyncSession` type hint, but `get_db()` returns synchronous `Session`
  * TypeError: `object Result can't be used in 'await' expression`
  * Fix: Changed to synchronous database calls (removed `await`, changed type hint to `Session`)
  * Files modified: `src/routers/reports.py`

- **Setup Flow Silent Role Assignment Failure** (Bug #025) - January 30, 2026
  * Root cause: `create_setup_user()` silently skipped role assignment if role lookup failed
  * Users created during setup had no roles, couldn't access Staff Management
  * Fix: Now raises `ValueError` if role not found; created migration `813f955b11af` to fix existing users
  * Files modified: `src/services/setup_service.py`, `src/db/migrations/versions/813f955b11af_fix_missing_user_roles.py`

- **Migration INSERT Missing is_system_role Column** (Bug #020)
  * Root cause: Raw SQL INSERT in `813f955b11af_fix_missing_user_roles.py` migration omitted required `is_system_role` column
  * PostgreSQL raised `NotNullViolation: null value in column "is_system_role" of relation "roles"`
  * Fix: Added `is_system_role` with value `true` to the INSERT statement
  * Files modified: `src/db/migrations/versions/813f955b11af_fix_missing_user_roles.py`

- **MemberClassification Enum Value Mismatch in Services** (Bug #021)
  * Root cause: `member_frontend_service.py` and `dues_seed.py` used non-existent enum values (JOURNEYMAN_WIREMAN, APPRENTICE_1, etc.)
  * Actual enum values are: JOURNEYMAN, APPRENTICE_1ST_YEAR, APPRENTICE_2ND_YEAR, etc.
  * Fix: Updated all service files to use correct MemberClassification enum values
  * Files modified: `src/services/member_frontend_service.py`, `src/seed/dues_seed.py`

- **passlib/bcrypt Compatibility Issue in Production** (Bug #012, revisited)
  * passlib 1.7.4 incompatible with bcrypt 4.1+ (`AttributeError: module 'bcrypt' has no attribute '__about__'`)
  * Fix: Replaced passlib with direct bcrypt usage in `src/core/security.py`
  * Removed passlib from requirements.txt
  * Files modified: `src/core/security.py`, `requirements.txt`

- **Reports Template TypeError - Dict Method Conflict** (Bug #013)
  * Root cause: Template used `category.items` which conflicted with Python dict's `.items()` method
  * Jinja2 found the method instead of the dict key, causing `TypeError: 'builtin_function_or_method' object is not iterable`
  * Fix: Renamed dict key from `items` to `reports` to avoid conflict
  * Files modified: `src/routers/reports.py`, `src/templates/reports/index.html`

- **Staff Service SQLAlchemy Cartesian Product Warning** (Bug #014)
  * Root cause: Count query created subquery from statement with `selectinload` options
  * SQLAlchemy warned about cartesian product between eager-loaded tables
  * Fix: Refactored to build separate count query without eager loading
  * Files modified: `src/services/staff_service.py`

- **Token Validation Errors Spamming Logs After Deployment** (Bug #015)
  * Root cause: Invalid cookies not cleared on auth redirect, causing repeated validation failures
  * Every request with stale tokens logged "Signature verification failed" warning
  * Fix: Added `delete_cookie()` calls in `_handle_unauthorized()` to clear invalid tokens
  * Users now see one redirect instead of log spam
  * Files modified: `src/routers/dependencies/auth_cookie.py`

- **Truncate Function Transaction Abort on Missing Table** (Bug #018)
  * Root cause: PostgreSQL aborts entire transaction when a TRUNCATE fails (e.g., table doesn't exist)
  * All subsequent TRUNCATEs failed with "current transaction is aborted"
  * Fix: Added SAVEPOINT mechanism to isolate each table truncation
  * Missing tables are now skipped gracefully
  * Files modified: `src/seed/truncate_all.py`

- **StudentStatus Enum in Seed (GRADUATED → COMPLETED)** (Bug #017, #019)
  * Root cause: Seed files used `StudentStatus.GRADUATED` which doesn't exist in the enum
  * Fix: Changed to use correct enum values (`COMPLETED`, `DROPPED`, etc.)
  * Files modified: `src/seed/seed_students.py`

- **Production Seed KeyError 'users_created'** (Bug #009)
  * Root cause: `production_seed.py` accessed `users_created` but `auth_seed.py` returns `admin_created`
  * Fixed dict key access to use correct key name
  * Railway was deploying cached old code; required fresh deployment

- **Missing Seed Files for Expanded Production Seed** (Bug #010)
  * Created `seed_grants.py`, `seed_expenses.py`, `seed_instructor_hours.py`, `truncate_all.py`
  * All new seed files now properly integrated with production seed

- **StudentStatus Enum Value Mismatch** (Bug #011, #017)
  * Seed files incorrectly used `GRADUATED` which doesn't exist in StudentStatus enum
  * Fixed to use correct values: `COMPLETED`, `DROPPED`, `ENROLLED`, etc.

- **passlib Bcrypt Compatibility Issue** (Bug #012)
  * passlib had compatibility issues with newer bcrypt versions
  * Replaced passlib with direct bcrypt usage in `src/core/security.py`

- **JWT Token Signature Verification Failed on Container Restart** (Bug #006)
  * Root cause: `AUTH_JWT_SECRET_KEY` not set in production, causing random secret generation on each restart
  * All user sessions invalidated when container restarts, users see "Signature verification failed"
  * Fix: Added `check_jwt_secret_configuration()` function to log warning at startup
  * Fix: Added startup event in main.py to call the check
  * Operators must set `AUTH_JWT_SECRET_KEY` environment variable for persistent sessions
  * Files modified: `src/config/auth_config.py`, `src/main.py`

- **Login page `[object Object]` error** (Bug #001)
  * Root cause: HTMX sends form data as `application/x-www-form-urlencoded` by default, but FastAPI `/auth/login` endpoint expects JSON body
  * This caused a 422 validation error with a Pydantic error format that JavaScript wasn't handling properly
  * Fix: Added HTMX `json-enc` extension to `base_auth.html` to send JSON to API endpoints
  * Fix: Updated login form with `hx-ext="json-enc"` attribute
  * Fix: Improved JavaScript error handling with better fallbacks and safeguard against `[object Object]` display
  * Files modified: `src/templates/base_auth.html`, `src/templates/auth/login.html`

- **Dashboard 500 error - dict access in navbar** (Bug #002)
  * Root cause: Navbar template used dot notation `current_user.first_name` but `current_user` is a dict
  * Jinja2 raises `UndefinedError` when accessing missing dict keys with dot notation
  * Fix: Changed to `.get()` method for safe dict access with fallbacks
  * Files modified: `src/templates/components/_navbar.html`

- **Frontend Services Async/Await TypeError** (Bug #003)
  * Root cause: Frontend service files incorrectly used `AsyncSession` and `await` with synchronous `Session`
  * Python raised `TypeError: object ChunkedIteratorResult can't be used in 'await' expression`
  * Fix: Changed all frontend services to use synchronous `Session` and removed `await` from db calls
  * Files modified: `src/services/member_frontend_service.py`, `src/services/training_frontend_service.py`, `src/services/operations_frontend_service.py`

- **Mixed Content Blocking Static Files** (Bug #004)
  * Root cause: FastAPI's `url_for()` generates HTTP URLs behind Railway's HTTPS reverse proxy
  * Browsers blocked HTTP resources on HTTPS pages as "Mixed Content"
  * Fix: Changed all static file references to use relative URLs (`/static/...`)
  * Files modified: `src/templates/base.html`, `src/templates/base_auth.html`

- **HTMX json-enc Extension Not Encoding Form Data** (Bug #005)
  * Root cause: HTMX `json-enc` extension was unreliable, not converting form data to JSON
  * Login form sent URL-encoded data causing 422 validation errors on `/auth/login`
  * Fix: Created form-based `POST /login` endpoint that accepts `Form()` data directly
  * Fix: Updated login form to POST to `/login` instead of `/auth/login`
  * Files modified: `src/routers/frontend.py`, `src/templates/auth/login.html`

- **Production Seed Causing Container Restart Loop** (Bug #007)
  * Root cause: `RUN_PRODUCTION_SEED=true` caused seed to run on every startup, taking too long
  * Railway health check failed before web server started, triggering restart loop
  * Database was truncated and re-seeded on each restart attempt
  * Fix: Set `RUN_PRODUCTION_SEED=false` after initial seed completes
  * Seed should be run as a one-time job, not on every startup

- **Browser Cookies Invalid After JWT Secret Key Change** (Bug #008)
  * Root cause: Existing JWT tokens were signed with old/random secrets
  * After setting `AUTH_JWT_SECRET_KEY`, old tokens fail signature verification
  * Fix: Users clear browser cookies and log in again with fresh tokens
  * This is expected security behavior when JWT secrets change

### Changed
- Updated CLAUDE.md with Week 10 Dues UI progress
- Updated sidebar navigation with Dues dropdown menu (Overview, Rates, Periods, Payments, Adjustments)
- Updated CLAUDE.md with frontend phase context
- Updated auth router to set/clear HTTP-only cookies on login/logout
- Updated frontend router with auth middleware and real data
- Updated login template to use correct /auth/login path
- Updated dashboard template with HTMX refresh and activity feed
- Created docs/instructions/ for Claude Code instruction documents
- Updated main.py with static file mounting and exception handlers

## [0.7.0] - 2026-01-28

### Added
- **Phase 4: Dues Tracking System**
  * 4 new models: DuesRate, DuesPeriod, DuesPayment, DuesAdjustment
  * 4 new enums: DuesPaymentStatus, DuesPaymentMethod, DuesAdjustmentType, AdjustmentStatus
  * Complete dues lifecycle: rate management, period tracking, payments, adjustments
  * Member classification-based rate lookup
  * Approval workflow for dues adjustments (pending/approved/denied)
  * Period management with close functionality
  * Overdue payment tracking
  * ~35 API endpoints across 4 routers
  * Dues seed data with rates for all 9 member classifications
  * 21 new tests (165 total passing)
  * Migration for dues tables with proper indexes

**Note:** This marks the completion of all backend phases. The system now has:
- 165 tests passing
- ~120 API endpoints
- 8 Architecture Decision Records

## [0.6.0] - 2026-01-28

### Added
- **Phase 3: Document Management System**
  * S3-compatible object storage integration (MinIO dev, AWS S3/Backblaze B2 production)
  * Complete document lifecycle: upload, download, delete with soft/hard delete options
  * Presigned URLs for secure, time-limited file access
  * Direct-to-S3 uploads for large files (presigned upload URLs)
  * File validation: extension whitelist (pdf, doc, docx, jpg, png, etc.), 50MB max
  * Organized storage paths: `uploads/{type}s/{name}_{id}/{category}/{year}/{month}/`
  * 8 REST API endpoints for document operations
  * Environment-based S3 configuration (works with any S3-compatible service)
  * MinIO service added to docker-compose for development
  * 11 new tests with mock S3 service
  * ADR-004 implemented
- **Phase 1.1-1.3: Complete Authentication System**
  * JWT-based authentication with bcrypt password hashing (12 rounds, OWASP compliant)
  * User registration with email verification
  * Password reset flow (forgot password)
  * RBAC with 6 default roles (admin, officer, staff, organizer, instructor, member)
  * Account security: lockout, token rotation, device tracking
  * Rate limiting on all auth endpoints
  * 52 authentication tests (model, service, router, security)
- **Phase 2 (Roadmap): Pre-Apprenticeship Training System**
  * 7 training models (Student, Course, ClassSession, Enrollment, Attendance, Grade, Certification)
  * ~35 API endpoints across 7 routers
  * Training seed data with 5 courses, 20 students
  * Student number auto-generation, attendance tracking, grade calculation
  * 33 new tests
- Phase 2 seed data for union operations (30 SALTing, 25 benevolence, 20 grievances)
- Documentation reorganization into docs/ folder
- Architecture Decision Records (ADRs)

### Changed
- Legacy Phase 0 tests archived to `archive/phase0_legacy/`
- Test count optimized: 144 tests (legacy tests archived)
- Downgraded bcrypt to 4.1.3 for passlib compatibility

### Fixed
- Test isolation issues resolved
- pytest.ini updated to exclude archive folder

## [0.2.0] - 2026-01-27

### Added
- Phase 1 Services Layer complete
- Organization, OrgContact, Member, MemberEmployment, AuditLog services
- 51 passing tests (35 Phase 1 + 16 Phase 0)
- Database management CLI (ip2adb)
- Stress testing system (10k members, 250k employments, 150k files)
- Integrity check system with auto-repair
- Load testing system (concurrent user simulation)
- Phase 2.1: Enhanced stress test and auto-healing system
- Auto-healing with admin notifications
- Long-term resilience checker
- Comprehensive audit logging (READ/CREATE/UPDATE/DELETE tracking)
- Production database optimizations (7 indexes)
- Scalability architecture documentation
- Phase 2: Union Operations
  * SALTing activities tracking
  * Benevolence fund management
  * Grievance system with arbitration steps
- File attachment reorganization with structured paths

### Changed
- Consolidated enums to src/db/enums/
- Updated documentation structure
- Organized file storage paths for better readability

### Fixed
- Circular import issues with enums
- Pre-commit hook configuration

## [0.1.1] - 2026-01-XX

### Fixed
- Stabilized src layout and project structure

## [0.1.0] - 2026-01-XX

### Added
- Initial backend stabilization
- PostgreSQL 16 database setup
- Docker development environment
- Base models and migrations
- SQLAlchemy ORM setup
- Alembic migrations framework
