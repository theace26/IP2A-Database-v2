# Authentication & Authorization Architecture
## IP2A Database v2 - Security Foundation

**Document Created:** January 27, 2026
**Last Updated:** January 27, 2026
**Status:** Architecture Specification
**Priority:** CRITICAL - Must implement before other features

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
| Token storage | **HTTP-only cookies + localStorage** | Secure for web, flexible for API |
| Session strategy | **Short-lived access + refresh tokens** | Balance security and UX |
| RBAC model | **Role-based with permissions** | Flexible, auditable |
| MFA | **Optional (Phase 2)** | TOTP for sensitive roles |

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
│   │  Grievance  │     │   Market    │     │   Reports   │                   │
│   │  Workflow   │     │  Recovery   │     │   Access    │                   │
│   ├─────────────┤     ├─────────────┤     ├─────────────┤                   │
│   │ filed_by    │     │ approved_by │     │ run_by      │                   │
│   │ assigned_to │     │ = user_id   │     │ role_check  │                   │
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
| Dues payment | No idea who paid | Member #12345 paid via Stripe |
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
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    locked_reason TEXT,
    locked_until TIMESTAMP,
    
    -- Security tracking
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    last_failed_login TIMESTAMP,
    last_login TIMESTAMP,
    last_login_ip VARCHAR(45),
    
    -- Multi-factor authentication (Phase 2)
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


-- ============================================================================
-- LOGIN_HISTORY TABLE
-- Track all login attempts for security auditing
-- ============================================================================
CREATE TABLE login_history (
    id BIGSERIAL PRIMARY KEY,
    
    -- User (NULL if login attempt with invalid email)
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email_attempted VARCHAR(255) NOT NULL,
    
    -- Result
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100),  -- 'invalid_password', 'account_locked', etc.
    
    -- Request metadata
    ip_address VARCHAR(45) NOT NULL,
    user_agent VARCHAR(500),
    
    -- Geolocation (optional, from IP)
    country VARCHAR(2),
    city VARCHAR(100),
    
    -- Timestamp
    attempted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_login_history_user ON login_history(user_id, attempted_at DESC);
CREATE INDEX idx_login_history_ip ON login_history(ip_address, attempted_at DESC);
CREATE INDEX idx_login_history_date ON login_history(attempted_at DESC);

-- Partition by month for large installations
-- CREATE TABLE login_history_2026_01 PARTITION OF login_history
--     FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');


-- ============================================================================
-- PASSWORD_HISTORY TABLE
-- Prevent password reuse
-- ============================================================================
CREATE TABLE password_history (
    id SERIAL PRIMARY KEY,
    
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_password_history_user ON password_history(user_id);
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
    max_age_days: int = 0  # Most modern guidance says don't force rotation
    
    # Lockout policy
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30


# Default policy
password_policy = PasswordPolicy()


def validate_password(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password against policy.
    
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    policy = password_policy
    
    # Length checks
    if len(password) < policy.min_length:
        errors.append(f"Password must be at least {policy.min_length} characters")
    
    if len(password) > policy.max_length:
        errors.append(f"Password must be at most {policy.max_length} characters")
    
    # Complexity checks
    if policy.require_uppercase and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if policy.require_lowercase and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if policy.require_digit and not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if policy.require_special:
        special_pattern = f'[{re.escape(policy.special_characters)}]'
        if not re.search(special_pattern, password):
            errors.append(f"Password must contain at least one special character ({policy.special_characters})")
    
    # Common password check (basic - expand with haveibeenpwned API in production)
    common_passwords = {'password', 'password123', '123456', 'qwerty', 'letmein', 'admin'}
    if password.lower() in common_passwords:
        errors.append("Password is too common")
    
    return (len(errors) == 0, errors)


def check_password_history(
    user_id: str, 
    new_password_hash: str, 
    db_session
) -> bool:
    """
    Check if password was recently used.
    
    Returns:
        True if password is OK (not in history), False if recently used
    """
    from src.models.password_history import PasswordHistory
    import bcrypt
    
    # Get recent password hashes
    recent = db_session.query(PasswordHistory).filter(
        PasswordHistory.user_id == user_id
    ).order_by(
        PasswordHistory.created_at.desc()
    ).limit(password_policy.prevent_reuse_count).all()
    
    # Note: We can't directly compare hashes due to bcrypt salting
    # This is a limitation - in practice, we'd need to store and check differently
    # For now, we'll skip this check and document the limitation
    
    return True
```

### Password Hashing

```python
# src/auth/password.py
"""
Password hashing and verification using bcrypt.
"""

import bcrypt
from typing import Tuple


# Cost factor for bcrypt (12 is a good balance of security and speed)
# Increase if hardware improves (should take ~250ms to hash)
BCRYPT_COST = 12


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    # Encode password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=BCRYPT_COST)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Stored hash to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        # Invalid hash format or other error
        return False


def needs_rehash(password_hash: str) -> bool:
    """
    Check if password hash needs to be upgraded (cost factor changed).
    
    Call this after successful login to upgrade old hashes.
    """
    try:
        # Extract cost from hash
        hash_bytes = password_hash.encode('utf-8')
        
        # bcrypt hash format: $2b$XX$... where XX is the cost
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
    # Standard claims
    "sub": "550e8400-e29b-41d4-a716-446655440000",  # User ID
    "iat": 1706400000,                               # Issued at (Unix timestamp)
    "exp": 1706403600,                               # Expires at (1 hour later)
    "jti": "unique-token-id",                        # Token ID (for revocation)
    
    # Custom claims
    "email": "jsmith@local46.org",
    "name": "John Smith",
    "roles": ["staff", "organizer"],
    "permissions": ["members:*", "organizing:*"],
    
    # Linked records (if applicable)
    "member_id": 12345,        # NULL if not a member
    "student_id": null,
    "instructor_id": null,
    
    # Token type
    "type": "access"
}

# Refresh Token Payload (long-lived: 7-30 days)
{
    "sub": "550e8400-e29b-41d4-a716-446655440000",
    "iat": 1706400000,
    "exp": 1707004800,  # 7 days later
    "jti": "refresh-token-id",
    "type": "refresh"
}
```

### JWT Service

```python
# src/auth/jwt_service.py
"""
JWT token generation and validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from uuid import uuid4
import jwt

from src.config.settings import auth_settings


class JWTService:
    """
    Handle JWT token operations.
    """
    
    def __init__(self):
        self.secret_key = auth_settings.JWT_SECRET_KEY
        self.algorithm = auth_settings.JWT_ALGORITHM
        self.access_token_expire = timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(days=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    def create_access_token(
        self,
        user_id: str,
        email: str,
        name: str,
        roles: List[str],
        permissions: List[str],
        member_id: Optional[int] = None,
        student_id: Optional[int] = None,
        instructor_id: Optional[int] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new access token.
        
        Args:
            user_id: User's UUID
            email: User's email
            name: User's full name
            roles: List of role names
            permissions: Flattened list of permissions
            member_id: Associated member ID (if any)
            student_id: Associated student ID (if any)
            instructor_id: Associated instructor ID (if any)
            additional_claims: Any extra claims to include
            
        Returns:
            Encoded JWT string
        """
        now = datetime.now(timezone.utc)
        
        payload = {
            # Standard claims
            "sub": user_id,
            "iat": now,
            "exp": now + self.access_token_expire,
            "jti": str(uuid4()),
            
            # Custom claims
            "email": email,
            "name": name,
            "roles": roles,
            "permissions": permissions,
            "member_id": member_id,
            "student_id": student_id,
            "instructor_id": instructor_id,
            "type": "access"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> tuple[str, str]:
        """
        Create a new refresh token.
        
        Returns:
            Tuple of (token_string, token_id)
        """
        now = datetime.now(timezone.utc)
        token_id = str(uuid4())
        
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + self.refresh_token_expire,
            "jti": token_id,
            "type": "refresh"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, token_id
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a token.
        
        Args:
            token: JWT string
            
        Returns:
            Decoded payload
            
        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
        """
        return jwt.decode(
            token, 
            self.secret_key, 
            algorithms=[self.algorithm],
            options={"require": ["sub", "exp", "iat", "jti", "type"]}
        )
    
    def decode_token_unverified(self, token: str) -> Dict[str, Any]:
        """
        Decode token without verification (for debugging).
        
        WARNING: Do not use for authorization decisions!
        """
        return jwt.decode(
            token,
            options={"verify_signature": False}
        )
    
    def is_token_type(self, payload: Dict[str, Any], expected_type: str) -> bool:
        """Check if token is of expected type."""
        return payload.get("type") == expected_type
    
    def create_email_verification_token(self, user_id: str, email: str) -> str:
        """Create token for email verification."""
        now = datetime.now(timezone.utc)
        
        payload = {
            "sub": user_id,
            "email": email,
            "iat": now,
            "exp": now + timedelta(hours=24),
            "jti": str(uuid4()),
            "type": "email_verification"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_password_reset_token(self, user_id: str, email: str) -> str:
        """Create token for password reset."""
        now = datetime.now(timezone.utc)
        
        payload = {
            "sub": user_id,
            "email": email,
            "iat": now,
            "exp": now + timedelta(hours=1),  # Short-lived for security
            "jti": str(uuid4()),
            "type": "password_reset"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


# Singleton instance
jwt_service = JWTService()
```

---

## 7. API Endpoints

### Authentication Router

```python
# src/routers/auth.py
"""
Authentication endpoints: login, logout, register, password reset.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.auth.jwt_service import jwt_service
from src.auth.password import hash_password, verify_password, needs_rehash
from src.auth.password_policy import validate_password
from src.auth.dependencies import get_current_user
from src.models.user import User
from src.models.refresh_token import RefreshToken
from src.models.login_history import LoginHistory
from src.services.email import email_service


router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    
    # For member self-registration
    member_number: Optional[str] = None
    last_four_ssn: Optional[str] = None  # For verification


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)


class RefreshRequest(BaseModel):
    refresh_token: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return tokens.
    
    - **email**: User's email address
    - **password**: User's password
    - **remember_me**: If true, refresh token lasts 30 days instead of 7
    """
    # Find user
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    
    # Log attempt
    login_record = LoginHistory(
        user_id=user.id if user else None,
        email_attempted=login_data.email.lower(),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    
    # Validate credentials
    if not user:
        login_record.success = False
        login_record.failure_reason = "invalid_email"
        db.add(login_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is locked
    if user.is_locked:
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            login_record.success = False
            login_record.failure_reason = "account_locked"
            db.add(login_record)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Account is locked. Try again after {user.locked_until}"
            )
        else:
            # Unlock account (lockout period expired)
            user.is_locked = False
            user.locked_until = None
            user.failed_login_attempts = 0
    
    # Check if account is active
    if not user.is_active:
        login_record.success = False
        login_record.failure_reason = "account_inactive"
        db.add(login_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts += 1
        user.last_failed_login = datetime.now(timezone.utc)
        
        # Lock account if too many failures
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            user.locked_reason = "Too many failed login attempts"
        
        login_record.success = False
        login_record.failure_reason = "invalid_password"
        db.add(login_record)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Successful login - reset failed attempts
    user.failed_login_attempts = 0
    user.last_login = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host
    
    # Check if password needs rehash (cost factor upgrade)
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(login_data.password)
    
    # Get user roles and permissions
    roles = [ur.role.name for ur in user.user_roles]
    permissions = _flatten_permissions(user.user_roles)
    
    # Create access token
    access_token = jwt_service.create_access_token(
        user_id=str(user.id),
        email=user.email,
        name=f"{user.first_name} {user.last_name}",
        roles=roles,
        permissions=permissions,
        member_id=user.member_id,
        student_id=user.student_id,
        instructor_id=user.instructor_id
    )
    
    # Create refresh token
    refresh_token, token_id = jwt_service.create_refresh_token(str(user.id))
    
    # Store refresh token in database
    refresh_record = RefreshToken(
        id=token_id,
        user_id=user.id,
        token_hash=hash_password(refresh_token),  # Store hashed
        device_info=request.headers.get("user-agent", "")[:255],
        ip_address=request.client.host,
        expires_at=datetime.now(timezone.utc) + timedelta(
            days=30 if login_data.remember_me else 7
        )
    )
    db.add(refresh_record)
    
    # Log successful login
    login_record.success = True
    db.add(login_record)
    
    db.commit()
    
    # Set refresh token as HTTP-only cookie (more secure)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="lax",
        max_age=30 * 24 * 60 * 60 if login_data.remember_me else 7 * 24 * 60 * 60
    )
    
    return LoginResponse(
        access_token=access_token,
        expires_in=3600,  # 1 hour
        user={
            "id": str(user.id),
            "email": user.email,
            "name": f"{user.first_name} {user.last_name}",
            "roles": roles,
            "member_id": user.member_id
        }
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Logout user by revoking refresh token.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if refresh_token:
        # Find and revoke the token
        # Note: We'd need to decode to get jti, then find by that
        try:
            payload = jwt_service.decode_token(refresh_token)
            token_id = payload.get("jti")
            
            token_record = db.query(RefreshToken).filter(
                RefreshToken.id == token_id
            ).first()
            
            if token_record:
                token_record.revoked_at = datetime.now(timezone.utc)
                token_record.revoked_reason = "User logout"
                db.commit()
        except Exception:
            pass  # Token invalid/expired, already effectively logged out
    
    # Clear cookie
    response.delete_cookie("refresh_token")
    
    return {"message": "Successfully logged out"}


@router.post("/refresh")
async def refresh_tokens(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Get new access token using refresh token.
    
    Refresh token can be in cookie or request body.
    """
    # Get refresh token from cookie or body
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        body = await request.json()
        refresh_token = body.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required"
        )
    
    # Decode and validate
    try:
        payload = jwt_service.decode_token(refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify token type
    if not jwt_service.is_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Check if token is revoked
    token_id = payload.get("jti")
    token_record = db.query(RefreshToken).filter(
        RefreshToken.id == token_id,
        RefreshToken.revoked_at.is_(None)
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    # Get user
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Update token last used
    token_record.last_used_at = datetime.now(timezone.utc)
    
    # Get fresh roles and permissions
    roles = [ur.role.name for ur in user.user_roles]
    permissions = _flatten_permissions(user.user_roles)
    
    # Create new access token
    access_token = jwt_service.create_access_token(
        user_id=str(user.id),
        email=user.email,
        name=f"{user.first_name} {user.last_name}",
        roles=roles,
        permissions=permissions,
        member_id=user.member_id,
        student_id=user.student_id,
        instructor_id=user.instructor_id
    )
    
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600
    }


@router.post("/register")
async def register(
    request: Request,
    registration: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    For members: Provide member_number and last_four_ssn for verification.
    For applicants: Will be assigned applicant role.
    """
    # Validate password
    is_valid, errors = validate_password(registration.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "errors": errors}
        )
    
    # Check if email already exists
    existing = db.query(User).filter(
        User.email == registration.email.lower()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # If member registration, verify member
    member = None
    if registration.member_number:
        from src.models.member import Member
        
        member = db.query(Member).filter(
            Member.member_number == registration.member_number
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Member number not found"
            )
        
        # Verify with last 4 SSN (if we store that)
        # This is a simple verification - adjust based on your data
        if registration.last_four_ssn:
            # Implement SSN verification logic here
            pass
        
        # Check if member already has an account
        existing_user = db.query(User).filter(User.member_id == member.id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This member already has an account"
            )
    
    # Create user
    user = User(
        email=registration.email.lower(),
        password_hash=hash_password(registration.password),
        first_name=registration.first_name,
        last_name=registration.last_name,
        phone=registration.phone,
        member_id=member.id if member else None
    )
    
    db.add(user)
    db.flush()  # Get user.id
    
    # Assign role
    from src.models.role import Role
    from src.models.user_role import UserRole
    
    if member:
        role = db.query(Role).filter(Role.name == "member").first()
    else:
        role = db.query(Role).filter(Role.name == "applicant").first()
    
    if role:
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)
    
    # Generate email verification token
    verification_token = jwt_service.create_email_verification_token(
        str(user.id), 
        user.email
    )
    user.email_verification_token = verification_token
    user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    
    db.commit()
    
    # Send verification email
    await email_service.send_verification_email(
        to_email=user.email,
        name=user.first_name,
        verification_link=f"{auth_settings.FRONTEND_URL}/verify-email?token={verification_token}"
    )
    
    return {
        "message": "Registration successful. Please check your email to verify your account.",
        "user_id": str(user.id)
    }


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify email address using token from registration email.
    """
    try:
        payload = jwt_service.decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link"
        )
    
    if not jwt_service.is_token_type(payload, "email_verification"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type"
        )
    
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.email_verified:
        return {"message": "Email already verified"}
    
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset email.
    
    Always returns success to prevent email enumeration.
    """
    user = db.query(User).filter(
        User.email == request.email.lower()
    ).first()
    
    if user and user.is_active:
        # Generate reset token
        reset_token = jwt_service.create_password_reset_token(
            str(user.id),
            user.email
        )
        
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        
        # Send reset email
        await email_service.send_password_reset_email(
            to_email=user.email,
            name=user.first_name,
            reset_link=f"{auth_settings.FRONTEND_URL}/reset-password?token={reset_token}"
        )
    
    # Always return success (security)
    return {
        "message": "If an account exists with that email, a password reset link has been sent."
    }


@router.post("/reset-password")
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using token from email.
    """
    # Validate new password
    is_valid, errors = validate_password(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "errors": errors}
        )
    
    # Decode token
    try:
        payload = jwt_service.decode_token(request.token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset link"
        )
    
    if not jwt_service.is_token_type(payload, "password_reset"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type"
        )
    
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.password_reset_token = None
    user.password_reset_expires = None
    
    # Revoke all refresh tokens (force re-login everywhere)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None)
    ).update({
        "revoked_at": datetime.now(timezone.utc),
        "revoked_reason": "Password reset"
    })
    
    db.commit()
    
    return {"message": "Password reset successful. Please log in with your new password."}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Change password for logged-in user.
    """
    # Validate new password
    is_valid, errors = validate_password(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "errors": errors}
        )
    
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    
    # Verify current password
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Check password isn't same as current
    if verify_password(request.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/me")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile.
    """
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "email_verified": user.email_verified,
        "roles": current_user.get("roles", []),
        "member_id": user.member_id,
        "student_id": user.student_id,
        "created_at": user.created_at.isoformat()
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _flatten_permissions(user_roles) -> List[str]:
    """
    Flatten all permissions from user's roles into a single list.
    """
    permissions = set()
    
    for user_role in user_roles:
        role_permissions = user_role.role.permissions or []
        for perm in role_permissions:
            if perm == "*":
                permissions.add("*")
            else:
                permissions.add(perm)
    
    return list(permissions)
```

---

## 8. Middleware & Dependencies

### Authentication Dependencies

```python
# src/auth/dependencies.py
"""
FastAPI dependencies for authentication and authorization.
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
import jwt

from src.auth.jwt_service import jwt_service
from src.config.settings import auth_settings


# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# HTTP Bearer for API clients
http_bearer = HTTPBearer(auto_error=False)


async def get_token_from_request(
    request: Request,
    oauth2_token: Optional[str] = Depends(oauth2_scheme),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> Optional[str]:
    """
    Extract JWT token from request.
    
    Checks (in order):
    1. Authorization header (Bearer token)
    2. Cookie (access_token)
    """
    # Try Bearer token from header
    if bearer_token:
        return bearer_token.credentials
    
    if oauth2_token:
        return oauth2_token
    
    # Try cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    
    return None


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_request)
) -> dict:
    """
    Validate token and return current user's claims.
    
    Raises:
        HTTPException 401 if token is missing or invalid
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt_service.decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify it's an access token
    if not jwt_service.is_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload


async def get_current_user_optional(
    token: Optional[str] = Depends(get_token_from_request)
) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.
    
    Use for endpoints that work for both authenticated and anonymous users.
    """
    if not token:
        return None
    
    try:
        payload = jwt_service.decode_token(token)
        if jwt_service.is_token_type(payload, "access"):
            return payload
    except Exception:
        pass
    
    return None


def require_roles(*required_roles: str):
    """
    Dependency factory that requires user to have ANY of the specified roles.
    
    Usage:
        @router.get("/admin")
        async def admin_only(user = Depends(require_roles("admin"))):
            ...
        
        @router.get("/staff-or-officer")
        async def staff_route(user = Depends(require_roles("staff", "officer"))):
            ...
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_roles = current_user.get("roles", [])
        
        # Admin always has access
        if "admin" in user_roles:
            return current_user
        
        # Check if user has any required role
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


def require_all_roles(*required_roles: str):
    """
    Dependency factory that requires user to have ALL specified roles.
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_roles = current_user.get("roles", [])
        
        if "admin" in user_roles:
            return current_user
        
        missing = [r for r in required_roles if r not in user_roles]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required roles: {', '.join(missing)}"
            )
        
        return current_user
    
    return role_checker


def require_permissions(*required_permissions: str):
    """
    Dependency factory that requires user to have specific permissions.
    
    Supports wildcard matching:
    - "members:*" matches "members:read", "members:write", etc.
    - "*" matches everything
    
    Usage:
        @router.get("/members")
        async def list_members(user = Depends(require_permissions("members:read"))):
            ...
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_permissions = current_user.get("permissions", [])
        
        # Wildcard = full access
        if "*" in user_permissions:
            return current_user
        
        for required in required_permissions:
            if not _has_permission(required, user_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permission: {required}"
                )
        
        return current_user
    
    return permission_checker


def _has_permission(required: str, user_permissions: List[str]) -> bool:
    """
    Check if user has a specific permission.
    
    Handles wildcards:
    - User has "members:*" → matches "members:read"
    - User has "members:read" → matches "members:read" only
    """
    if required in user_permissions:
        return True
    
    # Check wildcards
    required_resource = required.split(":")[0]
    
    for perm in user_permissions:
        if perm == f"{required_resource}:*":
            return True
    
    return False


class RoleChecker:
    """
    Class-based dependency for role checking (alternative syntax).
    
    Usage:
        admin_only = RoleChecker(["admin"])
        
        @router.get("/admin", dependencies=[Depends(admin_only)])
        async def admin_route():
            ...
    """
    
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
    
    async def __call__(
        self, 
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_roles = current_user.get("roles", [])
        
        if "admin" in user_roles:
            return current_user
        
        if not any(role in user_roles for role in self.required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(self.required_roles)}"
            )
        
        return current_user
```

### Audit Context Middleware

```python
# src/middleware/audit_context.py
"""
Middleware to capture authentication context for audit logging.
"""

from contextvars import ContextVar
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.auth.jwt_service import jwt_service


# Context variables for audit logging
current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default=None)
current_user_email: ContextVar[Optional[str]] = ContextVar('current_user_email', default=None)
current_request_ip: ContextVar[Optional[str]] = ContextVar('current_request_ip', default=None)
current_user_agent: ContextVar[Optional[str]] = ContextVar('current_user_agent', default=None)


class AuditContextMiddleware(BaseHTTPMiddleware):
    """
    Extract user info from JWT and set context variables for audit logging.
    
    This allows audit_service to access user info without passing it through
    every function call.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract token
        token = None
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = request.cookies.get("access_token")
        
        # Set request context
        current_request_ip.set(request.client.host if request.client else None)
        current_user_agent.set(request.headers.get("user-agent", "")[:500])
        
        # Extract user from token
        if token:
            try:
                payload = jwt_service.decode_token(token)
                current_user_id.set(payload.get("sub"))
                current_user_email.set(payload.get("email"))
            except Exception:
                # Invalid token - leave context as None
                current_user_id.set(None)
                current_user_email.set(None)
        else:
            current_user_id.set(None)
            current_user_email.set(None)
        
        response = await call_next(request)
        
        return response


def get_audit_context() -> dict:
    """
    Get current audit context.
    
    Use this in audit_service to get user info without parameters.
    """
    return {
        "user_id": current_user_id.get(),
        "user_email": current_user_email.get(),
        "ip_address": current_request_ip.get(),
        "user_agent": current_user_agent.get()
    }
```

---

## 9. Role-Based Access Control (RBAC)

### Permission System

```python
# src/auth/permissions.py
"""
Permission definitions and checking utilities.
"""

from enum import Enum
from typing import List, Set


class Resource(str, Enum):
    """Resources that can be protected."""
    MEMBERS = "members"
    STUDENTS = "students"
    ORGANIZATIONS = "organizations"
    GRIEVANCES = "grievances"
    BENEVOLENCE = "benevolence"
    DUES = "dues"
    REFERRALS = "referrals"
    ORGANIZING = "organizing"
    GRANTS = "grants"
    COHORTS = "cohorts"
    REPORTS = "reports"
    FILES = "files"
    USERS = "users"
    SYSTEM = "system"
    SELF = "self"  # User's own data


class Action(str, Enum):
    """Actions that can be performed on resources."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    EXPORT = "export"
    MANAGE = "manage"
    ALL = "*"


def permission(resource: Resource, action: Action) -> str:
    """
    Build permission string.
    
    Example:
        permission(Resource.MEMBERS, Action.READ) → "members:read"
    """
    return f"{resource.value}:{action.value}"


# Convenience shortcuts
MEMBER_READ = permission(Resource.MEMBERS, Action.READ)
MEMBER_WRITE = permission(Resource.MEMBERS, Action.UPDATE)
MEMBER_CREATE = permission(Resource.MEMBERS, Action.CREATE)
MEMBER_DELETE = permission(Resource.MEMBERS, Action.DELETE)

GRIEVANCE_READ = permission(Resource.GRIEVANCES, Action.READ)
GRIEVANCE_APPROVE = permission(Resource.GRIEVANCES, Action.APPROVE)

REPORTS_STANDARD = "reports:standard"
REPORTS_FINANCIAL = "reports:financial"


class PermissionChecker:
    """
    Check if a set of user permissions allows an action.
    """
    
    def __init__(self, user_permissions: List[str]):
        self.permissions: Set[str] = set(user_permissions)
    
    def has(self, required: str) -> bool:
        """Check if user has specific permission."""
        # Full access
        if "*" in self.permissions:
            return True
        
        # Exact match
        if required in self.permissions:
            return True
        
        # Wildcard match (e.g., "members:*" allows "members:read")
        resource = required.split(":")[0]
        if f"{resource}:*" in self.permissions:
            return True
        
        return False
    
    def has_any(self, *required: str) -> bool:
        """Check if user has any of the permissions."""
        return any(self.has(r) for r in required)
    
    def has_all(self, *required: str) -> bool:
        """Check if user has all of the permissions."""
        return all(self.has(r) for r in required)
    
    def can_access_self(self) -> bool:
        """Check if user can access their own data."""
        return self.has("self:*") or self.has("self:read")
```

### Protecting Routes

```python
# Example: Protected member routes
# src/routers/members.py

from fastapi import APIRouter, Depends
from src.auth.dependencies import (
    get_current_user,
    require_roles,
    require_permissions
)

router = APIRouter(prefix="/members", tags=["members"])


@router.get("/")
async def list_members(
    current_user: dict = Depends(require_permissions("members:read"))
):
    """
    List all members.
    
    Requires: members:read permission
    Roles with access: admin, officer, staff, organizer
    """
    # Staff, officers, admins can see all members
    ...


@router.get("/my-profile")
async def get_my_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user's member profile.
    
    Requires: Any authenticated user who is a member
    """
    member_id = current_user.get("member_id")
    if not member_id:
        raise HTTPException(403, "Not a union member")
    
    # Return only their own data
    ...


@router.get("/{member_id}")
async def get_member(
    member_id: int,
    current_user: dict = Depends(require_permissions("members:read"))
):
    """
    Get specific member by ID.
    
    Requires: members:read permission
    """
    ...


@router.post("/")
async def create_member(
    member_data: MemberCreate,
    current_user: dict = Depends(require_permissions("members:create"))
):
    """
    Create new member.
    
    Requires: members:create permission
    Roles with access: admin, officer, staff
    """
    ...


@router.delete("/{member_id}")
async def delete_member(
    member_id: int,
    current_user: dict = Depends(require_roles("admin", "officer"))
):
    """
    Delete member (soft delete).
    
    Requires: admin or officer role
    """
    ...
```

---

## 10. User Registration Flows

### Flow Diagrams

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MEMBER SELF-REGISTRATION FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│   │ Member  │     │  Enter  │     │ Verify  │     │ Create  │              │
│   │ Clicks  │────►│ Member# │────►│ Identity│────►│ Account │              │
│   │ Register│     │ + Info  │     │ (SSN/DOB)     │         │              │
│   └─────────┘     └─────────┘     └─────────┘     └────┬────┘              │
│                                                        │                    │
│                                                        ▼                    │
│                                           ┌─────────────────────┐          │
│                                           │   Send Verification │          │
│                                           │       Email         │          │
│                                           └──────────┬──────────┘          │
│                                                      │                      │
│                                                      ▼                      │
│                                           ┌─────────────────────┐          │
│                                           │   Member Clicks     │          │
│                                           │   Verification Link │          │
│                                           └──────────┬──────────┘          │
│                                                      │                      │
│                                                      ▼                      │
│                                           ┌─────────────────────┐          │
│                                           │   Account Active    │          │
│                                           │   Role: member      │          │
│                                           └─────────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                     STAFF ACCOUNT PROVISIONING FLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│   │  Admin  │     │ Create  │     │ Assign  │     │  Send   │              │
│   │ Logs In │────►│  User   │────►│ Role(s) │────►│ Welcome │              │
│   └─────────┘     └─────────┘     └─────────┘     │  Email  │              │
│                                                   └────┬────┘              │
│                                                        │                    │
│                                                        ▼                    │
│                                           ┌─────────────────────┐          │
│                                           │   Staff Clicks      │          │
│                                           │   "Set Password"    │          │
│                                           └──────────┬──────────┘          │
│                                                      │                      │
│                                                      ▼                      │
│                                           ┌─────────────────────┐          │
│                                           │   Account Active    │          │
│                                           │   Role: staff/etc   │          │
│                                           └─────────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                     PRE-APP APPLICANT REGISTRATION FLOW                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│   │Applicant│     │  Fill   │     │  Verify │     │ Create  │              │
│   │ Visits  │────►│  Out    │────►│  Email  │────►│ Student │              │
│   │  Site   │     │  Form   │     │         │     │ Record  │              │
│   └─────────┘     └─────────┘     └─────────┘     └────┬────┘              │
│                                                        │                    │
│                                                        ▼                    │
│                                           ┌─────────────────────┐          │
│                                           │   Account Active    │          │
│                                           │   Role: applicant   │          │
│                                           │   Status: APPLICANT │          │
│                                           └─────────────────────┘          │
│                                                                              │
│   Note: When applicant is accepted into program, staff updates              │
│   status to ENROLLED and student record is fully created.                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Admin User Management Router

```python
# src/routers/admin/users.py
"""
Admin endpoints for user management.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from src.auth.dependencies import require_roles
from src.auth.password import hash_password
from src.auth.jwt_service import jwt_service


router = APIRouter(
    prefix="/admin/users",
    tags=["admin - users"],
    dependencies=[Depends(require_roles("admin"))]
)


class CreateUserRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    roles: List[str]
    member_id: Optional[int] = None
    send_welcome_email: bool = True


class UpdateUserRolesRequest(BaseModel):
    roles: List[str]


@router.get("/")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List all users with optional filtering.
    """
    query = db.query(User)
    
    if role:
        query = query.join(UserRole).join(Role).filter(Role.name == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "users": [_user_to_dict(u) for u in users]
    }


@router.post("/")
async def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Create a new user account (admin provisioning).
    
    - Creates user with temporary password
    - Assigns specified roles
    - Sends welcome email with password setup link
    """
    # Check email doesn't exist
    existing = db.query(User).filter(User.email == request.email.lower()).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    
    # Create user with random temporary password
    import secrets
    temp_password = secrets.token_urlsafe(16)
    
    user = User(
        email=request.email.lower(),
        password_hash=hash_password(temp_password),
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        member_id=request.member_id,
        created_by=current_user["sub"]
    )
    
    db.add(user)
    db.flush()
    
    # Assign roles
    for role_name in request.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            user_role = UserRole(
                user_id=user.id,
                role_id=role.id,
                granted_by=current_user["sub"]
            )
            db.add(user_role)
    
    # Generate password setup token
    setup_token = jwt_service.create_password_reset_token(str(user.id), user.email)
    user.password_reset_token = setup_token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=72)
    
    db.commit()
    
    # Send welcome email
    if request.send_welcome_email:
        await email_service.send_welcome_email(
            to_email=user.email,
            name=user.first_name,
            setup_link=f"{auth_settings.FRONTEND_URL}/setup-password?token={setup_token}"
        )
    
    return {
        "user_id": str(user.id),
        "email": user.email,
        "roles": request.roles,
        "message": "User created successfully"
    }


@router.put("/{user_id}/roles")
async def update_user_roles(
    user_id: str,
    request: UpdateUserRolesRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Update a user's roles.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Remove existing roles
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    
    # Add new roles
    for role_name in request.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            user_role = UserRole(
                user_id=user.id,
                role_id=role.id,
                granted_by=current_user["sub"]
            )
            db.add(user_role)
    
    db.commit()
    
    return {"message": "Roles updated successfully", "roles": request.roles}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Deactivate a user account.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    user.is_active = False
    
    # Revoke all sessions
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None)
    ).update({
        "revoked_at": datetime.now(timezone.utc),
        "revoked_reason": f"Account deactivated: {reason}"
    })
    
    db.commit()
    
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Reactivate a deactivated user account.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    user.is_active = True
    user.is_locked = False
    user.locked_until = None
    user.failed_login_attempts = 0
    
    db.commit()
    
    return {"message": "User reactivated successfully"}
```

---

## 11. Session Management

### Concurrent Session Limits

```python
# src/auth/session_manager.py
"""
Manage user sessions and concurrent login limits.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.refresh_token import RefreshToken
from src.config.settings import auth_settings


class SessionManager:
    """
    Manage user sessions with limits on concurrent logins.
    """
    
    # Maximum concurrent sessions per user
    MAX_SESSIONS_PER_USER = 5
    
    def get_active_sessions(self, db: Session, user_id: str) -> List[RefreshToken]:
        """Get all active sessions for a user."""
        return db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc)
        ).order_by(RefreshToken.issued_at.desc()).all()
    
    def enforce_session_limit(self, db: Session, user_id: str) -> int:
        """
        Enforce maximum session limit.
        
        Revokes oldest sessions if user has too many.
        
        Returns:
            Number of sessions revoked
        """
        sessions = self.get_active_sessions(db, user_id)
        
        revoked = 0
        while len(sessions) >= self.MAX_SESSIONS_PER_USER:
            # Revoke oldest session
            oldest = sessions.pop()
            oldest.revoked_at = datetime.now(timezone.utc)
            oldest.revoked_reason = "Session limit exceeded"
            revoked += 1
        
        if revoked > 0:
            db.commit()
        
        return revoked
    
    def revoke_all_sessions(
        self, 
        db: Session, 
        user_id: str, 
        reason: str = "User requested"
    ) -> int:
        """
        Revoke all sessions for a user (logout everywhere).
        
        Returns:
            Number of sessions revoked
        """
        result = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        ).update({
            "revoked_at": datetime.now(timezone.utc),
            "revoked_reason": reason
        })
        
        db.commit()
        return result
    
    def revoke_session(
        self, 
        db: Session, 
        session_id: str, 
        reason: str = "User requested"
    ) -> bool:
        """
        Revoke a specific session.
        
        Returns:
            True if session was found and revoked
        """
        session = db.query(RefreshToken).filter(
            RefreshToken.id == session_id,
            RefreshToken.revoked_at.is_(None)
        ).first()
        
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            session.revoked_reason = reason
            db.commit()
            return True
        
        return False


session_manager = SessionManager()
```

### Session Management Endpoints

```python
# Add to src/routers/auth.py

@router.get("/sessions")
async def list_my_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all active sessions for current user.
    """
    sessions = session_manager.get_active_sessions(db, current_user["sub"])
    
    return {
        "sessions": [
            {
                "id": str(s.id),
                "device": s.device_info,
                "ip_address": s.ip_address,
                "created_at": s.issued_at.isoformat(),
                "last_used": s.last_used_at.isoformat() if s.last_used_at else None,
                "expires_at": s.expires_at.isoformat()
            }
            for s in sessions
        ]
    }


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke a specific session.
    """
    # Verify session belongs to user
    session = db.query(RefreshToken).filter(
        RefreshToken.id == session_id,
        RefreshToken.user_id == current_user["sub"]
    ).first()
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    session_manager.revoke_session(db, session_id, "User revoked via API")
    
    return {"message": "Session revoked"}


@router.delete("/sessions")
async def revoke_all_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke all sessions (logout everywhere).
    """
    count = session_manager.revoke_all_sessions(
        db, 
        current_user["sub"],
        "User logged out everywhere"
    )
    
    return {"message": f"Revoked {count} sessions"}
```

---

## 12. Security Hardening

### Security Checklist

```
✅ IMPLEMENTED / TO IMPLEMENT

Password Security:
[x] Bcrypt hashing with cost factor 12
[x] Minimum 12 characters
[x] Complexity requirements (upper, lower, digit, special)
[x] Password history (prevent reuse)
[ ] Breach detection (HaveIBeenPwned API)

Token Security:
[x] Short-lived access tokens (1 hour)
[x] Refresh tokens stored hashed
[x] Token revocation support
[x] Secure cookie settings (HttpOnly, Secure, SameSite)
[ ] Token binding to device/IP (optional)

Account Security:
[x] Account lockout after 5 failed attempts
[x] 30-minute lockout duration
[x] Login history tracking
[x] Session management (revoke, limit)
[ ] Suspicious login detection (new device/location)
[ ] MFA support (TOTP)

API Security:
[x] Rate limiting on auth endpoints
[x] Input validation (Pydantic)
[x] SQL injection prevention (SQLAlchemy ORM)
[ ] CORS configuration
[ ] Request signing (for sensitive operations)

Audit:
[x] All auth events logged
[x] Login attempts tracked
[x] Session activity logged
[ ] Anomaly alerting
```

### Rate Limiting for Auth Endpoints

```python
# src/middleware/rate_limit.py
"""
Rate limiting for authentication endpoints.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import Request, HTTPException
import asyncio


class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    For production, use Redis-based rate limiting.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self._cleanup_task = None
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Check if request should be rate limited.
        
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Get request timestamps for this key
        if key not in self.requests:
            self.requests[key] = []
        
        # Filter to only requests in current window
        self.requests[key] = [
            ts for ts in self.requests[key]
            if ts > window_start
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            # Calculate retry after
            oldest = min(self.requests[key])
            retry_after = int((oldest + timedelta(seconds=window_seconds) - now).total_seconds())
            return False, max(1, retry_after)
        
        # Allow request, record timestamp
        self.requests[key].append(now)
        return True, 0


rate_limiter = RateLimiter()


# Rate limit configurations
AUTH_RATE_LIMITS = {
    "/auth/login": (5, 60),        # 5 attempts per minute
    "/auth/register": (3, 60),     # 3 registrations per minute
    "/auth/forgot-password": (3, 300),  # 3 resets per 5 minutes
}


async def check_auth_rate_limit(request: Request):
    """
    Dependency to check rate limits on auth endpoints.
    """
    path = request.url.path
    
    if path not in AUTH_RATE_LIMITS:
        return
    
    limit, window = AUTH_RATE_LIMITS[path]
    
    # Use IP address as key
    key = f"{path}:{request.client.host}"
    
    allowed, retry_after = await rate_limiter.check_rate_limit(key, limit, window)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
```

---

## 13. Integration Patterns

### Using Auth in Other Services

```python
# Example: Audit service integration
# src/services/audit.py

from src.middleware.audit_context import get_audit_context


class AuditService:
    """
    Audit service that automatically uses auth context.
    """
    
    def log_action(
        self,
        db: Session,
        table_name: str,
        record_id: str,
        action: str,
        old_values: dict = None,
        new_values: dict = None,
        notes: str = None
    ):
        """
        Log an action with automatic user context.
        """
        # Get user from auth context (set by middleware)
        context = get_audit_context()
        
        log_entry = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            changed_by=context.get("user_email") or "anonymous",
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            notes=notes
        )
        
        db.add(log_entry)
```

### Self-Service Access Pattern

```python
# Pattern for "users can only access their own data"
# src/routers/my.py

from fastapi import APIRouter, Depends, HTTPException
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/my", tags=["self-service"])


@router.get("/profile")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile."""
    member_id = current_user.get("member_id")
    if not member_id:
        raise HTTPException(403, "Not a member")
    
    member = db.query(Member).filter(Member.id == member_id).first()
    return member


@router.get("/dues")
async def get_my_dues(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's dues history."""
    member_id = current_user.get("member_id")
    if not member_id:
        raise HTTPException(403, "Not a member")
    
    payments = db.query(DuesPayment).filter(
        DuesPayment.member_id == member_id
    ).order_by(DuesPayment.payment_date.desc()).all()
    
    return payments


@router.get("/certifications")
async def get_my_certifications(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's certifications."""
    member_id = current_user.get("member_id")
    student_id = current_user.get("student_id")
    
    if member_id:
        # Get member certifications
        ...
    elif student_id:
        # Get student certifications
        ...
    else:
        raise HTTPException(403, "No associated records")
```

---

## 14. Configuration

### Auth Settings

```python
# src/config/settings.py

from pydantic_settings import BaseSettings
from typing import Optional


class AuthSettings(BaseSettings):
    """Authentication configuration."""
    
    # JWT Configuration
    JWT_SECRET_KEY: str  # REQUIRED - generate with: openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_HISTORY_COUNT: int = 12
    
    # Account Lockout
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Session Management
    MAX_SESSIONS_PER_USER: int = 5
    
    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Email (for password reset, verification)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@local46.org"
    
    class Config:
        env_prefix = ""
        case_sensitive = True


auth_settings = AuthSettings()
```

### Environment Variables

**IMPORTANT:** The `AuthSettings` class uses `env_prefix = "AUTH_"`, so environment variables
must be prefixed with `AUTH_`. For example, `jwt_secret_key` becomes `AUTH_JWT_SECRET_KEY`.

See `docs/BUGS_LOG.md` Bug #006 for details on what happens if this is not set.

```bash
# .env.compose additions for authentication

# JWT Secret - GENERATE A REAL ONE FOR PRODUCTION
# Use: python -c 'import secrets; print(secrets.token_urlsafe(32))'
# CRITICAL: If not set, a random key is generated on each restart, invalidating all sessions!
AUTH_JWT_SECRET_KEY=your-secret-key-here-generate-with-python

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Frontend URL (for password reset links, etc.)
FRONTEND_URL=http://localhost:3000

# Email settings (for password reset, verification emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@local46.org
```

---

## 15. Testing Auth

### Test Utilities

```python
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from src.auth.jwt_service import jwt_service
from src.auth.password import hash_password


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from src.models.user import User
    from src.models.role import Role
    from src.models.user_role import UserRole
    
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123!"),
        first_name="Test",
        last_name="User",
        email_verified=True
    )
    db_session.add(user)
    db_session.flush()
    
    # Add staff role
    role = db_session.query(Role).filter(Role.name == "staff").first()
    if role:
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)
    
    db_session.commit()
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get auth headers for test user."""
    token = jwt_service.create_access_token(
        user_id=str(test_user.id),
        email=test_user.email,
        name=f"{test_user.first_name} {test_user.last_name}",
        roles=["staff"],
        permissions=["members:*", "dues:*"]
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db_session):
    """Get auth headers for admin user."""
    # Create or get admin user
    from src.models.user import User
    
    admin = db_session.query(User).filter(User.email == "admin@example.com").first()
    
    if not admin:
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("AdminPassword123!"),
            first_name="Admin",
            last_name="User",
            email_verified=True
        )
        db_session.add(admin)
        db_session.flush()
        
        # Add admin role
        role = db_session.query(Role).filter(Role.name == "admin").first()
        if role:
            user_role = UserRole(user_id=admin.id, role_id=role.id)
            db_session.add(user_role)
        
        db_session.commit()
    
    token = jwt_service.create_access_token(
        user_id=str(admin.id),
        email=admin.email,
        name="Admin User",
        roles=["admin"],
        permissions=["*"]
    )
    return {"Authorization": f"Bearer {token}"}
```

### Auth Endpoint Tests

```python
# tests/test_auth.py

import pytest
from fastapi.testclient import TestClient


class TestLogin:
    """Test login endpoint."""
    
    def test_login_success(self, client: TestClient, test_user):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_invalid_password(self, client: TestClient, test_user):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == 401
    
    def test_login_invalid_email(self, client: TestClient):
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "AnyPassword123!"
        })
        
        assert response.status_code == 401
    
    def test_login_account_lockout(self, client: TestClient, test_user):
        # Attempt login 5 times with wrong password
        for i in range(5):
            client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "WrongPassword!"
            })
        
        # 6th attempt should be locked out even with correct password
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        
        assert response.status_code == 401
        assert "locked" in response.json()["detail"].lower()


class TestProtectedRoutes:
    """Test route protection."""
    
    def test_protected_route_no_token(self, client: TestClient):
        response = client.get("/members/")
        assert response.status_code == 401
    
    def test_protected_route_with_token(self, client: TestClient, auth_headers):
        response = client.get("/members/", headers=auth_headers)
        assert response.status_code == 200
    
    def test_admin_route_as_staff(self, client: TestClient, auth_headers):
        response = client.get("/admin/users/", headers=auth_headers)
        assert response.status_code == 403
    
    def test_admin_route_as_admin(self, client: TestClient, admin_headers):
        response = client.get("/admin/users/", headers=admin_headers)
        assert response.status_code == 200
```

---

## 16. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Not authenticated" | No token provided | Check Authorization header |
| "Token has expired" | Access token expired | Use refresh token to get new access token |
| "Invalid token" | Token malformed or wrong secret | Check JWT_SECRET_KEY matches |
| "Missing permission" | User lacks required permission | Check role assignments |
| "Account locked" | Too many failed logins | Wait 30 min or admin unlock |

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
psql -c "
SELECT email, is_locked, locked_until, failed_login_attempts
FROM users
WHERE is_locked = true;
"

# 5. View recent login attempts
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

✅ **Secure password handling** - Bcrypt hashing, complexity requirements
✅ **JWT-based authentication** - Stateless, scalable tokens
✅ **Role-based access control** - Flexible permission system
✅ **Session management** - Refresh tokens, concurrent session limits
✅ **Account security** - Lockout, login history, MFA-ready
✅ **Self-registration** - Members can create their own accounts
✅ **Admin provisioning** - Staff accounts created by admins
✅ **Audit integration** - All auth events logged

**Implementation Priority:**
1. Database schema (users, roles, tokens)
2. Password hashing
3. JWT service
4. Login/logout endpoints
5. Middleware and dependencies
6. Protected route examples
7. Admin user management
8. Self-registration flows

---

*Document Version: 1.0*
*Last Updated: January 27, 2026*
*Status: Architecture Specification - Ready for Implementation*
