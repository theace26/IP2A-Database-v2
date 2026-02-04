#!/bin/bash
# Archive audit logs older than 1 year to S3 Glacier
# Note: Does NOT delete archived records - that must be done manually after verification

set -e

ARCHIVE_THRESHOLD_DAYS="${ARCHIVE_THRESHOLD_DAYS:-365}"
DB_HOST="${DB_HOST:-localhost}"
DB_NAME="${DB_NAME:-unioncore}"
DB_USER="${DB_USER:-postgres}"
S3_BUCKET="${S3_BUCKET:-}"
ARCHIVE_PREFIX="audit-archive"

echo "[$(date)] Starting audit log archival..."
echo "[$(date)] Archiving logs older than $ARCHIVE_THRESHOLD_DAYS days"

# Export old audit logs to CSV
ARCHIVE_FILE="/tmp/audit_logs_archive_$(date +%Y%m%d).csv"

PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\COPY (
    SELECT * FROM audit_logs
    WHERE created_at < NOW() - INTERVAL '$ARCHIVE_THRESHOLD_DAYS days'
) TO '$ARCHIVE_FILE' WITH CSV HEADER;"

if [ -s "$ARCHIVE_FILE" ]; then
    ROW_COUNT=$(wc -l < "$ARCHIVE_FILE")
    echo "[$(date)] Exported $((ROW_COUNT - 1)) records to $ARCHIVE_FILE"

    # Compress
    gzip "$ARCHIVE_FILE"

    # Upload to S3 Glacier if configured
    if [ -n "$S3_BUCKET" ]; then
        echo "[$(date)] Uploading to S3 Glacier..."
        aws s3 cp "${ARCHIVE_FILE}.gz" \
            "s3://$S3_BUCKET/$ARCHIVE_PREFIX/$(basename ${ARCHIVE_FILE}.gz)" \
            --storage-class GLACIER
        echo "[$(date)] Uploaded to S3 Glacier"
    else
        echo "[$(date)] S3 not configured - archive saved locally at ${ARCHIVE_FILE}.gz"
    fi

    # Note: Deletion is commented out for safety
    # Only uncomment after verifying backup and understanding NLRA retention requirements
    # PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
    #     DELETE FROM audit_logs
    #     WHERE created_at < NOW() - INTERVAL '$ARCHIVE_THRESHOLD_DAYS days';"

    rm -f "${ARCHIVE_FILE}.gz"
    echo "[$(date)] NOTE: Archived records were NOT deleted from database."
    echo "[$(date)] Review NLRA 7-year retention requirements before deleting."
else
    echo "[$(date)] No records to archive"
fi

echo "[$(date)] Audit archival complete!"
