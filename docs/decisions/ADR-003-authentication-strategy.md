# ADR-003: Authentication Strategy

## Status
**Accepted** - Phase 1.1 (Database Schema) Implemented 2026-01-28

## Date
2026-01-28 (Updated with implementation status)

## Context

We need authentication for the IP2A staff interface and future member portal. Requirements:
- Support internal users (staff, officers, admins)
- Support external users (members, stewards)
- Audit trail of who performed actions
- Session management
- Role-based access control (RBAC)

## Options Considered

### Option A: Session-based Authentication (Traditional)
- Server stores session in database/Redis
- Cookie-based identification
- Simple to implement
- Requires session storage infrastructure

### Option B: JWT (JSON Web Tokens)
- Stateless authentication
- Token contains user identity and roles
- No server-side session storage required
- Industry standard for APIs

### Option C: OAuth2 with External Provider
- Delegate auth to Google/Microsoft
- Less password management
- Dependency on external service
- May not suit all union members

## Decision

We will use **JWT-based authentication** with:
- Access tokens (15 minute expiry)
- Refresh tokens (7 day expiry, stored in database with rotation support)
- Bcrypt password hashing (to be implemented in Phase 1.2)
- Role-based access control (RBAC) with many-to-many User-Role relationship
- User optionally linked to Member record (one-to-one)

### Implementation Status

**Phase 1.1 (Database Schema) - ✅ COMPLETE**
- User model with email/password, optional Member link, soft delete
- Role model with system role protection
- UserRole junction table with assignment metadata (assigned_by, expires_at)
- RefreshToken model with token rotation, revocation, device tracking
- 6 default system roles: admin, officer, staff, organizer, instructor, member
- Migration: `e382f497c5e3`
- 16 tests passing

**Phase 1.2 (JWT Implementation) - 🔜 NEXT**
- Password hashing with bcrypt
- JWT token generation and validation
- Login/logout endpoints
- Token refresh flow
- Password reset flow

## Consequences

### Positive
- Stateless API (easier to scale)
- Standard approach, well-documented
- Works with future mobile apps
- No session storage infrastructure needed
- RBAC provides flexible, granular permissions
- User-Member link allows seamless portal access for union members
- Refresh token storage allows token rotation and revocation
- Soft delete on users maintains audit trail integrity

### Negative
- Token revocation requires refresh token tracking (implemented via RefreshToken table)
- Slightly more complex than session cookies
- RBAC adds database complexity vs simple role string

### Risks
- JWT secret key compromise = full breach
  - **Mitigation:** Rotate keys, use strong secrets, monitor for anomalies
- Refresh token theft could allow extended access
  - **Mitigation:** Device tracking, token rotation, revocation support

## Technical Details

### Database Schema (Implemented)

```
users
├── id (PK)
├── email (unique, indexed)
├── password_hash
├── first_name, last_name
├── is_active, is_verified
├── last_login, failed_login_attempts, locked_until
├── member_id (FK → members.id, nullable, unique)
├── timestamps (created_at, updated_at)
└── soft delete (is_deleted, deleted_at)

roles
├── id (PK)
├── name (unique, indexed)
├── display_name
├── description
├── is_system_role (prevents deletion)
└── timestamps

user_roles (junction table)
├── id (PK)
├── user_id (FK → users.id, CASCADE)
├── role_id (FK → roles.id, CASCADE)
├── assigned_by (audit trail)
├── assigned_at
├── expires_at (optional role expiration)
└── timestamps

refresh_tokens
├── id (PK)
├── user_id (FK → users.id, CASCADE)
├── token_hash (unique, indexed - tokens stored as hash)
├── expires_at
├── is_revoked, revoked_at
├── device_info, ip_address (device tracking)
└── timestamps
```

### Default Roles (Seeded)

1. **admin** - Full system access
2. **officer** - Union officer privileges (approve benevolence, manage grievances)
3. **staff** - Staff-level access (manage members, employment records)
4. **organizer** - SALTing and organizing access
5. **instructor** - Training program access
6. **member** - Basic member access (view own records, submit requests)

## References
- See: [docs/architecture/AUTHENTICATION_ARCHITECTURE.md](../architecture/AUTHENTICATION_ARCHITECTURE.md)
- Migration: `src/db/migrations/versions/e382f497c5e3_add_auth_models_user_role_userrole_.py`
- Models: `src/models/{user,role,user_role,refresh_token}.py`
- Services: `src/services/{user,role,user_role}_service.py`
- Tests: `src/tests/test_auth_{models,services}.py`
