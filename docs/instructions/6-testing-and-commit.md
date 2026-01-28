# Phase 6 Week 1: Document 6 - Testing & Commit

**Execution Order:** 6 of 6
**Estimated Time:** 30-45 minutes
**Goal:** Add tests, verify everything works, commit changes
**Prerequisites:** Document 5 complete (router integrated, app running)

---

## Overview

Final document in Week 1:
1. Create frontend tests
2. Run all tests (existing + new)
3. Manual browser verification
4. Commit all changes
5. Update CHANGELOG

---

## Task 6.1: Create Frontend Tests

**File:** `src/tests/test_frontend.py`

```python
"""
Frontend route tests.

Tests for HTML page rendering and static file serving.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestPublicRoutes:
    """Tests for routes that don't require authentication."""
    
    def test_root_redirects_to_login(self):
        """Root path should redirect to login."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
    
    def test_login_page_renders(self):
        """Login page should render with expected content."""
        response = client.get("/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "IBEW Local 46" in response.text
        assert "Log In" in response.text
        assert "Forgot password?" in response.text
    
    def test_forgot_password_page_renders(self):
        """Forgot password page should render."""
        response = client.get("/forgot-password")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Reset Password" in response.text


class TestProtectedRoutes:
    """Tests for routes that will require authentication.
    
    Note: These currently work without auth for Week 1.
    Week 2 will add auth requirements.
    """
    
    def test_dashboard_page_renders(self):
        """Dashboard page should render."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Dashboard" in response.text
        assert "Welcome back" in response.text
    
    def test_logout_redirects_to_login(self):
        """Logout should redirect to login."""
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"


class TestStaticFiles:
    """Tests for static file serving."""
    
    def test_css_file_served(self):
        """Custom CSS should be accessible."""
        response = client.get("/static/css/custom.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
    
    def test_js_file_served(self):
        """Custom JavaScript should be accessible."""
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        # JS content-type can vary
        assert response.status_code == 200


class TestErrorPages:
    """Tests for custom error pages."""
    
    def test_404_for_unknown_page(self):
        """Unknown routes should return 404 HTML page."""
        response = client.get("/this-page-definitely-does-not-exist-xyz")
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "Page Not Found" in response.text
    
    def test_api_404_returns_json(self):
        """API routes should return JSON 404."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        assert "application/json" in response.headers["content-type"]


class TestPageContent:
    """Tests for specific page content."""
    
    def test_login_has_form(self):
        """Login page should have a form with required fields."""
        response = client.get("/login")
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text
        assert 'hx-post="/api/auth/login"' in response.text
    
    def test_dashboard_has_stats_cards(self):
        """Dashboard should display stats cards."""
        response = client.get("/dashboard")
        assert "Total Members" in response.text
        assert "Students" in response.text
        assert "Open Grievances" in response.text
        assert "Dues MTD" in response.text
    
    def test_dashboard_has_quick_actions(self):
        """Dashboard should have quick action buttons."""
        response = client.get("/dashboard")
        assert "Quick Actions" in response.text
        assert "New Member" in response.text or "+ New Member" in response.text
```

---

## Task 6.2: Run All Tests

```bash
# Run just the frontend tests first
pytest src/tests/test_frontend.py -v

# Then run ALL tests to make sure nothing broke
pytest -v --tb=short
```

**Expected Result:**
- Frontend tests: 10+ tests passing
- Total: 175+ tests passing (165 existing + new frontend tests)

---

## Task 6.3: Manual Browser Testing

Open http://localhost:8000 in your browser and verify:

### Login Page (`/login`)
- [ ] Page loads with styling (not unstyled HTML)
- [ ] IBEW Local 46 logo/branding visible
- [ ] Email and password fields present
- [ ] "Forgot password?" link works
- [ ] Form submits (will fail auth - that's OK for now)

### Dashboard (`/dashboard`)
- [ ] Sidebar visible on desktop (left side)
- [ ] Navbar visible at top
- [ ] Stats cards display with placeholder values
- [ ] Quick actions buttons visible
- [ ] Mobile: hamburger menu appears, sidebar toggles

### Navigation
- [ ] Click on sidebar items (they'll 404 for now - that's expected)
- [ ] User menu dropdown works (top right)
- [ ] Logout redirects to login

### Error Pages
- [ ] Go to `/nonexistent` - should show 404 page
- [ ] Page is styled (not plain text)

---

## Task 6.4: Commit Changes

```bash
# Stage all new files
git add -A

# Verify what's being committed
git status

# Commit with detailed message
git commit -m "feat(frontend): Add Phase 6 Week 1 - Frontend foundation

Templates:
- base.html (full layout with sidebar)
- base_auth.html (centered auth layout)
- Components: navbar, sidebar, flash messages, modal
- Auth: login, forgot password pages
- Dashboard with stats cards and quick actions
- Error pages: 404, 500

Static Files:
- custom.css (HTMX indicators, transitions, responsive)
- app.js (toast notifications, HTMX handlers, shortcuts)

Router:
- src/routers/frontend.py with all HTML routes
- Placeholder routes for future pages
- Custom 404/500 handlers (HTML for browser, JSON for API)

Stack: Jinja2 + HTMX + DaisyUI + Alpine.js (no build step)

Tests: Added ~12 frontend route tests"

# Push to remote
git push origin main
```

---

## Task 6.5: Update CHANGELOG.md (if not done in Document 1)

Ensure `CHANGELOG.md` has the Phase 6 Week 1 entries:

```markdown
## [Unreleased]

### Added
- **Phase 6 Week 1: Frontend Foundation**
  * Base templates with DaisyUI + Tailwind CSS + HTMX + Alpine.js (CDN)
  * Login page with HTMX form submission
  * Forgot password page
  * Dashboard placeholder with stats cards
  * Responsive sidebar navigation with drawer component
  * Component templates (navbar, sidebar, flash messages, modal)
  * Custom CSS and JavaScript
  * Error pages (404, 500)
  * Frontend router for HTML page serving
  * ~12 frontend tests
```

---

## Week 1 Summary

### What's Built

| Item | Status |
|------|--------|
| Directory structure | ✅ |
| base.html | ✅ |
| base_auth.html | ✅ |
| Navbar component | ✅ |
| Sidebar component | ✅ |
| Flash messages | ✅ |
| Modal component | ✅ |
| Login page | ✅ |
| Forgot password page | ✅ |
| Dashboard | ✅ |
| Error pages (404, 500) | ✅ |
| Custom CSS | ✅ |
| Custom JavaScript | ✅ |
| Frontend router | ✅ |
| Static file serving | ✅ |
| Exception handlers | ✅ |
| Frontend tests | ✅ |

### What Works

- ✅ Visit `/login` → styled login form
- ✅ Visit `/dashboard` → sidebar + stats cards + quick actions
- ✅ Mobile responsive (sidebar toggles)
- ✅ Static files served
- ✅ 404/500 error pages render properly
- ✅ All tests pass

### What's Pending (Week 2)

- ❌ Login actually authenticates (stores JWT in cookie)
- ❌ Protected routes check authentication
- ❌ Dashboard shows real data from API
- ❌ Activity feed from audit log
- ❌ User profile dropdown works

---

## ✅ Document 6 Complete - Week 1 Done!

**Final Checklist:**
- [ ] Frontend tests created and passing
- [ ] All existing tests still pass (165+)
- [ ] Browser testing complete
- [ ] Changes committed and pushed
- [ ] CHANGELOG updated

**Total Time:** ~4-6 hours across 6 documents

---

## Week 2 Preview

Next week focuses on:
1. JWT cookie authentication (store token in HTTP-only cookie)
2. Protected route middleware
3. Dashboard with real API data
4. Activity feed from audit log
5. Working logout functionality

---

*Document 6 of 6 | Phase 6 Week 1 Complete*
