# Runbook: Disaster Recovery

## Overview
Recover IP2A Database from complete system failure.

**Estimated time:** 1-2 hours

## Prerequisites
- Access to backup files
- Access to new/rebuilt server
- Docker installation capability

---

## SCENARIOS

### Scenario A: Application Container Crashed

**Symptoms:** API not responding, database still running

**Recovery:**
```bash
docker-compose restart api
docker-compose logs --tail=50 api
```

### Scenario B: Database Container Crashed

**Symptoms:** API shows database connection errors

**Recovery:**
```bash
docker-compose restart db
# Wait 30 seconds
docker-compose restart api
```

### Scenario C: Server Unreachable

**Symptoms:** Cannot SSH to server

**Recovery:**
1. Contact hosting provider / check hardware
2. If server is lost, proceed to Scenario D

### Scenario D: Complete Data Loss (Rebuild from Backup)

**Recovery:**

1. **Set up new server** with Docker and Docker Compose

2. **Clone repository**
   ```bash
   git clone https://github.com/theace26/IP2A-Database-v2.git
   cd IP2A-Database-v2
   ```

3. **Copy environment file**
   ```bash
   cp .env.compose.example .env.compose
   # Edit with correct credentials
   ```

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Restore database from backup**
   Follow [backup-restore.md](backup-restore.md) restore procedure.

6. **Verify system**
   ```bash
   curl http://localhost:8000/health
   ```

---

## BACKUP LOCATIONS

| Backup Type | Location | Retention |
|-------------|----------|-----------|
| Database dumps | [TODO: Add path] | 30 days |
| File attachments | [TODO: Add path] | Indefinite |

---

## Contacts

### Primary
- Name: [TODO]
- Phone: [TODO]
- Email: [TODO]

### Backup
- Name: [TODO]
- Phone: [TODO]

### Hosting Provider
- Support: [TODO]
- Account: [TODO]
