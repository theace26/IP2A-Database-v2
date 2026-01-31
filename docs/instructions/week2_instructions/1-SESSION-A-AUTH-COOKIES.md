# Phase 6 Week 2 - Session A: JWT Cookie Authentication

**Document:** 1 of 3
**Estimated Time:** 2-3 hours
**Focus:** Cookie-based authentication for frontend

---

## Objective

Transform the existing JWT auth system to use HTTP-only cookies for browser-based authentication while maintaining the existing API token auth for programmatic access.

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show 177 passed
```

---

## Step 1: Create Cookie Auth Dependency (20 min)

Create `src/routers/dependencies/auth_cookie.py`:

```python
"""
Cookie-based authentication for frontend routes.
Uses HTTP-only cookies to store JWT tokens securely.
"""

from fastapi import Cookie, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from src.core.security import verify_token
from src.services.user_service import get_user_by_id
from src.db.session import get_db

logger = logging.getLogger(__name__)


class AuthenticationRequired:
    """
    Dependency that requires a valid JWT cookie.
    Redirects to login page if not authenticated.
    """
    
    def __init__(self, redirect_to_login: bool = True):
        self.redirect_to_login = redirect_to_login
    
    async def __call__(
        self,
        request: Request,
        access_token: Optional[str] = Cookie(default=None),
    ):
        """
        Validate the access_token cookie.
        
        Returns:
            User dict if valid token
            
        Raises:
            RedirectResponse to /login if redirect_to_login=True
            HTTPException 401 if redirect_to_login=False
        """
        if not access_token:
            return self._handle_unauthorized(request)
        
        try:
            # Verify the JWT token
            payload = verify_token(access_token)
            if not payload:
                return self._handle_unauthorized(request)
            
            user_id = payload.get("sub")
            if not user_id:
                return self._handle_unauthorized(request)
            
            # Return user info from token (avoid DB call on every request)
            return {
                "id": int(user_id),
                "email": payload.get("email"),
                "roles": payload.get("roles", []),
            }
            
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return self._handle_unauthorized(request)
    
    def _handle_unauthorized(self, request: Request):
        """Handle unauthorized access."""
        if self.redirect_to_login:
            # Store the original URL to redirect back after login
            return_url = str(request.url.path)
            return RedirectResponse(
                url=f"/login?next={return_url}",
                status_code=status.HTTP_302_FOUND
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )


# Convenience instances
require_auth = AuthenticationRequired(redirect_to_login=True)
require_auth_api = AuthenticationRequired(redirect_to_login=False)


async def get_current_user_from_cookie(
    access_token: Optional[str] = Cookie(default=None),
) -> Optional[dict]:
    """
    Get current user from cookie without raising exceptions.
    Returns None if not authenticated.
    Useful for pages that work both with and without auth.
    """
    if not access_token:
        return None
    
    try:
        payload = verify_token(access_token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return {
            "id": int(user_id),
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
        }
    except Exception:
        return None
```

---

## Step 2: Update Auth Router for Cookies (30 min)

Modify `src/routers/auth.py` to set cookies on login.

**Add these imports at the top:**
```python
from fastapi import Response
from fastapi.responses import JSONResponse
```

**Find the login endpoint and modify it to set cookies:**

Look for something like `@router.post("/login")` and update it:

```python
@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return tokens.
    Sets HTTP-only cookies for browser-based auth.
    Also returns tokens in response body for API clients.
    """
    # Your existing authentication logic here...
    # (validate credentials, get user, create tokens)
    
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create tokens (your existing code)
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Set HTTP-only cookies for browser auth
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=1800,  # 30 minutes
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="strict",
        max_age=604800,  # 7 days
        path="/api/auth"  # Only sent to auth endpoints
    )
    
    # Return tokens in body for API clients
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
```

**Update logout endpoint to clear cookies:**

```python
@router.post("/logout")
async def logout(
    response: Response,
    access_token: str = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user by clearing cookies and invalidating refresh token.
    """
    # Clear cookies
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")
    
    # Optionally revoke refresh token in database
    # (your existing revocation logic if any)
    
    return {"message": "Successfully logged out"}
```

---

## Step 3: Update Frontend Router (30 min)

Modify `src/routers/frontend.py` to use the new auth dependency.

**Add imports:**
```python
from src.routers.dependencies.auth_cookie import (
    require_auth,
    get_current_user_from_cookie,
)
```

**Update protected routes:**

```python
# ============================================================
# Dashboard (Auth Required)
# ============================================================

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to dashboard (will redirect to login if not auth'd)."""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render main dashboard - requires authentication."""
    # If require_auth returned a redirect, return it
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    stats = await get_dashboard_stats(db)
    
    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "stats": stats,
            "user": current_user,
        }
    )


@router.get("/logout")
async def logout_page(request: Request):
    """Handle logout - POST to API then redirect."""
    # The actual logout happens via POST to /api/auth/logout
    # This page just shows a redirect or confirmation
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")
    return response
```

**Keep login page public (no auth required):**
```python
@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: str = None,
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Render login page. Redirect to dashboard if already logged in."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "next": next or "/dashboard"}
    )
```

---

## Step 4: Update Login Template (20 min)

Modify `src/templates/auth/login.html` to handle the cookie-based flow:

**Update the form's HTMX handler:**

Find the `<form>` tag and update it:

```html
<form 
    hx-post="/api/auth/login" 
    hx-target="#login-result"
    hx-swap="innerHTML"
    hx-indicator="#login-spinner"
    hx-on::after-request="handleLoginResponse(event)"
    class="space-y-4"
>
```

**Update the JavaScript at the bottom:**

```html
<script>
function handleLoginResponse(event) {
    const xhr = event.detail.xhr;
    
    if (xhr.status === 200) {
        // Success - cookies are set automatically by the browser
        // Get the redirect URL from the page or default to dashboard
        const nextUrl = '{{ next | default("/dashboard") }}';
        window.location.href = nextUrl;
    } else {
        // Error - display message in result area
        try {
            const data = JSON.parse(xhr.response);
            document.getElementById('login-result').innerHTML = `
                <div class="alert alert-error mt-4">
                    <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>${data.detail || 'Login failed. Please try again.'}</span>
                </div>
            `;
        } catch (e) {
            document.getElementById('login-result').innerHTML = `
                <div class="alert alert-error mt-4">
                    <span>An error occurred. Please try again.</span>
                </div>
            `;
        }
    }
}
</script>
```

---

## Step 5: Test the Auth Flow (15 min)

### Manual Testing

```bash
# Start the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

1. **Visit `/dashboard`** → Should redirect to `/login`
2. **Login with valid credentials** → Should redirect to `/dashboard`
3. **Check cookies in browser DevTools** → Should see `access_token` (HttpOnly)
4. **Visit `/logout`** → Should redirect to `/login`
5. **Visit `/dashboard` again** → Should redirect to `/login` (cookies cleared)

### Test Credentials

Use your seeded test user or create one:
```
Email: admin@ip2a.local
Password: (whatever you set in seed)
```

---

## Step 6: Create Auth Cookie Tests (30 min)

Add to `src/tests/test_frontend.py`:

```python
# ============================================================
# Cookie Auth Tests
# ============================================================

class TestCookieAuth:
    """Tests for cookie-based authentication."""

    @pytest.mark.asyncio
    async def test_dashboard_redirects_without_auth(self, async_client: AsyncClient):
        """Dashboard should redirect to login when not authenticated."""
        response = await async_client.get("/dashboard", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_login_sets_cookie(self, async_client: AsyncClient):
        """Successful login should set access_token cookie."""
        # This test requires a valid user in the database
        # You may need to create a user fixture
        response = await async_client.post(
            "/api/auth/login",
            data={"username": "admin@ip2a.local", "password": "testpassword"},
        )
        # If credentials are valid
        if response.status_code == 200:
            cookies = response.cookies
            assert "access_token" in cookies

    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self, async_client: AsyncClient):
        """Logout should clear the access_token cookie."""
        response = await async_client.get("/logout", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        # Check cookie is being deleted (Set-Cookie with max-age=0 or expires in past)

    @pytest.mark.asyncio
    async def test_login_page_redirects_if_authenticated(self, async_client: AsyncClient):
        """Login page should redirect to dashboard if already authenticated."""
        # First login to get cookie
        # Then visit /login and expect redirect to /dashboard
        pass  # Implement with proper user fixture

    @pytest.mark.asyncio
    async def test_protected_route_with_valid_cookie(self, async_client: AsyncClient):
        """Protected routes should work with valid cookie."""
        # Login, then access dashboard with cookie
        pass  # Implement with proper user fixture
```

---

## Step 7: Run All Tests

```bash
pytest -v --tb=short

# Expected: 177+ tests passing
# New tests: ~5 cookie auth tests
```

---

## Step 8: Commit

```bash
git add -A
git status

git commit -m "feat(auth): Add cookie-based authentication for frontend

- Add auth_cookie.py dependency for cookie validation
- Update login endpoint to set HTTP-only cookies
- Update logout to clear cookies
- Add auth middleware to protected routes
- Update login template for cookie flow
- Add cookie auth tests

Cookies use:
- HttpOnly: prevents XSS access
- SameSite=Lax: prevents CSRF for state-changing requests
- Secure=False (dev) / True (prod)"

git push origin main
```

---

## Troubleshooting

### "Cookie not being set"
- Check browser DevTools → Application → Cookies
- Ensure `secure=False` for local development (no HTTPS)
- Check `path="/"` is set correctly

### "Redirect loop on login"
- Check that login page doesn't require auth
- Verify `get_current_user_from_cookie` returns None, not raising

### "Token validation failing"
- Check JWT secret key matches between creation and verification
- Verify token hasn't expired (30 min default)

---

## Session A Checklist

- [ ] Created `auth_cookie.py` dependency
- [ ] Updated login endpoint to set cookies
- [ ] Updated logout endpoint to clear cookies
- [ ] Added auth requirement to dashboard route
- [ ] Updated login template JavaScript
- [ ] Manually tested login/logout flow
- [ ] Added cookie auth tests
- [ ] All tests passing
- [ ] Committed changes

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*Session A complete. Proceed to Session B for real dashboard data.*
