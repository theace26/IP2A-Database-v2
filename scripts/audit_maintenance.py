#!/usr/bin/env python3
"""
Automated audit log maintenance job.

Handles:
- Archiving old logs to S3
- Deleting expired logs
- Vacuum and cleanup

Run via cron:
0 2 * * * cd /app && python scripts/audit_maintenance.py

Configuration via environment variables:
- ARCHIVE_DAYS: Days before archiving (default: 1095 = 3 years)
- DELETE_DAYS: Days before deletion (default: 2555 = 7 years)
- S3_BUCKET: S3 bucket for archives (default: ip2a-audit-archive)
- S3_PREFIX: S3 key prefix (default: audit_logs/)
"""

import sys
import os

sys.path.insert(0, "/app")

from datetime import datetime, timedelta
from sqlalchemy import text
from src.db.session import get_db
import gzip
import json

# Optional: AWS S3 (install with: pip install boto3)
try:
    import boto3

    HAS_S3 = True
except ImportError:
    HAS_S3 = False
    print("Warning: boto3 not installed. S3 archiving disabled.")

# Configuration
ARCHIVE_DAYS = int(os.getenv("ARCHIVE_DAYS", 1095))  # 3 years
DELETE_DAYS = int(os.getenv("DELETE_DAYS", 2555))  # 7 years
S3_BUCKET = os.getenv("S3_BUCKET", "ip2a-audit-archive")
S3_PREFIX = os.getenv("S3_PREFIX", "audit_logs/")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"


def archive_old_logs(db, days_old=ARCHIVE_DAYS):
    """
    Archive logs older than N days to S3.

    Args:
        db: Database session
        days_old: Age threshold in days

    Returns:
        Number of logs archived
    """
    cutoff = datetime.now() - timedelta(days=days_old)

    print(f"\n{'='*70}")
    print(f"ARCHIVING LOGS OLDER THAN {days_old} DAYS (before {cutoff.date()})")
    print(f"{'='*70}")

    if not HAS_S3:
        print("❌ Skipping: boto3 not installed")
        return 0

    # Count logs to archive
    result = db.execute(
        text("""
        SELECT COUNT(*) FROM audit_logs
        WHERE changed_at < :cutoff
    """),
        {"cutoff": cutoff},
    )

    count = result.scalar()

    if count == 0:
        print("✅ No logs to archive")
        return 0

    print(f"Found {count:,} logs to archive")

    if DRY_RUN:
        print("🔍 DRY RUN: Would archive but not executing")
        return 0

    # Query logs in batches
    batch_size = 100000
    offset = 0
    total_archived = 0

    while True:
        result = db.execute(
            text("""
            SELECT
                id, table_name, record_id, action,
                old_values, new_values, changed_fields,
                changed_by, changed_at, ip_address, user_agent, notes
            FROM audit_logs
            WHERE changed_at < :cutoff
            ORDER BY changed_at
            LIMIT :limit OFFSET :offset
        """),
            {"cutoff": cutoff, "limit": batch_size, "offset": offset},
        )

        logs = result.fetchall()

        if not logs:
            break

        # Convert to dicts
        data = []
        for log in logs:
            data.append(
                {
                    "id": log[0],
                    "table_name": log[1],
                    "record_id": log[2],
                    "action": log[3],
                    "old_values": log[4],
                    "new_values": log[5],
                    "changed_fields": log[6],
                    "changed_by": log[7],
                    "changed_at": log[8].isoformat() if log[8] else None,
                    "ip_address": log[9],
                    "user_agent": log[10],
                    "notes": log[11],
                }
            )

        # Compress
        json_data = json.dumps(data, default=str, indent=2)
        compressed = gzip.compress(json_data.encode())

        # Upload to S3
        s3 = boto3.client("s3")
        filename = (
            f"audit_logs_{cutoff.strftime('%Y%m')}_batch_{offset//batch_size}.json.gz"
        )
        key = f"{S3_PREFIX}{filename}"

        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=compressed,
                StorageClass="GLACIER_IR",
                Metadata={
                    "record_count": str(len(logs)),
                    "cutoff_date": cutoff.isoformat(),
                    "archived_at": datetime.now().isoformat(),
                },
            )

            print(
                f"   ✅ Uploaded {filename} ({len(logs):,} logs, {len(compressed):,} bytes)"
            )

            # Delete archived logs from PostgreSQL
            ids = [log[0] for log in logs]
            db.execute(
                text("""
                DELETE FROM audit_logs
                WHERE id = ANY(:ids)
            """),
                {"ids": ids},
            )
            db.commit()

            total_archived += len(logs)

        except Exception as e:
            print(f"   ❌ Failed to archive batch: {e}")
            db.rollback()
            break

        offset += batch_size

    print(f"\n✅ Archived {total_archived:,} logs to S3://{S3_BUCKET}/{S3_PREFIX}")
    return total_archived


def delete_expired_logs(db, days_old=DELETE_DAYS):
    """
    Delete logs older than N days (past retention period).

    Args:
        db: Database session
        days_old: Age threshold in days

    Returns:
        Number of logs deleted
    """
    cutoff = datetime.now() - timedelta(days=days_old)

    print(f"\n{'='*70}")
    print(f"DELETING EXPIRED LOGS OLDER THAN {days_old} DAYS (before {cutoff.date()})")
    print(f"{'='*70}")

    # Count logs to delete
    result = db.execute(
        text("""
        SELECT COUNT(*) FROM audit_logs
        WHERE changed_at < :cutoff
    """),
        {"cutoff": cutoff},
    )

    count = result.scalar()

    if count == 0:
        print("✅ No expired logs to delete")
        return 0

    print(f"Found {count:,} expired logs")

    if DRY_RUN:
        print("🔍 DRY RUN: Would delete but not executing")
        return 0

    # Delete in batches to avoid long transactions
    batch_size = 10000
    total_deleted = 0

    while True:
        result = db.execute(
            text("""
            DELETE FROM audit_logs
            WHERE id IN (
                SELECT id FROM audit_logs
                WHERE changed_at < :cutoff
                LIMIT :limit
            )
            RETURNING id
        """),
            {"cutoff": cutoff, "limit": batch_size},
        )

        deleted = result.rowcount
        db.commit()

        if deleted == 0:
            break

        total_deleted += deleted
        print(f"   ✅ Deleted {deleted:,} logs (total: {total_deleted:,})")

        if deleted < batch_size:
            break

    print(f"\n✅ Deleted {total_deleted:,} expired logs (older than {days_old} days)")
    return total_deleted


def vacuum_and_analyze(db):
    """Reclaim space and update statistics."""
    print(f"\n{'='*70}")
    print("VACUUMING AND ANALYZING TABLE")
    print(f"{'='*70}")

    if DRY_RUN:
        print("🔍 DRY RUN: Would vacuum but not executing")
        return

    try:
        # Get table size before
        result = db.execute(
            text("""
            SELECT pg_size_pretty(pg_total_relation_size('audit_logs')) as size
        """)
        )
        size_before = result.scalar()

        print(f"Table size before: {size_before}")

        # Vacuum and analyze
        db.execute(text("VACUUM ANALYZE audit_logs"))
        db.commit()

        # Get table size after
        result = db.execute(
            text("""
            SELECT pg_size_pretty(pg_total_relation_size('audit_logs')) as size
        """)
        )
        size_after = result.scalar()

        print(f"Table size after:  {size_after}")
        print("✅ Vacuum and analyze complete")

    except Exception as e:
        print(f"❌ Vacuum failed: {e}")


def get_table_stats(db):
    """Get current table statistics."""
    print(f"\n{'='*70}")
    print("CURRENT TABLE STATISTICS")
    print(f"{'='*70}")

    # Total count
    result = db.execute(text("SELECT COUNT(*) FROM audit_logs"))
    total = result.scalar()

    # Table size
    result = db.execute(
        text("""
        SELECT pg_size_pretty(pg_total_relation_size('audit_logs')) as size,
               pg_total_relation_size('audit_logs') as size_bytes
    """)
    )
    size_pretty, size_bytes = result.fetchone()

    # By action
    result = db.execute(
        text("""
        SELECT action, COUNT(*) as count
        FROM audit_logs
        GROUP BY action
        ORDER BY count DESC
    """)
    )
    by_action = result.fetchall()

    # Age distribution
    result = db.execute(
        text("""
        SELECT
            COUNT(*) FILTER (WHERE changed_at > NOW() - INTERVAL '30 days') as last_30_days,
            COUNT(*) FILTER (WHERE changed_at > NOW() - INTERVAL '90 days') as last_90_days,
            COUNT(*) FILTER (WHERE changed_at > NOW() - INTERVAL '1 year') as last_year,
            COUNT(*) as total
        FROM audit_logs
    """)
    )
    age_dist = result.fetchone()

    print(f"Total logs:     {total:>15,}")
    print(f"Table size:     {size_pretty:>15s} ({size_bytes:,} bytes)")
    print("\nBy action:")
    for action, count in by_action:
        print(f"  {action:12s}: {count:>10,} ({count/total*100:>5.1f}%)")

    print("\nAge distribution:")
    print(f"  Last 30 days:   {age_dist[0]:>10,} ({age_dist[0]/total*100:>5.1f}%)")
    print(f"  Last 90 days:   {age_dist[1]:>10,} ({age_dist[1]/total*100:>5.1f}%)")
    print(f"  Last year:      {age_dist[2]:>10,} ({age_dist[2]/total*100:>5.1f}%)")
    print(
        f"  Older than 1yr: {total - age_dist[2]:>10,} ({(total-age_dist[2])/total*100:>5.1f}%)"
    )


def main():
    """Main maintenance routine."""
    db = next(get_db())

    print(f"\n{'='*70}")
    print("AUDIT LOG MAINTENANCE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    print(f"Archive threshold: {ARCHIVE_DAYS} days")
    print(f"Delete threshold:  {DELETE_DAYS} days")
    print(f"S3 Bucket:         {S3_BUCKET}")
    print(f"Dry run:           {DRY_RUN}")

    # Get current stats
    get_table_stats(db)

    # Archive old logs (3+ years)
    archived = archive_old_logs(db, days_old=ARCHIVE_DAYS)

    # Delete expired logs (7+ years)
    deleted = delete_expired_logs(db, days_old=DELETE_DAYS)

    # Vacuum and analyze
    if archived > 0 or deleted > 0:
        vacuum_and_analyze(db)

    # Final stats
    get_table_stats(db)

    print(f"\n{'='*70}")
    print("MAINTENANCE SUMMARY")
    print(f"{'='*70}")
    print(f"Logs archived: {archived:>10,}")
    print(f"Logs deleted:  {deleted:>10,}")
    print(f"Completed:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
