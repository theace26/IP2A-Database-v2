# 5. Deployment Verification

**Duration:** 30 minutes
**Goal:** Verify both deployments are working correctly

---

## Pre-Verification Checklist

Before testing, ensure:

- [x] Railway deployment is green (healthy)
- [x] Render deployment is green (healthy)
- [x] S3 credentials are configured on both
- [x] Database migrations have run
- [x] Demo data has been seeded
- [x] Admin user has been created

**Current Project Stats (v0.7.9):**
- Backend Tests: 165
- Frontend Tests: ~167
- Total Tests: ~330
- API Endpoints: ~130
- ADRs: 11 (including ADR-008 Audit Logging, ADR-011 Dues Frontend)

---

## Verification Tests

Run these tests on **both** Railway and Render deployments.

### Test 1: Health Check

```bash
# Railway
curl https://YOUR-RAILWAY-APP.up.railway.app/health

# Render
curl https://YOUR-RENDER-APP.onrender.com/health
```

**Expected Response:**
```json
{"status":"healthy","version":"0.7.9"}
```

✅ Pass: Returns 200 with healthy status
❌ Fail: Connection refused, timeout, or error status

---

### Test 2: API Documentation

Visit in browser:
- Railway: `https://YOUR-RAILWAY-APP.up.railway.app/docs`
- Render: `https://YOUR-RENDER-APP.onrender.com/docs`

**Expected:** Swagger UI loads with all endpoints listed

✅ Pass: Swagger UI displays
❌ Fail: 404 or blank page

> Note: If docs disabled in production, this will 404 (expected)

---

### Test 3: First-Time Setup (Fresh Deployment)

If this is a fresh deployment (no users besides default admin):

1. Visit root URL
2. **Expected:** Redirect to `/setup`
3. Verify:
   - Default admin info displayed (`admin@ibew46.com`)
   - "Disable the default admin account" checkbox visible
   - Form requires email, name, password

4. Complete setup:
   - Enter your email (NOT `admin@ibew46.com`)
   - Enter name
   - Enter password meeting requirements
   - Check "Disable default admin" (recommended for production)
   - Click "Complete Setup"

**Expected:** Redirect to login page with success message

✅ Pass: Setup completes, redirects to login
❌ Fail: Error messages, cannot complete setup

---

### Test 4: Login Page

Visit in browser:
- Railway: `https://YOUR-RAILWAY-APP.up.railway.app/login`
- Render: `https://YOUR-RENDER-APP.onrender.com/login`

**Expected:** Styled login page with email/password fields

✅ Pass: Login form displays with DaisyUI styling
❌ Fail: Unstyled page, 500 error, or missing assets

---

### Test 5: Authentication Flow

1. Visit `/login`
2. Enter your admin credentials (created during setup):
   - Email: Your email from setup
   - Password: Your password from setup
3. Click Login

**Expected:** Redirect to dashboard with stats

✅ Pass: Dashboard loads with activity feed
❌ Fail: Login error, redirect loop, or 500

---

### Test 6: Dashboard Stats

On the dashboard, verify:
- Active Members count shows a number
- Students count shows a number
- Grievances count shows a number
- Dues MTD shows a dollar amount
- Activity feed shows recent items

**Expected:** All stats populated (may be 0 if no seed data)

✅ Pass: Stats display correctly
❌ Fail: Errors, missing data, or broken layout

---

### Test 7: Navigation

Test each sidebar link:

| Link | Expected Page |
|------|---------------|
| Dashboard | Stats and activity feed |
| Members → Overview | Member stats dashboard |
| Members → List | Member table with search |
| Training → Overview | Training stats |
| Training → Students | Student list |
| Training → Courses | Course cards |
| Operations → Overview | Module cards |
| Operations → SALTing | Activities list |
| Operations → Benevolence | Applications list |
| Operations → Grievances | Grievances list |
| Dues → Overview | Dues stats |
| Dues → Rates | Rates table |
| Dues → Periods | Periods list |
| Dues → Payments | Payments table |
| Dues → Adjustments | Adjustments list |
| Documents | Upload/browse interface |
| Reports | Report categories |
| Staff | User management |

✅ Pass: All pages load without errors
❌ Fail: 404s, 500s, or missing content

---

### Test 8: Search Functionality

On Members List (`/members/list`):
1. Type in search box
2. Wait 300ms

**Expected:** Table filters via HTMX without page reload

✅ Pass: Table updates dynamically
❌ Fail: Full page reload or no response

---

### Test 9: Document Upload (S3)

1. Navigate to Documents
2. Click Upload
3. Select a small PDF or image
4. Set entity type and ID
5. Click Upload

**Expected:** File uploads, appears in list

✅ Pass: File uploads and appears in browse
❌ Fail: Upload error or file not saved

---

### Test 10: Report Generation

1. Navigate to Reports
2. Click on "Member Roster"
3. Select PDF or Excel format

**Expected:** Report downloads

✅ Pass: PDF/Excel file downloads
❌ Fail: Error or no download

---

### Test 11: Mobile Responsiveness

On your phone or browser DevTools (mobile view):
1. Visit the login page
2. Login
3. Open sidebar (hamburger menu)
4. Navigate to a few pages

**Expected:** Responsive layout, drawer navigation works

✅ Pass: Mobile-friendly interface
❌ Fail: Broken layout or inaccessible navigation

---

## Verification Scorecard

| Test | Railway | Render |
|------|---------|--------|
| 1. Health Check | ⬜ | ⬜ |
| 2. API Docs | ⬜ | ⬜ |
| 3. First-Time Setup | ⬜ | ⬜ |
| 4. Login Page | ⬜ | ⬜ |
| 5. Auth Flow | ⬜ | ⬜ |
| 6. Dashboard Stats | ⬜ | ⬜ |
| 7. Navigation | ⬜ | ⬜ |
| 8. Search | ⬜ | ⬜ |
| 9. Document Upload | ⬜ | ⬜ |
| 10. Reports | ⬜ | ⬜ |
| 11. Mobile | ⬜ | ⬜ |

**Goal:** All 11 tests passing on at least one platform

---

## Common Issues & Fixes

### CSS/JS Not Loading
- Check static files are included in Docker build
- Verify StaticFiles mount in main.py
- Check browser console for 404s

### Database Errors
- Run migrations: `alembic upgrade head`
- Check DATABASE_URL is set correctly
- Verify database is running

### Session/Cookie Issues
- Check SECRET_KEY is set
- Verify HTTPS is working (cookies require secure)
- Clear browser cookies and retry

### S3 Upload Fails
- Verify all S3_* environment variables
- Check bucket permissions
- Test with shell script from Step 6 of S3 guide

### Slow Render Response
- Free tier sleeps after 15 min
- First request takes ~30 seconds
- Use keep-alive service or upgrade

---

## Performance Check

Use browser DevTools Network tab:

| Metric | Acceptable | Good |
|--------|------------|------|
| Initial page load | < 3s | < 1s |
| HTMX partial update | < 500ms | < 200ms |
| Login response | < 1s | < 500ms |
| Report generation | < 10s | < 5s |

---

## Final Verification

Once all tests pass:

```bash
# Ensure you're on develop
git checkout develop

# Tag the verified release (on develop for reference)
git tag -a v0.8.0 -m "Production deployment verified

Verified deployments:
- Railway: https://xxx.up.railway.app
- Render: https://xxx.onrender.com

All verification tests passing
Branch strategy: main (demo) / develop (work)"

git push origin v0.8.0

# Main branch already has these changes from earlier merge
# Both Railway and Render are deploying from main
```

**Branch Status:**
- `main` → Deployed to Railway + Render (stable demo)
- `develop` → Your working branch (continues development)

---

**Verification complete!** ✅

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

**Next:** `6-DEMO-WALKTHROUGH.md` →
