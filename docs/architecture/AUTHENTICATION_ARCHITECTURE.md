# Authentication & Authorization Architecture
## IP2A Database v2 - Security Foundation

**Document Created:** January 27, 2026
**Last Updated:** February 3, 2026
**Status:** ✅ IMPLEMENTED — Core auth operational since Week 1, Stripe auth added Week 11, security hardening Week 16
**Priority:** CRITICAL - Foundation for all other features

---

## Implementation Status

> **This document was originally written as a pre-implementation specification (v1.0, January 27, 2026).**
> As of v0.9.4-alpha (February 2026), the authentication system is **fully implemented and production-deployed on Railway**. Code examples below reflect the architectural design; actual implementation may differ in minor details. Always reference the source code as the single source of truth.

| Component | Status | Week Implemented |
|-----------|--------|------------------|
| JWT access + refresh tokens | ✅ Implemented | Week 1 |
| HTTP-only cookie auth for frontend | ✅ Implemented | Week 1 |
| Role-based access control (RBAC) | ✅ Implemented | Week 1 |
| Account lockout (`locked_until` datetime) | ✅ Implemented | Week 1 |
| Login/logout/register endpoints | ✅ Implemented | Week 1 |
| Password hashing (bcrypt) | ✅ Implemented | Week 1 |
| Stripe payment auth integration | ✅ Implemented | Week 11 |
| Security headers (CSP, HSTS, etc.) | ✅ Implemented | Week 16 |
| Sentry error tracking | ✅ Implemented | Week 16 |
| Structured logging | ✅ Implemented | Week 16 |
| Connection pooling | ✅ Implemented | Week 16 |
| MFA (TOTP) | 🔜 Future | — |
| Email verification flow | 🔜 Future | — |
| Password reset via email | 🔜 Future | — |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Why Auth First](#2-why-auth-first)
3. [User Types & Roles](#3-user-types--roles)
4. [Database Schema](#4-database-schema)
5. [Password Security](#5-password-security)
6. [JWT Implementation](#6-jwt-implementation)
7. [API Endpoints](#7-api-endpoints)
8. [Middleware & Dependencies](#8-middleware--dependencies)
9. [Role-Based Access Control (RBAC)](#9-role-based-access-control-rbac)
10. [User Registration Flows](#10-user-registration-flows)
11. [Session Management](#11-session-management)
12. [Security Hardening](#12-security-hardening)
13. [Integration Patterns](#13-integration-patterns)
14. [Configuration](#14-configuration)
15. [Testing Auth](#15-testing-auth)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Executive Summary

This document defines the authentication and authorization architecture for IP2A Database v2. Authentication is the **foundation** that all other features depend on.

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth method | **JWT (JSON Web Tokens)** | Stateless, scalable, industry standard |
| Password hashing | **bcrypt** | Battle-tested, adaptive cost factor |
| Token storage | **HTTP-only cookies** | Secure for browser sessions (Jinja2 frontend) |
| Session strategy | **Short-lived access + refresh tokens** | Balance security and UX |
| RBAC model | **Role-based with permissions** | Flexible, auditable |
| MFA | **Optional (Future)** | TOTP for sensitive roles |

### User Populations

| User Type | Count | Access Level |
|-----------|-------|--------------|
| Admin | 1-2 | Full system access |
| Officers | 5-10 | Approvals, all reports |
| Staff | 15-20 | Daily operations |
| Organizers | 5-10 | SALTing data only |
| Members | ~4,000 | Self-service only |
| Applicants | ~100 | Pre-app application only |

---

## 2. Why Auth First

Every feature depends on knowing WHO is making the request:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FEATURES THAT DEPEND ON AUTH                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│   │   Audit     │     │    File     │     │    Dues     │                   │
│   │   Logging   │     │   Storage   │     │  Payments   │                   │
│   ├─────────────┤     ├─────────────┤     ├─────────────┤                   │
│   │ changed_by  │     │ uploaded_by │     │ paid_by     │                   │
│   │ = user_id   │     │ = user_id   │     │ = member_id │                   │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                   │
│          │                   │                   │                          │
│          └───────────────────┼───────────────────┘                          │
│                              │                                               │
│                              ▼                                               │
│                    ┌─────────────────┐                                       │
│                    │ AUTHENTICATION  │                                       │
│                    │   (This Doc)    │                                       │
│                    └─────────────────┘                                       │
│                              │                                               │
│          ┌───────────────────┼───────────────────┐                          │
│          │                   │                   │                          │
│   ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐                   │
│   │  Grievance  │     │   Stripe    │     │   Reports   │                   │
│   │  Workflow   │     │  Payments   │     │   Access    │                   │
│   ├─────────────┤     ├─────────────┤     ├─────────────┤                   │
│   │ filed_by    │     │ checkout    │     │ run_by      │                   │
│   │ assigned_to │     │ session_id  │     │ role_check  │                   │
│   └─────────────┘     └─────────────┘     └─────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Without Auth vs. With Auth

| Scenario | Without Auth | With Auth |
|----------|--------------|-----------|
| Audit log entry | "Someone changed member address" | "jsmith@local46.org changed member address" |
| File download | Anyone can access | Only staff or the member themselves |
| Grievance approval | Anyone clicks approve | Only officers can approve |
| Dues payment | No idea who paid | Member #12345 paid via Stripe checkout |
| Report access | All reports public | Financial reports officer-only |

---

## 3. User Types & Roles

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ROLE HIERARCHY                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                              ┌─────────┐                                     │
│                              │  ADMIN  │                                     │
│                              │  (1-2)  │                                     │
│                              └────┬────┘                                     │
│                                   │ Full access                              │
│                                   │ User management                          │
│                                   │ System config                            │
│                                   ▼                                          │
│                              ┌─────────┐                                     │
│                              │ OFFICER │                                     │
│                              │ (5-10)  │                                     │
│                              └────┬────┘                                     │
│                                   │ Approve grievances                       │
│                                   │ Approve benevolence                      │
│                                   │ All reports                              │
│                    ┌──────────────┼──────────────┐                          │
│                    │              │              │                          │
│                    ▼              ▼              ▼                          │
│              ┌─────────┐   ┌───────────┐   ┌───────────┐                    │
│              │  STAFF  │   │ ORGANIZER │   │INSTRUCTOR │                    │
│              │ (15-20) │   │   (5-10)  │   │   (var)   │                    │
│              └────┬────┘   └─────┬─────┘   └─────┬─────┘                    │
│                   │              │               │                          │
│                   │              │               │ Pre-app only             │
│                   │              │               │ Student grades           │
│                   │              │               │ Attendance               │
│                   │              │                                          │
│                   │              │ SALTing only                             │
│                   │              │ Organizing campaigns                     │
│                   │              │ Target employer data                     │
│                   │                                                         │
│                   │ Member CRUD                                             │
│                   │ Dues processing                                         │
│                   │ Referral dispatch                                       │
│                   │ Standard reports                                        │
│                   │                                                         │
│                   ▼                                                         │
│    ┌──────────────────────────────────────────────┐                        │
│    │              EXTERNAL USERS                   │                        │
│    ├──────────────────────┬───────────────────────┤                        │
│    │       MEMBER         │      APPLICANT        │                        │
│    │      (~4,000)        │       (~100)          │                        │
│    ├──────────────────────┼───────────────────────┤                        │
│    │ • View own profile   │ • View application    │                        │
│    │ • Update contact     │ • Submit documents    │                        │
│    │ • Pay dues online    │ • Check status        │                        │
│    │ • View certifications│                       │                        │
│    │ • View referral hist │                       │                        │
│    └──────────────────────┴───────────────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Role Definitions

| Role | Description | Typical Users | Key Permissions |
|------|-------------|---------------|-----------------|
| `admin` | System administrators | IT staff, DB admin | Everything, user management |
| `officer` | Elected union officers | President, VP, Bus. Mgr | Approvals, sensitive reports |
| `staff` | Office employees | Dispatchers, clerical | Daily operations CRUD |
| `organizer` | Field organizers | Organizers, salts | SALTing module only |
| `instructor` | Pre-app instructors | Teachers | Student records only |
| `member` | Union members | Journeymen, apprentices | Self-service only |
| `applicant` | Pre-app applicants | Students applying | Application only |

### Permission Matrix

```
Permission Key Format: {resource}:{action}

Resources: members, students, organizations, grievances, dues, referrals,
           organizing, benevolence, grants, reports, users, files, system

Actions: create, read, update, delete, approve, export, manage, *
```

| Permission | Admin | Officer | Staff | Organizer | Instructor | Member | Applicant |
|------------|:-----:|:-------:|:-----:|:---------:|:----------:|:------:|:---------:|
| `members:read` | ✅ | ✅ | ✅ | ✅ | ❌ | self | ❌ |
| `members:write` | ✅ | ✅ | ✅ | ❌ | ❌ | self | ❌ |
| `students:*` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | self |
| `organizing:*` | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `grievances:read` | ✅ | ✅ | ✅ | ❌ | ❌ | self | ❌ |
| `grievances:approve` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `benevolence:approve` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `dues:process` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `dues:pay` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| `referrals:dispatch` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `reports:financial` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `reports:standard` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `users:manage` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `system:config` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 4. Database Schema

### Core Tables

> **⚠️ CRITICAL NOTE:** The actual implementation uses `locked_until` as a **datetime field** for account lockout. The User model does NOT use a boolean `is_locked` flag. Lockout is determined by checking whether `locked_until` is set and is in the future. The SQL below reflects the **design intent**; always reference `src/models/user.py` for the actual schema.

```sql
-- ============================================================================
-- USERS TABLE
-- Anyone who can log into the system
-- ============================================================================
CREATE TABLE users (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Login credentials
    email VARCHAR(255) NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP,

    -- Password (hashed with bcrypt)
    password_hash VARCHAR(255) NOT NULL,
    password_changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,

    -- Profile information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),

    -- Link to member record (NULL if not a union member)
    member_id INTEGER REFERENCES members(id) ON DELETE SET NULL,

    -- Link to student record (NULL if not a pre-app student)
    student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,

    -- Link to instructor record (NULL if not an instructor)
    instructor_id INTEGER REFERENCES instructors(id) ON DELETE SET NULL,

    -- Account status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Account lockout (datetime-based, NOT boolean)
    -- Account is locked if locked_until IS NOT NULL AND locked_until > NOW()
    locked_until TIMESTAMP,
    locked_reason TEXT,

    -- Security tracking
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    last_failed_login TIMESTAMP,
    last_login TIMESTAMP,
    last_login_ip VARCHAR(45),

    -- Multi-factor authentication (Future)
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    mfa_backup_codes JSONB,

    -- Preferences
    preferences JSONB DEFAULT '{}',
    timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    -- Constraints
    CONSTRAINT unique_email UNIQUE (email),
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_member ON users(member_id) WHERE member_id IS NOT NULL;
CREATE INDEX idx_users_student ON users(student_id) WHERE student_id IS NOT NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;


-- ============================================================================
-- ROLES TABLE
-- Define available roles in the system
-- ============================================================================
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,

    -- Role identification
    name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Role level (for hierarchy - higher = more access)
    level INTEGER NOT NULL DEFAULT 0,

    -- Permissions as JSONB array
    -- e.g., ["members:read", "members:write", "reports:*"]
    permissions JSONB NOT NULL DEFAULT '[]',

    -- Is this a system role that can't be deleted?
    is_system BOOLEAN NOT NULL DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_role_name UNIQUE (name)
);


-- ============================================================================
-- USER_ROLES TABLE
-- Junction table for user-role assignments (many-to-many)
-- Uses Association Object pattern in SQLAlchemy for extra fields
-- ============================================================================
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,

    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,

    -- Who granted this role and when
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Optional expiration (for temporary roles)
    expires_at TIMESTAMP,

    -- Notes (why this role was granted)
    notes TEXT,

    -- Prevent duplicate assignments
    CONSTRAINT unique_user_role UNIQUE (user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);


-- ============================================================================
-- REFRESH_TOKENS TABLE
-- Store refresh tokens for session management
-- ============================================================================
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Token hash (never store raw token)
    token_hash VARCHAR(255) NOT NULL,

    -- Token metadata
    device_info VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),

    -- Lifecycle
    issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    revoked_reason TEXT,

    -- Was this token used to get a new access token?
    last_used_at TIMESTAMP,

    CONSTRAINT unique_token_hash UNIQUE (token_hash)
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at)
    WHERE revoked_at IS NULL;
```

### Seed Default Roles

```sql
-- Insert system roles
INSERT INTO roles (name, display_name, description, level, permissions, is_system) VALUES

-- Admin: Full system access
('admin', 'Administrator', 'Full system access including user management and configuration', 100,
 '["*"]'::jsonb, TRUE),

-- Officer: Elected union officers
('officer', 'Union Officer', 'Elected officers with approval authority', 80,
 '["members:*", "students:*", "organizations:*", "grievances:*", "benevolence:*",
   "dues:*", "referrals:*", "grants:*", "reports:*", "files:*"]'::jsonb, TRUE),

-- Staff: Office employees
('staff', 'Office Staff', 'Office staff handling daily operations', 60,
 '["members:*", "students:*", "organizations:read", "organizations:update",
   "grievances:read", "grievances:create", "grievances:update",
   "benevolence:read", "benevolence:create",
   "dues:*", "referrals:*", "grants:read", "reports:standard", "files:*"]'::jsonb, TRUE),

-- Organizer: Field organizers (SALTing)
('organizer', 'Organizer', 'Field organizers with access to organizing campaigns', 50,
 '["organizing:*", "members:read", "organizations:read", "files:read", "files:create"]'::jsonb, TRUE),

-- Instructor: Pre-apprenticeship instructors
('instructor', 'Instructor', 'Pre-apprenticeship program instructors', 40,
 '["students:*", "cohorts:read", "files:read", "files:create"]'::jsonb, TRUE),

-- Member: Union members (self-service)
('member', 'Union Member', 'Union members with self-service access', 20,
 '["self:*", "dues:pay"]'::jsonb, TRUE),

-- Applicant: Pre-apprenticeship applicants
('applicant', 'Applicant', 'Pre-apprenticeship program applicants', 10,
 '["self:read", "self:update", "application:*"]'::jsonb, TRUE);
```

---

## 5. Password Security

### Password Requirements

```python
# src/auth/password_policy.py
"""
Password policy configuration and validation.
"""

from dataclasses import dataclass
from typing import List, Tuple
import re


@dataclass
class PasswordPolicy:
    """Password requirements configuration."""

    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    special_characters: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Password history
    prevent_reuse_count: int = 12  # Can't reuse last 12 passwords

    # Expiration (0 = never expires)
    max_age_days: int = 0  # Modern guidance says don't force rotation

    # Lockout policy
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30
```

### Password Hashing

```python
# src/auth/password.py
"""
Password hashing and verification using bcrypt.
Cost factor 12 (~250ms per hash — good balance of security and speed).
"""

import bcrypt

BCRYPT_COST = 12

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_COST)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False

def needs_rehash(password_hash: str) -> bool:
    """Check if password hash needs cost factor upgrade (call after successful login)."""
    try:
        parts = password_hash.split('$')
        if len(parts) >= 3:
            current_cost = int(parts[2])
            return current_cost < BCRYPT_COST
    except Exception:
        pass
    return False
```

---

## 6. JWT Implementation

### Token Structure

```python
# Access Token Payload (short-lived: 15 minutes - 1 hour)
{
    "sub": "550e8400-e29b-41d4-a716-446655440000",  # User ID
    "iat": 1706400000,                               # Issued at
    "exp": 1706403600,                               # Expires at
    "jti": "unique-token-id",                        # Token ID

    "email": "jsmith@local46.org",
    "name": "John Smith",
    "roles": ["staff", "organizer"],
    "permissions": ["members:*", "organizing:*"],

    "member_id": 12345,
    "student_id": null,
    "instructor_id": null,

    "type": "access"
}

# Refresh Token Payload (long-lived: 7-30 days)
{
    "sub": "550e8400-e29b-41d4-a716-446655440000",
    "iat": 1706400000,
    "exp": 1707004800,
    "jti": "refresh-token-id",
    "type": "refresh"
}
```

### Frontend Auth Pattern

The Jinja2 frontend uses **HTTP-only cookies** for both access and refresh tokens. This means:
- Tokens are never exposed to JavaScript (XSS-safe)
- The `auth_middleware.py` extracts tokens from cookies on every request
- HTMX requests automatically include cookies (no manual header management)
- Logout clears cookies server-side

```python
# Setting cookie on login
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,      # HTTPS only
    samesite="lax",   # CSRF protection
    max_age=30 * 24 * 60 * 60  # 30 days if remember_me
)
```

---

## 7-11. API Endpoints, Middleware, RBAC, Registration, Sessions

> **Reference the original v1.0 specification (January 27, 2026) for detailed code examples of:**
> - Login/logout/register/refresh endpoints (`src/routers/auth.py`)
> - Auth middleware and dependency injection (`src/middleware/auth_middleware.py`)
> - Permission checking decorators (`require_role`, `require_permission`)
> - Member self-registration flow with member number verification
> - Refresh token rotation and concurrent session management
>
> The implementation follows the patterns described in the v1.0 spec with these key differences:
> - Account lockout uses `locked_until` datetime, not `is_locked` boolean
> - Frontend auth uses HTTP-only cookies exclusively (not Authorization headers)
> - Stripe Checkout Sessions integrate with auth for dues payments (Week 11)

---

## 12. Security Hardening (Week 16)

Production security hardening was implemented in Week 16 (v0.9.1-alpha) and includes:

### Security Headers
All responses include:
- `Content-Security-Policy` — Restricts resource loading origins
- `Strict-Transport-Security` — Forces HTTPS
- `X-Frame-Options: DENY` — Prevents clickjacking
- `X-Content-Type-Options: nosniff` — Prevents MIME type sniffing
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` — Restricts browser feature access

### Error Tracking
- **Sentry** integration for production error monitoring
- Sensitive data scrubbed before sending to Sentry
- Performance monitoring enabled

### Structured Logging
- JSON-formatted logs with correlation IDs
- Request/response logging with timing
- Audit events logged with structured metadata

### Connection Pooling
- SQLAlchemy `QueuePool` with `pool_size=20`, `max_overflow=10`
- `pool_pre_ping=True` for connection health checks
- `pool_recycle=3600` for connection refresh

### 32 Production Tests
Validate all hardening measures are properly configured and functional.

---

## 13-14. Integration Patterns & Configuration

> **Reference the v1.0 specification for:**
> - Auth configuration via environment variables
> - Integration with audit logging (all auth events are audited)
> - Integration with Stripe (payment auth flows)
> - CORS configuration for API clients

### Key Configuration (Environment Variables)

```bash
# JWT
JWT_SECRET_KEY=<generated-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Stripe (added Week 11)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Security (added Week 16)
SENTRY_DSN=https://...@sentry.io/...
CORS_ORIGINS=["https://ip2a.railway.app"]
```

---

## 15. Testing Auth

Authentication tests are part of the broader ~470 test suite:

- **Unit tests** — JWT creation/validation, password hashing, permission checks
- **Integration tests** — Login/logout flows, token refresh, account lockout
- **Frontend tests** — Auth-protected page access, redirect to login
- **Stripe tests** — 25 tests covering payment auth integration

```python
# Example: Account lockout test
class TestAccountLockout:
    def test_lockout_after_failed_attempts(self, client, test_user):
        for _ in range(5):
            client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "WrongPassword!"
            })

        # 6th attempt should be locked even with correct password
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })

        assert response.status_code == 401
        assert "locked" in response.json()["detail"].lower()
```

---

## 16. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Not authenticated" | No token provided | Check cookies are set (HTTP-only) |
| "Token has expired" | Access token expired | Refresh flow should handle automatically |
| "Invalid token" | Token malformed or wrong secret | Check JWT_SECRET_KEY matches |
| "Missing permission" | User lacks required permission | Check role assignments |
| "Account locked" | Too many failed logins | Wait for `locked_until` to pass or admin unlock |

### Debug Checklist

```bash
# 1. Check if JWT_SECRET_KEY is set
echo $JWT_SECRET_KEY

# 2. Decode a token (without verification) to inspect claims
python -c "
import jwt
token = 'your-token-here'
print(jwt.decode(token, options={'verify_signature': False}))
"

# 3. Check user's roles in database
psql -c "
SELECT u.email, r.name as role
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.email = 'test@example.com';
"

# 4. Check for locked accounts
# NOTE: Uses locked_until datetime, NOT a boolean is_locked field
psql -c "
SELECT email, locked_until, failed_login_attempts
FROM users
WHERE locked_until IS NOT NULL AND locked_until > NOW();
"

# 5. View recent login attempts (if login_history table exists)
psql -c "
SELECT email_attempted, success, failure_reason, ip_address, attempted_at
FROM login_history
ORDER BY attempted_at DESC
LIMIT 20;
"
```

---

## Summary

This authentication system provides:

✅ **Secure password handling** — Bcrypt hashing, complexity requirements
✅ **JWT-based authentication** — Stateless, scalable tokens via HTTP-only cookies
✅ **Role-based access control** — 7 roles with flexible permission system
✅ **Session management** — Refresh tokens, concurrent session support
✅ **Account security** — Lockout via `locked_until` datetime, login history
✅ **Production hardening** — Security headers, Sentry, structured logging (Week 16)
✅ **Stripe integration** — Payment auth for dues via Checkout Sessions (Week 11)
✅ **Audit integration** — All auth events logged with NLRA compliance

### Future Enhancements
- MFA (TOTP) for admin/officer roles
- Email verification flow
- Password reset via email
- API key authentication for third-party integrations

---

> **⚠️ SESSION RULE — MANDATORY:**
> At the end of every development session, update *ANY* and *ALL* relevant documents to capture progress made. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.
> See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md`

---

*Document Version: 2.0*
*Last Updated: February 3, 2026*
*Previous Version: 1.0 (January 27, 2026 — pre-implementation specification, 3200+ lines with full code examples)*
*Note: v1.0 code examples remain valid reference material. Consult source code for actual implementation details.*
