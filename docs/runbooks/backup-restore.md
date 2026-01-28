# Runbook: Database Backup and Restore

## Overview
Procedures for backing up and restoring the IP2A PostgreSQL database.

**Estimated time:**
- Backup: 5 minutes
- Restore: 15-30 minutes

## Prerequisites
- SSH access to server
- Docker access
- Backup storage location access

---

## BACKUP PROCEDURE

### Step 1: Connect to Server
```bash
ssh user@ip2a-server
cd ~/Projects/IP2A-Database-v2
```

### Step 2: Create Backup
```bash
docker exec ip2a-db pg_dump -U postgres ip2a_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 3: Verify Backup
```bash
ls -lh backup_*.sql | tail -1
```
File should be > 1MB.

### Step 4: Copy to Safe Location
```bash
cp backup_*.sql /path/to/backup/location/
```

---

## RESTORE PROCEDURE

⚠️ **WARNING: This OVERWRITES the current database!**

### Step 1: Stop Application
```bash
docker-compose stop api
```

### Step 2: Restore Database
```bash
docker exec -i ip2a-db psql -U postgres -c "DROP DATABASE IF EXISTS ip2a_db;"
docker exec -i ip2a-db psql -U postgres -c "CREATE DATABASE ip2a_db;"
docker exec -i ip2a-db psql -U postgres ip2a_db < /path/to/backup_file.sql
```

### Step 3: Restart Application
```bash
docker-compose start api
```

### Step 4: Verify
```bash
curl http://localhost:8000/health
```

---

## Troubleshooting

### Problem: "database is being accessed by other users"
**Solution:** `docker-compose down` then `docker-compose up -d db`, wait 10 seconds, retry.

---

## Contacts
- Primary: [TODO: Add contact]
- Backup: [TODO: Add contact]
