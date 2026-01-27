"""Database integrity checker - validates data consistency and structure."""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import os

from src.models import (
    Member, MemberEmployment, Student, Instructor, Location,
    Organization, OrganizationContact, FileAttachment, AuditLog
)
from src.db.enums import (
    MemberStatus, MemberClassification, OrganizationType,
    SaltingScore, CohortStatus
)


class IntegrityIssue:
    """Represents an integrity issue found during checks."""

    def __init__(
        self,
        category: str,
        severity: str,  # 'critical', 'warning', 'info'
        table: str,
        record_id: Optional[int],
        description: str,
        auto_fixable: bool = False,
        fix_action: Optional[str] = None
    ):
        self.category = category
        self.severity = severity
        self.table = table
        self.record_id = record_id
        self.description = description
        self.auto_fixable = auto_fixable
        self.fix_action = fix_action
        self.timestamp = datetime.now()


class IntegrityChecker:
    """Comprehensive database integrity checker."""

    def __init__(self, db: Session):
        self.db = db
        self.issues: List[IntegrityIssue] = []

    def run_all_checks(self, check_files: bool = True) -> List[IntegrityIssue]:
        """Run all integrity checks."""
        print("🔍 Running Database Integrity Checks")
        print("=" * 60)

        # Category 1: Structural Integrity
        print("\n📋 Category 1: Structural Integrity")
        self.check_foreign_keys()
        self.check_required_fields()
        self.check_enum_values()

        # Category 2: Logical Consistency
        print("\n🧮 Category 2: Logical Consistency")
        self.check_date_logic()
        self.check_employment_logic()
        self.check_contact_logic()

        # Category 3: Data Quality
        print("\n✨ Category 3: Data Quality")
        self.check_duplicates()
        self.check_data_anomalies()

        # Category 4: File System Integrity (optional, can be slow)
        if check_files:
            print("\n📎 Category 4: File System Integrity")
            self.check_file_attachments()

        return self.issues

    # === CATEGORY 1: STRUCTURAL INTEGRITY ===

    def check_foreign_keys(self):
        """Check for orphaned records (invalid foreign keys)."""
        print("   Checking foreign key integrity...")

        # Member employments -> Members
        orphaned = self.db.execute(text("""
            SELECT me.id FROM member_employments me
            LEFT JOIN members m ON me.member_id = m.id
            WHERE m.id IS NULL
        """)).fetchall()

        for row in orphaned:
            self.issues.append(IntegrityIssue(
                category="foreign_key",
                severity="critical",
                table="member_employments",
                record_id=row[0],
                description=f"Employment record {row[0]} references non-existent member",
                auto_fixable=True,
                fix_action="delete"
            ))

        # Member employments -> Organizations
        orphaned = self.db.execute(text("""
            SELECT me.id FROM member_employments me
            LEFT JOIN organizations o ON me.organization_id = o.id
            WHERE o.id IS NULL
        """)).fetchall()

        for row in orphaned:
            self.issues.append(IntegrityIssue(
                category="foreign_key",
                severity="critical",
                table="member_employments",
                record_id=row[0],
                description=f"Employment record {row[0]} references non-existent organization",
                auto_fixable=True,
                fix_action="delete"
            ))

        # Organization contacts -> Organizations
        orphaned = self.db.execute(text("""
            SELECT oc.id FROM organization_contacts oc
            LEFT JOIN organizations o ON oc.organization_id = o.id
            WHERE o.id IS NULL
        """)).fetchall()

        for row in orphaned:
            self.issues.append(IntegrityIssue(
                category="foreign_key",
                severity="critical",
                table="organization_contacts",
                record_id=row[0],
                description=f"Contact record {row[0]} references non-existent organization",
                auto_fixable=True,
                fix_action="delete"
            ))

        # File attachments -> Parent records (skip if table doesn't exist)
        try:
            orphaned = self.db.execute(text("""
                SELECT fa.id, fa.record_type, fa.record_id
                FROM file_attachments fa
                WHERE fa.record_type = 'member'
                AND NOT EXISTS (SELECT 1 FROM members m WHERE m.id = fa.record_id)
            """)).fetchall()

            for row in orphaned:
                self.issues.append(IntegrityIssue(
                    category="foreign_key",
                    severity="warning",
                    table="file_attachments",
                    record_id=row[0],
                    description=f"File attachment {row[0]} references non-existent {row[1]} record {row[2]}",
                    auto_fixable=True,
                    fix_action="delete"
                ))
        except Exception:
            # Table doesn't exist yet - rollback and continue
            self.db.rollback()

        print(f"      ✓ Foreign key check complete")

    def check_required_fields(self):
        """Check for missing required fields."""
        print("   Checking required fields...")

        # Members: member_number, first_name, last_name required
        missing = self.db.query(Member).filter(
            (Member.member_number == None) |
            (Member.first_name == None) |
            (Member.last_name == None)
        ).all()

        for member in missing:
            self.issues.append(IntegrityIssue(
                category="required_field",
                severity="critical",
                table="members",
                record_id=member.id,
                description=f"Member {member.id} missing required field(s)",
                auto_fixable=False
            ))

        # Organizations: name, org_type required
        missing = self.db.query(Organization).filter(
            (Organization.name == None) |
            (Organization.org_type == None)
        ).all()

        for org in missing:
            self.issues.append(IntegrityIssue(
                category="required_field",
                severity="critical",
                table="organizations",
                record_id=org.id,
                description=f"Organization {org.id} missing required field(s)",
                auto_fixable=False
            ))

        print(f"      ✓ Required field check complete")

    def check_enum_values(self):
        """Check for invalid enum values."""
        print("   Checking enum value validity...")

        # Member status enums
        valid_statuses = [s.value for s in MemberStatus]
        invalid = self.db.query(Member).filter(
            ~Member.status.in_(valid_statuses)
        ).all()

        for member in invalid:
            self.issues.append(IntegrityIssue(
                category="enum_value",
                severity="critical",
                table="members",
                record_id=member.id,
                description=f"Member {member.id} has invalid status: {member.status}",
                auto_fixable=True,
                fix_action=f"set to '{MemberStatus.ACTIVE.value}'"
            ))

        # Member classification enums
        valid_classifications = [c.value for c in MemberClassification]
        invalid = self.db.query(Member).filter(
            ~Member.classification.in_(valid_classifications)
        ).all()

        for member in invalid:
            self.issues.append(IntegrityIssue(
                category="enum_value",
                severity="critical",
                table="members",
                record_id=member.id,
                description=f"Member {member.id} has invalid classification: {member.classification}",
                auto_fixable=False
            ))

        # Organization type enums
        valid_org_types = [t.value for t in OrganizationType]
        invalid = self.db.query(Organization).filter(
            ~Organization.org_type.in_(valid_org_types)
        ).all()

        for org in invalid:
            self.issues.append(IntegrityIssue(
                category="enum_value",
                severity="critical",
                table="organizations",
                record_id=org.id,
                description=f"Organization {org.id} has invalid org_type: {org.org_type}",
                auto_fixable=False
            ))

        print(f"      ✓ Enum value check complete")

    # === CATEGORY 2: LOGICAL CONSISTENCY ===

    def check_date_logic(self):
        """Check for date logic issues."""
        print("   Checking date logic...")

        # Employment: end_date must be >= start_date
        invalid = self.db.query(MemberEmployment).filter(
            MemberEmployment.end_date != None,
            MemberEmployment.end_date < MemberEmployment.start_date
        ).all()

        for emp in invalid:
            self.issues.append(IntegrityIssue(
                category="date_logic",
                severity="critical",
                table="member_employments",
                record_id=emp.id,
                description=f"Employment {emp.id} has end_date before start_date",
                auto_fixable=True,
                fix_action="swap dates or set end_date to NULL"
            ))

        # Employment: is_current=True must have end_date=NULL
        invalid = self.db.query(MemberEmployment).filter(
            MemberEmployment.is_current == True,
            MemberEmployment.end_date != None
        ).all()

        for emp in invalid:
            self.issues.append(IntegrityIssue(
                category="date_logic",
                severity="warning",
                table="member_employments",
                record_id=emp.id,
                description=f"Employment {emp.id} marked current but has end_date",
                auto_fixable=True,
                fix_action="set is_current=False or end_date=NULL"
            ))

        # Members: hire_date should not be in future
        from datetime import date
        future_hires = self.db.query(Member).filter(
            Member.hire_date > date.today()
        ).all()

        for member in future_hires:
            self.issues.append(IntegrityIssue(
                category="date_logic",
                severity="warning",
                table="members",
                record_id=member.id,
                description=f"Member {member.id} has future hire_date: {member.hire_date}",
                auto_fixable=False
            ))

        print(f"      ✓ Date logic check complete")

    def check_employment_logic(self):
        """Check employment-specific business logic."""
        print("   Checking employment logic...")

        # Members with multiple "current" jobs
        duplicates = self.db.execute(text("""
            SELECT member_id, COUNT(*) as current_count
            FROM member_employments
            WHERE is_current = true
            GROUP BY member_id
            HAVING COUNT(*) > 1
        """)).fetchall()

        for row in duplicates:
            self.issues.append(IntegrityIssue(
                category="employment_logic",
                severity="warning",
                table="member_employments",
                record_id=None,
                description=f"Member {row[0]} has {row[1]} current employments (should be 0 or 1)",
                auto_fixable=False
            ))

        # Hourly rate sanity check ($10-$150 range)
        invalid = self.db.query(MemberEmployment).filter(
            (MemberEmployment.hourly_rate < 10) |
            (MemberEmployment.hourly_rate > 150)
        ).all()

        for emp in invalid:
            self.issues.append(IntegrityIssue(
                category="employment_logic",
                severity="info",
                table="member_employments",
                record_id=emp.id,
                description=f"Employment {emp.id} has unusual hourly_rate: ${emp.hourly_rate}",
                auto_fixable=False
            ))

        print(f"      ✓ Employment logic check complete")

    def check_contact_logic(self):
        """Check organization contact logic."""
        print("   Checking contact logic...")

        # Organizations with multiple primary contacts
        duplicates = self.db.execute(text("""
            SELECT organization_id, COUNT(*) as primary_count
            FROM organization_contacts
            WHERE is_primary = true
            GROUP BY organization_id
            HAVING COUNT(*) > 1
        """)).fetchall()

        for row in duplicates:
            self.issues.append(IntegrityIssue(
                category="contact_logic",
                severity="warning",
                table="organization_contacts",
                record_id=None,
                description=f"Organization {row[0]} has {row[1]} primary contacts (should be 0 or 1)",
                auto_fixable=True,
                fix_action="keep most recent as primary"
            ))

        # Organizations with no contacts
        no_contacts = self.db.execute(text("""
            SELECT o.id, o.name
            FROM organizations o
            WHERE NOT EXISTS (
                SELECT 1 FROM organization_contacts oc
                WHERE oc.organization_id = o.id
            )
        """)).fetchall()

        for row in no_contacts:
            self.issues.append(IntegrityIssue(
                category="contact_logic",
                severity="info",
                table="organizations",
                record_id=row[0],
                description=f"Organization {row[0]} ({row[1]}) has no contacts",
                auto_fixable=False
            ))

        print(f"      ✓ Contact logic check complete")

    # === CATEGORY 3: DATA QUALITY ===

    def check_duplicates(self):
        """Check for duplicate records."""
        print("   Checking for duplicates...")

        # Duplicate member numbers
        duplicates = self.db.execute(text("""
            SELECT member_number, COUNT(*) as count
            FROM members
            GROUP BY member_number
            HAVING COUNT(*) > 1
        """)).fetchall()

        for row in duplicates:
            self.issues.append(IntegrityIssue(
                category="duplicate",
                severity="critical",
                table="members",
                record_id=None,
                description=f"Duplicate member_number: {row[0]} ({row[1]} records)",
                auto_fixable=False
            ))

        # Duplicate student emails
        duplicates = self.db.execute(text("""
            SELECT email, COUNT(*) as count
            FROM students
            WHERE email IS NOT NULL
            GROUP BY email
            HAVING COUNT(*) > 1
        """)).fetchall()

        for row in duplicates:
            self.issues.append(IntegrityIssue(
                category="duplicate",
                severity="warning",
                table="students",
                record_id=None,
                description=f"Duplicate student email: {row[0]} ({row[1]} records)",
                auto_fixable=False
            ))

        print(f"      ✓ Duplicate check complete")

    def check_data_anomalies(self):
        """Check for data anomalies and outliers."""
        print("   Checking for data anomalies...")

        # Members with no employments (may be new or inactive)
        try:
            no_jobs = self.db.execute(text(f"""
                SELECT m.id, m.member_number, m.status
                FROM members m
                WHERE m.status = '{MemberStatus.ACTIVE.value}'
                AND NOT EXISTS (
                    SELECT 1 FROM member_employments me
                    WHERE me.member_id = m.id
                )
            """)).fetchall()

            if len(no_jobs) > 0:
                self.issues.append(IntegrityIssue(
                    category="data_anomaly",
                    severity="info",
                    table="members",
                    record_id=None,
                    description=f"{len(no_jobs)} active members have no employment history",
                    auto_fixable=False
                ))
        except Exception:
            # Skip if members table doesn't exist or enum mismatch
            self.db.rollback()

        print(f"      ✓ Data anomaly check complete")

    # === CATEGORY 4: FILE SYSTEM INTEGRITY ===

    def check_file_attachments(self):
        """Check file attachment integrity."""
        print("   Checking file attachments...")
        print("   (This may take a while for large datasets...)")

        try:
            attachments = self.db.query(FileAttachment).all()
        except Exception:
            # Table doesn't exist yet - skip this check
            print("      ⚠️  file_attachments table not found - skipping")
            return

        checked = 0
        for attachment in attachments:
            # Check if file path is valid
            if not attachment.file_path:
                self.issues.append(IntegrityIssue(
                    category="file_system",
                    severity="critical",
                    table="file_attachments",
                    record_id=attachment.id,
                    description=f"Attachment {attachment.id} has no file_path",
                    auto_fixable=True,
                    fix_action="delete record"
                ))
                continue

            # Check if file exists (if storage is local)
            # Note: Skip this check if using S3 or remote storage
            full_path = os.path.join("/app", attachment.file_path)
            if not attachment.file_path.startswith("http") and not os.path.exists(full_path):
                self.issues.append(IntegrityIssue(
                    category="file_system",
                    severity="warning",
                    table="file_attachments",
                    record_id=attachment.id,
                    description=f"Attachment {attachment.id} file not found: {attachment.file_path}",
                    auto_fixable=False  # Requires user decision
                ))

            # Check file size is reasonable
            if attachment.file_size and (attachment.file_size < 0 or attachment.file_size > 100_000_000):
                self.issues.append(IntegrityIssue(
                    category="file_system",
                    severity="info",
                    table="file_attachments",
                    record_id=attachment.id,
                    description=f"Attachment {attachment.id} has unusual file_size: {attachment.file_size} bytes",
                    auto_fixable=False
                ))

            checked += 1
            if checked % 1000 == 0:
                print(f"      Checked {checked}/{len(attachments)} attachments...")

        print(f"      ✓ File attachment check complete ({checked} files checked)")

    def generate_report(self) -> str:
        """Generate a summary report of all issues."""
        if not self.issues:
            return "\n✅ No integrity issues found! Database is healthy.\n"

        report = ["\n" + "=" * 60]
        report.append("📊 INTEGRITY CHECK REPORT")
        report.append("=" * 60)

        # Count by severity
        critical = [i for i in self.issues if i.severity == "critical"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        info = [i for i in self.issues if i.severity == "info"]

        report.append(f"\n🔴 Critical Issues: {len(critical)}")
        report.append(f"🟡 Warnings: {len(warnings)}")
        report.append(f"🔵 Info: {len(info)}")
        report.append(f"   Total Issues: {len(self.issues)}")

        # Count auto-fixable
        auto_fixable = [i for i in self.issues if i.auto_fixable]
        report.append(f"\n🔧 Auto-fixable: {len(auto_fixable)}/{len(self.issues)}")

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
            report.append(f"\n{category.upper().replace('_', ' ')}: {len(issues)} issues")

            # Show first 5 of each category
            for issue in issues[:5]:
                severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[issue.severity]
                report.append(f"  {severity_icon} {issue.description}")
                if issue.auto_fixable:
                    report.append(f"     → Auto-fix: {issue.fix_action}")

            if len(issues) > 5:
                report.append(f"  ... and {len(issues) - 5} more")

        report.append("\n" + "=" * 60)

        return "\n".join(report)
