"""Database integrity repair - fixes issues found by integrity checker."""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.models import Member, MemberEmployment, OrganizationContact, FileAttachment
from src.db.enums import MemberStatus
from .integrity_check import IntegrityIssue


class RepairAction:
    """Represents a repair action taken."""

    def __init__(
        self,
        issue: IntegrityIssue,
        action_taken: str,
        success: bool,
        details: Optional[str] = None,
    ):
        self.issue = issue
        self.action_taken = action_taken
        self.success = success
        self.details = details
        self.timestamp = datetime.now()


class IntegrityRepairer:
    """Repairs database integrity issues."""

    def __init__(self, db: Session, dry_run: bool = False):
        self.db = db
        self.dry_run = dry_run
        self.actions: List[RepairAction] = []

    def repair_all_auto_fixable(
        self, issues: List[IntegrityIssue]
    ) -> List[RepairAction]:
        """Repair all auto-fixable issues."""
        print("\n🔧 Starting Auto-Repair Process")
        print("=" * 60)

        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made")
            print()

        auto_fixable = [i for i in issues if i.auto_fixable]

        if not auto_fixable:
            print("No auto-fixable issues found.")
            return []

        print(f"Found {len(auto_fixable)} auto-fixable issues")
        print()

        # Group by category for organized repair
        by_category = {}
        for issue in auto_fixable:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)

        # Repair each category
        for category, category_issues in sorted(by_category.items()):
            print(
                f"📋 Repairing {category.replace('_', ' ').title()}: {len(category_issues)} issues"
            )

            for issue in category_issues:
                action = self._repair_issue(issue)
                self.actions.append(action)

                if action.success:
                    print(f"   ✅ Fixed: {issue.description}")
                else:
                    print(f"   ❌ Failed: {issue.description}")
                    if action.details:
                        print(f"      {action.details}")

        if not self.dry_run:
            self.db.commit()
            print("\n✅ Auto-repair complete - changes committed")
        else:
            self.db.rollback()
            print("\n⚠️  Dry run complete - no changes made")

        return self.actions

    def _repair_issue(self, issue: IntegrityIssue) -> RepairAction:
        """Repair a single issue."""
        try:
            if issue.category == "foreign_key":
                return self._repair_foreign_key(issue)
            elif issue.category == "enum_value":
                return self._repair_enum_value(issue)
            elif issue.category == "date_logic":
                return self._repair_date_logic(issue)
            elif issue.category == "contact_logic":
                return self._repair_contact_logic(issue)
            elif issue.category == "file_system":
                return self._repair_file_system(issue)
            else:
                return RepairAction(
                    issue=issue,
                    action_taken="skip",
                    success=False,
                    details=f"No repair handler for category: {issue.category}",
                )
        except Exception as e:
            return RepairAction(
                issue=issue, action_taken="error", success=False, details=str(e)
            )

    def _repair_foreign_key(self, issue: IntegrityIssue) -> RepairAction:
        """Repair foreign key issues (delete orphaned records)."""
        if issue.fix_action != "delete":
            return RepairAction(
                issue=issue,
                action_taken="skip",
                success=False,
                details="Unexpected fix_action",
            )

        if not self.dry_run:
            if issue.table == "member_employments":
                emp = (
                    self.db.query(MemberEmployment)
                    .filter(MemberEmployment.id == issue.record_id)
                    .first()
                )
                if emp:
                    self.db.delete(emp)

            elif issue.table == "organization_contacts":
                contact = (
                    self.db.query(OrganizationContact)
                    .filter(OrganizationContact.id == issue.record_id)
                    .first()
                )
                if contact:
                    self.db.delete(contact)

            elif issue.table == "file_attachments":
                attachment = (
                    self.db.query(FileAttachment)
                    .filter(FileAttachment.id == issue.record_id)
                    .first()
                )
                if attachment:
                    self.db.delete(attachment)

        return RepairAction(
            issue=issue,
            action_taken="delete",
            success=True,
            details=f"Deleted orphaned {issue.table} record {issue.record_id}",
        )

    def _repair_enum_value(self, issue: IntegrityIssue) -> RepairAction:
        """Repair invalid enum values."""
        if not self.dry_run:
            if issue.table == "members" and "status" in issue.description:
                member = (
                    self.db.query(Member).filter(Member.id == issue.record_id).first()
                )
                if member:
                    member.status = MemberStatus.ACTIVE
                    return RepairAction(
                        issue=issue,
                        action_taken="update",
                        success=True,
                        details="Set member status to ACTIVE",
                    )

        return RepairAction(
            issue=issue,
            action_taken="skip" if self.dry_run else "update",
            success=True,
            details="Would set to default value"
            if self.dry_run
            else "Set to default value",
        )

    def _repair_date_logic(self, issue: IntegrityIssue) -> RepairAction:
        """Repair date logic issues."""
        if not self.dry_run:
            emp = (
                self.db.query(MemberEmployment)
                .filter(MemberEmployment.id == issue.record_id)
                .first()
            )

            if not emp:
                return RepairAction(
                    issue=issue,
                    action_taken="skip",
                    success=False,
                    details="Record not found",
                )

            if "end_date before start_date" in issue.description:
                # Set end_date to NULL (safer than swapping)
                emp.end_date = None
                return RepairAction(
                    issue=issue,
                    action_taken="update",
                    success=True,
                    details="Set end_date to NULL",
                )

            elif "marked current but has end_date" in issue.description:
                # Set is_current to False (preserve end_date)
                emp.is_current = False
                return RepairAction(
                    issue=issue,
                    action_taken="update",
                    success=True,
                    details="Set is_current to False",
                )

        return RepairAction(
            issue=issue,
            action_taken="skip" if self.dry_run else "update",
            success=True,
            details="Would fix date logic" if self.dry_run else "Fixed date logic",
        )

    def _repair_contact_logic(self, issue: IntegrityIssue) -> RepairAction:
        """Repair organization contact logic (multiple primary contacts)."""
        if "multiple primary contacts" in issue.description:
            # Extract organization_id from description
            org_id = int(issue.description.split("Organization ")[1].split(" ")[0])

            if not self.dry_run:
                # Get all primary contacts for this org, ordered by created_at desc
                contacts = (
                    self.db.query(OrganizationContact)
                    .filter(
                        OrganizationContact.organization_id == org_id,
                        OrganizationContact.is_primary == True,
                    )
                    .order_by(OrganizationContact.created_at.desc())
                    .all()
                )

                # Keep first (most recent) as primary, set rest to non-primary
                for i, contact in enumerate(contacts):
                    if i > 0:
                        contact.is_primary = False

                return RepairAction(
                    issue=issue,
                    action_taken="update",
                    success=True,
                    details=f"Set {len(contacts)-1} contacts to non-primary, kept most recent as primary",
                )

        return RepairAction(
            issue=issue,
            action_taken="skip" if self.dry_run else "update",
            success=True,
            details="Would fix primary contact"
            if self.dry_run
            else "Fixed primary contact",
        )

    def _repair_file_system(self, issue: IntegrityIssue) -> RepairAction:
        """Repair file system issues (delete records with no file_path)."""
        if "has no file_path" in issue.description:
            if not self.dry_run:
                attachment = (
                    self.db.query(FileAttachment)
                    .filter(FileAttachment.id == issue.record_id)
                    .first()
                )
                if attachment:
                    self.db.delete(attachment)

            return RepairAction(
                issue=issue,
                action_taken="delete",
                success=True,
                details="Deleted attachment with no file_path",
            )

        return RepairAction(
            issue=issue,
            action_taken="skip",
            success=False,
            details="Requires manual intervention (file not found)",
        )

    def interactive_repair_files(
        self, issues: List[IntegrityIssue]
    ) -> List[RepairAction]:
        """Interactively repair file attachment issues."""
        file_issues = [
            i
            for i in issues
            if i.category == "file_system" and "file not found" in i.description
        ]

        if not file_issues:
            return []

        print("\n📎 Interactive File Repair")
        print("=" * 60)
        print(
            f"Found {len(file_issues)} file attachment issues requiring manual review"
        )
        print()

        for issue in file_issues:
            attachment = (
                self.db.query(FileAttachment)
                .filter(FileAttachment.id == issue.record_id)
                .first()
            )

            if not attachment:
                continue

            print(f"\n📄 File Attachment #{attachment.id}")
            print(f"   Type: {attachment.record_type}")
            print(f"   Record ID: {attachment.record_id}")
            print(f"   Original Name: {attachment.original_name}")
            print(f"   Path: {attachment.file_path}")
            print(f"   Size: {attachment.file_size:,} bytes")
            print(f"   Description: {attachment.description}")
            print()
            print("Options:")
            print("  1) Delete this attachment record")
            print("  2) Keep record (maybe file will be restored later)")
            print("  3) Skip (decide later)")
            print("  4) Delete ALL remaining file attachment issues")
            print("  5) Keep ALL remaining records")
            print("  6) Abort repair")

            choice = input("\nChoice (1-6): ").strip()

            if choice == "1":
                if not self.dry_run:
                    self.db.delete(attachment)
                self.actions.append(
                    RepairAction(
                        issue=issue,
                        action_taken="delete",
                        success=True,
                        details="User chose to delete",
                    )
                )
                print("   ✅ Deleted")

            elif choice == "2":
                self.actions.append(
                    RepairAction(
                        issue=issue,
                        action_taken="keep",
                        success=True,
                        details="User chose to keep record",
                    )
                )
                print("   ℹ️  Kept record")

            elif choice == "3":
                print("   ⏭️  Skipped")
                continue

            elif choice == "4":
                # Delete all remaining
                remaining = file_issues[file_issues.index(issue) :]
                for rem_issue in remaining:
                    rem_attachment = (
                        self.db.query(FileAttachment)
                        .filter(FileAttachment.id == rem_issue.record_id)
                        .first()
                    )
                    if rem_attachment and not self.dry_run:
                        self.db.delete(rem_attachment)
                    self.actions.append(
                        RepairAction(
                            issue=rem_issue,
                            action_taken="delete",
                            success=True,
                            details="User chose to delete all remaining",
                        )
                    )
                print(f"   ✅ Deleted {len(remaining)} file attachment records")
                break

            elif choice == "5":
                # Keep all remaining
                remaining = file_issues[file_issues.index(issue) :]
                for rem_issue in remaining:
                    self.actions.append(
                        RepairAction(
                            issue=rem_issue,
                            action_taken="keep",
                            success=True,
                            details="User chose to keep all remaining",
                        )
                    )
                print(f"   ℹ️  Kept {len(remaining)} file attachment records")
                break

            elif choice == "6":
                print("   ❌ Repair aborted by user")
                return self.actions

        if not self.dry_run:
            self.db.commit()
            print("\n✅ Interactive repair complete - changes committed")

        return self.actions

    def generate_repair_report(self) -> str:
        """Generate a report of repair actions taken."""
        if not self.actions:
            return "\nNo repairs performed.\n"

        report = ["\n" + "=" * 60]
        report.append("🔧 REPAIR REPORT")
        report.append("=" * 60)

        successful = [a for a in self.actions if a.success]
        failed = [a for a in self.actions if not a.success]

        report.append(f"\n✅ Successful: {len(successful)}")
        report.append(f"❌ Failed: {len(failed)}")
        report.append(f"   Total Actions: {len(self.actions)}")

        # Group by action type
        by_action = {}
        for action in self.actions:
            if action.action_taken not in by_action:
                by_action[action.action_taken] = []
            by_action[action.action_taken].append(action)

        report.append("\n" + "-" * 60)
        report.append("Actions Taken:")
        report.append("-" * 60)

        for action_type, actions in sorted(by_action.items()):
            report.append(f"\n{action_type.upper()}: {len(actions)}")

            for action in actions[:5]:
                status = "✅" if action.success else "❌"
                report.append(f"  {status} {action.issue.description}")
                if action.details:
                    report.append(f"     → {action.details}")

            if len(actions) > 5:
                report.append(f"  ... and {len(actions) - 5} more")

        report.append("\n" + "=" * 60)

        return "\n".join(report)
