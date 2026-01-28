"""Long-term database and file system resilience checker."""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta
import os
import json

from src.models import FileAttachment, Member, MemberEmployment


class ResilienceIssue:
    """Represents a long-term resilience issue."""

    def __init__(
        self,
        category: str,
        severity: str,  # 'critical', 'warning', 'info'
        description: str,
        details: Optional[dict] = None,
        recommended_action: Optional[str] = None,
    ):
        self.category = category
        self.severity = severity
        self.description = description
        self.details = details or {}
        self.recommended_action = recommended_action
        self.timestamp = datetime.now()


class ResilienceChecker:
    """
    Long-term database and file system resilience checker.

    Checks that go beyond basic integrity to ensure long-term health:
    - File corruption detection (checksums)
    - Database growth trends
    - Storage capacity monitoring
    - Data staleness detection
    - Backup verification
    - Performance degradation
    """

    def __init__(self, db: Session):
        self.db = db
        self.issues: List[ResilienceIssue] = []
        self.metrics_dir = "/app/logs/resilience_metrics"
        self._ensure_metrics_dir()

    def _ensure_metrics_dir(self):
        """Ensure metrics directory exists."""
        os.makedirs(self.metrics_dir, exist_ok=True)

    def run_all_checks(self) -> List[ResilienceIssue]:
        """Run all resilience checks."""
        print("\n" + "=" * 60)
        print("🛡️  RESILIENCE CHECK - Long-term Database Health")
        print("=" * 60)

        # File system resilience
        print("\n📁 Category 1: File System Resilience")
        self.check_file_corruption()
        self.check_storage_capacity()
        self.check_orphaned_files()

        # Database resilience
        print("\n💾 Category 2: Database Resilience")
        self.check_database_growth()
        self.check_data_staleness()
        self.check_record_distribution()

        # Performance resilience
        print("\n⚡ Category 3: Performance Resilience")
        self.check_query_performance()
        self.check_index_health()

        # Backup resilience
        print("\n💼 Category 4: Backup & Recovery")
        self.check_backup_status()

        return self.issues

    # === FILE SYSTEM RESILIENCE ===

    def check_file_corruption(self):
        """
        Check for file corruption using checksums.

        For production: Store checksums when files are uploaded, verify periodically.
        For stress test: Sample check of file readability.
        """
        print("   Checking file corruption...")

        try:
            attachments = self.db.query(FileAttachment).limit(1000).all()

            if not attachments:
                print("      ℹ️  No file attachments to check")
                return

            corrupted_count = 0
            checked_count = 0
            missing_count = 0

            for attachment in attachments:
                full_path = os.path.join("/app", attachment.file_path)

                # Skip URLs and S3 paths
                if attachment.file_path.startswith(("http", "s3://")):
                    continue

                # Check if file exists
                if not os.path.exists(full_path):
                    missing_count += 1
                    continue

                # Basic corruption check: try to read file
                try:
                    with open(full_path, "rb") as f:
                        # Read first and last 1KB to detect truncation
                        f.read(1024)
                        f.seek(-min(1024, os.path.getsize(full_path)), 2)
                        f.read()
                    checked_count += 1
                except Exception:
                    corrupted_count += 1

            if corrupted_count > 0:
                self.issues.append(
                    ResilienceIssue(
                        category="file_corruption",
                        severity="critical",
                        description=f"Found {corrupted_count} potentially corrupted files",
                        details={
                            "corrupted": corrupted_count,
                            "checked": checked_count,
                            "missing": missing_count,
                        },
                        recommended_action="Restore corrupted files from backup or request re-upload",
                    )
                )

            print(
                f"      ✓ Checked {checked_count} files, {corrupted_count} corrupted, {missing_count} missing"
            )

        except Exception as e:
            print(f"      ⚠️  File corruption check skipped: {e}")

    def check_storage_capacity(self):
        """Check storage capacity and growth trends."""
        print("   Checking storage capacity...")

        try:
            # Get disk usage for uploads directory
            uploads_path = "/app/uploads"

            if not os.path.exists(uploads_path):
                print("      ℹ️  Uploads directory not found")
                return

            # Calculate total size
            total_size = 0
            file_count = 0

            for dirpath, dirnames, filenames in os.walk(uploads_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                        file_count += 1
                    except:
                        pass

            total_gb = total_size / (1024**3)

            # Check available disk space
            statvfs = os.statvfs(uploads_path)
            available_gb = (statvfs.f_bavail * statvfs.f_frsize) / (1024**3)
            total_disk_gb = (statvfs.f_blocks * statvfs.f_frsize) / (1024**3)
            used_percent = (1 - (available_gb / total_disk_gb)) * 100

            # Warning if >80% full
            if used_percent > 80:
                self.issues.append(
                    ResilienceIssue(
                        category="storage_capacity",
                        severity="warning" if used_percent < 90 else "critical",
                        description=f"Storage is {used_percent:.1f}% full",
                        details={
                            "total_disk_gb": f"{total_disk_gb:.2f}",
                            "available_gb": f"{available_gb:.2f}",
                            "used_percent": f"{used_percent:.1f}",
                            "uploads_size_gb": f"{total_gb:.2f}",
                            "file_count": file_count,
                        },
                        recommended_action="Free up disk space, archive old files, or expand storage",
                    )
                )

            print(
                f"      ✓ Storage: {total_gb:.2f} GB in {file_count:,} files ({used_percent:.1f}% disk used)"
            )

        except Exception as e:
            print(f"      ⚠️  Storage check skipped: {e}")

    def check_orphaned_files(self):
        """Check for files in uploads directory not referenced in database."""
        print("   Checking for orphaned files...")

        try:
            uploads_path = "/app/uploads"

            if not os.path.exists(uploads_path):
                print("      ℹ️  Uploads directory not found")
                return

            # Get all file paths from database
            db_files = set()
            for attachment in self.db.query(FileAttachment).all():
                db_files.add(attachment.file_path.replace("/app/", ""))

            # Get all files in uploads directory
            disk_files = set()
            for dirpath, dirnames, filenames in os.walk(uploads_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(filepath, "/app")
                    disk_files.add(rel_path)

            # Find orphaned files (on disk but not in DB)
            orphaned = disk_files - db_files

            if len(orphaned) > 100:
                total_orphaned_size = 0
                for file_path in orphaned:
                    try:
                        total_orphaned_size += os.path.getsize(
                            os.path.join("/app", file_path)
                        )
                    except:
                        pass

                self.issues.append(
                    ResilienceIssue(
                        category="orphaned_files",
                        severity="info",
                        description=f"Found {len(orphaned)} orphaned files in uploads directory",
                        details={
                            "orphaned_count": len(orphaned),
                            "orphaned_size_gb": f"{total_orphaned_size / (1024**3):.2f}",
                        },
                        recommended_action="Review and delete orphaned files to free up storage",
                    )
                )

            print(f"      ✓ Found {len(orphaned)} orphaned files")

        except Exception as e:
            print(f"      ⚠️  Orphaned files check skipped: {e}")

    # === DATABASE RESILIENCE ===

    def check_database_growth(self):
        """Monitor database growth trends."""
        print("   Checking database growth...")

        try:
            # Get table sizes
            tables = [
                "members",
                "member_employments",
                "organizations",
                "organization_contacts",
                "students",
                "file_attachments",
            ]

            growth_data = {}
            for table in tables:
                try:
                    result = self.db.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    ).fetchone()
                    growth_data[table] = result[0]
                except:
                    pass

            # Save growth metrics for trending
            metrics_file = os.path.join(
                self.metrics_dir, f"{datetime.now().strftime('%Y-%m-%d')}_growth.json"
            )

            with open(metrics_file, "w") as f:
                json.dump(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "table_counts": growth_data,
                    },
                    f,
                )

            # Check for unusual growth (basic heuristic)
            total_records = sum(growth_data.values())
            if total_records > 1_000_000:
                self.issues.append(
                    ResilienceIssue(
                        category="database_growth",
                        severity="info",
                        description=f"Database has grown to {total_records:,} total records",
                        details=growth_data,
                        recommended_action="Consider archiving old data or implementing data retention policies",
                    )
                )

            print(f"      ✓ Total records: {total_records:,}")

        except Exception as e:
            print(f"      ⚠️  Growth check skipped: {e}")

    def check_data_staleness(self):
        """Check for stale data (records not updated recently)."""
        print("   Checking data staleness...")

        try:
            # Find members not updated in >1 year
            one_year_ago = datetime.now() - timedelta(days=365)
            stale_members = (
                self.db.query(Member).filter(Member.updated_at < one_year_ago).count()
            )

            # Find employments with very old end dates (>10 years)
            ten_years_ago = datetime.now().date() - timedelta(days=3650)
            old_employments = (
                self.db.query(MemberEmployment)
                .filter(MemberEmployment.end_date < ten_years_ago)
                .count()
            )

            if stale_members > 1000:
                self.issues.append(
                    ResilienceIssue(
                        category="data_staleness",
                        severity="info",
                        description=f"{stale_members:,} member records not updated in >1 year",
                        details={
                            "stale_members": stale_members,
                            "old_employments": old_employments,
                        },
                        recommended_action="Consider archiving or reviewing inactive member records",
                    )
                )

            print(
                f"      ✓ Stale members: {stale_members:,}, Old employments: {old_employments:,}"
            )

        except Exception as e:
            print(f"      ⚠️  Staleness check skipped: {e}")

    def check_record_distribution(self):
        """Check for skewed data distribution."""
        print("   Checking record distribution...")

        try:
            # Check for members with unusual employment counts
            result = self.db.execute(
                text("""
                SELECT
                    MIN(job_count) as min_jobs,
                    MAX(job_count) as max_jobs,
                    AVG(job_count) as avg_jobs
                FROM (
                    SELECT member_id, COUNT(*) as job_count
                    FROM member_employments
                    GROUP BY member_id
                ) as counts
            """)
            ).fetchone()

            if result:
                min_jobs, max_jobs, avg_jobs = result

                # Check for extreme outliers
                if max_jobs and max_jobs > 200:
                    self.issues.append(
                        ResilienceIssue(
                            category="data_distribution",
                            severity="info",
                            description=f"Some members have unusually high employment counts (max: {max_jobs})",
                            details={
                                "min_jobs": min_jobs,
                                "max_jobs": max_jobs,
                                "avg_jobs": f"{avg_jobs:.1f}" if avg_jobs else None,
                            },
                            recommended_action="Review members with >200 employments for data quality",
                        )
                    )

                print(
                    f"      ✓ Employment distribution: min={min_jobs}, max={max_jobs}, avg={avg_jobs:.1f}"
                )

        except Exception as e:
            print(f"      ⚠️  Distribution check skipped: {e}")

    # === PERFORMANCE RESILIENCE ===

    def check_query_performance(self):
        """Basic query performance checks."""
        print("   Checking query performance...")

        try:
            # Sample queries to test
            queries = [
                ("members", "SELECT COUNT(*) FROM members"),
                ("employments", "SELECT COUNT(*) FROM member_employments"),
                (
                    "join query",
                    "SELECT COUNT(*) FROM members m JOIN member_employments me ON m.id = me.member_id",
                ),
            ]

            slow_queries = []

            for name, query in queries:
                start = datetime.now()
                self.db.execute(text(query))
                duration = (datetime.now() - start).total_seconds()

                if duration > 5:  # >5 seconds is slow
                    slow_queries.append((name, duration))

            if slow_queries:
                self.issues.append(
                    ResilienceIssue(
                        category="query_performance",
                        severity="warning",
                        description=f"{len(slow_queries)} queries are running slow",
                        details={
                            "slow_queries": [
                                {"query": name, "seconds": f"{dur:.2f}"}
                                for name, dur in slow_queries
                            ]
                        },
                        recommended_action="Review slow queries, check indexes, consider query optimization",
                    )
                )

            print(f"      ✓ Tested {len(queries)} queries, {len(slow_queries)} slow")

        except Exception as e:
            print(f"      ⚠️  Performance check skipped: {e}")

    def check_index_health(self):
        """Check database index health."""
        print("   Checking index health...")

        try:
            # For PostgreSQL, check index usage
            result = self.db.execute(
                text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                LIMIT 10
            """)
            ).fetchall()

            unused_indexes = len(result)

            if unused_indexes > 0:
                self.issues.append(
                    ResilienceIssue(
                        category="index_health",
                        severity="info",
                        description=f"Found {unused_indexes} unused indexes",
                        recommended_action="Review unused indexes, consider removing if not needed",
                    )
                )

            print(f"      ✓ Found {unused_indexes} unused indexes")

        except Exception as e:
            # Not all databases support pg_stat_user_indexes
            print(f"      ⚠️  Index health check skipped: {e}")

    # === BACKUP RESILIENCE ===

    def check_backup_status(self):
        """Check backup status and recency."""
        print("   Checking backup status...")

        # This is a placeholder - in production, integrate with backup system
        backup_dir = "/app/backups"

        if not os.path.exists(backup_dir):
            self.issues.append(
                ResilienceIssue(
                    category="backup_status",
                    severity="critical",
                    description="No backup directory found",
                    recommended_action="Configure automated database backups immediately",
                )
            )
            print("      ⚠️  No backup directory found")
            return

        # Find most recent backup
        try:
            backups = []
            for filename in os.listdir(backup_dir):
                if filename.endswith((".sql", ".dump", ".backup")):
                    filepath = os.path.join(backup_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    backups.append((filename, datetime.fromtimestamp(mtime)))

            if not backups:
                self.issues.append(
                    ResilienceIssue(
                        category="backup_status",
                        severity="critical",
                        description="No database backups found",
                        recommended_action="Create database backup immediately",
                    )
                )
                print("      ⚠️  No backups found")
                return

            # Check most recent backup age
            most_recent = max(backups, key=lambda x: x[1])
            backup_age_hours = (datetime.now() - most_recent[1]).total_seconds() / 3600

            if backup_age_hours > 48:  # >48 hours old
                self.issues.append(
                    ResilienceIssue(
                        category="backup_status",
                        severity="warning"
                        if backup_age_hours < 168
                        else "critical",  # 1 week
                        description=f"Most recent backup is {backup_age_hours:.1f} hours old",
                        details={
                            "most_recent_backup": most_recent[0],
                            "backup_age_hours": f"{backup_age_hours:.1f}",
                            "total_backups": len(backups),
                        },
                        recommended_action="Run database backup soon, review backup schedule",
                    )
                )

            print(
                f"      ✓ Most recent backup: {backup_age_hours:.1f} hours ago ({len(backups)} total backups)"
            )

        except Exception as e:
            print(f"      ⚠️  Backup check failed: {e}")

    def generate_report(self) -> str:
        """Generate resilience check report."""
        if not self.issues:
            return "\n✅ No resilience issues found! Database is healthy for the long term.\n"

        report = ["\n" + "=" * 60]
        report.append("🛡️  RESILIENCE CHECK REPORT")
        report.append("=" * 60)

        # Count by severity
        critical = [i for i in self.issues if i.severity == "critical"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        info = [i for i in self.issues if i.severity == "info"]

        report.append(f"\n🔴 Critical: {len(critical)}")
        report.append(f"🟡 Warnings: {len(warnings)}")
        report.append(f"🔵 Info: {len(info)}")

        # Group by category
        report.append("\n" + "-" * 60)
        report.append("Issues by Category:")
        report.append("-" * 60)

        categories = {}
        for issue in self.issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)

        for category, issues in sorted(categories.items()):
            report.append(f"\n{category.upper().replace('_', ' ')}: {len(issues)}")

            for issue in issues:
                severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[
                    issue.severity
                ]
                report.append(f"  {severity_icon} {issue.description}")
                if issue.recommended_action:
                    report.append(f"     → {issue.recommended_action}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)
