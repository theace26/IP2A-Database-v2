# IP2A Database v2 - Project Strategy & Game Plan

**Document Created:** January 27, 2026
**Project Owner:** Xerxes (Union Business Rep, IBEW Local 46)
**Purpose:** Strategic roadmap for building a modular union data platform

---

## Executive Summary

This document outlines the strategy for building IP2A Database v2, a modular database platform that will:

1. **Immediately:** Serve as a pre-apprenticeship program management system
2. **Over time:** Expand to replace/supplement existing union management systems
3. **Long-term:** Potentially become a competitive alternative to commercial union software (LaborPower, UnionWare, etc.)

The approach is deliberately incremental—start small, prove value, expand methodically.

---

## Table of Contents

1. [Current State](#1-current-state)
2. [The Vision](#2-the-vision)
3. [Phase 1: Pre-Apprenticeship System](#3-phase-1-pre-apprenticeship-system)
4. [Phase 2+: Union Management Modules](#4-phase-2-union-management-modules)
5. [Existing Systems & Integration Strategy](#5-existing-systems--integration-strategy)
6. [Technical Architecture](#6-technical-architecture)
7. [Data Migration Strategy](#7-data-migration-strategy)
8. [Scaling Considerations](#8-scaling-considerations)
9. [Timeline & Milestones](#9-timeline--milestones)
10. [Key Decisions Made](#10-key-decisions-made)
11. [Open Questions](#11-open-questions)
12. [Reference Documents](#12-reference-documents)

---

## 1. Current State

### What's Been Built

The IP2A Database v2 project has a solid foundation:

| Component | Status | Notes |
|-----------|--------|-------|
| **Database Schema** | ✅ Complete | PostgreSQL 16, well-normalized |
| **Core Tables** | ✅ Complete | Members, Organizations, Students, Instructors, Locations, Cohorts |
| **File Attachments** | ✅ Complete | Document storage with metadata |
| **Audit Logging** | ✅ Complete | Full trail: READ, CREATE, UPDATE, DELETE |
| **Auto-Healing** | ✅ Complete | Self-repairing data integrity system |
| **CLI Tools** | ✅ Complete | `ip2adb` for seeding, integrity checks, load testing |
| **API Layer** | ✅ Partial | FastAPI backend, basic endpoints |
| **Authentication** | ❌ Not Started | JWT + roles needed |
| **Web UI** | ❌ Not Started | Required for staff/member access |
| **Payment Processing** | ❌ Not Started | Will integrate with Stripe/Square |

### Stress Test Results (Validates Scalability)

- **515,356 records** processed in 10.5 minutes
- **84 MB** database size
- **818 records/second** throughput
- **4,537 issues** auto-detected and repaired (100% success rate)
- **Capacity:** Proven to handle 500K+ records easily

### Repository & Technical Stack

- **Repository:** https://github.com/theace26/IP2A-Database-v2
- **Database:** PostgreSQL 16
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x
- **Environment:** Docker containers, VS Code Dev Containers
- **Current Version:** v0.2.0

---

## 2. The Vision

### The Problem

Currently operating with fragmented data across multiple systems:

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   LaborPower    │  │   LaborPower    │  │   Access DB     │  │   QuickBooks    │
│   (Referral/    │  │   (Dues         │  │   (Market       │  │   (Accounting)  │
│    Dispatch)    │  │    Collection)  │  │    Recovery)    │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
        │                    │                    │                    │
        └────────────────────┴────────────────────┴────────────────────┘
                                      │
                    No unified view, duplicate data entry,
                    manual reconciliation required
```

### The Solution

One modular database platform with pluggable modules:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IP2A DATABASE v2                                     │
│                      (Unified Data Platform)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │    CORE     │  │   PRE-APP   │  │    UNION    │  │  EXTERNAL   │        │
│   │   TABLES    │  │   MODULE    │  │   MODULES   │  │   SYNC      │        │
│   ├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤        │
│   │ Users       │  │ Grants      │  │ Dues        │  │ QuickBooks  │        │
│   │ Orgs        │  │ Students    │  │ Referrals   │  │ (export)    │        │
│   │ Audit Logs  │  │ Cohorts     │  │ Market Rec  │  │             │        │
│   │ Files       │  │ Certs       │  │ Grievances  │  │             │        │
│   │             │  │ Placements  │  │ Benevolence │  │             │        │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │                │                 │
│         └────────────────┴────────────────┴────────────────┘                 │
│                                 │                                            │
│                    Single source of truth                                    │
│                    Cross-module reporting                                    │
│                    Unified member journey                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Long-Term Potential

If the system proves successful:
1. Use internally at Local 46
2. Offer to other IBEW locals as alternative to LaborPower
3. Potentially commercialize as competing union management platform

---

## 3. Phase 1: Pre-Apprenticeship System

### Why Start Here

| Reason | Explanation |
|--------|-------------|
| **Contained scope** | Clear boundaries, limited users |
| **Lower stakes** | Won't break existing union operations if issues arise |
| **Real need** | Grant reporting is painful without proper tracking |
| **Proves concept** | Success here validates the approach |
| **Foundation** | Students become members—data follows them |

### Features Required

#### Student Management
- Application/intake tracking
- Demographics (required for grant reporting)
- Contact information
- Eligibility verification
- Status tracking (APPLICANT → ENROLLED → ACTIVE → COMPLETED → PLACED)

#### Grant Management
- Grant sources (DOL, state, foundation, etc.)
- Funding amounts and periods
- Reporting requirements and deadlines
- Per-student cost tracking
- Enrollment caps

#### Cohort Management
- Class/session groupings
- Instructor assignments
- Location assignments
- Schedule tracking
- Capacity management

#### Progress Tracking
- Curriculum completion
- Attendance tracking
- Assessment scores
- Competency sign-offs

#### Certification Tracking
- OSHA 10/30
- First Aid/CPR
- Forklift
- Other industry certifications
- Expiration tracking and alerts

#### Placement Tracking
- Apprenticeship applications
- Acceptance/rejection tracking
- Employer placement
- Follow-up surveys (30/60/90 day)

#### Reporting (Critical for Grants)
- Demographics breakdown
- Completion rates
- Certification attainment
- Placement rates
- Cost per student
- Custom date range filtering
- Export to Excel/PDF

### Schema Additions for Phase 1

```sql
-- Grant Management
CREATE TABLE grants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    source VARCHAR(100),  -- DOL, State, Foundation, etc.
    grant_number VARCHAR(50),
    total_amount DECIMAL(12,2),
    start_date DATE,
    end_date DATE,
    reporting_frequency VARCHAR(20),  -- MONTHLY, QUARTERLY, ANNUALLY
    max_students INTEGER,
    cost_per_student DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Link students to grants
CREATE TABLE grant_enrollments (
    id SERIAL PRIMARY KEY,
    grant_id INTEGER REFERENCES grants(id),
    student_id INTEGER REFERENCES students(id),
    enrolled_date DATE,
    funding_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    notes TEXT,
    UNIQUE(grant_id, student_id)
);

-- Student Progress Tracking
CREATE TABLE student_progress (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    cohort_id INTEGER REFERENCES cohorts(id),
    enrollment_date DATE,
    expected_completion DATE,
    actual_completion DATE,
    status VARCHAR(30),  -- ENROLLED, ACTIVE, ON_HOLD, COMPLETED, DROPPED
    attendance_percentage DECIMAL(5,2),
    grade_average DECIMAL(5,2),
    notes TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Certifications
CREATE TABLE certifications (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    issuing_body VARCHAR(100),
    validity_period_months INTEGER,  -- NULL if doesn't expire
    is_required BOOLEAN DEFAULT FALSE,
    description TEXT
);

CREATE TABLE student_certifications (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    certification_id INTEGER REFERENCES certifications(id),
    earned_date DATE,
    expiration_date DATE,
    certificate_number VARCHAR(50),
    file_attachment_id INTEGER REFERENCES file_attachments(id),
    verified_by VARCHAR(100),
    verified_date DATE,
    UNIQUE(student_id, certification_id, earned_date)
);

-- Placements
CREATE TABLE placements (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    employer_id INTEGER REFERENCES organizations(id),
    placement_type VARCHAR(30),  -- APPRENTICESHIP, DIRECT_HIRE, CONTINUING_ED
    application_date DATE,
    start_date DATE,
    starting_wage DECIMAL(8,2),
    status VARCHAR(20),  -- APPLIED, ACCEPTED, DECLINED, STARTED, RETAINED
    followup_30_day DATE,
    followup_60_day DATE,
    followup_90_day DATE,
    still_employed_30 BOOLEAN,
    still_employed_60 BOOLEAN,
    still_employed_90 BOOLEAN,
    notes TEXT
);

-- Attendance (simple version)
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    cohort_id INTEGER REFERENCES cohorts(id),
    class_date DATE,
    status VARCHAR(20),  -- PRESENT, ABSENT, EXCUSED, TARDY
    notes TEXT,
    UNIQUE(student_id, cohort_id, class_date)
);
```

### Phase 1 Timeline

| Month | Focus | Deliverable |
|-------|-------|-------------|
| **1** | Schema + Auth | Grants table, JWT authentication, basic roles |
| **2** | Core tracking | Student progress, cohort enrollment, attendance |
| **3** | Certifications | Cert tracking, expiration alerts |
| **4** | Basic UI | Staff can enter/view data via web interface |
| **5** | Reporting | Grant reports, demographics, placements |
| **6** | Polish + Deploy | Production deployment, training materials |

---

## 4. Phase 2+: Union Management Modules

These modules will be added after Phase 1 is stable and proven:

### Module: Members (Foundation for Everything)

Extends the current `members` table to become the single source of truth.

**Key addition:** Link students to members when they graduate to apprenticeship:
```sql
ALTER TABLE members ADD COLUMN former_student_id INTEGER REFERENCES students(id);
```

### Module: Dues Collection

```sql
CREATE TABLE dues_rates (
    id SERIAL PRIMARY KEY,
    classification VARCHAR(50),  -- JOURNEYMAN, APPRENTICE, RETIRED
    effective_date DATE,
    monthly_amount DECIMAL(8,2),
    io_per_capita DECIMAL(8,2),  -- International Office portion
    local_portion DECIMAL(8,2),
    building_fund DECIMAL(8,2),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE dues_payments (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    payment_date TIMESTAMP,
    amount DECIMAL(10,2),
    period_start DATE,  -- What period this covers
    period_end DATE,
    payment_method VARCHAR(20),  -- CHECK, CASH, PAYROLL_DEDUCT, ONLINE
    reference_number VARCHAR(50),
    stripe_payment_id VARCHAR(100),  -- For online payments
    quickbooks_sync_id VARCHAR(100),
    status VARCHAR(20),  -- PENDING, COMPLETED, FAILED, REFUNDED
    notes TEXT
);
```

**Payment Processing Strategy:**
- Integrate with Stripe or Square (don't build payment processing)
- They handle PCI compliance, fraud, disputes
- We generate payment links, receive webhooks when paid
- Record transaction in our system, sync to QuickBooks

### Module: Referral/Dispatch

```sql
CREATE TABLE out_of_work_list (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    sign_in_date TIMESTAMP,
    book_number INTEGER,  -- Book 1, Book 2, etc.
    classification VARCHAR(50),
    position_on_list INTEGER,
    status VARCHAR(20),  -- ACTIVE, REFERRED, REMOVED, EXPIRED
    removed_date TIMESTAMP,
    removed_reason VARCHAR(100)
);

CREATE TABLE referrals (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    employer_id INTEGER REFERENCES organizations(id),
    dispatch_date TIMESTAMP,
    job_type VARCHAR(30),  -- SHORT_CALL, LONG_CALL, EMERGENCY
    job_location TEXT,
    foreman VARCHAR(100),
    expected_duration VARCHAR(50),
    status VARCHAR(20),  -- DISPATCHED, WORKING, COMPLETED, QUIT, TERMINATED
    start_date DATE,
    end_date DATE,
    termination_reason TEXT,
    hours_worked DECIMAL(10,2),
    notes TEXT
);
```

### Module: Market Recovery

Replaces the Access database:

```sql
CREATE TABLE market_recovery_programs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    effective_date DATE,
    end_date DATE,
    subsidy_rate DECIMAL(8,2),  -- Per hour subsidy
    max_hours_per_member INTEGER,
    total_budget DECIMAL(12,2),
    funding_source TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT
);

CREATE TABLE market_recovery_assignments (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    employer_id INTEGER REFERENCES organizations(id),
    program_id INTEGER REFERENCES market_recovery_programs(id),
    project_name VARCHAR(200),
    project_address TEXT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20),  -- ACTIVE, COMPLETED, TERMINATED
    notes TEXT
);

CREATE TABLE market_recovery_hours (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER REFERENCES market_recovery_assignments(id),
    week_ending DATE,
    hours_worked DECIMAL(6,2),
    regular_rate DECIMAL(8,2),
    subsidy_amount DECIMAL(10,2),  -- Calculated: hours × subsidy_rate
    submitted_by INTEGER REFERENCES users(id),
    submitted_date TIMESTAMP,
    approved_by INTEGER REFERENCES users(id),
    approved_date TIMESTAMP,
    status VARCHAR(20),  -- SUBMITTED, APPROVED, REJECTED, PAID
    quickbooks_sync_id VARCHAR(100),
    notes TEXT
);
```

### Module: Grievances

```sql
CREATE TABLE grievances (
    id SERIAL PRIMARY KEY,
    grievance_number VARCHAR(20) UNIQUE,
    member_id INTEGER REFERENCES members(id),
    employer_id INTEGER REFERENCES organizations(id),
    filed_date DATE,
    incident_date DATE,
    contract_article VARCHAR(50),
    violation_description TEXT,
    remedy_sought TEXT,
    current_step VARCHAR(30),  -- STEP_1, STEP_2, STEP_3, ARBITRATION
    status VARCHAR(20),  -- OPEN, SETTLED, WITHDRAWN, ARBITRATION, CLOSED
    assigned_rep INTEGER REFERENCES users(id),
    resolution TEXT,
    resolution_date DATE,
    settlement_amount DECIMAL(10,2),
    notes TEXT
);

CREATE TABLE grievance_steps (
    id SERIAL PRIMARY KEY,
    grievance_id INTEGER REFERENCES grievances(id),
    step_number INTEGER,
    meeting_date DATE,
    union_attendees TEXT,
    employer_attendees TEXT,
    outcome VARCHAR(20),  -- DENIED, SETTLED, ADVANCED
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Module: Benevolence Fund

```sql
CREATE TABLE benevolence_applications (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    application_date DATE,
    reason VARCHAR(50),  -- MEDICAL, DEATH_IN_FAMILY, HARDSHIP, DISASTER
    description TEXT,
    amount_requested DECIMAL(10,2),
    supporting_documents TEXT,  -- File attachment IDs
    status VARCHAR(20),  -- SUBMITTED, UNDER_REVIEW, APPROVED, DENIED, PAID
    approved_amount DECIMAL(10,2),
    approved_by INTEGER REFERENCES users(id),
    approved_date DATE,
    payment_date DATE,
    payment_method VARCHAR(20),
    quickbooks_sync_id VARCHAR(100),
    notes TEXT
);
```

---

## 5. Existing Systems & Integration Strategy

### Current Systems Inventory

| System | Purpose | Data Volume | Integration Plan |
|--------|---------|-------------|------------------|
| **LaborPower (Referral)** | Dispatch, job calls | ~10K members | Phase 2: Import historical, parallel run |
| **LaborPower (Dues)** | Payment collection | ~10K members | Phase 2+: Import historical, may replace |
| **Access DB** | Market Recovery | Unknown | Phase 2: Replace entirely |
| **QuickBooks** | Accounting | All financials | Ongoing sync (export/import) |

### Integration Strategy

#### LaborPower
- **Short-term:** Export data periodically for unified reporting
- **Medium-term:** One-time import of historical data
- **Long-term:** Run parallel, eventually migrate fully

**Export approach:** LaborPower is Windows desktop software. Likely options:
1. Built-in report export to CSV/Excel
2. Direct database access (SQL Server)
3. Contact Working Systems for data export assistance

#### Access Database
- **Strategy:** Full replacement
- **Process:** 
  1. Export all tables to CSV
  2. Map fields to new schema
  3. Import historical data
  4. Retire Access DB

#### QuickBooks
- **Strategy:** Sync, not replace
- **Direction:** 
  - IP2A → QuickBooks (dues income, MR expenses, benevolence)
  - QuickBooks → IP2A (payment cleared status)
- **Method:** CSV export/import initially, API integration later

### Data Migration Workflow

```
┌─────────────────┐
│  Source System  │
│  (LP/Access/QB) │
└────────┬────────┘
         │
         ▼ Export (CSV/Excel)
┌─────────────────┐
│  Raw Export     │
│  Files          │
└────────┬────────┘
         │
         ▼ Transform (Python script)
┌─────────────────┐
│  Cleaned &      │
│  Mapped Data    │
└────────┬────────┘
         │
         ▼ Validate (ip2adb import --preview)
┌─────────────────┐
│  Preview        │
│  Report         │
└────────┬────────┘
         │
         ▼ Import (ip2adb import --execute)
┌─────────────────┐
│  IP2A Database  │
└─────────────────┘
```

---

## 6. Technical Architecture

### Current Stack
- **Database:** PostgreSQL 16
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x (sync)
- **Container:** Docker, Docker Compose
- **Development:** VS Code Dev Containers

### Planned Additions
- **Authentication:** JWT tokens, role-based access control
- **Frontend:** TBD (React, Vue, or simple HTML/Jinja templates)
- **Payment Processing:** Stripe or Square integration
- **File Storage:** Local initially, S3 for production
- **Caching:** Redis (when needed, not immediately)

### Modular Architecture Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER                                 │
│   /api/v1/students    /api/v1/members    /api/v1/dues   ...     │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
│   student_service    member_service    dues_service    ...      │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│   Student model      Member model      DuesPayment model  ...   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   SHARED INFRASTRUCTURE                          │
│   Audit Logging    Auth/RBAC    File Storage    Notifications   │
└─────────────────────────────────────────────────────────────────┘
```

**Key principles:**
1. **Loose coupling:** Modules don't directly depend on each other
2. **Shared core:** Users, organizations, audit logs used by all
3. **Consistent patterns:** Every module follows same CRUD/API patterns
4. **Feature flags:** Modules can be enabled/disabled per installation

---

## 7. Data Migration Strategy

### Phase 1: Pre-Apprenticeship
- Likely manual entry or spreadsheet import
- Small volume, can be done by hand if needed

### Phase 2: LaborPower Import

**Data to import:**
| Table | Source | Est. Records | Priority |
|-------|--------|--------------|----------|
| Members | LaborPower | ~10,000 | Critical |
| Employers | LaborPower | ~500-700 | Critical |
| Employment history | LaborPower | ~50,000+ | High |
| Dues payments | LaborPower Dues | ~100,000+ | High |
| Referrals | LaborPower Referral | ~20,000+ | Medium |

**Import CLI design:**
```bash
# Preview import (no changes)
ip2adb import members --source laborpower --file members.csv --preview

# Execute import
ip2adb import members --source laborpower --file members.csv --execute

# Import with field mapping file
ip2adb import employers --source laborpower --file employers.csv --mapping employer_map.json

# Validate imported data
ip2adb integrity --tables members,organizations
```

### Phase 2: Access DB Import

**Process:**
1. Open Access database
2. Export each table to CSV
3. Map fields to IP2A schema
4. Import via CLI

---

## 8. Scaling Considerations

### Current Capacity
- **Tested:** 50 concurrent users
- **Proven data volume:** 500,000+ records

### When to Scale (Not Now)
Scaling infrastructure should be added when you see:
- Connection pool exhaustion errors
- Response times > 500ms under normal load
- Database CPU consistently > 70%

### Scaling Path (For Reference)

| Phase | Trigger | Solution | Capacity |
|-------|---------|----------|----------|
| Current | N/A | Single PostgreSQL | ~50 users |
| Scale 1 | Connection errors | Add PgBouncer | ~500 users |
| Scale 2 | Read bottleneck | Add read replicas | ~2,000 users |
| Scale 3 | Repeated queries | Add Redis cache | ~5,000 users |
| Scale 4 | CPU bottleneck | Multiple API servers | ~10,000+ users |

**Key point:** Don't implement scaling until needed. Build features first.

---

## 9. Timeline & Milestones

### Year 1 Roadmap

```
Q1 2026: Pre-Apprenticeship Foundation
├── Month 1: Auth + Grants schema
├── Month 2: Student progress tracking
└── Month 3: Certifications + basic UI

Q2 2026: Pre-Apprenticeship Complete
├── Month 4: Reporting + dashboards
├── Month 5: Polish + testing
└── Month 6: Production deployment

Q3 2026: Begin Union Modules
├── Month 7: Member import from LaborPower
├── Month 8: Market Recovery module (replace Access)
└── Month 9: Market Recovery UI + testing

Q4 2026: Expand Union Functionality
├── Month 10: Dues tracking (import history)
├── Month 11: Payment integration (Stripe)
└── Month 12: Member self-service portal
```

### Key Milestones

| Milestone | Target Date | Success Criteria |
|-----------|-------------|------------------|
| **Auth working** | Month 1 | Staff can log in with roles |
| **First grant tracked** | Month 2 | Complete grant + students in system |
| **First report generated** | Month 5 | Push-button grant report |
| **Pre-app in production** | Month 6 | Staff using daily for real cohort |
| **Access DB retired** | Month 9 | Market Recovery fully in IP2A |
| **Member portal live** | Month 12 | Members can view own records |

---

## 10. Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Start with pre-apprenticeship** | Yes | Lower stakes, proves concept, clear scope |
| **Combine LP + Access into one DB** | Yes | Single source of truth, unified reporting |
| **Keep QuickBooks separate** | Yes | Don't rebuild accounting, just sync |
| **Integrate payments, don't build** | Stripe/Square | PCI compliance handled by experts |
| **Build modular architecture** | Yes | Add features without breaking existing |
| **Scale later, features first** | Yes | Current capacity sufficient for months |
| **Web-based UI** | Yes | Accessible from anywhere, modern approach |

---

## 11. Open Questions

### Technical Questions
- [ ] What frontend framework? (React, Vue, or server-rendered templates)
- [ ] Self-hosted or cloud deployment?
- [ ] Backup strategy for production?

### Data Questions
- [ ] What format can LaborPower export? (CSV, direct DB access?)
- [ ] What tables exist in the Access database?
- [ ] Which QuickBooks version? (Desktop or Online)

### Business Questions
- [ ] Who are the primary users for pre-apprenticeship system?
- [ ] What grants are currently being tracked?
- [ ] What reports are required for funders?
- [ ] What's the approval workflow for Market Recovery hours?

### To Investigate
- [ ] Get sample exports from LaborPower (column headers only)
- [ ] Get table/field list from Access database
- [ ] Document current grant reporting requirements
- [ ] Identify pain points in current Market Recovery workflow

---

## 12. Reference Documents

### In This Repository

| Document | Location | Purpose |
|----------|----------|---------|
| **CLAUDE.md** | `/CLAUDE.md` | Project context for AI assistance |
| **CONTINUITY.md** | `/CONTINUITY.md` | Handoff procedures |
| **Scaling Assessment** | `/Documentation/Reports/SCALING_READINESS_ASSESSMENT.md` | Production readiness analysis |
| **Scalability Architecture** | `/Documentation/Architecture/SCALABILITY_ARCHITECTURE.md` | Full scaling plan |
| **Stress Test Report** | `/Documentation/Reports/STRESS_TEST_ANALYTICS_REPORT.md` | Performance benchmarks |
| **Audit Logging Standards** | `/Documentation/Standards/AUDIT_LOGGING_STANDARDS.md` | Compliance requirements |
| **Database Tools** | `/DATABASE_TOOLS_OVERVIEW.md` | CLI tool documentation |

### Key Commands

```bash
# Development
docker-compose up -d
./ip2adb seed --quick        # Populate test data
./ip2adb integrity           # Check data integrity
./ip2adb auto-heal           # Fix issues automatically

# Testing
./ip2adb load --quick        # Quick performance test
./ip2adb seed --stress       # Large-scale test (500K records)
```

---

## Summary

**The Plan:**
1. Build pre-apprenticeship system first (6 months)
2. Prove it works with real users
3. Expand to union modules (Market Recovery first)
4. Eventually run parallel to or replace LaborPower
5. Potentially commercialize for other locals

**The Approach:**
- Modular architecture—add features without breaking existing
- Start small, validate, expand
- Keep QuickBooks for accounting, sync data
- Integrate payment processing, don't build it

**The Reality:**
- This is a 12-18 month project at part-time pace
- Phase 1 (pre-apprenticeship) achievable in 6 months
- Each module after that: 2-3 months

**Next Steps:**
1. Get sample data exports from LaborPower and Access
2. Document current grant reporting requirements
3. Build authentication system
4. Create grants schema and import tools

---

*Document Version: 1.0*
*Last Updated: January 27, 2026*
*Status: Strategic Planning Complete, Ready for Implementation*
