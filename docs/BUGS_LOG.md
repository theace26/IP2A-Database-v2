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

*Last Updated: 2026-01-30*
