# 2. Railway Deployment

**Duration:** 1-1.5 hours
**Goal:** Deploy IP2A-v2 to Railway with PostgreSQL

Railway is the fastest path to a working demo. Free tier includes $5/month credit.

---

## Prerequisites

- [x] Railway account: https://railway.app (sign in with GitHub)
- [x] Production config committed and **merged to `main`** (from `1-PRODUCTION-CONFIG.md`)
- [x] GitHub repo accessible
- [x] Branch strategy set up (`main` for demo, `develop` for work)

---

## Important: Branch Configuration

Railway deploys from `main` by default. This is what we want:
- Your demo stays stable on `main`
- Development continues on `develop`
- Updates deploy only when you merge `develop → main`

---

## Step 1: Create Railway Project

1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Find and select `IP2A-Database-v2`
5. Railway will detect the Dockerfile automatically

**Don't click Deploy yet!** We need to add the database first.

---

## Step 2: Add PostgreSQL Database

1. In your new project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway provisions a PostgreSQL instance

Wait ~30 seconds for the database to be ready.

---

## Step 3: Connect App to Database

1. Click on your **IP2A-Database-v2** service (not the database)
2. Go to **"Variables"** tab
3. Click **"Add Variable"**
4. Click **"Add Reference"** → select **PostgreSQL** → **DATABASE_URL**

Railway automatically injects the database connection string.

---

## Step 4: Add Required Environment Variables

Still in the **Variables** tab, add these:

### Critical Authentication Variables (ADD FIRST!)

| Variable | Value | Notes |
|----------|-------|-------|
| `AUTH_JWT_SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` | **CRITICAL** - Run command locally, paste output |
| `DEFAULT_ADMIN_PASSWORD` | (your secure password) | Password for admin@ibew46.com |

> ⚠️ **WARNING:** If `AUTH_JWT_SECRET_KEY` is not set, a random key is generated on each restart, invalidating ALL user sessions. Users will see "Signature verification failed" errors. See Bug #006 in `docs/BUGS_LOG.md`.

### Application Variables

| Variable | Value |
|----------|-------|
| `IP2A_ENV` | `prod` |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `RUN_PRODUCTION_SEED` | `false` |

> **Note:** Only set `RUN_PRODUCTION_SEED=true` for initial deployment, then set to `false` immediately. Leaving it `true` will cause database wipes on every restart!

**For S3 (add after Step 4 of `4-S3-STORAGE.md`):**
| Variable | Value |
|----------|-------|
| `S3_ENDPOINT_URL` | `https://s3.us-west-002.backblazeb2.com` |
| `S3_ACCESS_KEY_ID` | (from Backblaze) |
| `S3_SECRET_ACCESS_KEY` | (from Backblaze) |
| `S3_BUCKET_NAME` | `ip2a-documents` |
| `S3_REGION` | `us-west-002` |

---

## Step 5: Configure Deployment Settings

1. Click on your service
2. Go to **"Settings"** tab
3. Under **"Deploy"**:
   - Build Command: (leave empty, uses Dockerfile)
   - Start Command: (leave empty, uses Dockerfile CMD)
   - Health Check Path: `/health`

> **Note:** The `railway.json` file in the repo configures these settings. Don't add a custom start command — the Dockerfile's CMD handles `$PORT` expansion correctly.

4. Under **"Networking"**:
   - Click **"Generate Domain"** to get a public URL
   - Note your URL: `https://ip2a-database-v2-production.up.railway.app` (or similar)

---

## Step 6: Deploy

1. Railway should auto-deploy when you push to GitHub
2. If not, click **"Deploy"** → **"Deploy Now"**
3. Watch the build logs in the **"Deployments"** tab

Build takes ~3-5 minutes on first deploy.

---

## Step 7: Verify Deployment

Once deployed (green checkmark):

1. **Health Check:**
   ```bash
   curl https://YOUR-APP.up.railway.app/health
   # Should return: {"status":"healthy","version":"0.7.9"}
   ```

2. **API Docs (if enabled):**
   - Visit: `https://YOUR-APP.up.railway.app/docs`

3. **Login Page:**
   - Visit: `https://YOUR-APP.up.railway.app/login`

---

## Step 8: Run Database Migrations

If migrations didn't run automatically, use Railway CLI:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Run migrations
railway run alembic upgrade head
```

---

## Step 9: Seed Demo Data

Use Railway CLI to seed the database:

```bash
# Connect to project
railway link

# Run seed commands
railway run python -c "
from src.db.database import SessionLocal
from src.seed.all_seeds import seed_all

db = SessionLocal()
seed_all(db)
db.close()
print('Seeding complete!')
"
```

Or create a seed endpoint (add to `src/main.py`):

```python
@app.post("/admin/seed", include_in_schema=False)
async def seed_database(db: Session = Depends(get_db)):
    """Seed database with demo data. Remove in production!"""
    from src.seed.all_seeds import seed_all
    seed_all(db)
    return {"status": "seeded"}
```

Then:
```bash
curl -X POST https://YOUR-APP.up.railway.app/admin/seed
```

**⚠️ Remove this endpoint after seeding!**

---

## Step 10: Create Admin User

```bash
railway run python -c "
from src.db.database import SessionLocal
from src.db.models import User, Role
from src.services.auth_service import AuthService

db = SessionLocal()

# Find admin role
admin_role = db.query(Role).filter(Role.name == 'admin').first()

# Create admin user
user = AuthService.create_user(
    db,
    email='admin@ip2a.local',
    password='DemoAdmin2026!',  # Change this!
    first_name='Admin',
    last_name='User'
)

# Assign admin role
user.roles.append(admin_role)
db.commit()

print(f'Admin user created: {user.email}')
"
```

---

## Railway Dashboard Overview

Your Railway project should now show:

```
┌─────────────────────────────────────────┐
│  IP2A-Database-v2 (Project)             │
├─────────────────────────────────────────┤
│  🟢 ip2a-database-v2     (Web Service)  │
│     └─ https://xxx.up.railway.app       │
│                                         │
│  🟢 PostgreSQL           (Database)     │
│     └─ Connected                        │
└─────────────────────────────────────────┘
```

---

## Cost Estimate (Railway)

| Resource | Free Tier | After Free |
|----------|-----------|------------|
| Web Service | $5/mo credit | ~$5-10/mo |
| PostgreSQL | Included | ~$5/mo (hobby) |
| **Total** | Free for demo | ~$10-15/mo |

---

## Troubleshooting

### Build Fails
- Check logs in Deployments tab
- Ensure `requirements.txt` is complete
- Verify `Dockerfile` syntax

### Database Connection Error
- Check DATABASE_URL variable is set
- Verify PostgreSQL is provisioned and running
- Check logs for connection string issues

### Health Check Fails
- Ensure `/health` endpoint exists
- Check app is binding to `$PORT` (Railway provides this)
- Review startup logs for errors

### Migrations Don't Run
- Check `alembic.ini` has correct path
- Verify migrations folder is included in Docker build
- Run manually via Railway CLI

### Container Restart Loop (Seed Timeout)
**Symptom:** Container starts, runs seed, gets killed, restarts indefinitely
**Cause:** `RUN_PRODUCTION_SEED=true` causes 30-60s seed on every startup, exceeding health check timeout
**Fix:** Set `RUN_PRODUCTION_SEED=false` in Railway variables
**See:** Bug #007 in `docs/BUGS_LOG.md`

### "Signature verification failed" Errors
**Symptom:** Logs show repeated token validation failures, users can't access protected pages
**Cause:** `AUTH_JWT_SECRET_KEY` not set - random key generated on each restart
**Fix:**
1. Generate key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. Add `AUTH_JWT_SECRET_KEY` variable in Railway with the generated value
3. Users must clear browser cookies and log in again
**See:** Bug #006 in `docs/BUGS_LOG.md`

### Users Can't Log In After Deployment
**Symptom:** Login page loads but login fails, or users see blank page
**Possible Causes:**
1. Old cookies with invalid tokens - clear browser cookies
2. `DEFAULT_ADMIN_PASSWORD` not set - add to Railway variables
3. Database not seeded - check if seed ran successfully
**Fix:** Clear cookies, verify environment variables, check logs

### Health Check Fails - KeyError in Seed
**Symptom:** Build succeeds but health check fails, logs show `KeyError: 'users_created'`
**Cause:** Railway deployed cached/old code; production_seed.py has a bug
**Fix:**
1. Verify latest code is pushed to `main`
2. In Railway dashboard, go to Deployments
3. Click "Deploy" to trigger fresh build (don't use cached)
4. Or clear build cache in Settings
**See:** Bug #009 in `docs/BUGS_LOG.md`

### Seed Fails - Missing Seed Files
**Symptom:** Production seed fails with `ImportError` for grants, expenses, or instructor_hours
**Cause:** Production seed expanded but seed files not created yet
**Fix:** Ensure you have these files in `src/seed/`:
- `seed_grants.py`
- `seed_expenses.py`
- `seed_instructor_hours.py`
- `truncate_all.py`
**See:** Bug #010 in `docs/BUGS_LOG.md`

### Seed Fails - Enum Value Errors
**Symptom:** Seed fails with `ValueError` for StudentStatus or other enums
**Cause:** Seed data uses old enum values that were renamed
**Fix:** Update seed files to use current enum values:
- `StudentStatus.GRADUATED` (not COMPLETED)
- `StudentStatus.WITHDRAWN` (not DROPPED)
**See:** Bug #011 in `docs/BUGS_LOG.md`

### Authentication Fails - passlib Error
**Symptom:** Login fails with cryptic error related to password hashing
**Cause:** passlib library has compatibility issues with bcrypt versions
**Fix:** Code has been updated to use direct bcrypt (no passlib)
- Ensure you have the latest `src/core/security.py`
**See:** Bug #012 in `docs/BUGS_LOG.md`

---

## Auto-Deploy from Main

Railway auto-deploys when you push to `main`. Your workflow:

```bash
# Working on Windows (develop branch)
git checkout develop
# ... make changes ...
git add -A && git commit -m "fix: something"
git push origin develop

# Ready to update demo? Merge to main
git checkout main
git merge develop
git push origin main  # ← Railway auto-deploys here

# Back to work
git checkout develop
```

**Never push directly to `main`** — always merge from `develop`.

---

## Quick Reference

```bash
# Railway CLI commands
railway login          # Authenticate
railway link           # Connect to project
railway run <cmd>      # Run command in project context
railway logs           # View logs
railway open           # Open dashboard

# Useful commands
railway run alembic upgrade head     # Run migrations
railway run pytest -v                # Run tests
railway run python -c "..."          # Python one-liner
```

---

**Railway deployment complete!** ✅

**Next:** `3-RENDER-DEPLOY.md` or `4-S3-STORAGE.md` →
