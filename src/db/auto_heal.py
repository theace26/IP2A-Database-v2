"""Auto-healing database integrity system with scheduling and notifications."""

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import os
import json

from .integrity_check import IntegrityChecker
from .integrity_repair import IntegrityRepairer
from .admin_notifications import NotificationManager


class AutoHealResult:
    """Result of an auto-heal operation."""

    def __init__(
        self,
        run_id: str,
        timestamp: datetime,
        issues_found: int,
        issues_fixed: int,
        issues_requiring_attention: int,
        notifications_sent: int,
        success: bool,
        error_message: Optional[str] = None,
    ):
        self.run_id = run_id
        self.timestamp = timestamp
        self.issues_found = issues_found
        self.issues_fixed = issues_fixed
        self.issues_requiring_attention = issues_requiring_attention
        self.notifications_sent = notifications_sent
        self.success = success
        self.error_message = error_message

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "issues_requiring_attention": self.issues_requiring_attention,
            "notifications_sent": self.notifications_sent,
            "success": self.success,
            "error_message": self.error_message,
        }


class AutoHealingSystem:
    """
    Automated database integrity checking and repair system.

    Features:
    - Automatic integrity checking
    - Self-healing for fixable issues
    - Admin notifications for complex issues
    - Logging and audit trail
    - Scheduling support
    """

    def __init__(self, db: Session, check_files: bool = True, dry_run: bool = False):
        """
        Initialize auto-healing system.

        Args:
            db: Database session
            check_files: Whether to check file system integrity (can be slow)
            dry_run: If True, don't actually make repairs (test mode)
        """
        self.db = db
        self.check_files = check_files
        self.dry_run = dry_run
        self.log_dir = "/app/logs/auto_heal"
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """Ensure the log directory exists."""
        os.makedirs(self.log_dir, exist_ok=True)

    def run_auto_heal(self, notify_admin: bool = True) -> AutoHealResult:
        """
        Run full auto-heal cycle: check → repair → notify.

        Args:
            notify_admin: Whether to send admin notifications for unfixable issues

        Returns:
            AutoHealResult with summary of operations
        """
        run_id = f"AH-{int(datetime.now().timestamp())}"
        timestamp = datetime.now()

        print("\n" + "=" * 60)
        print("🔄 AUTO-HEALING SYSTEM - Starting Run")
        print(f"Run ID: {run_id}")
        print(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made")
        print("=" * 60)

        try:
            # STEP 1: Run integrity checks
            print("\n📋 STEP 1: Running Integrity Checks")
            checker = IntegrityChecker(self.db)
            issues = checker.run_all_checks(check_files=self.check_files)

            if not issues:
                print("\n✅ No integrity issues found! Database is healthy.")
                result = AutoHealResult(
                    run_id=run_id,
                    timestamp=timestamp,
                    issues_found=0,
                    issues_fixed=0,
                    issues_requiring_attention=0,
                    notifications_sent=0,
                    success=True,
                )
                self._log_result(result)
                return result

            print(f"\n📊 Found {len(issues)} integrity issues")
            print(checker.generate_report())

            # STEP 2: Auto-repair fixable issues
            print("\n🔧 STEP 2: Auto-Repairing Fixable Issues")
            repairer = IntegrityRepairer(self.db, dry_run=self.dry_run)
            auto_fixable = [i for i in issues if i.auto_fixable]

            if auto_fixable:
                print(f"Found {len(auto_fixable)} auto-fixable issues")
                repair_actions = repairer.repair_all_auto_fixable(issues)
                successful_repairs = [a for a in repair_actions if a.success]
                print(repairer.generate_repair_report())
            else:
                print("No auto-fixable issues found.")
                successful_repairs = []

            # STEP 3: Notify admin about unfixable issues
            notifications_sent = 0
            unfixable_issues = [i for i in issues if not i.auto_fixable]

            if notify_admin and unfixable_issues:
                print(
                    f"\n📧 STEP 3: Notifying Admin About {len(unfixable_issues)} Unfixable Issues"
                )
                notification_manager = NotificationManager()
                notifications = notification_manager.analyze_and_notify(
                    unfixable_issues
                )
                notifications_sent = len(notifications)
                print(f"   ✅ Sent {notifications_sent} admin notifications")
            elif notify_admin:
                print("\n✅ STEP 3: No unfixable issues - No notifications needed")

            # Create result summary
            result = AutoHealResult(
                run_id=run_id,
                timestamp=timestamp,
                issues_found=len(issues),
                issues_fixed=len(successful_repairs),
                issues_requiring_attention=len(unfixable_issues),
                notifications_sent=notifications_sent,
                success=True,
            )

            # Log result
            self._log_result(result)

            # Print final summary
            print("\n" + "=" * 60)
            print("✅ AUTO-HEALING COMPLETE")
            print("=" * 60)
            print(f"Issues Found: {result.issues_found}")
            print(f"Issues Fixed: {result.issues_fixed}")
            print(f"Issues Requiring Attention: {result.issues_requiring_attention}")
            print(f"Admin Notifications Sent: {result.notifications_sent}")
            print("=" * 60)

            return result

        except Exception as e:
            error_msg = f"Auto-heal failed: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}")

            result = AutoHealResult(
                run_id=run_id,
                timestamp=timestamp,
                issues_found=0,
                issues_fixed=0,
                issues_requiring_attention=0,
                notifications_sent=0,
                success=False,
                error_message=error_msg,
            )

            self._log_result(result)
            return result

    def _log_result(self, result: AutoHealResult):
        """Log auto-heal result to file."""
        log_file = os.path.join(
            self.log_dir, f"{result.timestamp.strftime('%Y-%m-%d')}_auto_heal.jsonl"
        )

        with open(log_file, "a") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

        print(f"\n📝 Result logged to: {log_file}")

    def get_recent_runs(self, days: int = 7) -> list[dict]:
        """
        Get recent auto-heal run results.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            List of auto-heal results
        """
        results = []
        today = datetime.now()

        for day_offset in range(days):
            date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_dir, f"{date}_auto_heal.jsonl")

            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    for line in f:
                        if line.strip():
                            results.append(json.loads(line))

        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def get_health_summary(self, days: int = 7) -> dict:
        """
        Get database health summary based on recent auto-heal runs.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with health metrics
        """
        runs = self.get_recent_runs(days)

        if not runs:
            return {
                "status": "unknown",
                "message": "No auto-heal runs in the specified period",
                "days_analyzed": days,
            }

        total_runs = len(runs)
        successful_runs = len([r for r in runs if r["success"]])
        total_issues_found = sum(r["issues_found"] for r in runs)
        total_issues_fixed = sum(r["issues_fixed"] for r in runs)
        total_requiring_attention = sum(r["issues_requiring_attention"] for r in runs)

        # Determine health status
        if total_requiring_attention > 50:
            status = "critical"
            message = (
                f"{total_requiring_attention} issues require immediate admin attention"
            )
        elif total_requiring_attention > 10:
            status = "warning"
            message = f"{total_requiring_attention} issues need review"
        elif total_issues_found > 100:
            status = "fair"
            message = f"High volume of issues ({total_issues_found}) but most are auto-fixable"
        else:
            status = "healthy"
            message = "Database integrity is good"

        return {
            "status": status,
            "message": message,
            "days_analyzed": days,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "total_issues_found": total_issues_found,
            "total_issues_fixed": total_issues_fixed,
            "total_requiring_attention": total_requiring_attention,
            "auto_fix_rate": f"{(total_issues_fixed / total_issues_found * 100) if total_issues_found > 0 else 0:.1f}%",
            "most_recent_run": runs[0] if runs else None,
        }


class ScheduledAutoHeal:
    """
    Scheduled auto-healing with cron-like functionality.

    Note: This is a basic scheduler. In production, use:
    - Celery Beat for distributed task scheduling
    - APScheduler for more advanced scheduling
    - Kubernetes CronJob for containerized environments
    """

    def __init__(self, db_session_factory):
        """
        Initialize scheduled auto-heal.

        Args:
            db_session_factory: Function that returns a database session
        """
        self.db_session_factory = db_session_factory
        self.last_run_file = "/app/logs/auto_heal/.last_run"

    def should_run(self, interval_hours: int = 24) -> bool:
        """
        Check if auto-heal should run based on interval.

        Args:
            interval_hours: Minimum hours between runs (default: 24)

        Returns:
            bool: True if enough time has passed since last run
        """
        if not os.path.exists(self.last_run_file):
            return True

        with open(self.last_run_file, "r") as f:
            last_run_str = f.read().strip()
            last_run = datetime.fromisoformat(last_run_str)

        time_since_last = datetime.now() - last_run
        return time_since_last.total_seconds() >= interval_hours * 3600

    def run_if_due(self, interval_hours: int = 24) -> Optional[AutoHealResult]:
        """
        Run auto-heal if enough time has passed.

        Args:
            interval_hours: Minimum hours between runs (default: 24)

        Returns:
            AutoHealResult if ran, None if skipped
        """
        if not self.should_run(interval_hours):
            print("⏭️  Skipping auto-heal (not due yet)")
            return None

        print("⏰ Auto-heal is due - running now")

        db = self.db_session_factory()
        try:
            healer = AutoHealingSystem(db, check_files=True, dry_run=False)
            result = healer.run_auto_heal(notify_admin=True)

            # Update last run timestamp
            with open(self.last_run_file, "w") as f:
                f.write(datetime.now().isoformat())

            return result
        finally:
            db.close()


# Convenience function for quick auto-heal
def quick_heal(db: Session, dry_run: bool = False) -> AutoHealResult:
    """
    Quick auto-heal function for manual runs.

    Args:
        db: Database session
        dry_run: If True, don't make actual repairs

    Returns:
        AutoHealResult with summary
    """
    healer = AutoHealingSystem(db, check_files=True, dry_run=dry_run)
    return healer.run_auto_heal(notify_admin=True)
