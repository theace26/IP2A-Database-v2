# Changelog

All notable changes to IP2A-Database-v2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Phase 1.1: Authentication Database Schema**
  * User model with email/password authentication, optional Member link, soft delete
  * Role model for RBAC with system role protection
  * UserRole many-to-many junction with assignment metadata (assigned_by, expires_at)
  * RefreshToken model for JWT token management with rotation/revocation
  * Auth enums: RoleType (6 default roles), TokenType (4 token types)
  * Pydantic schemas for all auth models (Create/Update/Read variants)
  * Service layer: user_service, role_service, user_role_service with full CRUD
  * Role seed data with 6 default system roles (admin, officer, staff, organizer, instructor, member)
  * 16 new tests (98 total passing) - model tests + service tests
  * Member.user relationship backref (one user per member)
  * Database migration: e382f497c5e3 - replaces old simple user.role string with RBAC
  * Test fixture (db_session) added to conftest.py for direct model testing
  * Enhanced SoftDeleteMixin with soft_delete() method
  * Timezone-aware datetime handling in RefreshToken model
- Phase 2 seed data for union operations
  * Realistic test data for SALTing activities (30 records)
  * Benevolence applications with multi-level review workflow (25 applications, 47 reviews)
  * Grievances with step-by-step progression tracking (20 grievances, 31 step records)
  * Integrated with run_seed.py for complete database setup
  * Standalone execution: `python -m src.seed.phase2_seed`
- Documentation reorganization
- Architecture Decision Records (ADRs)
- Consolidated reference documentation
- Contribution guidelines

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
