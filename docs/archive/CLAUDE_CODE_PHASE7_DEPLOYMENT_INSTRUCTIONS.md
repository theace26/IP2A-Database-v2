# Claude Code Instructions: Phase 7 - Deployment

**Document Version:** 1.0
**Created:** January 28, 2026
**Estimated Time:** 2-3 hours
**Priority:** Medium (makes system accessible)
**Target Version:** v0.9.0

---

## Objective

Deploy IP2A to a cloud platform (Railway or Render) with PostgreSQL database, making the system accessible from anywhere.

---

## Platform Comparison

| Feature | Railway | Render |
|---------|---------|--------|
| **Free Tier** | $5 credit/month | 750 hrs/month |
| **PostgreSQL** | Built-in | Built-in |
| **Deploy from Git** | Yes | Yes |
| **Custom Domains** | Yes | Yes |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Pricing** | Usage-based | Fixed tiers |
| **S3/MinIO** | External only | External only |

**Recommendation:** Start with **Railway** for fastest deployment. Migrate to Render or union server later if needed.

---

## Pre-Deployment Checklist

Before deploying, ensure:

```bash
cd ~/Projects/IP2A-Database-v2
git status                    # Clean working directory
pytest -v                     # All tests passing
docker-compose up -d          # Local environment works
```

---

## Option A: Railway Deployment

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub
3. Authorize Railway to access your repositories

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose `theace26/IP2A-Database-v2`
4. Railway will auto-detect Python/FastAPI

### Step 3: Add PostgreSQL

1. In your project, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway provisions a PostgreSQL instance
4. Note the connection string (auto-injected as `DATABASE_URL`)

### Step 4: Configure Environment Variables

In Railway dashboard → **Variables**, add:

```bash
# Database (Railway auto-provides DATABASE_URL, but we need our format)
POSTGRES_USER=${{Postgres.PGUSER}}
POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}
POSTGRES_DB=${{Postgres.PGDATABASE}}
POSTGRES_HOST=${{Postgres.PGHOST}}
POSTGRES_PORT=${{Postgres.PGPORT}}

# Auth
AUTH_JWT_SECRET_KEY=your-production-secret-key-here
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=7

# S3/MinIO (use Backblaze B2 or AWS S3 for production)
S3_ENDPOINT_URL=https://s3.us-west-002.backblazeb2.com
S3_ACCESS_KEY_ID=your-b2-key-id
S3_SECRET_ACCESS_KEY=your-b2-secret
S3_BUCKET_NAME=ip2a-files
S3_REGION=us-west-002

# Email (optional - use SendGrid, Mailgun, or AWS SES)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Step 5: Create Procfile

**File:** `Procfile` (in project root)

```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
release: alembic upgrade head
```

The `release` command runs migrations automatically on each deploy.

### Step 6: Create railway.json (Optional)

**File:** `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "startCommand": "uvicorn src.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

### Step 7: Add Health Check Endpoint

**File:** `src/routers/health.py`

```python
"""Health check endpoint for deployment platforms."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for load balancers."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "0.7.0",
    }
```

Register in `src/main.py`:
```python
from src.routers.health import router as health_router
app.include_router(health_router)
```

### Step 8: Push and Deploy

```bash
git add Procfile railway.json src/routers/health.py
git commit -m "chore: Add Railway deployment configuration"
git push origin main
```

Railway automatically deploys on push to main.

### Step 9: Run Initial Seed (One-time)

In Railway dashboard → **"Shell"** or via CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login

# Run seed command
railway run python -m src.seed.run_seed
```

### Step 10: Verify Deployment

1. Railway provides a URL like `https://ip2a-production.up.railway.app`
2. Visit `/health` to verify
3. Visit `/docs` to see API documentation
4. Test a few endpoints

---

## Option B: Render Deployment

### Step 1: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name:** ip2a-api
   - **Region:** Oregon (or closest)
   - **Branch:** main
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add PostgreSQL

1. Click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** ip2a-db
   - **Region:** Same as web service
3. Note the **Internal Database URL**

### Step 4: Configure Environment Variables

In Render dashboard → **Environment**, add:

```bash
DATABASE_URL=<internal-database-url-from-render>
AUTH_JWT_SECRET_KEY=your-production-secret-key
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=7
S3_ENDPOINT_URL=https://s3.us-west-002.backblazeb2.com
S3_ACCESS_KEY_ID=your-key
S3_SECRET_ACCESS_KEY=your-secret
S3_BUCKET_NAME=ip2a-files
ENVIRONMENT=production
DEBUG=false
```

### Step 5: Create render.yaml (Blueprint)

**File:** `render.yaml`

```yaml
services:
  - type: web
    name: ip2a-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: ip2a-db
          property: connectionString
      - key: AUTH_JWT_SECRET_KEY
        generateValue: true
      - key: ENVIRONMENT
        value: production

databases:
  - name: ip2a-db
    plan: free
```

### Step 6: Deploy

1. Commit render.yaml
2. Push to main
3. Render auto-deploys

---

## Production Configuration

### Update Database Session for Production

**File:** `src/db/session.py`

```python
"""Database session configuration."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Support both DATABASE_URL (Render) and individual vars (Railway)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Build from individual components
    user = os.getenv("POSTGRES_USER", "ip2a")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ip2a_dev")
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}"

# Handle Render's postgres:// vs postgresql:// difference
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Add CORS for Frontend

**File:** `src/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

# After app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ip2a.ibew46.org",  # Production domain
        "http://localhost:3000",     # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Configure Object Storage (Backblaze B2)

Backblaze B2 is S3-compatible and cheaper than AWS:

1. Create account at https://www.backblaze.com/b2
2. Create a bucket: `ip2a-files`
3. Create application key with read/write access
4. Set environment variables:
   - `S3_ENDPOINT_URL=https://s3.us-west-002.backblazeb2.com`
   - `S3_ACCESS_KEY_ID=<keyID>`
   - `S3_SECRET_ACCESS_KEY=<applicationKey>`
   - `S3_BUCKET_NAME=ip2a-files`

---

## Custom Domain Setup

### Railway

1. Go to project → **Settings** → **Domains**
2. Click **"+ Custom Domain"**
3. Add: `api.ip2a.ibew46.org`
4. Add DNS CNAME record pointing to Railway URL

### Render

1. Go to service → **Settings** → **Custom Domains**
2. Add: `api.ip2a.ibew46.org`
3. Add DNS CNAME record pointing to Render URL

---

## Monitoring & Logs

### Railway
- Logs: Project → **Deployments** → **View Logs**
- Metrics: Built-in CPU/Memory graphs

### Render
- Logs: Service → **Logs**
- Metrics: Service → **Metrics**

### Add Sentry (Optional)

```bash
pip install sentry-sdk[fastapi]
```

**File:** `src/main.py`

```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "development"),
    traces_sample_rate=0.1,
)
```

---

## Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Environment variables documented
- [ ] Health check endpoint created
- [ ] Procfile/render.yaml created
- [ ] Database session handles production URLs

### Deployment
- [ ] Platform account created
- [ ] GitHub repository connected
- [ ] PostgreSQL database provisioned
- [ ] Environment variables configured
- [ ] Initial deployment successful
- [ ] Health check returns healthy

### Post-Deployment
- [ ] Run database migrations
- [ ] Run seed data (one-time)
- [ ] Verify API endpoints work
- [ ] Configure custom domain (optional)
- [ ] Set up monitoring/alerts (optional)

---

## Troubleshooting

### "Database connection refused"
- Check DATABASE_URL format
- Verify PostgreSQL is running
- Check firewall/network settings

### "Module not found"
- Ensure requirements.txt is complete
- Check Python version compatibility

### "Port already in use"
- Use `$PORT` environment variable
- Don't hardcode port numbers

### Migrations not running
- Check Procfile release command
- Run manually: `railway run alembic upgrade head`

---

## Cost Estimates

### Railway (Hobby)
- Web service: ~$5/month
- PostgreSQL: ~$5/month
- **Total: ~$10/month**

### Render (Free Tier)
- Web service: Free (spins down after inactivity)
- PostgreSQL: Free (90 days, then $7/month)
- **Total: Free → $7/month**

### Production (Estimated)
- Railway/Render Pro: $20-50/month
- Backblaze B2: $5/month (10GB storage)
- SendGrid: Free (100 emails/day)
- Sentry: Free (5K errors/month)
- **Total: $25-55/month**

---

## Expected Outcome

- ✅ API accessible at public URL
- ✅ PostgreSQL database running
- ✅ Migrations applied automatically
- ✅ Health check endpoint working
- ✅ Ready for frontend development

---

*End of Instructions*
