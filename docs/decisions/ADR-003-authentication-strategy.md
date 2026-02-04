# ADR-003: Authentication Strategy

> **Document Created:** 2026-01-28
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented — JWT + Cookie auth with RBAC, live in production

## Status
**Implemented** — Phase 1.1, 1.2, and Phase 6 Cookie Auth Complete. Enhanced in Week 16 (production hardening).

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
- Access tokens (30 minute expiry)
- Refresh tokens (7 day expiry, stored in database with rotation support)
- Bcrypt password hashing (12 rounds, version 2b, OWASP compliant)
- Role-based access control (RBAC) with many-to-many User-Role relationship
- User optionally linked to Member record (one-to-one)
- HTTP-only cookies for frontend session management

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| User/Role/UserRole/RefreshToken models | ✅ | 1 | Phase 1.1 — 16 tests |
| JWT token generation + validation | ✅ | 1 | Phase 1.2 — HS256, 30min/7day |
| Password hashing (bcrypt 12 rounds) | ✅ | 1 | OWASP, NIST SP 800-63B compliant |
| Account lockout (`locked_until` datetime) | ✅ | 1 | 5 attempts → 30min lockout |
| 6 default system roles (seeded) | ✅ | 1 | admin, officer, staff, organizer, instructor, member |
| 6 auth API endpoints | ✅ | 1 | login, logout, refresh, me, change-password, verify-token |
| Cookie-based auth for frontend | ✅ | 6 | HTTP-only cookies, redirect on expiry |
| Form-based login endpoint | ✅ | 6 | Bug #005 fix — POST /login accepts form data |
| First-time setup flow | ✅ | 6 | /setup with default admin management |
| Security headers (HSTS, CSP, etc.) | ✅ | 16 | Production hardening |
| Sentry error tracking | ✅ | 16 | Auth failure monitoring |
| Connection pooling | ✅ | 16 | Prevents auth-related DB exhaustion |

### Test Coverage
- 16 auth model/service tests (Phase 1.1)
- 26 authentication tests (Phase 1.2)
- 16 security robustness tests
- 22 frontend auth tests (cookie flow)
- 25 setup tests

> ⚠️ **IMPORTANT — Account Lockout Pattern:** The User model uses a `locked_until` **datetime** field, NOT a boolean `is_locked`. The lockout check is `user.locked_until and user.locked_until > datetime.utcnow()`. This allows automatic unlock after the lockout period expires without a separate unlock operation.

### Phase 1.1 (Database Schema) — ✅ COMPLETE
- User model with email/password, optional Member link, soft delete
- Role model with system role protection
- UserRole junction table with assignment metadata (assigned_by, expires_at)
- RefreshToken model with token rotation, revocation, device tracking
- 6 default system roles: admin, officer, staff, organizer, instructor, member
- Migration: `e382f497c5e3`

### Phase 1.2 (JWT Implementation) — ✅ COMPLETE
- Password hashing with bcrypt (12 rounds, version 2b, OWASP compliant)
- JWT token generation and validation (HS256 algorithm)
- Access tokens: 30-minute expiry
- Refresh tokens: 7-day expiry with automatic rotation
- Authentication middleware and FastAPI dependencies
- Role-based access control decorators
- Account lockout (5 failed attempts, 30-minute lockout via `locked_until` datetime)
- Device tracking (IP address, user-agent)
- 6 API endpoints: login, logout, refresh, me, change-password, verify-token
- OWASP, NIST SP 800-63B, PCI DSS 4.0 compliant

### Phase 6 Week 2 (Cookie-Based Auth for Frontend) — ✅ COMPLETE
- Cookie dependency: `src/routers/dependencies/auth_cookie.py`
- HTTP-only cookies set on login/logout
- Access token cookie: 30 min, path `/`
- Refresh token cookie: 7 days, path `/api/auth`
- Protected routes redirect to `/login` with flash message
- Token expiry handled gracefully with redirect

**Cookie Flow:**
1. User submits login form via HTMX to `POST /login` (form-based endpoint)
2. Server accepts URL-encoded form data via FastAPI `Form()` parameters
3. Server validates credentials using `authenticate_user()` service
4. Server creates tokens and sets HTTP-only cookies in response
5. Browser automatically sends cookies on subsequent requests
6. `auth_cookie.py` validates JWT from cookie on protected routes
7. On logout, cookies are cleared and user redirected to login

**Two Login Endpoints:**

| Endpoint | Content-Type | Use Case |
|----------|--------------|----------|
| `POST /login` | `application/x-www-form-urlencoded` | HTML forms (HTMX) |
| `POST /auth/login` | `application/json` | API clients (mobile, external services) |

**Form-Based Login (Bug #005 Fix — 2026-01-30):**

The original approach used the HTMX `json-enc` extension to convert form data to JSON for the `/auth/login` endpoint. This was unreliable in production (Railway deployment). Solution: Created a dedicated `POST /login` endpoint in `frontend.py` that accepts URL-encoded form data directly. See [docs/BUGS_LOG.md](../BUGS_LOG.md#bug-005-htmx-json-enc-extension-not-encoding-form-data) for full details.

### Week 16 (Production Hardening) — ✅ COMPLETE
- Security headers: HSTS, X-Content-Type-Options, X-Frame-Options, CSP
- Sentry integration for auth error monitoring
- Structured logging for auth events
- Connection pooling to prevent DB exhaustion under auth load

## Consequences

### Positive
- Stateless API (easier to scale)
- Standard approach, well-documented
- Works with future mobile apps and PWA (confirmed in Week 18)
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
  - **Mitigation:** Sentry alerting on auth anomalies (Week 16)
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
├── last_login, failed_login_attempts, locked_until  ← DATETIME, not boolean
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

1. **admin** — Full system access
2. **officer** — Union officer privileges (approve benevolence, manage grievances)
3. **staff** — Staff-level access (manage members, employment records)
4. **organizer** — SALTing and organizing access
5. **instructor** — Training program access
6. **member** — Basic member access (view own records, submit requests)

### System Setup Flow — ✅ COMPLETE (January 30, 2026)

The system has a first-time setup flow for creating initial user accounts:

**Setup Page:** `/setup`
- Service: `src/services/setup_service.py`
- Template: `src/templates/auth/setup.html`
- Route: `src/routers/frontend.py`
- Tests: `src/tests/test_setup.py` (25 tests)

**Default Admin Account (`admin@ibew46.com`):**
- Seeded automatically on deployment via `src/seed/auth_seed.py`
- Cannot be deleted or have email/password changed via setup page
- CAN be disabled via checkbox during setup (recommended for production)
- Can be re-enabled later from Staff Management if needed

**Setup Required When:**
- No users exist at all
- Only the default admin account exists (system not yet configured)

**Security Notes:**
- Strong password requirements enforced (8+ chars, 3 unique numbers, special char, capital, no repeating letters, no sequential numbers)
- Password validation with real-time client-side feedback (Alpine.js)
- Default admin account exists for recovery purposes but should be disabled in production

## References

### Phase 1.1 (Database Schema)
- Architecture: [docs/architecture/AUTHENTICATION_ARCHITECTURE.md](../architecture/AUTHENTICATION_ARCHITECTURE.md)
- Migration: `src/db/migrations/versions/e382f497c5e3_add_auth_models_user_role_userrole_.py`
- Models: `src/models/{user,role,user_role,refresh_token}.py`
- Services: `src/services/{user,role,user_role}_service.py`
- Tests: `src/tests/test_auth_{models,services}.py`

### Phase 1.2 (JWT Implementation)
- Configuration: `src/config/auth_config.py`
- Core utilities: `src/core/{security,jwt}.py`
- Schemas: `src/schemas/auth.py`
- Services: `src/services/auth_service.py` (updated: `user_service.py`)
- Dependencies: `src/routers/dependencies/auth.py`
- Router: `src/routers/auth.py`
- Tests: `src/tests/test_auth_{jwt,authentication,router}.py`
- Security tests: `src/tests/test_security_robustness.py`
- Security documentation: [docs/standards/password-security.md](../standards/password-security.md)

### Phase 6 (Cookie Auth)
- Cookie dependency: `src/routers/dependencies/auth_cookie.py`
- Form endpoint: `src/routers/frontend.py` (POST `/login`)
- API endpoint: `src/routers/auth.py` (POST `/auth/login`)
- Login template: `src/templates/auth/login.html`
- Frontend tests: `src/tests/test_frontend.py` (22 tests)

### Week 16 (Production Hardening)
- Security headers middleware
- Sentry configuration: `src/config/sentry_config.py`
- Structured logging: `src/config/logging_config.py`

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-01-28 — original with Phase 1.1/1.2 and Phase 6 implementation details)
