# Deployment Prep: Master Instructions

**Version:** v0.7.9 → v0.8.0-alpha1 (Deployment Active)
**Current State:** Phase 6 Week 10 Complete, ~330 tests, 11 ADRs
**Estimated Time:** 4-6 hours total
**Goal:** Deploy IP2A-v2 to cloud for leadership demo

---

## Important: Documentation Updates

**Add this instruction to ALL future instruction documents:**

> **Documentation Maintenance (End of Every Session):**
> Update *ANY* and *ALL* relevant documents to capture progress made this session.
> Scan `/docs/*` and make or create any relevant updates/documents to keep a
> historical record as the project progresses. Do not forget about ADRs—update
> as necessary.

---

## Overview

This guide covers deploying IP2A-v2 to both Railway and Render, giving you:
- **Railway**: Quick demo deployment (simpler, faster)
- **Render**: Production-ready deployment (more control)

Your setup:
- **MacOS**: Demo machine (show to leadership)
- **Windows 11**: Development environment (continue building)

Both deployments connect to the same codebase, so changes you push from Windows automatically deploy.

---

## Document Structure

| # | Document | Time | Focus |
|---|----------|------|-------|
| 1 | `1-PRODUCTION-CONFIG.md` | 1-2 hrs | Production settings, Dockerfile, env vars |
| 2 | `2-RAILWAY-DEPLOY.md` | 1-1.5 hrs | Railway setup + PostgreSQL |
| 3 | `3-RENDER-DEPLOY.md` | 1.5-2 hrs | Render setup + managed database |
| 4 | `4-S3-STORAGE.md` | 30-45 min | Backblaze B2 or AWS S3 for documents |
| 5 | `5-VERIFICATION.md` | 30 min | Test deployments, seed data |
| 6 | `6-DEMO-WALKTHROUGH.md` | 30 min | Leadership demo script |

---

## Quick Decision Guide

| Factor | Railway | Render |
|--------|---------|--------|
| Setup time | ~30 min | ~45 min |
| Free tier | $5 credit/month | 750 hrs/month (sleeps after 15 min) |
| PostgreSQL | Add-on ($5/mo hobby) | Managed ($7/mo starter) |
| Auto-deploy | Yes | Yes |
| Custom domain | Yes (free) | Yes (free) |
| Best for | Quick demo | Long-term production |

**Recommendation:** Start with Railway for the demo, then migrate to Render for production if leadership approves.

---

## Branch Strategy

**Set this up FIRST before any deployment:**

```
main     → Production/Demo (stable, auto-deploys to Railway/Render)
develop  → Ongoing development (your Windows dev environment)
```

| Branch | Purpose | Deploys To |
|--------|---------|------------|
| `main` | Stable demo/production | Railway + Render (auto) |
| `develop` | Active development | Nothing (local only) |

**Why separate branches:**
- Demo stays frozen while you keep building
- Railway/Render default to `main` — no config changes needed
- Merge `develop → main` only when intentional
- Protects you from showing half-finished features to leadership

**Setup (do this now):**
```bash
cd ~/Projects/IP2A-Database-v2
git checkout main
git pull origin main

# Create develop branch
git checkout -b develop
git push -u origin develop

# You now work on develop
# main stays frozen at v0.7.9 (demo-ready)
```

**Daily workflow (Windows):**
```bash
git checkout develop
git pull origin develop
# ... work ...
git add -A && git commit -m "feat: description"
git push origin develop
```

**When ready to update demo:**
```bash
git checkout main
git merge develop
git push origin main  # Triggers auto-deploy
git tag -a v0.8.x -m "Demo update"
git push origin v0.8.x
git checkout develop  # Back to work
```

---

## Prerequisites

Before starting:

1. **GitHub repo is public** (or you have a paid plan for private repos)
   - Your repo: `https://github.com/theace26/IP2A-Database-v2`

2. **Branch strategy configured** (see above)

3. **Accounts created:**
   - Railway: https://railway.app (sign in with GitHub)
   - Render: https://render.com (sign in with GitHub)
   - Backblaze B2: https://www.backblaze.com/b2 (for S3 storage, free 10GB)

4. **Local environment working:**
   ```bash
   cd ~/Projects/IP2A-Database-v2
   docker-compose up -d
   pytest -v  # All ~330 tests passing
   ```

---

## Environment Variables Reference

You'll need these for both platforms:

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-super-secret-key-min-32-chars
ENVIRONMENT=production

# S3 Storage (for documents)
S3_ENDPOINT_URL=https://s3.us-west-002.backblazeb2.com
S3_ACCESS_KEY_ID=your-key-id
S3_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=ip2a-documents
S3_REGION=us-west-002

# Optional
ALLOWED_HOSTS=your-app.railway.app,your-app.onrender.com
DEBUG=false
LOG_LEVEL=INFO
```

---

## Execution Order

### Day 1: Prep + Railway (Demo Ready)
1. Run `1-PRODUCTION-CONFIG.md` (create production files)
2. Run `2-RAILWAY-DEPLOY.md` (deploy to Railway)
3. Run `4-S3-STORAGE.md` (set up Backblaze B2)
4. Run `5-VERIFICATION.md` (test Railway deployment)

### Day 2: Render + Demo Prep (Optional, Production)
1. Run `3-RENDER-DEPLOY.md` (deploy to Render)
2. Run `5-VERIFICATION.md` (test Render deployment)
3. Run `6-DEMO-WALKTHROUGH.md` (prepare demo script)

---

## First-Time Setup (After Deployment)

After deploying, the first user to access the system will need to complete setup:

1. **Navigate to the app URL** - System redirects to `/setup` automatically
2. **Default admin account exists** (`admin@ibew46.com`) - seeded during database initialization
3. **Create your own admin account** - Cannot use `admin@ibew46.com` email
4. **Optionally disable default admin** - Checkbox available, recommended for production
5. **Log in with your new credentials**

**Important Notes:**
- The default admin account exists for system recovery purposes
- It cannot be deleted, only disabled
- Its email/password cannot be changed via the setup page
- Can be re-enabled later from Staff Management if needed

---

## Post-Demo: What Changes?

After leadership approval:

1. **Add custom domain** (e.g., `ip2a.ibew46.org`)
2. **Upgrade database tier** if needed
3. **Set up backups** (automated with managed DB)
4. **Add monitoring** (both platforms have built-in)
5. **Configure CI/CD** for test runs before deploy

---

## Rollback Plan

If something breaks:

**Railway:**
```bash
# Railway keeps deployment history
# Click "Deployments" → select previous → "Redeploy"
```

**Render:**
```bash
# Render auto-saves previous deploys
# Dashboard → Deploys → select previous → "Redeploy"
```

---

## Support Resources

- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- Backblaze B2 Docs: https://www.backblaze.com/b2/docs/

---

*Start with `1-PRODUCTION-CONFIG.md` →*
