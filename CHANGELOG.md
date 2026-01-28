# Changelog

All notable changes to IP2A-Database-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Phase 6 Week 1: Frontend Foundation** (In Progress)
  * Base templates with DaisyUI + Tailwind CSS + HTMX + Alpine.js (CDN)
  * Login page with HTMX form submission
  * Dashboard placeholder with stats cards
  * Responsive sidebar navigation with drawer component
  * Component templates (navbar, sidebar, flash messages, modal)
  * Custom CSS and JavaScript
  * Error pages (404, 500)
  * Frontend router for HTML page serving

### Changed
- Updated CLAUDE.md with frontend phase context
- Created docs/instructions/ for Claude Code instruction documents

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
