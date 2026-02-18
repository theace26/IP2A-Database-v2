# UnionCore — Week 43: Developer Super Admin Role (Backend)
**Spoke:** Spoke 3: Infrastructure (⚠️ Scope Note: Backend role system is technically Spoke 1 territory, but this was assigned via Hub handoff as part of the infrastructure enhancement bundle. Proceed with implementation.)
**Phase:** UI Enhancement Bundle — Item 3A of 5
**Estimated Effort:** 2–3 hours
**Prerequisites:** Item 1 (Flatten Sidebar) committed and merged, git status clean
**Source:** Hub Handoff Document (February 10, 2026) + ADR-019 (Developer Super Admin Role)

---

## Context

The Developer role (level 255) is an unrestricted super admin role for dev/demo environments only. It enables:
- Full access to every endpoint and UI element
- A "View As" toggle to impersonate any business role for testing RBAC
- Audit logging always records the real user identity, never the impersonated role

This item covers the **backend** implementation. The frontend View As toggle is Item 3B (separate instruction document).

**CRITICAL: The Developer role must NEVER be seeded in production data. Dev and demo seed data only.**

---

## Pre-Flight Checklist

- [ ] `git status` is clean
- [ ] Create and checkout branch: `git checkout -b feature/developer-role`
- [ ] App starts without errors
- [ ] Record current test count: `pytest --tb=short -q 2>&1 | tail -5`
- [ ] Read ADR-019 if it exists: `cat docs/adr/ADR-019*.md` (or similar path — search for it)

---

## Step 1: Discover the Role System

**Do this before writing any code. This step is mandatory.**

Find and read every file involved in the role system:

```bash
# Find the role definition
grep -rn "role" src/models/ --include="*.py" -l
grep -rn "ROLE_LEVELS\|role_level\|RoleEnum\|UserRole" src/ --include="*.py" -l

# Find permission check functions
grep -rn "has_permission\|check_permission\|require_role\|role_required" src/ --include="*.py" -l

# Find hardcoded admin checks
grep -rn "role == .admin.\|role == \"admin\"\|== 'admin'\|== \"admin\"" src/ --include="*.py"
grep -rn "role_level >= 100" src/ --include="*.py"

# Find the auth middleware
grep -rn "middleware\|get_current_user\|authenticate" src/ --include="*.py" -l

# Find seed data scripts
find . -name "seed*.py" -o -name "*seed*" -o -name "fixtures*" | head -20
grep -rn "seed\|populate\|initial_data" src/ --include="*.py" -l

# Find session management
grep -rn "session\|cookie\|SessionMiddleware" src/ --include="*.py" -l
```

Read every file these searches turn up. Document:

1. **Role definition location** — where is the enum/model? What are the current roles and levels?
2. **Permission check pattern** — is it level-based (`>=`), role-name-based (`in [...]`), or permission-string-based (`has_permission('manage_members')`)?
3. **Auth middleware** — how does the current user get attached to the request? What object/attribute holds the role?
4. **Session implementation** — is there server-side session? Cookie-based? What library (e.g., `starlette.middleware.sessions`, `itsdangerous`)?
5. **Seed data** — where do test/demo users get created? What's the pattern?
6. **Audit logging** — how are user actions logged? What field records the acting user?

**If any of these don't exist yet**, note it — you'll need to create them.

---

## Step 2: Add the Developer Role

In the role definition file (found in Step 1), add:

```python
# Role level 255 — above all business roles, dev/demo only
DEVELOPER = "developer"  # Level 255
```

Update the role hierarchy/level mapping:

```python
# Add to existing mapping — keep all current entries, just add this one
"developer": 255,  # Dev/demo environments only — see ADR-019
```

**Adapt to the actual pattern.** If roles are an Enum class, add an enum member. If it's a dict, add a key. If it's a list of tuples, add a tuple. Match what's there.

### Verification
```bash
python -c "from src.models.whatever import RoleEnum; print(RoleEnum.DEVELOPER)"
# OR
python -c "from src.models.whatever import ROLE_LEVELS; print(ROLE_LEVELS['developer'])"
```

Adjust import path to match actual location.

---

## Step 3: Update Permission Checks

Search for every permission check in the codebase and ensure `developer` (level 255) passes all of them.

```bash
# Find ALL permission checks
grep -rn "has_permission\|check_permission\|require_role\|role_required\|role ==" src/ --include="*.py"
grep -rn "role in \[" src/ --include="*.py"
grep -rn "role_level >=" src/ --include="*.py"
```

**Three scenarios:**

### Scenario A: Level-based checks (`role_level >= N`)
If all permission checks use `>=` level comparisons, the developer role (255) already passes everything. **Verify this is true for every check**, then no changes needed.

### Scenario B: Role-name-based checks (`role in ['admin', 'officer']`)
Every such check needs `'developer'` added to the list. Example:

```python
# Before
if current_user.role in ['admin', 'officer']:

# After
if current_user.role in ['admin', 'officer', 'developer']:
```

**Do this for every occurrence.** Use find-and-replace carefully — each check has a different set of roles, so you can't do a blind global replace.

### Scenario C: Permission-string-based checks (`has_permission('manage_members')`)
The `has_permission` function needs to return `True` for developer role on ALL permission strings. Add an early return:

```python
def has_permission(user, permission: str) -> bool:
    if user.role == "developer":
        return True  # Developer bypasses all permission checks
    # ... existing logic
```

### Scenario D: Mixed approach
Some codebases mix approaches. Handle each pattern as found.

**Also check templates:**
```bash
grep -rn "has_permission\|current_user.role" src/templates/ --include="*.html"
```

Template permission checks need the same treatment. If they use `{% if current_user.role in ['admin'] %}`, add `'developer'`. If they use a function that you've already updated with an early return, no template changes needed.

---

## Step 4: Add View As Session Middleware

Create a new middleware that:
1. Checks if the current user's role is `developer`
2. Reads a `viewing_as` value from the session
3. Sets `request.state.effective_role` (or equivalent) for templates and permission checks
4. **NEVER** modifies the actual user record or audit trail

### Pre-Requisite: Session Support

Check if session middleware already exists:

```bash
grep -rn "SessionMiddleware\|session" src/main.py
```

If **no session middleware exists**, add it. FastAPI/Starlette example:

```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "dev-secret-change-in-prod"))
```

Add `SESSION_SECRET` to `.env.template` with a comment that it must be changed in production.

### The Middleware

Create a new file or add to existing middleware:

**File:** `src/middleware/view_as.py` (or wherever middleware lives — match existing pattern)

```python
async def view_as_middleware(request, call_next):
    """
    Developer View As middleware.

    When a developer user has set a 'viewing_as' session value,
    inject the effective role into request state so templates and
    permission checks can use it.

    Audit logging ALWAYS uses request.user (real identity), never effective_role.
    """
    # Default: effective role matches actual role
    request.state.effective_role = getattr(request.user, 'role', None)
    request.state.is_impersonating = False
    request.state.viewing_as = None

    if hasattr(request, 'user') and getattr(request.user, 'role', None) == 'developer':
        viewing_as = request.session.get('viewing_as', None)
        if viewing_as:
            request.state.effective_role = viewing_as
            request.state.is_impersonating = True
            request.state.viewing_as = viewing_as

    response = await call_next(request)
    return response
```

**Adapt this to the actual codebase patterns.** If the app uses a dependency injection pattern instead of middleware (e.g., `Depends(get_current_user)`), the View As logic might belong in the `get_current_user` dependency instead. Match the existing architecture.

### Wire Up the Middleware

Register the middleware in `src/main.py` (or wherever app initialization happens). The View As middleware must run **after** authentication middleware (so `request.user` exists):

```python
# Order matters — middleware runs in reverse registration order in Starlette
app.add_middleware(ViewAsMiddleware)  # Runs second (after auth)
# ... auth middleware already registered  # Runs first
```

### Update Permission Checks to Use Effective Role

Now that `request.state.effective_role` exists, permission checks (from Step 3) should read from it when evaluating **UI visibility and page access**, but NOT when logging audit events.

This is the most delicate part. There are two approaches:

**Approach A (Recommended): Update the permission function to read effective_role**

```python
def has_permission(request_or_user, permission: str) -> bool:
    # Use effective_role for permission checks (respects View As)
    effective_role = getattr(request_or_user, 'state', None)
    if effective_role:
        role = request_or_user.state.effective_role
    else:
        role = request_or_user.role

    # Developer role (real, not impersonated) bypasses everything
    if role == "developer" and not getattr(request_or_user.state, 'is_impersonating', False):
        return True

    # Normal permission logic using role
    ...
```

**Approach B: Update the template context to pass effective_role**

Make the Jinja2 template context include `effective_role` so templates can use `{% if effective_role in [...] %}`:

```python
# In the template context / dependency that sets template variables
templates.TemplateResponse("page.html", {
    "request": request,
    "current_user": request.user,
    "effective_role": request.state.effective_role,
    "is_impersonating": request.state.is_impersonating,
    "viewing_as": request.state.viewing_as,
})
```

**Discover which approach fits the codebase** by reading how templates currently access user role info.

---

## Step 5: Add View As API Endpoints

Create a new router for developer-only endpoints.

**File:** `src/routers/dev_router.py` (or similar)

```python
# POST /api/v1/dev/view-as
# Body: {"role": "organizer"} or {"role": null}
# Only accessible by developer role (real role, not effective)
# Sets viewing_as in session
# Returns 200 OK

# DELETE /api/v1/dev/view-as
# Clears viewing_as from session
# Returns 200 OK
```

Implementation requirements:

1. **Guard with real role check** — use `request.user.role`, NOT `request.state.effective_role`
2. **Validate the target role** — only allow valid business roles (admin, officer, staff, organizer, instructor, steward, member, applicant). Reject "developer" as a View As target (you're already developer).
3. **Set/clear session value** — `request.session['viewing_as'] = role` or `del request.session['viewing_as']`
4. **Return simple JSON response** — `{"status": "ok", "viewing_as": "organizer"}` or `{"status": "ok", "viewing_as": null}`
5. **Non-developer users get 403** — hard 403, no information leakage

Register the router in `src/main.py`:

```python
from src.routers.dev_router import router as dev_router
app.include_router(dev_router, prefix="/api/v1/dev", tags=["developer"])
```

---

## Step 6: Update Seed Data

Find the seed data scripts (located in Step 1) and add developer users.

**Dev seed data:**
```python
{
    "email": "dev@ibew46.dev",
    "password": "dev-password-change-me",  # Use whatever password hashing the codebase uses
    "first_name": "Developer",
    "last_name": "Admin",
    "role": "developer",
    "is_active": True,
}
```

**Demo seed data** (if separate):
```python
{
    "email": "demo_dev@ibew46.demo",
    "password": "demo-dev-password",
    "first_name": "Dev",
    "last_name": "User",
    "role": "developer",
    "is_active": True,
}
```

**CRITICAL: Do NOT add a developer user to any production seed data.** If there's a production seed script or a conditional check like `if environment == 'production'`, the developer user must be excluded.

---

## Step 7: Write Tests

Create tests in the test infrastructure. File location should match existing test patterns (e.g., `tests/test_auth/`, `tests/test_infrastructure/`, or `tests/test_api/`).

### Required Tests

**Role system tests:**
```python
def test_developer_role_exists():
    """Developer role is defined with level 255."""

def test_developer_role_has_highest_level():
    """Developer level (255) exceeds admin level (100)."""

def test_developer_bypasses_all_permissions():
    """Developer role passes every permission check."""
```

**View As endpoint tests:**
```python
def test_view_as_set_role(developer_client):
    """POST /api/v1/dev/view-as sets viewing_as in session."""
    response = developer_client.post("/api/v1/dev/view-as", json={"role": "organizer"})
    assert response.status_code == 200

def test_view_as_clear_role(developer_client):
    """DELETE /api/v1/dev/view-as clears viewing_as from session."""
    response = developer_client.delete("/api/v1/dev/view-as")
    assert response.status_code == 200

def test_view_as_rejects_non_developer(admin_client):
    """Non-developer roles get 403 on View As endpoints."""
    response = admin_client.post("/api/v1/dev/view-as", json={"role": "member"})
    assert response.status_code == 403

def test_view_as_rejects_invalid_role(developer_client):
    """View As rejects invalid role names."""
    response = developer_client.post("/api/v1/dev/view-as", json={"role": "superuser"})
    assert response.status_code in (400, 422)

def test_view_as_rejects_developer_target(developer_client):
    """Cannot View As developer — you already are one."""
    response = developer_client.post("/api/v1/dev/view-as", json={"role": "developer"})
    assert response.status_code in (400, 422)
```

**Effective role tests:**
```python
def test_effective_role_matches_actual_when_not_impersonating(developer_client):
    """Without View As active, effective_role equals actual role."""

def test_effective_role_changes_when_viewing_as(developer_client):
    """With View As active, effective_role reflects the impersonated role."""

def test_permission_check_uses_effective_role(developer_client):
    """Permission checks respect effective_role during impersonation."""
```

**Audit integrity tests:**
```python
def test_audit_log_records_real_user_during_impersonation():
    """Audit logs always record the real developer identity, never the impersonated role."""
    # Set View As to organizer
    # Perform an action that creates an audit log entry
    # Verify the audit log shows the developer user, not "organizer"
```

### Test Fixtures

Add to `conftest.py` (or wherever shared fixtures live):

```python
@pytest.fixture
def developer_user(db_session):
    """Create a developer user for testing."""
    # Use the same pattern as existing user fixtures
    ...

@pytest.fixture
def developer_client(app, developer_user):
    """Authenticated test client with developer role."""
    # Use the same pattern as existing authenticated client fixtures
    ...
```

---

## Step 8: Verify End-to-End

```bash
# Run full test suite
pytest --tb=short -q

# Verify test count increased (new tests should add ~8-12 tests)
# Verify zero failures

# Manual verification
# 1. Start the app
# 2. Login as dev@ibew46.dev
# 3. Verify you can access all pages
# 4. Hit POST /api/v1/dev/view-as with {"role": "organizer"} via curl or browser devtools
# 5. Verify subsequent page loads show organizer-level access
# 6. Hit DELETE /api/v1/dev/view-as
# 7. Verify full access restored
```

---

## Anti-Patterns to Avoid

- **DO NOT** modify the User model's `role` field during impersonation. The session holds `viewing_as`; the user record is untouched.
- **DO NOT** create a separate "developer" database table. Developer is just another role value.
- **DO NOT** add developer users to production seed data.
- **DO NOT** skip the early-return optimization in permission checks — checking level 255 against every rule is wasteful.
- **DO NOT** log the impersonated role in audit events. Always log `request.user` (real identity).
- **DO NOT** allow View As to target "developer" — that's circular and pointless.
- **DO NOT** forget to validate that the target role in View As is a real role. Arbitrary strings should be rejected.

---

## Acceptance Criteria

- [ ] Developer role exists in the role system with level 255
- [ ] Developer role passes all permission checks in the codebase
- [ ] `POST /api/v1/dev/view-as` sets session correctly
- [ ] `DELETE /api/v1/dev/view-as` clears session correctly
- [ ] Non-developer roles get 403 on `/api/v1/dev/view-as`
- [ ] Invalid/missing roles are rejected with 400/422
- [ ] Audit logs record real user identity during impersonation
- [ ] Dev seed data includes developer user
- [ ] Production seed data does NOT include developer user
- [ ] Session middleware correctly sets `effective_role` and `is_impersonating`
- [ ] All existing tests still pass
- [ ] New tests written and passing (target: 8-12 new tests minimum)

---

## File Manifest

**Created files:**
- `src/middleware/view_as.py` (or integrated into existing middleware — match pattern)
- `src/routers/dev_router.py`
- `tests/test_developer_role.py` (or wherever test pattern dictates)

**Modified files:**
- Role definition file (model/enum — location found in Step 1)
- Permission check function(s) — add developer bypass
- `src/main.py` — register dev_router, add session middleware if missing
- Seed data script(s) — add developer user
- `conftest.py` — add developer_user and developer_client fixtures
- `.env.template` — add `SESSION_SECRET` if session middleware was added

**Deleted files:**
- None

---

## Git Commit Message

```
feat(auth): add Developer super admin role (level 255) with View As

- Add developer role to role system at level 255
- Developer bypasses all permission checks
- Add View As API endpoints (POST/DELETE /api/v1/dev/view-as)
- Add session middleware for effective role impersonation
- Audit logs always record real user identity
- Add developer user to dev/demo seed data (NOT production)
- Add comprehensive tests for role, endpoints, and impersonation
- Implements ADR-019
- Spoke 3: Infrastructure (via Hub handoff)
```

---

## Session Close-Out

After committing:

1. Update `CLAUDE.md` — note developer role addition, new test count
2. Update `CHANGELOG.md` — add entry for developer role feature
3. Update docs under `/docs/` — especially any auth/role documentation
4. **Cross-Spoke Impact Note:** This changes the permission system globally. Generate a handoff note for Spoke 1 and Spoke 2 informing them that:
   - A new `developer` role exists at level 255
   - `request.state.effective_role` is now available in all request contexts
   - Any new permission checks they write should either use the centralized `has_permission()` function (which already handles developer bypass) or add `'developer'` to role lists
5. **ADR-019:** If it doesn't exist yet, flag to the user that it should be created in the Hub

---

*Spoke 3: Infrastructure — Item 3A of UI Enhancement Bundle*
*UnionCore v0.9.16-alpha*
