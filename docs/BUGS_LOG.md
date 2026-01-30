# IP2A-v2 Bugs Log

A historical record of bugs encountered and resolved during development.

---

## Bug #001: Login Page `[object Object]` Error

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** High (blocking user login)
**Status:** RESOLVED

### Symptoms
- User sees `[object Object]` displayed in the error alert on the login page
- Unable to see actual error message (e.g., "Invalid email or password")
- Login functionality appears broken even though backend is working

### Root Cause Analysis

The issue stemmed from a mismatch between how HTMX sends form data and how FastAPI expects to receive it:

1. **HTMX Default Behavior**: HTMX sends form data as `application/x-www-form-urlencoded` by default
   ```
   Content-Type: application/x-www-form-urlencoded
   Body: email=user%40example.com&password=secret123
   ```

2. **FastAPI Expectation**: The `/auth/login` endpoint uses a Pydantic model (`LoginRequest`) which expects JSON:
   ```python
   @router.post("/login", response_model=TokenResponse)
   def login(login_data: LoginRequest, ...):  # Expects JSON body
   ```

3. **422 Response**: FastAPI returns a 422 Unprocessable Entity with Pydantic validation errors:
   ```json
   {
     "detail": [
       {
         "type": "model_attributes_type",
         "loc": ["body"],
         "msg": "Input should be a valid dictionary or object to extract fields from",
         "input": "email=xxx&password=xxx"
       }
     ]
   }
   ```

4. **JavaScript Error Handling Gap**: The error handling code tried to extract error messages but had edge cases where `String(errorObject)` produced `[object Object]`.

### Solution

**1. Added HTMX JSON Extension** (`src/templates/base_auth.html`):
```html
<!-- HTMX JSON encoding extension for sending JSON to API endpoints -->
<script src="https://unpkg.com/htmx.org@1.9.10/dist/ext/json-enc.js"></script>
```

**2. Updated Login Form** (`src/templates/auth/login.html`):
```html
<form id="login-form"
      hx-post="/auth/login"
      hx-ext="json-enc"  <!-- Added this attribute -->
      ...>
```

**3. Improved JavaScript Error Handling**:
```javascript
// Handle array of errors (like Pydantic validation)
errorText = response.detail.map(function(e) {
    if (typeof e === 'string') return e;
    if (e && typeof e === 'object') {
        return e.msg || e.message || e.detail || JSON.stringify(e);
    }
    return 'Validation error';
}).join(', ');

// Safeguard against [object Object]
if (errorText === '[object Object]') {
    errorText = 'Invalid email or password';
}
```

### Files Modified
- `src/templates/base_auth.html` - Added json-enc extension script
- `src/templates/auth/login.html` - Added `hx-ext="json-enc"` and improved error handling

### Commit
- `fcc983b fix: resolve [object Object] error on login page`

### Lessons Learned

1. **HTMX + FastAPI Integration**: When using HTMX forms with FastAPI JSON endpoints, always use the `json-enc` extension or configure FastAPI to accept form data with `Form()`.

2. **Defensive JavaScript**: Always have fallback error messages and safeguards when parsing API responses.

3. **Testing Gap**: The test suite used `json={}` in HTTP client calls, which worked correctly. Real browser testing with HTMX revealed the content-type mismatch.

### Prevention
- Added json-enc extension to base_auth.html so all auth forms can use JSON encoding
- Improved error handling to gracefully degrade to user-friendly messages
- Consider adding integration tests that simulate HTMX form submissions

---

## Bug #002: Dashboard 500 Error - Dict Access in Navbar

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** High (blocking dashboard access)
**Status:** RESOLVED

### Symptoms
- User logs in successfully
- Immediately sees 500 "Something Went Wrong" error page
- Cannot access dashboard or any protected pages

### Root Cause Analysis

The navbar template used dot notation to access `current_user` attributes:

```html
<!-- WRONG - treating dict as object -->
{{ current_user.first_name[0] if current_user else 'U' }}
```

But `current_user` is passed as a Python **dict**, not an object:

```python
# From auth_cookie.py
current_user = {
    "id": user.id,
    "email": user.email,
    "first_name": user.first_name,
    ...
}
```

Jinja2 can access dict keys with dot notation in some cases, but when the key doesn't exist, it raises `UndefinedError` instead of returning `None`.

### Solution

Changed to use `.get()` method for safe dict access:

```html
<!-- CORRECT - dict-style access with fallback -->
{{ current_user.get('first_name', 'U')[0] if current_user else 'U' }}
```

### Files Modified
- `src/templates/components/_navbar.html` - Lines 41, 46

### Commit
- `079d274 fix: use dict access for current_user in navbar template`

### Lessons Learned

1. **Jinja2 Dict vs Object Access**: When passing dicts to templates, use `.get()` for safe access with fallbacks.

2. **Consistency in User Data**: Consider whether `current_user` should be a dict or a proper User object/dataclass throughout the codebase.

3. **Error Visibility**: Railway logs showed the full stack trace - this was essential for diagnosis. Local testing didn't catch this because the test fixtures may differ from production flow.

### Prevention
- Use `.get()` method for all dict access in templates
- Consider creating a UserContext dataclass for type safety
- Add template rendering tests with mock user data

---

## Bug #003: Frontend Services Async/Await TypeError

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** High (blocking members/training/operations pages)
**Status:** RESOLVED

### Symptoms
- User logs in successfully
- Dashboard loads correctly
- Clicking on Members, Training, or Operations pages causes 500 error
- User gets logged out and redirected to login page
- Railway logs show: `TypeError: object ChunkedIteratorResult can't be used in 'await' expression`

### Root Cause Analysis

The frontend service files were incorrectly using `AsyncSession` and `await` keywords, but the actual database session is **synchronous** (`Session` from `sqlalchemy.orm`).

```python
# WRONG - using AsyncSession with synchronous db
from sqlalchemy.ext.asyncio import AsyncSession

class MemberFrontendService:
    def __init__(self, db: AsyncSession):  # Wrong type hint
        self.db = db

    async def get_member_stats(self) -> dict:
        total = (await self.db.execute(total_stmt)).scalar()  # await on sync!
```

When `await` is used on a synchronous `ChunkedIteratorResult`, Python raises:
```
TypeError: object ChunkedIteratorResult can't be used in 'await' expression
```

### Solution

Changed all three frontend service files to use synchronous patterns:

```python
# CORRECT - using Session without await
from sqlalchemy.orm import Session

class MemberFrontendService:
    def __init__(self, db: Session):  # Correct type hint
        self.db = db

    async def get_member_stats(self) -> dict:
        total = (self.db.execute(total_stmt)).scalar()  # No await
```

### Files Modified
- `src/services/member_frontend_service.py` - Changed AsyncSession to Session, removed await
- `src/services/training_frontend_service.py` - Changed AsyncSession to Session, removed await
- `src/services/operations_frontend_service.py` - Changed AsyncSession to Session, removed await

### Commit
- `28547db fix: remove async/await from synchronous db sessions`

### Lessons Learned

1. **SQLAlchemy Session Types**: The codebase uses synchronous `Session`, not `AsyncSession`. All database operations should NOT use `await`.

2. **FastAPI Async/Sync Compatibility**: FastAPI endpoints can be `async def` even when using synchronous database sessions - you just don't `await` the db calls.

3. **Production vs Local Testing**: Tests passed locally because httpx test client handles async correctly, but real production deployment exposed the mismatch.

4. **Copy-Paste Errors**: All three service files had the same bug, suggesting copy-paste from an async template without adapting to the synchronous session pattern.

### Prevention
- Establish clear pattern: services use `Session`, not `AsyncSession`
- Add type checking (mypy) to catch session type mismatches
- Document the synchronous session pattern in CLAUDE.md
- Review all service files for consistent session handling

---

## Bug #004: Mixed Content Blocking Static Files

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (completely blocking login and all functionality)
**Status:** RESOLVED

### Symptoms
- Login page shows "Input should be a valid dictionary or object to extract fields from"
- Browser console shows "Mixed Content" errors
- Static files (CSS, JS) blocked by browser
- All pages unstyled or non-functional

### Root Cause Analysis

Railway serves the application over HTTPS, but FastAPI's `url_for()` function generates absolute URLs using the internal HTTP protocol:

```html
<!-- url_for generates -->
<link href="http://app.railway.app/static/css/custom.css">

<!-- But page is served over -->
https://app.railway.app/...
```

Modern browsers block HTTP resources on HTTPS pages as "Mixed Content" for security.

This caused the `json-enc.js` script to fail loading, meaning HTMX forms still sent URL-encoded data instead of JSON - explaining why Bug #001 fix appeared not to work.

### Solution

Changed all `url_for('static', path='...')` calls to relative paths:

```html
<!-- Before -->
<link rel="stylesheet" href="{{ url_for('static', path='css/custom.css') }}">
<script src="{{ url_for('static', path='js/app.js') }}"></script>

<!-- After -->
<link rel="stylesheet" href="/static/css/custom.css">
<script src="/static/js/app.js"></script>
```

Relative URLs inherit the protocol from the page, avoiding mixed content.

### Files Modified
- `src/templates/base.html` - favicon, custom.css, app.js
- `src/templates/base_auth.html` - favicon, custom.css

### Commit
- `721d6fa fix: use relative URLs for static files to avoid mixed content`

### Lessons Learned

1. **Proxy Headers Matter**: FastAPI behind a reverse proxy (Railway, Heroku, etc.) needs proper proxy header handling to generate correct URLs.

2. **Relative URLs are Safer**: For static files, relative URLs (`/static/...`) avoid protocol mismatch issues entirely.

3. **Browser DevTools Essential**: The Mixed Content errors were only visible in browser console, not Railway logs.

4. **Cascading Failures**: This bug made Bug #001 fix appear not to work, because the `json-enc.js` script wasn't loading.

### Prevention
- Use relative URLs for all static file references
- Consider adding proxy header middleware for production deployments
- Test with browser DevTools open to catch console errors
- Document the static file URL pattern for the project

---

## Bug #005: HTMX json-enc Extension Not Encoding Form Data

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (blocking user login)
**Status:** RESOLVED

### Symptoms
- Login form returns 422 "Unprocessable Entity" error
- Browser console shows POST to `/auth/login` with 422 status
- Even after Bug #004 fix (Mixed Content), login still fails
- Error message: "Input should be a valid dictionary or object to extract fields from"

### Root Cause Analysis

The HTMX `json-enc` extension was supposed to convert form data to JSON before sending, but it wasn't working reliably:

1. **Extension Loading**: Even though `json-enc.js` was loading after the Mixed Content fix, the extension wasn't properly encoding the form data.

2. **Form Data vs JSON**:
   ```
   Expected by FastAPI: Content-Type: application/json
                        Body: {"email": "...", "password": "..."}

   Actual sent by HTMX: Content-Type: application/x-www-form-urlencoded
                        Body: email=...&password=...
   ```

3. **Pydantic Validation**: FastAPI's `LoginRequest` Pydantic model expects a JSON body, and URL-encoded form data causes a 422 validation error.

4. **Extension Unreliability**: The `hx-ext="json-enc"` attribute wasn't being recognized or applied consistently, possibly due to timing issues with extension loading.

### Solution

Created a dedicated form-based login endpoint that accepts URL-encoded form data directly, bypassing the need for the json-enc extension:

**1. Added Form-Based Login Endpoint** (`src/routers/frontend.py`):
```python
@router.post("/login")
async def login_form_submit(
    request: Request,
    response: HTMLResponse,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
):
    # Accepts URL-encoded form data directly
    # Uses same authenticate_user service as /auth/login
    # Sets HTTP-only cookies on success
```

**2. Updated Login Form** (`src/templates/auth/login.html`):
```html
<!-- Before -->
<form hx-post="/auth/login" hx-ext="json-enc" ...>

<!-- After -->
<form hx-post="/login" ...>
```

**3. Updated JavaScript Handler**:
```javascript
// Changed path check from '/auth/login' to '/login'
if (evt.detail.pathInfo.requestPath === '/login') {
```

### Files Modified
- `src/routers/frontend.py` - Added POST `/login` endpoint with Form() parameters
- `src/templates/auth/login.html` - Changed endpoint and removed json-enc extension

### Commit
- `439e10c fix: add form-based login endpoint to bypass json-enc extension`

### Lessons Learned

1. **CDN Extension Reliability**: Third-party HTMX extensions loaded from CDNs can be unreliable. For critical functionality, don't depend on them.

2. **Form Data is Default**: HTMX sends forms as URL-encoded by default. Instead of fighting this with extensions, accept form data on the backend.

3. **FastAPI Form() vs JSON**: FastAPI can easily accept form data using `Form()` parameters. This is often more robust than requiring JSON from HTML forms.

4. **Separate Endpoints**: Having a form-friendly endpoint (`/login`) separate from the JSON API endpoint (`/auth/login`) provides flexibility for different clients.

### Prevention
- Use FastAPI `Form()` parameters for HTML form submissions
- Reserve JSON body parsing for API clients (mobile apps, other services)
- Don't rely on browser extensions for critical authentication flows
- Test forms without JavaScript extensions to ensure fallback works

---

## Bug #006: JWT Token Signature Verification Failed on Container Restart

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (all users logged out on every deployment)
**Status:** RESOLVED

### Symptoms
- Users see "Token validation failed: Invalid token: Signature verification failed" errors in Railway logs
- After every container restart/deployment, all users are logged out
- Users must re-login after each deployment
- Error appears repeatedly in logs for every authenticated request

### Root Cause Analysis

The `AUTH_JWT_SECRET_KEY` environment variable was not set in production, causing the application to generate a new random secret on every startup:

```python
# src/config/auth_config.py
jwt_secret_key: str = Field(
    default_factory=lambda: secrets.token_urlsafe(32),  # Random on each startup!
    ...
)
```

**The Problem Chain:**
1. Container starts → new random `jwt_secret_key` generated
2. Users have cookies with JWTs signed by the OLD secret
3. Token verification fails because signatures don't match
4. All users see "Signature verification failed" and get logged out

**Why This Wasn't Caught Earlier:**
- Local development uses the same container, so the secret persists
- Tests use fresh tokens for each test run
- The issue only manifests in production with container restarts

### Solution

**1. Added Startup Warning** (`src/config/auth_config.py`):
```python
# Check if secret was provided BEFORE settings load
_SECRET_KEY_PROVIDED = bool(os.environ.get("AUTH_JWT_SECRET_KEY"))

def check_jwt_secret_configuration() -> None:
    """Log a warning if JWT secret key was auto-generated."""
    if not _SECRET_KEY_PROVIDED:
        logger.warning(
            "WARNING: AUTH_JWT_SECRET_KEY not set in environment!\n"
            "A random secret was generated. This means:\n"
            "  - All user sessions will be invalidated on restart\n"
            "  - Users will see 'Signature verification failed' errors\n"
            "\n"
            "To fix, set AUTH_JWT_SECRET_KEY in your environment:\n"
            "  python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
```

**2. Added Startup Event** (`src/main.py`):
```python
@app.on_event("startup")
async def startup_event():
    """Run configuration checks on startup."""
    check_jwt_secret_configuration()
    logger.info("IP2A Database API started successfully")
```

**3. Production Fix Required:**
Operators must set `AUTH_JWT_SECRET_KEY` in Railway/production environment:
```bash
# Generate a secure key
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Add to Railway environment variables:
AUTH_JWT_SECRET_KEY=<generated-key>
```

### Files Modified
- `src/config/auth_config.py` - Added `_SECRET_KEY_PROVIDED` check and `check_jwt_secret_configuration()` function
- `src/main.py` - Added startup event to call configuration check

### Commit
- `91ee142 fix: add startup warning when JWT secret key not configured`

### Lessons Learned

1. **Environment Variables for Secrets**: Never rely on default_factory for production secrets. The default should fail loudly or warn clearly.

2. **Pydantic default_factory Gotcha**: Using `default_factory=lambda: secrets.token_urlsafe(32)` is fine for development but dangerous if not caught in production.

3. **Deployment Testing Gap**: Local testing doesn't simulate container restarts. Need integration tests that verify token persistence across restarts.

4. **Proactive Warnings**: Adding startup warnings for misconfiguration catches issues before they affect users.

5. **Railway Environment Variables**: Critical secrets like JWT keys must be set as environment variables in Railway dashboard, not in code.

### Prevention

1. **Startup Configuration Check**: The new `check_jwt_secret_configuration()` function logs a clear warning when the secret is auto-generated.

2. **Documentation Updated**: Added JWT configuration to:
   - CLAUDE.md (Important Patterns section)
   - CHANGELOG.md (Fixed section)
   - Deployment runbook

3. **Future Improvement Ideas**:
   - Consider failing startup if `AUTH_JWT_SECRET_KEY` not set in production (`ENVIRONMENT=production`)
   - Add health check that verifies configuration
   - Create deployment checklist with required environment variables

---

## Bug #007: Production Seed Causing Container Restart Loop

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (application unable to start)
**Status:** RESOLVED

### Symptoms
- Railway container starts, runs migrations, then gets killed before web server starts
- Container restart loop - repeatedly starting and stopping
- Logs show seed running but never reach "Starting application server..."
- Health check fails because server never becomes available

### Root Cause Analysis

The `RUN_PRODUCTION_SEED=true` environment variable causes the startup script to run a full database seed (1000+ members, 500 students, etc.) on EVERY container startup:

```bash
# scripts/start.sh
if [ "$RUN_PRODUCTION_SEED" = "true" ]; then
    echo "Checking if production seed is needed..."
    python -m src.seed.production_seed  # Takes 30-60 seconds
fi
```

**The Problem Chain:**
1. Container starts → migrations run → seed starts
2. Seed takes 30-60 seconds (seeding 1000 members, 500 students, etc.)
3. Railway health check times out (default ~30s) - no web server responding
4. Railway kills container and restarts it
5. New container starts → runs seed AGAIN → cycle repeats
6. Database gets truncated and re-seeded on each attempt

**Why This Caused Data Loss:**
The production seed script calls `truncate_all_tables(db)` first, wiping all existing data before seeding fresh data. This is intentional for initial setup but destructive if triggered repeatedly.

### Solution

**1. Set `RUN_PRODUCTION_SEED=false` in Railway:**
```bash
# Railway Dashboard → Variables
RUN_PRODUCTION_SEED=false
```

**2. The seed should only run ONCE for initial data population:**
- The environment variable is a one-time flag
- After initial seed completes, set it to `false`
- Or remove the variable entirely

**3. If database needs seeding, do it as a one-time job:**
```bash
# Railway CLI
railway run python -m src.seed.production_seed

# Or via Railway shell
python -m src.seed.production_seed
```

### Files Related
- `scripts/start.sh` - Startup script that checks RUN_PRODUCTION_SEED
- `src/seed/production_seed.py` - Seed script that truncates and re-seeds

### Resolution
Set `RUN_PRODUCTION_SEED=false` in Railway environment variables. The container then starts quickly (migrations only), web server comes up, and health check passes.

### Lessons Learned

1. **One-Time Seeds vs Startup Scripts**: Production seeds should be run as one-time jobs, not on every container startup. The startup script should only do quick tasks (migrations).

2. **Health Check Timing**: Railway's health check timeout is relatively short. Any startup task taking >30s risks triggering a restart loop.

3. **Destructive Operations**: A seed script that truncates tables is dangerous if it can run multiple times. Consider adding idempotency checks.

4. **Environment Variable Hygiene**: One-time configuration flags like `RUN_PRODUCTION_SEED` should be disabled immediately after use.

### Prevention

1. **Document the seed workflow**: Added to deployment documentation that `RUN_PRODUCTION_SEED` must be `false` after initial setup.

2. **Future Improvement Ideas**:
   - Add a "seed_completed" marker in database to prevent re-seeding
   - Check if data already exists before truncating
   - Move seed to a Railway job instead of startup script
   - Add a confirmation prompt for destructive operations

---

## Bug #008: Browser Cookies Invalid After JWT Secret Key Change

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Medium (users need to clear cookies)
**Status:** RESOLVED (user action required)

### Symptoms
- User accesses the site after deployment
- Sees login page or blank page
- Railway logs show repeated: "Token validation failed: Invalid token: Signature verification failed"
- User appears stuck in a redirect loop or sees errors

### Root Cause Analysis

This is a side effect of Bug #006 (JWT Secret Key not set) and the fix (setting a new key):

1. **Before fix**: Random JWT secret generated on each startup
2. **User logs in**: Gets JWT token signed with secret A
3. **Container restarts**: New random secret B generated
4. **User returns**: Browser sends token signed with A, but server validates with B
5. **Signature mismatch**: "Signature verification failed" error

**After setting `AUTH_JWT_SECRET_KEY`:**
- Server now uses consistent secret C
- But user's browser still has old cookie signed with A or B
- Same signature mismatch occurs

### Solution

**Users must clear their browser cookies or use incognito mode:**

1. Open browser DevTools (F12)
2. Go to Application → Cookies
3. Delete cookies for the Railway app URL
4. Refresh the page
5. Log in with fresh credentials

Or simply use an incognito/private browser window.

### Files Related
- None - this is expected behavior after fixing Bug #006

### Lessons Learned

1. **Token Invalidation is Expected**: When JWT secrets change, ALL existing tokens become invalid. This is by design for security.

2. **User Communication**: After JWT key changes in production, notify users they may need to log in again.

3. **Graceful Token Handling**: The application correctly detects invalid signatures and redirects to login, which is the correct security behavior.

### Prevention

1. **Set JWT secret BEFORE first users**: Configure `AUTH_JWT_SECRET_KEY` before any real users log in.

2. **Document the impact**: Added to deployment checklist that changing JWT secret invalidates all sessions.

---

## Bug #009: Production Seed KeyError - 'users_created' Key Missing

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (blocking deployment - health check fails)
**Status:** RESOLVED

### Symptoms
- Railway deployment fails health check: "1/1 replicas never became healthy!"
- Container builds successfully but application never starts
- Railway logs show: `KeyError: 'users_created'`
- Error traceback points to `production_seed.py` line 79

### Root Cause Analysis

The `production_seed.py` file tried to access a dict key that didn't exist:

```python
# production_seed.py tried to access:
print(f"Created {auth_results['users_created']} users")

# But auth_seed.py returns:
return {
    "roles_created": len(roles),
    "admin_created": admin is not None,  # Note: 'admin_created', not 'users_created'
}
```

**The Problem Chain:**
1. Container starts → migrations run → production seed starts
2. `run_auth_seed(db)` returns dict with `admin_created` key
3. `production_seed.py` tries to access `users_created` key (doesn't exist)
4. Python raises `KeyError: 'users_created'`
5. Startup script exits with error (due to `set -e`)
6. Web server never starts
7. Health check times out → Railway kills container

**Why Railway Deployed Old Code:**
- The fix was committed locally (`aa1d98b fix: correct auth_results key`)
- Railway cached the Docker image from a previous build
- The new build used cached layers, including the old `production_seed.py`
- Fix was pushed but Railway needed a fresh deployment to pick it up

### Solution

**1. Fixed Key Access** (`src/seed/production_seed.py`):
```python
# Before (WRONG)
print(f"Created {auth_results['roles_created']} roles, {auth_results['users_created']} users")

# After (CORRECT)
admin_status = "created" if auth_results['admin_created'] else "already exists"
print(f"Created {auth_results['roles_created']} roles, admin user {admin_status}")
```

**2. Triggered Fresh Railway Deployment:**
After pushing the fix to `origin/main`, a new Railway deployment picked up the corrected code.

### Files Modified
- `src/seed/production_seed.py` - Fixed dict key access

### Commit
- `aa1d98b fix: correct auth_results key in production seed script`

### Lessons Learned

1. **Dict Key Consistency**: When returning dicts from functions, document the expected keys and be consistent with naming.

2. **Railway Caching**: Railway aggressively caches Docker layers. If code changes aren't reflected, trigger a fresh build or clear the build cache.

3. **Error Propagation**: `set -e` in shell scripts causes immediate exit on any error. Good for catching problems, but can make debugging harder.

4. **Test Coverage Gap**: The production seed path wasn't fully tested in CI - the integration between `production_seed.py` and `auth_seed.py` return values should have been caught.

### Prevention

1. **Type Hints for Return Values**: Add TypedDict or dataclass for seed return values:
   ```python
   class AuthSeedResult(TypedDict):
       roles_created: int
       admin_created: bool
   ```

2. **Integration Tests**: Add tests that call the full production seed flow.

3. **Clear Railway Cache**: When fixing critical deployment issues, clear Railway's build cache to ensure fresh code is used.

---

## Bug #010: Production Seed Expanded - Missing Seed Files

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** High (blocking production seed)
**Status:** RESOLVED

### Symptoms
- Production seed fails with `ImportError` or `AttributeError`
- Missing seed files for grants, expenses, instructor_hours
- Missing `truncate_all.py` for database cleanup

### Root Cause Analysis

The `production_seed.py` was expanded to include new seed functions, but the corresponding seed files didn't exist:

```python
# production_seed.py imported:
from .seed_grants import seed_grants            # File missing
from .seed_expenses import seed_expenses        # File missing
from .seed_instructor_hours import seed_instructor_hours  # File missing
from .truncate_all import truncate_all_tables   # File missing
```

### Solution

Created the missing seed files:

**1. `src/seed/seed_grants.py`** - Seeds grant/funding source data
**2. `src/seed/seed_expenses.py`** - Seeds expense records linked to grants
**3. `src/seed/seed_instructor_hours.py`** - Seeds instructor hour entries
**4. `src/seed/truncate_all.py`** - Truncates all tables in dependency order

### Files Created
- `src/seed/seed_grants.py`
- `src/seed/seed_expenses.py`
- `src/seed/seed_instructor_hours.py`
- `src/seed/truncate_all.py`

### Commit
- `3346ed1 feat: add missing seed files for grants, expenses, instructor_hours`

### Lessons Learned

1. **Complete the Feature**: When expanding imports in a file, ensure all imported modules exist before committing.

2. **Local Testing**: Run the full seed locally before deploying to catch import errors.

---

## Bug #011: StudentStatus Enum Value Mismatch (Initial Discovery)

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Medium (seed data generation fails)
**Status:** RESOLVED

### Symptoms
- Seed fails with `AttributeError` for StudentStatus enum
- Error: `type object 'StudentStatus' has no attribute 'GRADUATED'`
- Production seed crashes during student seeding step

### Root Cause Analysis

The seed file used enum values that don't exist in the `StudentStatus` enum:

```python
# Seed file incorrectly used:
StudentStatus.GRADUATED  # Doesn't exist!

# Correct StudentStatus enum values:
class StudentStatus(str, Enum):
    APPLICANT = "applicant"
    ENROLLED = "enrolled"
    ON_LEAVE = "on_leave"
    COMPLETED = "completed"  # <-- Use this
    DROPPED = "dropped"
    DISMISSED = "dismissed"
```

### Solution

Updated seed file to use correct enum values:

```python
# Before (WRONG)
status=StudentStatus.GRADUATED

# After (CORRECT)
status=StudentStatus.COMPLETED
```

### Files Modified
- `src/seed/seed_students.py` - Fixed enum values to use COMPLETED instead of GRADUATED

### Commit
- `8fefc63 fix: use correct StudentStatus enum values (COMPLETED, DROPPED)`

**Note:** See Bug #017 for more detailed analysis of this issue when it resurfaced.

---

## Bug #012: passlib Bcrypt Compatibility Issue

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (authentication completely broken)
**Status:** RESOLVED

### Symptoms
- Login fails with cryptic error
- Password hashing/verification throws exceptions
- Error related to bcrypt version compatibility

### Root Cause Analysis

The `passlib` library had compatibility issues with newer versions of `bcrypt`. The passlib bcrypt handler was failing due to internal API changes in bcrypt.

### Solution

Replaced passlib with direct bcrypt usage:

```python
# Before (passlib)
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context.hash(password)
pwd_context.verify(password, hash)

# After (direct bcrypt)
import bcrypt
bcrypt.hashpw(password.encode(), bcrypt.gensalt())
bcrypt.checkpw(password.encode(), hash.encode())
```

### Files Modified
- `src/core/security.py` - Replaced passlib with direct bcrypt

### Commit
- `a78f810 fix: replace passlib with direct bcrypt to fix compatibility issue`

### Lessons Learned

1. **Library Dependencies**: When libraries have compatibility issues, sometimes it's simpler to use the underlying library directly.

2. **bcrypt is Sufficient**: For password hashing, direct bcrypt usage is straightforward and doesn't require wrapper libraries.

---

## Bug #013: Reports Template TypeError - `category.items` Dict Method Conflict

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (Reports page completely broken)
**Status:** RESOLVED

### Symptoms
- User navigates to Reports page
- Railway logs show: `TypeError: 'builtin_function_or_method' object is not iterable`
- Error at `src/templates/reports/index.html, line 48`
- Reports page crashes with 500 error

### Root Cause Analysis

The Jinja2 template used dot notation to access a dict key named `items`:

```html
<!-- WRONG - 'items' conflicts with dict.items() method -->
{% for item in category.items %}
```

In Jinja2, `category.items` is resolved as attribute access first. Since `category` is a Python dict, `items` matches the built-in `dict.items()` method, not the "items" key in the dict.

**The Problem Chain:**
1. Router creates: `{"category": "Members", "items": [...]}`
2. Template accesses: `category.items`
3. Jinja2 finds `dict.items` method (not the "items" key)
4. Template tries to iterate over the method itself
5. Python raises: `TypeError: 'builtin_function_or_method' object is not iterable`

### Solution

**Option 1 (Not chosen):** Use bracket notation in template:
```html
{% for item in category['items'] %}
```

**Option 2 (Chosen):** Rename the dict key to avoid conflict:
```python
# Router - changed 'items' to 'reports'
{"category": "Members", "reports": [...]}
```
```html
<!-- Template - use the new key name -->
{% for item in category['reports'] %}
```

Option 2 was chosen because "reports" is more descriptive and avoids future confusion with Python's built-in dict methods.

### Files Modified
- `src/routers/reports.py` - Changed `items` key to `reports` (lines 64-85)
- `src/templates/reports/index.html` - Changed to `category['reports']` (line 48)

### Commit
- `013cf92 fix: resolve production deployment bugs`

### Lessons Learned

1. **Avoid Python Built-in Names as Dict Keys**: Keys like `items`, `keys`, `values`, `get`, `pop` conflict with dict methods in Jinja2 dot notation.

2. **Jinja2 Attribute vs Key Access**: Jinja2's dot notation (`obj.attr`) checks attributes first, then dict keys. Use bracket notation (`obj['key']`) for guaranteed dict key access.

3. **Test Template Rendering**: This bug passed local tests but failed in production because tests may not render all template paths.

### Prevention

1. **Naming Convention**: Use descriptive, unique names for dict keys passed to templates. Avoid: `items`, `keys`, `values`, `update`, `get`, `pop`, `copy`, `clear`.

2. **Template Testing**: Add tests that actually render templates with data, not just check HTTP status codes.

---

## Bug #014: Staff Service SQLAlchemy Cartesian Product Warning

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Medium (performance warning, not breaking)
**Status:** RESOLVED

### Symptoms
- Railway logs show SQLAlchemy warning:
  ```
  SAWarning: SELECT statement has a cartesian product between FROM element(s) "users" and FROM element "anon_1"
  ```
- Warning occurs when accessing Staff Management page
- Points to `src/services/staff_service.py:89`

### Root Cause Analysis

The count query was creating a subquery from a statement that included `selectinload` options:

```python
# Base query with eager loading
stmt = select(User).options(selectinload(User.user_roles).selectinload(UserRole.role))

# ... apply filters ...

# PROBLEM: Creating subquery from stmt with selectinload
count_stmt = select(func.count(func.distinct(User.id))).select_from(stmt.subquery())
```

When `stmt` is converted to a subquery:
1. The eager loading options create implicit joins in the subquery
2. The outer `select_from()` doesn't have join conditions with the inner subquery
3. SQLAlchemy warns about the cartesian product (all rows × all rows)

### Solution

Refactored to build a separate, simpler count query without eager loading:

```python
# Build conditions list shared between queries
conditions = []
# ... populate conditions ...

# Separate count query (no eager loading)
if role and role != "all":
    count_stmt = (
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(User.user_roles)
        .join(UserRole.role)
        .where(Role.name == role)
    )
else:
    count_stmt = select(func.count(User.id)).select_from(User)

if conditions:
    count_stmt = count_stmt.where(and_(*conditions))

total = self.db.execute(count_stmt).scalar() or 0

# Separate data query (with eager loading)
stmt = select(User).options(selectinload(User.user_roles).selectinload(UserRole.role))
# ... apply same conditions and pagination ...
```

### Files Modified
- `src/services/staff_service.py` - Refactored `search_users()` method to use separate count/data queries

### Commit
- `013cf92 fix: resolve production deployment bugs`

### Lessons Learned

1. **Eager Loading and Subqueries Don't Mix**: Don't create subqueries from statements with `selectinload`/`joinedload` options.

2. **Separate Count Queries**: For paginated results, build count queries separately without relationship loading.

3. **SQLAlchemy Warnings Matter**: Cartesian product warnings indicate inefficient queries that may cause performance issues.

### Prevention

1. **Query Pattern**: For paginated search with eager loading:
   - Build filter conditions as a list
   - Create simple count query with conditions
   - Create data query with eager loading and conditions
   - Apply sorting/pagination only to data query

---

## Bug #015: Token Validation Errors Spamming Logs After Deployment

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Medium (log spam, user experience)
**Status:** RESOLVED

### Symptoms
- After deployment with new JWT secret, Railway logs flood with:
  ```
  Token validation failed: Invalid token: Signature verification failed.
  ```
- Same error appears repeatedly for every page request
- Users redirected to login but old cookies remain
- Logs become hard to read due to repeated errors

### Root Cause Analysis

When JWT tokens become invalid (after secret key change), the auth middleware:
1. Validates token → fails with `TokenInvalidError`
2. Logs warning: "Token validation failed"
3. Redirects to login page
4. **But cookies are NOT cleared**

Since cookies persist, the next request:
1. Sends same invalid token
2. Validation fails again
3. Same warning logged
4. Redirect to login again
5. Cycle continues until user manually clears cookies

### Solution

Modified `_handle_unauthorized()` in `auth_cookie.py` to clear cookies when redirecting:

```python
def _handle_unauthorized(self, request: Request):
    """Handle unauthorized access by clearing invalid cookies and redirecting."""
    if self.redirect_to_login:
        return_url = str(request.url.path)
        response = RedirectResponse(
            url=f"/login?next={return_url}&message=Please+log+in+to+continue&type=info",
            status_code=status.HTTP_302_FOUND,
        )
        # Clear any invalid cookies to prevent repeated validation errors
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        return response
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )
```

Now when tokens are invalid:
1. Token validation fails
2. Warning logged once
3. Response clears cookies AND redirects to login
4. Next request has no token → clean redirect
5. No repeated warnings

### Files Modified
- `src/routers/dependencies/auth_cookie.py` - Added `delete_cookie()` calls in `_handle_unauthorized()`

### Commit
- `013cf92 fix: resolve production deployment bugs`

### Lessons Learned

1. **Clear Invalid Cookies**: When authentication fails, always clear the invalid tokens to prevent retry loops.

2. **Log Spam Impact**: Repeated log warnings make debugging harder. One warning per issue is sufficient.

3. **Deployment Experience**: After JWT key changes, users should only see one redirect, not repeated failures.

### Prevention

1. **Cookie Lifecycle Management**: Auth redirects should always clean up invalid tokens.

2. **Error Rate Monitoring**: Consider rate-limiting log messages for the same error type.

---

## Bug #016: Documents Frontend 500 Error When S3 Not Configured

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Medium (feature unavailable but not blocking)
**Status:** RESOLVED

### Symptoms
- User navigates to Documents page
- Browser shows 500 "Something Went Wrong" error
- No clear indication that the feature requires S3 configuration
- Console shows `Failed to load resource: the server responded with a status of 500`

### Root Cause Analysis

The Documents frontend attempted to query the `FileAttachment` model and interact with S3/MinIO storage, but:

1. **S3 Not Configured**: Production deployment doesn't have S3/MinIO configured yet
2. **No Graceful Fallback**: The router attempted database queries without checking if storage was available
3. **Confusing Error**: Users saw a generic 500 error instead of a helpful message

### Solution

Replaced the document routes with a friendly "Feature Not Implemented" placeholder page:

```python
@router.get("", response_class=HTMLResponse)
async def documents_landing(request: Request, ...):
    # Feature not implemented - show placeholder page
    return templates.TemplateResponse(
        "documents/not_implemented.html",
        {"request": request, "user": current_user},
    )
```

Created `not_implemented.html` template with:
- Clear "Feature Not Implemented" heading
- "Document management is coming in a future update" message
- Info box explaining S3/MinIO requirement
- Back to Dashboard button

### Files Modified
- `src/routers/documents_frontend.py` - Updated landing, upload, browse routes
- `src/templates/documents/not_implemented.html` - New placeholder template

### Commit
- `83f9220 feat: show friendly 'Feature not implemented' page for documents`

### Lessons Learned

1. **Graceful Degradation**: Features depending on external services (S3) should have fallback behavior when those services aren't available.

2. **User-Friendly Errors**: Instead of cryptic 500 errors, show clear messages about feature availability.

3. **Progressive Deployment**: It's acceptable to deploy with some features disabled, as long as users understand the status.

### Prevention

1. **Feature Flags**: Consider using feature flags to explicitly enable/disable features based on configuration.

2. **Service Availability Checks**: Check if required services (S3, etc.) are configured before attempting to use them.

---

## Bug #017: StudentStatus.GRADUATED AttributeError in Production Seed

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (blocking production seed)
**Status:** RESOLVED

### Symptoms
- Production seed fails at step [8/18] Seeding students
- Railway logs show: `AttributeError: type object 'StudentStatus' has no attribute 'GRADUATED'`
- Container continues but database is partially seeded
- Error traceback points to `src/seed/seed_students.py` line 88

### Root Cause Analysis

The `seed_students.py` file used enum values that don't exist:

```python
# seed_students.py used (WRONG):
StudentStatus.GRADUATED  # Doesn't exist!
StudentStatus.ACTIVE     # Doesn't exist!

# Actual StudentStatus enum (src/db/enums/training_enums.py):
class StudentStatus(str, Enum):
    APPLICANT = "applicant"
    ENROLLED = "enrolled"
    ON_LEAVE = "on_leave"
    COMPLETED = "completed"    # <-- Correct value
    DROPPED = "dropped"
    DISMISSED = "dismissed"
```

The seed file was likely created from outdated documentation or a different codebase where the enum had different values.

### Solution

Updated `seed_students.py` to use correct enum values:

```python
# Before (WRONG)
status = random.choice([
    StudentStatus.ENROLLED,
    StudentStatus.GRADUATED,  # Doesn't exist
    StudentStatus.ACTIVE,     # Doesn't exist
])

# After (CORRECT)
status = random.choice([
    StudentStatus.APPLICANT,
    StudentStatus.ENROLLED,
    StudentStatus.ON_LEAVE,
    StudentStatus.COMPLETED,
    StudentStatus.DROPPED,
])
```

### Files Modified
- `src/seed/seed_students.py` - Fixed enum values

### Commit
- `8fefc63 fix: use correct StudentStatus enum values (COMPLETED, DROPPED)`

### Lessons Learned

1. **Verify Enum Values**: Always check enum definitions against actual model files, not documentation.

2. **Test Seeds Locally**: Run `python -m src.seed.production_seed` locally before deploying.

3. **IDE Autocomplete**: Use IDE features to autocomplete enum values to catch typos.

### Prevention

1. **Import and Use Enums**: Import enums at the top of seed files and let the IDE validate values.

2. **Seed Tests**: Add unit tests that verify seed files can run without errors.

---

## Bug #018: Truncate Function Transaction Abort on Missing Table

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (blocking production seed)
**Status:** RESOLVED

### Symptoms
- Production seed starts truncating tables
- First 4 tables truncate successfully (dues_adjustments, dues_payments, dues_periods, dues_rates)
- "documents" table throws error: `relation "documents" does not exist`
- ALL subsequent truncate operations fail with: `current transaction is aborted, commands ignored until end of transaction block`
- Seed continues but database not properly cleared
- Container enters restart loop

### Root Cause Analysis

The `truncate_all.py` function listed the `documents` table, but this table doesn't exist in the production database (the Documents feature was disabled with a placeholder page):

```python
tables = [
    "dues_adjustments",
    "dues_payments",
    ...
    "documents",  # This table doesn't exist!
    "certifications",
    ...
]
```

**The Problem Chain:**
1. PostgreSQL starts an implicit transaction
2. TRUNCATE on `documents` fails with `UndefinedTable` error
3. PostgreSQL marks transaction as "aborted"
4. ALL subsequent SQL commands fail immediately
5. "All tables truncated" message prints (misleading - only 4 were truncated)
6. Seed tries to INSERT into tables that weren't truncated
7. Container crashes or data integrity issues

### Solution

**1. Added SAVEPOINT mechanism** to isolate each truncate operation:

```python
for table in tables:
    try:
        # Use savepoint so one failure doesn't abort entire transaction
        db.execute(text("SAVEPOINT truncate_savepoint"))
        db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
        db.execute(text("RELEASE SAVEPOINT truncate_savepoint"))
        print(f"  Truncated: {table}")
    except Exception as e:
        # Rollback to savepoint and continue with next table
        db.execute(text("ROLLBACK TO SAVEPOINT truncate_savepoint"))
        error_msg = str(e).split('\n')[0][:60]
        print(f"  Skipped {table}: {error_msg}")
```

**2. Removed non-existent `documents` table** from the list.

Now when a table doesn't exist:
1. SAVEPOINT created before TRUNCATE
2. TRUNCATE fails → rollback to savepoint
3. Transaction continues normally
4. Next table can be truncated
5. Only missing tables are skipped

### Files Modified
- `src/seed/truncate_all.py` - Added SAVEPOINT handling, removed `documents` table

### Commit
- `ca54c6a fix: use savepoints in truncate to handle missing tables`

### Lessons Learned

1. **PostgreSQL Transaction Behavior**: A single error aborts the entire transaction unless using SAVEPOINTs.

2. **Table Existence**: Don't hardcode table names that might not exist. Consider querying `information_schema.tables` for actual tables.

3. **Error Recovery**: For batch operations, use SAVEPOINTs to allow individual failures without aborting the whole batch.

4. **Misleading Output**: The "All tables truncated" message printed even when most tables were skipped due to the aborted transaction.

### Prevention

1. **SAVEPOINT Pattern**: For any batch database operations where partial failure is acceptable, use SAVEPOINTs.

2. **Dynamic Table Discovery**:
   ```python
   # Query actual tables instead of hardcoding
   result = db.execute(text(
       "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
   ))
   ```

3. **Accurate Reporting**: Count successful operations and report accurately:
   ```python
   print(f"Truncated {success_count} tables, skipped {skip_count}")
   ```

---

## Bug #019: Production Seed Student Count Mismatch

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Low (seed data quantity issue)
**Status:** RESOLVED

### Symptoms
- Railway logs show "Seeded 50 members" instead of requested 500
- Production seed appeared to use old code with lower counts
- Database had fewer records than expected

### Root Cause Analysis

Railway was deploying cached Docker images that didn't include recent code changes:

1. User pushed commit with `seed_members(db, count=500)`
2. Railway triggered deployment
3. Railway used cached Docker layers from previous build
4. Production ran with old `count=50` value

**Contributing Factors:**
- Docker layer caching aggressive in Railway
- No cache-busting mechanism for Python source files
- Multiple rapid commits didn't trigger fresh builds

### Solution

The fix was already pushed - just needed Railway to pull fresh code:

1. Wait for Railway to pick up latest commit
2. Or manually trigger "Redeploy" with "Clear build cache" option
3. Verify logs show correct counts (500 members, 200 students, etc.)

### Files Related
- `src/seed/production_seed.py` - Contains seed count configurations

### Lessons Learned

1. **Railway Caching**: Railway aggressively caches Docker layers. Code changes may not appear immediately.

2. **Verify Deployments**: After pushing fixes, verify Railway logs show the expected behavior.

3. **Cache Busting**: For critical fixes, manually clear the build cache or add a dummy file change.

### Prevention

1. **Check Logs After Deploy**: Verify expected output appears in Railway logs.

2. **Build Cache Awareness**: Know when to clear Railway's build cache for urgent fixes.

---

## Template for New Bugs

```markdown
## Bug #XXX: Brief Description

**Date Discovered:** YYYY-MM-DD
**Date Fixed:** YYYY-MM-DD
**Severity:** Critical/High/Medium/Low
**Status:** RESOLVED/IN PROGRESS/WONT FIX

### Symptoms
- What the user sees/experiences

### Root Cause Analysis
- Technical explanation of why this happened

### Solution
- What was done to fix it

### Files Modified
- List of files changed

### Commit
- Commit hash and message

### Lessons Learned
- What we learned from this bug

### Prevention
- Steps taken to prevent similar bugs
```

---

## Bug #020: Migration INSERT Missing `is_system_role` Column

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (blocking deployment - migration fails)
**Status:** RESOLVED

### Symptoms
- Railway deployment fails during migration `813f955b11af_fix_missing_user_roles`
- Container starts then immediately stops
- Railway logs show: `psycopg2.errors.NotNullViolation: null value in column "is_system_role" of relation "roles" violates not-null constraint`
- DETAIL shows: `Failing row contains (3, admin, Administrator, Full system access, null, ...)`

### Root Cause Analysis

The data migration `813f955b11af_fix_missing_user_roles.py` created admin role if missing, but the INSERT statement didn't include the `is_system_role` column which has a NOT NULL constraint:

```python
# WRONG - missing is_system_role
conn.execute(
    sa.text("""
        INSERT INTO roles (name, display_name, description, created_at, updated_at)
        VALUES ('admin', 'Administrator', 'Full system access', NOW(), NOW())
    """)
)
```

PostgreSQL rejected the INSERT because `is_system_role` was NULL but the column has `NOT NULL` constraint.

### Solution

Added `is_system_role` with value `true` to the INSERT:

```python
# CORRECT - includes is_system_role
conn.execute(
    sa.text("""
        INSERT INTO roles (name, display_name, description, is_system_role, created_at, updated_at)
        VALUES ('admin', 'Administrator', 'Full system access', true, NOW(), NOW())
    """)
)
```

### Files Modified
- `src/db/migrations/versions/813f955b11af_fix_missing_user_roles.py` - Added `is_system_role` to INSERT

### Commit
- `8916563 fix: add is_system_role to migration INSERT for production compatibility`

### Lessons Learned

1. **Check Table Constraints**: When writing data migrations with raw SQL, verify all NOT NULL columns are included in INSERT statements.

2. **Test Migrations on Fresh Database**: Migration may work on dev (where role exists) but fail on fresh prod database.

3. **Railway Deploy Logs**: The DETAIL line in PostgreSQL errors shows exactly which values are problematic.

### Prevention

1. **Migration Testing**: Test data migrations against empty database, not just populated dev database.

2. **Include All Required Columns**: When inserting records, explicitly list all NOT NULL columns.

---

## Bug #021: MemberClassification Enum Values Mismatch

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** High (blocking /members page)
**Status:** RESOLVED

### Symptoms
- User navigates to Members page
- Railway logs show: `AttributeError: type object 'MemberClassification' has no attribute 'JOURNEYMAN_WIREMAN'`
- Error traceback points to `src/services/member_frontend_service.py` line 348
- Members page returns 500 error

### Root Cause Analysis

The `member_frontend_service.py` file used enum values that don't exist in `MemberClassification`:

```python
# WRONG - these enum values don't exist
mapping = {
    MemberClassification.JOURNEYMAN_WIREMAN: "Journeyman Wireman",
    MemberClassification.APPRENTICE_WIREMAN: "Apprentice Wireman",
    MemberClassification.JOURNEYMAN_TECHNICIAN: "Journeyman Technician",
    ...
}
```

Actual enum values in `src/db/enums/organization_enums.py`:

```python
class MemberClassification(str, enum.Enum):
    APPRENTICE_1ST_YEAR = "apprentice_1"
    APPRENTICE_2ND_YEAR = "apprentice_2"
    APPRENTICE_3RD_YEAR = "apprentice_3"
    APPRENTICE_4TH_YEAR = "apprentice_4"
    APPRENTICE_5TH_YEAR = "apprentice_5"
    JOURNEYMAN = "journeyman"
    FOREMAN = "foreman"
    RETIREE = "retiree"
    HONORARY = "honorary"
```

The service file was created with incorrect enum values, possibly from outdated documentation or a different schema.

**Same issue in `src/seed/dues_seed.py`:**
```python
# WRONG - APPRENTICE_1 doesn't exist, should be APPRENTICE_1ST_YEAR
MemberClassification.APPRENTICE_1: Decimal("35.00"),
```

### Solution

Updated both files to use correct enum values:

**member_frontend_service.py:**
```python
mapping = {
    MemberClassification.APPRENTICE_1ST_YEAR: "1st Year Apprentice",
    MemberClassification.APPRENTICE_2ND_YEAR: "2nd Year Apprentice",
    MemberClassification.APPRENTICE_3RD_YEAR: "3rd Year Apprentice",
    MemberClassification.APPRENTICE_4TH_YEAR: "4th Year Apprentice",
    MemberClassification.APPRENTICE_5TH_YEAR: "5th Year Apprentice",
    MemberClassification.JOURNEYMAN: "Journeyman",
    MemberClassification.FOREMAN: "Foreman",
    MemberClassification.RETIREE: "Retiree",
    MemberClassification.HONORARY: "Honorary",
}
```

**dues_seed.py:**
```python
rate_schedule = {
    MemberClassification.APPRENTICE_1ST_YEAR: Decimal("35.00"),
    MemberClassification.APPRENTICE_2ND_YEAR: Decimal("40.00"),
    ...
}
```

### Files Modified
- `src/services/member_frontend_service.py` - Fixed `format_classification()` and `get_classification_badge_class()` methods
- `src/seed/dues_seed.py` - Fixed `seed_dues_rates()` function

### Commit
- `70df236 fix: correct MemberClassification enum values in frontend service and seed`

### Lessons Learned

1. **Verify Enum Values**: Always reference the actual enum definition when using enum values in code.

2. **IDE Autocomplete**: Use IDE autocomplete to avoid typos in enum names.

3. **Single Source of Truth**: Enums defined in `src/db/enums/` are the source of truth. Don't assume values from documentation.

4. **Multiple Files Affected**: When an enum mismatch is found, search the entire codebase for other occurrences.

### Prevention

1. **Type Checking**: Use mypy or pyright to catch invalid enum attribute access at development time.

2. **Enum Import Validation**: Import enums directly and let Python validate at import time:
   ```python
   from src.db.enums import MemberClassification
   # Any typo would cause ImportError or AttributeError at startup
   ```

3. **Comprehensive Grep**: When fixing enum issues, search for all usages:
   ```bash
   grep -r "MemberClassification\." src/
   ```

---

## Template for New Bugs

```markdown
## Bug #XXX: Brief Description

**Date Discovered:** YYYY-MM-DD
**Date Fixed:** YYYY-MM-DD
**Severity:** Critical/High/Medium/Low
**Status:** RESOLVED/IN PROGRESS/WONT FIX

### Symptoms
- What the user sees/experiences

### Root Cause Analysis
- Technical explanation of why this happened

### Solution
- What was done to fix it

### Files Modified
- List of files changed

### Commit
- Commit hash and message

### Lessons Learned
- What we learned from this bug

### Prevention
- Steps taken to prevent similar bugs
```

---

---

## Bug #022: HTMX 401 Errors Not Handled Gracefully

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Medium (poor user experience on session expiry)
**Status:** RESOLVED

### Symptoms
- User's session expires while browsing
- HTMX search/filter requests return 401 Unauthorized
- Browser console shows: `Response Status Error Code 401 from /operations/grievances/search`
- User sees generic "An error occurred. Please try again." toast
- User is NOT redirected to login page
- Error repeats on every HTMX request

### Root Cause Analysis

When HTMX makes an AJAX request and the session has expired:
1. Backend returns 401 Unauthorized with HTML "Session expired"
2. HTMX triggers `htmx:responseError` event
3. JavaScript handler only showed a generic error toast
4. No redirect to login, no HX-Redirect header

The backend returned 401 but didn't use HTMX's `HX-Redirect` header mechanism for client-side redirect.

### Solution

**1. Added specific 401 handling in JavaScript** (`src/static/js/app.js`):
```javascript
document.body.addEventListener('htmx:responseError', function(evt) {
    var status = evt.detail.xhr ? evt.detail.xhr.status : 0;

    // Handle 401 Unauthorized - redirect to login
    if (status === 401) {
        showToast('Session expired. Redirecting to login...', 'warning');
        setTimeout(function() {
            window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
        }, 1000);
        return;
    }

    // Handle 404, 403, 500+ with specific messages...
});
```

**2. Added HX-Redirect header to backend 401 responses**:
```python
# operations_frontend.py, member_frontend.py, dues_frontend.py
if isinstance(current_user, RedirectResponse):
    return HTMLResponse(
        "Session expired",
        status_code=401,
        headers={"HX-Redirect": "/auth/login?next=/operations/grievances"},
    )
```

### Files Modified
- `src/static/js/app.js` - Added status-specific error handling (401, 403, 404, 500+)
- `src/routers/operations_frontend.py` - Added HX-Redirect header to 401 responses
- `src/routers/member_frontend.py` - Added HX-Redirect header to 401 responses
- `src/routers/dues_frontend.py` - Added HX-Redirect header to 401 responses

### Commit
- `8564840 fix: improve HTMX error handling and auth redirects`

### Lessons Learned

1. **HTMX Redirect Mechanism**: For HTMX requests, use `HX-Redirect` header instead of relying on client-side JavaScript.

2. **Specific Error Messages**: Different HTTP status codes deserve different user-facing messages.

3. **Graceful Session Handling**: When sessions expire, redirect to login automatically rather than showing cryptic errors.

### Prevention

1. **HTMX Response Pattern**: For all HTMX partial endpoints, handle authentication failures with HX-Redirect header.

2. **Client-Side Fallback**: The JavaScript handler provides a fallback if the header isn't present.

---

## Bug #023: bcrypt 4.1.x Incompatibility with passlib

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Medium (log spam, potential auth issues)
**Status:** RESOLVED

### Symptoms
- Railway logs show repeated error: `(trapped) error reading bcrypt version`
- Traceback shows: `AttributeError: module 'bcrypt' has no attribute '__about__'`
- Error occurs during password hashing/verification operations
- Authentication still works but logs are polluted

### Root Cause Analysis

The `requirements.txt` specified `bcrypt==4.1.3`, but bcrypt 4.1+ removed the `__about__` attribute that passlib tries to access:

```python
# passlib tries to do:
version = _bcrypt.__about__.__version__  # Fails in bcrypt 4.1+
```

bcrypt 4.0.x still had `__about__`, but 4.1.0 removed it as part of internal API cleanup.

### Solution

Pinned bcrypt to 4.0.1 which is compatible with passlib:

```txt
# requirements.txt
# --- Authentication ---
bcrypt>=4.0.1
python-jose[cryptography]==3.3.0
```

Also removed `passlib[bcrypt]` since we now use direct bcrypt in `src/core/security.py` (see Bug #012).

### Files Modified
- `requirements.txt` - Changed bcrypt version constraint

### Commit
- `8564840 fix: improve HTMX error handling and auth redirects`

### Lessons Learned

1. **Version Pinning**: For security-critical libraries, pin to tested versions rather than using `>=`.

2. **Library Compatibility**: When using wrapper libraries (passlib), check compatibility with underlying libraries (bcrypt).

3. **Direct Usage**: Since we replaced passlib with direct bcrypt (Bug #012), we could use bcrypt>=4.1 if we wanted, but pinning avoids potential future issues.

### Prevention

1. **Test with Specific Versions**: CI should test with exact pinned versions.

2. **Monitor Deprecations**: Watch for deprecation warnings in library changelogs.

---

## Bug #024: Reports Router Async/Sync Session Mismatch

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (Reports page 500 error)
**Status:** RESOLVED

### Symptoms
- User navigates to Reports page
- Browser shows 500 "Something Went Wrong" error
- Railway logs show: `TypeError: object Result can't be used in 'await' expression`
- Reports page completely broken

### Root Cause Analysis

The `reports.py` router was incorrectly using async database operations with a synchronous session:

```python
# WRONG - reports.py
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/members/roster")
async def member_roster_report(
    db: AsyncSession = Depends(get_db),  # Type hint says async
):
    result = await db.execute(stmt)  # await on sync session!
```

But `get_db()` returns a synchronous `Session`:

```python
# session.py - returns SYNC session
def get_db() -> Session:
    db = SessionLocal()  # Sync session
    yield db
```

When `await` is used on a synchronous `Result` object, Python raises TypeError.

### Solution

Changed reports router to use synchronous database calls:

```python
# CORRECT - reports.py
from sqlalchemy.orm import Session

@router.get("/members/roster")
async def member_roster_report(
    db: Session = Depends(get_db),  # Correct type hint
):
    result = db.execute(stmt)  # No await
```

### Files Modified
- `src/routers/reports.py` - Changed `AsyncSession` to `Session`, removed all `await` keywords from db calls

### Commit
- `9543c5b fix: reports router using sync db session instead of async`

### Lessons Learned

1. **Consistent Session Type**: The codebase uses synchronous `Session`, not `AsyncSession`. All routers must match.

2. **FastAPI Async Endpoints**: FastAPI routes can be `async def` even with sync database - just don't `await` db calls.

3. **Type Hints Matter**: Incorrect type hints can mask bugs that only appear at runtime.

### Prevention

1. **Pattern Consistency**: Document that all database operations use sync `Session`, not `AsyncSession`.

2. **IDE Type Checking**: Enable strict type checking to catch type mismatches.

3. **Template Router**: Create a router template with correct imports for copy-paste.

---

## Bug #025: Setup Flow Silent Role Assignment Failure

**Date Discovered:** 2026-01-30
**Date Fixed:** 2026-01-30
**Severity:** Critical (new admin users have no permissions)
**Status:** RESOLVED

### Symptoms
- User creates account via setup flow, selects "Administrator" role
- User logs in successfully
- User clicks "Staff & Permissions" - sees 403 Access Denied
- User has NO roles despite selecting admin during setup
- Railway logs show: "Token validation failed" but user IS logged in

### Root Cause Analysis

The `create_setup_user()` function in `setup_service.py` had silent failure when role lookup failed:

```python
# setup_service.py - WRONG (silent failure)
db_role = db.execute(
    select(Role).where(Role.name == role.lower())
).scalar_one_or_none()

if db_role:  # If role not found, this block is SKIPPED SILENTLY
    user_role = UserRole(...)
    db.add(user_role)

# User created WITHOUT roles!
```

If the Role table wasn't seeded or the role name didn't match, the user was created without any roles - but no error was raised.

### Solution

**1. Fixed setup_service.py to raise error if role not found:**
```python
db_role = db.execute(
    select(Role).where(Role.name == role.lower())
).scalar_one_or_none()

if not db_role:
    db.rollback()
    raise ValueError(
        f"Role '{role}' not found in database. Please ensure roles are seeded. "
        "Run: python -m src.seed.run_seed"
    )

# Role definitely exists now
user_role = UserRole(...)
db.add(user_role)
```

**2. Created migration to fix existing users without roles:**
```python
# 813f955b11af_fix_missing_user_roles.py
def upgrade():
    # Find users with no roles
    result = conn.execute(sa.text("""
        SELECT u.id, u.email FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        WHERE ur.id IS NULL
        AND u.email != 'admin@ibew46.com'
    """))

    # Assign admin role to each
    for user in users_without_roles:
        conn.execute(sa.text("""
            INSERT INTO user_roles (user_id, role_id, assigned_by, created_at)
            VALUES (:user_id, :role_id, 'migration_fix', NOW())
        """), {"user_id": user_id, "role_id": admin_role_id})
```

### Files Modified
- `src/services/setup_service.py` - Changed silent failure to explicit error
- `src/db/migrations/versions/813f955b11af_fix_missing_user_roles.py` - New migration to fix existing users

### Commit
- `2f16502 fix: add migration to fix users with missing roles`
- `e9a4c77 fix: include display_name in role creation for production compatibility`

### Lessons Learned

1. **Never Fail Silently**: Critical operations like role assignment should raise errors on failure, not skip silently.

2. **Defensive Coding**: Check for required data and fail fast with clear messages.

3. **Data Integrity**: Users created without roles are in an invalid state - enforce data integrity at creation time.

4. **Migration Fixes**: Data migrations can fix existing invalid data while code fixes prevent new invalid data.

### Prevention

1. **Required Relationships**: Consider making role assignment mandatory (raise error if no roles assigned).

2. **Validation Layer**: Add validation that newly created users have at least one role.

3. **Startup Checks**: Add health check that verifies no users exist without roles.

---

*Last Updated: 2026-01-30 (Bugs #022-#025 added - HTMX error handling, bcrypt compatibility, reports async/sync, setup role assignment)*
