# 3. Render Deployment

**Duration:** 1.5-2 hours
**Goal:** Deploy IP2A-v2 to Render with managed PostgreSQL

Render provides more control and better production features. Free tier sleeps after 15 min of inactivity (wakes on request, ~30 sec delay).

---

## Prerequisites

- [x] Render account: https://render.com (sign in with GitHub)
- [x] Production config committed and **merged to `main`** (from `1-PRODUCTION-CONFIG.md`)
- [x] GitHub repo accessible
- [x] Branch strategy set up (`main` for demo, `develop` for work)

---

## Important: Branch Configuration

Render deploys from `main` by default. This is what we want:
- Your demo stays stable on `main`
- Development continues on `develop`
- Updates deploy only when you merge `develop → main`

---

## Option A: Blueprint Deploy (Recommended)

The `render.yaml` file configures everything automatically.

### Step 1: Create New Blueprint

1. Go to https://dashboard.render.com
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repo: `IP2A-Database-v2`
4. Render detects `render.yaml` automatically
5. Review the resources:
   - Web Service: `ip2a-api`
   - Database: `ip2a-db`
6. Click **"Apply"**

### Step 2: Wait for Provisioning

- Database: ~2-3 minutes
- Web Service: ~5-7 minutes (Docker build)

### Step 3: Add S3 Variables

After deploy, add S3 credentials:

1. Go to **ip2a-api** service
2. Click **"Environment"**
3. Add:
   | Key | Value |
   |-----|-------|
   | `S3_ENDPOINT_URL` | `https://s3.us-east-005.backblazeb2.com` |
   | `S3_ACCESS_KEY_ID` | 005523a5e5813450000000002 |
   | `S3_SECRET_ACCESS_KEY` | K005/UPiJ0byKOZUgGWxqAG+nRzF8H8 |
4. Click **"Save Changes"** (triggers redeploy)

---

## Option B: Manual Setup

If you prefer manual control or Blueprint doesn't work:

### Step 1: Create PostgreSQL Database

1. Go to https://dashboard.render.com
2. Click **"New"** → **"PostgreSQL"**
3. Configure:
   - Name: `ip2a-db`
   - Database: `ip2a`
   - User: `ip2a_user`
   - Region: Oregon (us-west-2) or nearest
   - Plan: **Starter** ($7/mo) or **Free** (expires in 90 days)
4. Click **"Create Database"**
5. **Copy the Internal Database URL** (starts with `postgresql://`)

### Step 2: Create Web Service

1. Click **"New"** → **"Web Service"**
2. Connect your GitHub repo
3. Configure:
   - Name: `ip2a-api`
   - Region: Same as database
   - Branch: `main`
   - Runtime: **Docker**
   - Dockerfile Path: `./Dockerfile`
4. Instance Type: **Free** or **Starter** ($7/mo)
5. Click **"Create Web Service"** (don't deploy yet)

### Step 3: Add Environment Variables

In the web service settings, add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | (paste Internal Database URL from Step 1) |
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | (generate: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `S3_ENDPOINT_URL` | `https://s3.us-west-002.backblazeb2.com` |
| `S3_ACCESS_KEY_ID` | (from Backblaze) |
| `S3_SECRET_ACCESS_KEY` | (from Backblaze) |
| `S3_BUCKET_NAME` | `ip2a-documents` |
| `S3_REGION` | `us-west-002` |

### Step 4: Configure Health Check

In service settings:
- Health Check Path: `/health`
- Health Check Timeout: `30` seconds

### Step 5: Deploy

Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## Step 4: Verify Deployment

Once deployed (green checkmark):

1. **Get your URL:**
   - Find it in service dashboard: `https://ip2a-api.onrender.com` (or similar)

2. **Health Check:**
   ```bash
   curl https://ip2a-api.onrender.com/health
   # Should return: {"status":"healthy","version":"0.7.9"}
   ```

3. **API Docs:**
   - Visit: `https://ip2a-api.onrender.com/docs`

4. **Login Page:**
   - Visit: `https://ip2a-api.onrender.com/login`

---

## Step 5: Run Database Migrations

Render runs migrations automatically if configured in Dockerfile. If not:

### Option 1: Shell Access

1. Go to your web service
2. Click **"Shell"** tab
3. Run:
   ```bash
   alembic upgrade head
   ```

### Option 2: Deploy Hook

Add to `Dockerfile` before `CMD`:
```dockerfile
# Run migrations on startup
RUN echo '#!/bin/bash\nalembic upgrade head\nexec "$@"' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
```

### Option 3: Pre-Deploy Command

In Render service settings:
- Build Command: `pip install -r requirements.txt && alembic upgrade head`

---

## Step 6: Seed Demo Data

Using Render Shell:

1. Go to web service → **"Shell"**
2. Run:
   ```python
   python -c "
   from src.db.database import SessionLocal
   from src.seed.all_seeds import seed_all
   
   db = SessionLocal()
   seed_all(db)
   db.close()
   print('Seeding complete!')
   "
   ```

---

## Step 7: Create Admin User

In Render Shell:

```python
python -c "
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

## Render Dashboard Overview

Your Render dashboard should show:

```
┌─────────────────────────────────────────┐
│  Services                               │
├─────────────────────────────────────────┤
│  🟢 ip2a-api          Web Service       │
│     └─ https://ip2a-api.onrender.com    │
│                                         │
│  🟢 ip2a-db           PostgreSQL        │
│     └─ Connected (Starter)              │
└─────────────────────────────────────────┘
```

---

## Free Tier Considerations

### Sleep Behavior
- Free tier sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- For demo: visit the URL 5 minutes before presenting

### Keep Alive (Optional)
Use an external service to ping your app:
- https://uptimerobot.com (free, pings every 5 min)
- https://cron-job.org (free, scheduled requests)

Configure to ping `/health` every 14 minutes.

---

## Cost Estimate (Render)

| Resource | Free Tier | Paid Tier |
|----------|-----------|-----------|
| Web Service | Free (sleeps) | $7/mo (Starter) |
| PostgreSQL | Free (90 day limit) | $7/mo (Starter) |
| **Total** | Free for demo | ~$14/mo |

---

## Auto-Deploy Setup

Render auto-deploys on push by default. To configure:

1. Go to service **"Settings"**
2. Under **"Build & Deploy"**:
   - Auto-Deploy: **Yes** (default)
   - Branch: `main` ← **Important: keep this as main**
3. Every push to `main` triggers a new deploy

**Your workflow:**
```bash
# Working on Windows (develop branch)
git checkout develop
# ... make changes ...
git add -A && git commit -m "fix: something"
git push origin develop

# Ready to update demo? Merge to main
git checkout main
git merge develop
git push origin main  # ← Render auto-deploys here

# Back to work
git checkout develop
```

**Never push directly to `main`** — always merge from `develop`.

---

## Custom Domain (Optional)

1. Go to service **"Settings"**
2. Click **"Add Custom Domain"**
3. Add: `ip2a.yourdomain.com`
4. Add CNAME record in your DNS:
   - Name: `ip2a`
   - Value: `ip2a-api.onrender.com`
5. Render provisions SSL automatically

---

## Troubleshooting

### Build Fails
- Check build logs in **"Events"** tab
- Ensure Dockerfile builds locally first
- Check for missing dependencies

### Database Connection Timeout
- Use **Internal Database URL** (not External)
- Check database is in same region as web service
- Verify DATABASE_URL format

### Health Check Fails
- Ensure `/health` endpoint exists and returns 200
- Check app binds to `0.0.0.0:$PORT`
- Increase health check timeout to 60 seconds

### Slow Cold Starts
- Free tier limitation
- Upgrade to Starter ($7/mo) for always-on
- Use keep-alive service

---

## Comparison: Railway vs Render

| Feature | Railway | Render |
|---------|---------|--------|
| Setup Speed | Faster | Slower |
| Free Tier | $5 credit | Sleeps after 15 min |
| Database | Same-region auto | Manual connection |
| Shell Access | CLI only | Web shell |
| Logs | Real-time | Real-time |
| Custom Domain | Free | Free |
| Best For | Quick demo | Production |

---

**Render deployment complete!** ✅

**Next:** `4-S3-STORAGE.md` →
