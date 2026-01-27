"""Admin notification system for database integrity issues."""

from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import os

from .integrity_check import IntegrityIssue


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    LOG = "log"
    SLACK = "slack"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AdminNotification:
    """Represents a notification to send to database administrators."""

    def __init__(
        self,
        title: str,
        message: str,
        priority: NotificationPriority,
        issues: List[IntegrityIssue],
        recommended_action: Optional[str] = None
    ):
        self.title = title
        self.message = message
        self.priority = priority
        self.issues = issues
        self.recommended_action = recommended_action
        self.timestamp = datetime.now()
        self.notification_id = f"DBADM-{int(self.timestamp.timestamp())}"

    def to_dict(self) -> dict:
        """Convert notification to dictionary."""
        return {
            "notification_id": self.notification_id,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "issue_count": len(self.issues),
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "table": issue.table,
                    "record_id": issue.record_id,
                    "description": issue.description,
                    "auto_fixable": issue.auto_fixable
                }
                for issue in self.issues
            ],
            "recommended_action": self.recommended_action
        }


class NotificationManager:
    """Manages admin notifications for database integrity issues."""

    def __init__(self, channels: List[NotificationChannel] = None):
        """
        Initialize notification manager.

        Args:
            channels: List of notification channels to use (default: [LOG])
        """
        self.channels = channels or [NotificationChannel.LOG]
        self.notifications_dir = "/app/logs/admin_notifications"
        self._ensure_notification_dir()

    def _ensure_notification_dir(self):
        """Ensure the notifications directory exists."""
        os.makedirs(self.notifications_dir, exist_ok=True)

    def send_notification(self, notification: AdminNotification) -> bool:
        """
        Send notification through configured channels.

        Args:
            notification: The notification to send

        Returns:
            bool: True if sent successfully through at least one channel
        """
        success = False

        for channel in self.channels:
            try:
                if channel == NotificationChannel.LOG:
                    self._send_log(notification)
                    success = True
                elif channel == NotificationChannel.EMAIL:
                    self._send_email(notification)
                    success = True
                elif channel == NotificationChannel.SLACK:
                    self._send_slack(notification)
                    success = True
                elif channel == NotificationChannel.WEBHOOK:
                    self._send_webhook(notification)
                    success = True
            except Exception as e:
                print(f"   ⚠️  Failed to send notification via {channel.value}: {e}")

        return success

    def _send_log(self, notification: AdminNotification):
        """Write notification to log file."""
        log_file = os.path.join(
            self.notifications_dir,
            f"{datetime.now().strftime('%Y-%m-%d')}_notifications.jsonl"
        )

        with open(log_file, "a") as f:
            f.write(json.dumps(notification.to_dict()) + "\n")

        # Also print to console
        priority_icon = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "⚠️",
            NotificationPriority.HIGH: "🔴",
            NotificationPriority.CRITICAL: "🚨"
        }[notification.priority]

        print(f"\n{priority_icon} ADMIN NOTIFICATION [{notification.priority.value.upper()}]")
        print("=" * 60)
        print(f"ID: {notification.notification_id}")
        print(f"Title: {notification.title}")
        print(f"Message: {notification.message}")
        print(f"Issues: {len(notification.issues)}")
        if notification.recommended_action:
            print(f"Recommended Action: {notification.recommended_action}")
        print(f"Logged to: {log_file}")
        print("=" * 60)

    def _send_email(self, notification: AdminNotification):
        """
        Send notification via email.

        Note: This is a placeholder. In production, integrate with email service
        (e.g., SendGrid, AWS SES, SMTP).
        """
        # TODO: Implement email sending
        # For now, just log that we would send an email
        print(f"   📧 Would send email notification: {notification.title}")
        # In production:
        # - Get admin email from settings
        # - Format HTML email with issue details
        # - Send via email service

    def _send_slack(self, notification: AdminNotification):
        """
        Send notification via Slack.

        Note: This is a placeholder. In production, integrate with Slack webhook.
        """
        # TODO: Implement Slack webhook
        # For now, just log that we would send to Slack
        print(f"   💬 Would send Slack notification: {notification.title}")
        # In production:
        # - Get Slack webhook URL from settings
        # - Format Slack message blocks
        # - POST to webhook URL

    def _send_webhook(self, notification: AdminNotification):
        """
        Send notification via custom webhook.

        Note: This is a placeholder. In production, POST to configured webhook URL.
        """
        # TODO: Implement webhook POST
        # For now, just log that we would send to webhook
        print(f"   🔗 Would send webhook notification: {notification.title}")
        # In production:
        # - Get webhook URL from settings
        # - POST JSON payload
        # - Handle response

    def analyze_and_notify(self, issues: List[IntegrityIssue]) -> List[AdminNotification]:
        """
        Analyze integrity issues and send appropriate notifications.

        Args:
            issues: List of integrity issues from checker

        Returns:
            List of notifications sent
        """
        notifications = []

        # Categorize issues by severity and auto-fixability
        critical_unfixable = [
            i for i in issues
            if i.severity == "critical" and not i.auto_fixable
        ]
        warnings_unfixable = [
            i for i in issues
            if i.severity == "warning" and not i.auto_fixable
        ]
        many_issues = len(issues) > 100

        # CRITICAL: Critical issues that can't be auto-fixed
        if critical_unfixable:
            notification = AdminNotification(
                title=f"CRITICAL: {len(critical_unfixable)} Database Issues Require Manual Intervention",
                message=(
                    f"The database integrity check found {len(critical_unfixable)} critical issues "
                    f"that cannot be automatically fixed. These require immediate admin attention."
                ),
                priority=NotificationPriority.CRITICAL,
                issues=critical_unfixable,
                recommended_action=(
                    "1. Review the integrity check log for full details\n"
                    "2. Back up the database before making changes\n"
                    "3. Investigate root cause of each issue\n"
                    "4. Manually correct data or implement custom repair logic"
                )
            )
            self.send_notification(notification)
            notifications.append(notification)

        # HIGH: Many warnings that can't be auto-fixed
        if warnings_unfixable and len(warnings_unfixable) > 10:
            notification = AdminNotification(
                title=f"HIGH: {len(warnings_unfixable)} Database Warnings Need Review",
                message=(
                    f"The database integrity check found {len(warnings_unfixable)} warnings "
                    f"that cannot be automatically fixed. While not critical, these should be reviewed."
                ),
                priority=NotificationPriority.HIGH,
                issues=warnings_unfixable[:50],  # Limit to first 50 for notification
                recommended_action=(
                    "1. Review the integrity check log for full details\n"
                    "2. Assess impact of each warning\n"
                    "3. Prioritize fixes based on business impact\n"
                    "4. Consider implementing preventive measures"
                )
            )
            self.send_notification(notification)
            notifications.append(notification)

        # MEDIUM: Large number of total issues (potential systemic problem)
        if many_issues and not critical_unfixable:
            notification = AdminNotification(
                title=f"MEDIUM: Database Has {len(issues)} Total Integrity Issues",
                message=(
                    f"The database integrity check found {len(issues)} total issues. "
                    f"While many may be auto-fixable, the large volume suggests a systemic problem."
                ),
                priority=NotificationPriority.MEDIUM,
                issues=issues[:20],  # Sample of issues
                recommended_action=(
                    "1. Review auto-repair results\n"
                    "2. Investigate if there's a common root cause\n"
                    "3. Consider improving data validation at input\n"
                    "4. Review database maintenance procedures"
                )
            )
            self.send_notification(notification)
            notifications.append(notification)

        # LOW: Few warnings, informational
        if warnings_unfixable and len(warnings_unfixable) <= 10 and not many_issues:
            notification = AdminNotification(
                title=f"LOW: {len(warnings_unfixable)} Minor Database Warnings",
                message=(
                    f"The database integrity check found {len(warnings_unfixable)} minor warnings. "
                    f"No immediate action required, but review when convenient."
                ),
                priority=NotificationPriority.LOW,
                issues=warnings_unfixable,
                recommended_action="Review issues when convenient and address as needed."
            )
            self.send_notification(notification)
            notifications.append(notification)

        return notifications

    def get_recent_notifications(self, days: int = 7) -> List[dict]:
        """
        Get recent notifications from log files.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            List of notification dictionaries
        """
        notifications = []
        today = datetime.now()

        for day_offset in range(days):
            date = (today - timedelta(days=day_offset)).strftime('%Y-%m-%d')
            log_file = os.path.join(self.notifications_dir, f"{date}_notifications.jsonl")

            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            notifications.append(json.loads(line))

        return sorted(notifications, key=lambda x: x['timestamp'], reverse=True)


def create_notification_summary(issues: List[IntegrityIssue]) -> str:
    """
    Create a human-readable summary of issues for notifications.

    Args:
        issues: List of integrity issues

    Returns:
        Formatted summary string
    """
    if not issues:
        return "No issues found."

    summary = []
    summary.append(f"Total Issues: {len(issues)}")

    # Count by category
    by_category = {}
    for issue in issues:
        if issue.category not in by_category:
            by_category[issue.category] = 0
        by_category[issue.category] += 1

    summary.append("\nIssues by Category:")
    for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        summary.append(f"  • {category.replace('_', ' ').title()}: {count}")

    # Show sample of most critical
    critical = [i for i in issues if i.severity == "critical"][:5]
    if critical:
        summary.append("\nSample Critical Issues:")
        for issue in critical:
            summary.append(f"  • [{issue.table}] {issue.description}")

    return "\n".join(summary)


# Convenience function for quick notifications
def notify_admin(
    title: str,
    message: str,
    issues: List[IntegrityIssue],
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    recommended_action: Optional[str] = None
) -> bool:
    """
    Quick function to send admin notification.

    Args:
        title: Notification title
        message: Notification message
        issues: List of integrity issues
        priority: Notification priority (default: MEDIUM)
        recommended_action: Recommended action for admin

    Returns:
        bool: True if notification sent successfully
    """
    manager = NotificationManager()
    notification = AdminNotification(
        title=title,
        message=message,
        priority=priority,
        issues=issues,
        recommended_action=recommended_action
    )
    return manager.send_notification(notification)
