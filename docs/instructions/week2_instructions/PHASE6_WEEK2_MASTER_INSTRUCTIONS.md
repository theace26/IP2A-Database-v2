# Phase 6 Week 2: Auth Cookies + Real Dashboard

**Created:** January 28, 2026
**Estimated Time:** 6-8 hours (3-4 sessions)
**Prerequisites:** Week 1 complete (login page, dashboard, frontend router)

---

## Overview

Week 2 transforms the static frontend into a working authenticated application:

| Session | Focus | Time |
|---------|-------|------|
| A | JWT Cookie Auth + Middleware | 2-3 hrs |
| B | Real Dashboard Data + Activity Feed | 2-3 hrs |
| C | Polish + Tests + Commit | 1-2 hrs |

---

## Week 2 Objectives

### Must Have (MVP)
- [ ] Store JWT in HTTP-only cookie on successful login
- [ ] Auth middleware redirects unauthenticated users to `/login`
- [ ] Dashboard shows real counts from database
- [ ] Logout clears cookie and redirects to login
- [ ] 10+ new tests

### Nice to Have
- [ ] Activity feed from audit log
- [ ] "Remember me" extends cookie duration
- [ ] Flash messages on login/logout

---

## Architecture Decisions

### Why HTTP-only Cookies (not localStorage)?

| Approach | XSS Vulnerable | CSRF Vulnerable | Recommendation |
|----------|----------------|-----------------|----------------|
| localStorage | ✅ Yes | No | ❌ Don't use |
| HTTP-only Cookie | No | ✅ Yes | ✅ Use with CSRF token |

**Decision:** Use HTTP-only cookies with SameSite=Lax (protects against CSRF for GET requests).

### Cookie Structure

```
access_token: JWT (HttpOnly, Secure in prod, SameSite=Lax, 30min)
refresh_token: JWT (HttpOnly, Secure in prod, SameSite=Strict, 7days)
```

### Auth Flow

```
1. User submits login form (HTMX POST to /api/auth/login)
2. Backend validates credentials
3. Backend sets HTTP-only cookies with tokens
4. Backend returns JSON success + redirect URL
5. Frontend JavaScript redirects to /dashboard
6. Dashboard page request includes cookies automatically
7. Auth middleware validates cookie, allows access
```

---

## File Changes Summary

### New Files
- `src/routers/dependencies/auth_cookie.py` - Cookie-based auth dependency
- `src/templates/partials/activity_feed.html` - HTMX partial for activity

### Modified Files
- `src/routers/auth.py` - Add cookie setting on login
- `src/routers/frontend.py` - Add auth middleware to protected routes
- `src/templates/dashboard/index.html` - Replace placeholders with real data
- `src/templates/auth/login.html` - Handle cookie-based redirect
- `src/tests/test_frontend.py` - Add auth tests

---

## Session Breakdown

### Session A: Auth Cookies (Document 1)
1. Create `auth_cookie.py` dependency
2. Modify login endpoint to set cookies
3. Modify logout endpoint to clear cookies
4. Add auth middleware to protected routes
5. Test login/logout flow manually

### Session B: Dashboard Data (Document 2)
1. Create dashboard service with real queries
2. Update dashboard route to fetch data
3. Create activity feed partial
4. Add audit log query for recent activity
5. Wire up HTMX refresh

### Session C: Polish & Tests (Document 3)
1. Add flash messages on login/logout
2. Handle token expiry gracefully
3. Write comprehensive tests
4. Update documentation
5. Final commit

---

## Quick Reference

### Setting a Cookie (FastAPI)
```python
from fastapi import Response

response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    secure=False,  # True in production
    samesite="lax",
    max_age=1800,  # 30 minutes
    path="/"
)
```

### Reading a Cookie
```python
from fastapi import Cookie

async def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401)
    # Verify token...
```

### Clearing a Cookie
```python
response.delete_cookie(key="access_token", path="/")
```

---

## Success Criteria

Week 2 is complete when:
- [ ] Login sets HTTP-only cookies
- [ ] Unauthenticated users redirected to /login
- [ ] Dashboard shows real member/student/grievance counts
- [ ] Logout clears cookies and redirects
- [ ] All tests pass (187+ total)
- [ ] Browser testing confirms full flow works

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

*Proceed to Document 1 (Session A) to begin implementation.*
