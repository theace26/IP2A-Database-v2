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

*Last Updated: 2026-01-30 (Bug #006 added)*
