# Changelog

All notable changes to IP2A-Database-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
