# ADR-019: Developer Super Admin Role with View As Impersonation

**Status:** Accepted
**Date:** February 10, 2026
**Decision Makers:** Xerxes (Project Lead)
**Affects:** Spoke 1 (Core Platform), Spoke 3 (Infrastructure/UI)

---

## Context

UnionCore's RBAC hierarchy has Admin (level 100) as the highest business role, with full CRUD and user management. However, no single business role organically has visibility into how every other role experiences the UI. During development and QA, the developer needs to:

1. Access every feature and every page in the system without restriction.
2. Verify that RBAC correctly restricts each role's view (e.g., confirm an Organizer truly cannot see Benevolence).
3. Test UI rendering for each role without maintaining 8+ separate test accounts.

The current Admin role is a **business role** — it represents the IT admin or Business Manager. It should not be overloaded with developer/QA capabilities that would be inappropriate in production.

## Decision

Add a **Developer** role at level 255 with the following characteristics:

| Attribute | Value |
|---|---|
| Role name | `developer` |
| Level | 255 |
| Inherits | All permissions from all roles |
| Additional capability | "View As" role impersonation toggle |
| Production presence | **NEVER** — dev/demo environments only |

### View As Impersonation

The Developer role includes a persistent UI toggle (top navbar, next to the user menu) that allows rendering the entire UI as any other role would see it.

**Behavior when View As is active:**

- Sidebar navigation shows/hides items per the impersonated role's permissions
- Dashboard cards display data scoped to the impersonated role
- Page-level access restrictions apply as if the user holds the impersonated role
- A visible banner indicates impersonation is active: "Viewing as: [Role Name]"
- **Audit logging ALWAYS records the real user (Developer), never the impersonated role**
- The `viewing_as` parameter is stored in the session, not the JWT
- API-level permissions are NOT bypassed — the impersonation only affects UI rendering and frontend permission checks

**Behavior when View As is inactive (default):**

- Developer sees everything — equivalent to Admin + all specialized role views combined
- No restrictions on navigation, pages, or data visibility

### Security Constraints

1. The Developer role **must not exist in production**. The production deployment checklist must include verification that no user accounts have the `developer` role.
2. Seed data creates one Developer account. Demo data creates one Developer account.
3. The `developer` role cannot be assigned through the UI — it requires direct database insertion or seed script execution.
4. The View As toggle must be invisible to all non-Developer roles (not just disabled — absent from the DOM).

## Consequences

**Positive:**
- Single account for comprehensive QA across all role perspectives
- Explicit separation between business admin and developer capabilities
- Audit trail integrity maintained during impersonation
- Reduces need for 8+ test accounts during development

**Negative:**
- One more role in the RBAC system to maintain
- Requires discipline to exclude from production deployments
- View As middleware adds a small layer of complexity to request processing

**Risks:**
- If a Developer account accidentally reaches production, it bypasses all business role restrictions. Mitigated by: deployment checklist verification, no UI-based assignment, and audit logging that makes Developer actions visible.

## Implementation Notes

- Backend: Add `developer` to the Role enum/model at level 255. Update permission checks to recognize level 255 as unrestricted. Add `viewing_as` session middleware.
- Frontend: Add View As dropdown to navbar (Developer-only). Add impersonation banner. Update all `{% if has_permission() %}` checks to respect `viewing_as` context.
- Seed data: Add one developer user to both dev and demo seed scripts.
- Tests: Add tests verifying View As renders correctly for each role, and that audit logs record the real user during impersonation.

---

## Implementation Status

**Status: ✅ COMPLETE — February 10, 2026 (v0.9.24-alpha → v0.9.25-alpha)**

| Component | Status | Location |
|-----------|--------|----------|
| Developer role enum (`RoleType.DEVELOPER`) | ✅ Complete | `src/db/enums/auth_enums.py` |
| Role level 255 in hierarchy | ✅ Complete | `src/core/permissions.py` |
| All audit permissions granted | ✅ Complete | `src/core/permissions.py` |
| Sensitive field redaction bypassed | ✅ Complete | `src/core/permissions.py` |
| Developer role seed | ✅ Complete | `src/seed/auth_seed.py` |
| Demo developer account | ✅ Complete | `src/db/demo_seed.py` |
| View As API endpoints (3) | ✅ Complete | `src/routers/view_as.py` |
| SessionMiddleware configured | ✅ Complete | `src/main.py` |
| `viewing_as` injected into request context | ✅ Complete | `src/routers/dependencies/auth_cookie.py` |
| View As dropdown in navbar | ✅ Complete | `src/templates/components/_navbar.html` |
| Impersonation banner in base template | ✅ Complete | `src/templates/base.html` |
| Template permission checks use `effective_role` | ✅ Complete | All templates |
| Comprehensive tests (24+) | ✅ Complete | `src/tests/test_developer_view_as.py` |

### Files Created

```
src/routers/view_as.py                           # View As API (POST set, POST clear, GET current)
src/tests/test_developer_view_as.py              # 24+ tests covering all scenarios
```

### Files Modified

```
src/db/enums/auth_enums.py                       # Added DEVELOPER to RoleType
src/seed/auth_seed.py                            # Developer role creation + seed function
src/core/permissions.py                          # Level 255 bypass + audit permissions
src/routers/dependencies/auth_cookie.py          # viewing_as injected into user context
src/main.py                                      # SessionMiddleware + view_as router
src/templates/components/_navbar.html            # View As dropdown (developer-only)
src/templates/base.html                          # Impersonation banner (sticky, warning style)
src/db/demo_seed.py                              # demo_developer@ibew46.demo account
```

### Demo Accounts

| Email | Password | Role |
|-------|----------|------|
| `demo_developer@ibew46.demo` | `Demo2026!` | developer |
| `dev@ibew46.local` | `D3v3l0p3r!` | developer (dev seed only) |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/view-as/set/{role}` | POST | Set viewing role in session |
| `/api/v1/view-as/clear` | POST | Clear impersonation session |
| `/api/v1/view-as/current` | GET | Get current viewing_as role |

### Test Coverage

- Developer role enum validation and level 255 confirmation
- Authentication with developer credentials
- All audit permissions granted (VIEW_ALL, VIEW_USERS, VIEW_MEMBERS, VIEW_OWN, EXPORT)
- Sensitive field redaction disabled for developer
- View As: set role, clear role, get current role
- Invalid role rejection (400)
- Non-developer access denial (403)
- All business roles available for impersonation
- Session-based storage (not JWT)
- Production safety: developer role must not exist in production

### Production Safety Checklist

Before any production deployment:
```sql
SELECT u.email, r.name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE r.name = 'developer';
-- Must return 0 rows in production
```

---

*ADR-019 | Created: February 10, 2026 | Implemented: February 10, 2026 | UnionCore Hub*
