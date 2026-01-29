# Changelog

All notable changes to IP2A-Database-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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

### Changed
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
