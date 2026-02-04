#!/bin/bash
# Database backup script for UnionCore
# Run via cron: 0 2 * * * /path/to/backup_database.sh

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/unioncore}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DB_HOST="${DB_HOST:-localhost}"
DB_NAME="${DB_NAME:-unioncore}"
DB_USER="${DB_USER:-postgres}"
S3_BUCKET="${S3_BUCKET:-}"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/unioncore_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# Create backup
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    | gzip > "$BACKUP_FILE"

# Verify backup
if [ ! -s "$BACKUP_FILE" ]; then
    echo "[$(date)] ERROR: Backup file is empty!"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Upload to S3 if configured
if [ -n "$S3_BUCKET" ]; then
    echo "[$(date)] Uploading to S3..."
    aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/backups/$(basename $BACKUP_FILE)"
    echo "[$(date)] S3 upload complete"
fi

# Clean up old backups
echo "[$(date)] Cleaning backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "unioncore_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup complete!"
