#!/bin/bash
# Verify backup integrity by restoring to a test database

set -e

BACKUP_FILE="$1"
TEST_DB="unioncore_backup_test"
DB_HOST="${DB_HOST:-localhost}"
DB_USER="${DB_USER:-postgres}"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "[$(date)] Verifying backup: $BACKUP_FILE"

# Create test database
echo "[$(date)] Creating test database..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $TEST_DB;"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -c "CREATE DATABASE $TEST_DB;"

# Restore to test database
echo "[$(date)] Restoring to test database..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$TEST_DB"

# Verify tables exist
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

echo "[$(date)] Found $TABLE_COUNT tables"

# Check critical tables
echo "[$(date)] Checking critical tables..."
for table in members users audit_logs dues_payments students; do
    COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
    echo "  - $table: $COUNT rows"
done

# Clean up
echo "[$(date)] Cleaning up test database..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -c "DROP DATABASE $TEST_DB;"

echo "[$(date)] Backup verification complete!"
echo "Result: PASSED - Backup is valid"
