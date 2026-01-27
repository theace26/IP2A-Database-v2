"""
Database Load Testing - Simulates concurrent users performing realistic operations.

Tests database performance under concurrent load with various usage patterns:
- Read-heavy users (searching, viewing records)
- Write-heavy users (creating, updating records)
- Mixed operations (typical user behavior)
- File attachment operations

Collects metrics: response times, throughput, errors, connection pool stats
"""

import time
import random
import threading
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict
from faker import Faker

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db.session import get_db_session
from src.models import (
    Member, MemberEmployment, Student, Organization,
    OrganizationContact, FileAttachment, Location, Instructor
)
from src.db.enums import (
    MemberStatus, MemberClassification, OrganizationType,
    SaltingScore, EnrollmentStatus
)


fake = Faker()


@dataclass
class OperationResult:
    """Result of a single database operation."""
    operation: str
    duration_ms: float
    success: bool
    error: str = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UserMetrics:
    """Metrics for a single simulated user."""
    user_id: int
    operations: List[OperationResult] = field(default_factory=list)
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration_ms: float = 0

    def add_result(self, result: OperationResult):
        """Add an operation result."""
        self.operations.append(result)
        self.total_operations += 1
        self.total_duration_ms += result.duration_ms
        if result.success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1

    def avg_response_time_ms(self) -> float:
        """Average response time in milliseconds."""
        return self.total_duration_ms / self.total_operations if self.total_operations > 0 else 0


class LoadTestUser:
    """Simulates a single user performing database operations."""

    def __init__(
        self,
        user_id: int,
        pattern: str = "mixed",
        operations_count: int = 50,
        think_time_ms: int = 100
    ):
        self.user_id = user_id
        self.pattern = pattern
        self.operations_count = operations_count
        self.think_time_ms = think_time_ms
        self.metrics = UserMetrics(user_id=user_id)
        self.db: Session = None

    def run(self):
        """Execute the user's operation pattern."""
        try:
            self.db = get_db_session()

            for _ in range(self.operations_count):
                # Select operation based on pattern
                operation = self._select_operation()

                # Execute operation and record metrics
                start_time = time.time()
                try:
                    operation()
                    duration_ms = (time.time() - start_time) * 1000
                    self.metrics.add_result(OperationResult(
                        operation=operation.__name__,
                        duration_ms=duration_ms,
                        success=True
                    ))
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    self.metrics.add_result(OperationResult(
                        operation=operation.__name__,
                        duration_ms=duration_ms,
                        success=False,
                        error=str(e)
                    ))

                # Think time (simulate user pause)
                time.sleep(self.think_time_ms / 1000)

        finally:
            if self.db:
                self.db.close()

    def _select_operation(self) -> Callable:
        """Select operation based on user pattern."""
        if self.pattern == "read_heavy":
            return random.choice([
                self.read_member_list,
                self.read_member_detail,
                self.search_members,
                self.read_organization_list,
                self.read_student_list,
            ])

        elif self.pattern == "write_heavy":
            return random.choice([
                self.create_member,
                self.update_member,
                self.create_employment,
                self.update_employment,
                self.create_organization_contact,
            ])

        elif self.pattern == "file_operations":
            return random.choice([
                self.list_file_attachments,
                self.create_file_attachment,
                self.read_file_attachment,
            ])

        else:  # mixed pattern
            return random.choice([
                self.read_member_list,
                self.read_member_detail,
                self.search_members,
                self.update_member,
                self.create_employment,
                self.read_organization_list,
                self.create_organization_contact,
                self.list_file_attachments,
            ])

    # === READ OPERATIONS ===

    def read_member_list(self):
        """List members with pagination."""
        skip = random.randint(0, 1000)
        limit = random.randint(10, 100)
        self.db.query(Member).offset(skip).limit(limit).all()

    def read_member_detail(self):
        """Read a single member with employments."""
        # Get random member
        count = self.db.query(func.count(Member.id)).scalar()
        if count == 0:
            return

        random_offset = random.randint(0, count - 1)
        member = self.db.query(Member).offset(random_offset).first()

        if member:
            # Fetch related employments
            self.db.query(MemberEmployment).filter(
                MemberEmployment.member_id == member.id
            ).all()

    def search_members(self):
        """Search members by various criteria."""
        search_type = random.choice(["status", "classification", "name"])

        if search_type == "status":
            status = random.choice(list(MemberStatus))
            self.db.query(Member).filter(Member.status == status).limit(50).all()

        elif search_type == "classification":
            classification = random.choice(list(MemberClassification))
            self.db.query(Member).filter(Member.classification == classification).limit(50).all()

        else:  # name search
            letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            self.db.query(Member).filter(Member.last_name.like(f"{letter}%")).limit(50).all()

    def read_organization_list(self):
        """List organizations with pagination."""
        skip = random.randint(0, 100)
        limit = random.randint(10, 50)
        self.db.query(Organization).offset(skip).limit(limit).all()

    def read_student_list(self):
        """List students with pagination."""
        skip = random.randint(0, 100)
        limit = random.randint(10, 50)
        self.db.query(Student).offset(skip).limit(limit).all()

    # === WRITE OPERATIONS ===

    def create_member(self):
        """Create a new member."""
        member = Member(
            member_number=f"LOAD{self.user_id}_{fake.random_int(min=10000, max=99999)}",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            status=random.choice(list(MemberStatus)),
            classification=random.choice(list(MemberClassification)),
            email=fake.email() if random.random() > 0.3 else None,
            phone=fake.phone_number()[:50] if random.random() > 0.3 else None,
        )
        self.db.add(member)
        self.db.commit()

    def update_member(self):
        """Update an existing member."""
        count = self.db.query(func.count(Member.id)).scalar()
        if count == 0:
            return

        random_offset = random.randint(0, count - 1)
        member = self.db.query(Member).offset(random_offset).first()

        if member:
            # Update a random field
            updates = [
                lambda: setattr(member, 'phone', fake.phone_number()[:50]),
                lambda: setattr(member, 'email', fake.email()),
                lambda: setattr(member, 'notes', fake.sentence()),
            ]
            random.choice(updates)()
            self.db.commit()

    def create_employment(self):
        """Create a new employment record."""
        # Get random member
        member_count = self.db.query(func.count(Member.id)).scalar()
        if member_count == 0:
            return

        member = self.db.query(Member).offset(random.randint(0, member_count - 1)).first()

        # Get random organization
        org_count = self.db.query(func.count(Organization.id)).scalar()
        if org_count == 0:
            return

        org = self.db.query(Organization).offset(random.randint(0, org_count - 1)).first()

        if member and org:
            employment = MemberEmployment(
                member_id=member.id,
                organization_id=org.id,
                start_date=fake.date_between(start_date="-2y", end_date="today"),
                job_title=random.choice(["Electrician", "Journeyman", "Apprentice"]),
                hourly_rate=random.randint(25, 65),
                is_current=random.random() > 0.7
            )
            self.db.add(employment)
            self.db.commit()

    def update_employment(self):
        """Update an existing employment record."""
        count = self.db.query(func.count(MemberEmployment.id)).scalar()
        if count == 0:
            return

        employment = self.db.query(MemberEmployment).offset(random.randint(0, count - 1)).first()

        if employment and employment.is_current:
            # End the current employment
            employment.is_current = False
            employment.end_date = fake.date_between(start_date="-1m", end_date="today")
            self.db.commit()

    def create_organization_contact(self):
        """Create a new organization contact."""
        org_count = self.db.query(func.count(Organization.id)).scalar()
        if org_count == 0:
            return

        org = self.db.query(Organization).offset(random.randint(0, org_count - 1)).first()

        if org:
            contact = OrganizationContact(
                organization_id=org.id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email() if random.random() > 0.2 else None,
                phone=fake.phone_number()[:50] if random.random() > 0.2 else None,
                is_primary=False  # Avoid creating multiple primary contacts
            )
            self.db.add(contact)
            self.db.commit()

    # === FILE OPERATIONS ===

    def list_file_attachments(self):
        """List file attachments for a random record."""
        record_type = random.choice(["member", "student", "organization"])

        self.db.query(FileAttachment).filter(
            FileAttachment.record_type == record_type
        ).limit(20).all()

    def create_file_attachment(self):
        """Create a new file attachment record."""
        # Get random member
        member_count = self.db.query(func.count(Member.id)).scalar()
        if member_count == 0:
            return

        member = self.db.query(Member).offset(random.randint(0, member_count - 1)).first()

        if member:
            attachment = FileAttachment(
                record_type="member",
                record_id=member.id,
                file_name=f"load_test_{fake.uuid4()[:8]}.pdf",
                original_name=f"{fake.word()}.pdf",
                file_path=f"uploads/member/load_test/{fake.uuid4()}.pdf",
                file_type="application/pdf",
                file_size=random.randint(100000, 5000000),
                description="Load test file attachment"
            )
            self.db.add(attachment)
            self.db.commit()

    def read_file_attachment(self):
        """Read a file attachment record."""
        count = self.db.query(func.count(FileAttachment.id)).scalar()
        if count == 0:
            return

        self.db.query(FileAttachment).offset(random.randint(0, count - 1)).first()


class LoadTest:
    """Orchestrates load testing with multiple concurrent users."""

    def __init__(
        self,
        num_users: int = 50,
        operations_per_user: int = 50,
        think_time_ms: int = 100,
        ramp_up_seconds: int = 10
    ):
        self.num_users = num_users
        self.operations_per_user = operations_per_user
        self.think_time_ms = think_time_ms
        self.ramp_up_seconds = ramp_up_seconds
        self.users: List[LoadTestUser] = []
        self.threads: List[threading.Thread] = []
        self.start_time: datetime = None
        self.end_time: datetime = None

    def run(self, pattern_distribution: Dict[str, float] = None):
        """
        Run the load test.

        Args:
            pattern_distribution: Distribution of user patterns
                Example: {"read_heavy": 0.6, "write_heavy": 0.2, "mixed": 0.2}
        """
        if pattern_distribution is None:
            pattern_distribution = {
                "read_heavy": 0.5,      # 50% read-heavy users
                "write_heavy": 0.2,     # 20% write-heavy users
                "mixed": 0.25,          # 25% mixed users
                "file_operations": 0.05 # 5% file operations
            }

        print(f"🚀 Starting Load Test")
        print(f"   Users: {self.num_users}")
        print(f"   Operations per user: {self.operations_per_user}")
        print(f"   Total operations: {self.num_users * self.operations_per_user:,}")
        print(f"   Think time: {self.think_time_ms}ms")
        print(f"   Ramp-up: {self.ramp_up_seconds}s")
        print()

        # Create users with distributed patterns
        patterns = list(pattern_distribution.keys())
        weights = list(pattern_distribution.values())

        for i in range(self.num_users):
            pattern = random.choices(patterns, weights=weights)[0]
            user = LoadTestUser(
                user_id=i + 1,
                pattern=pattern,
                operations_count=self.operations_per_user,
                think_time_ms=self.think_time_ms
            )
            self.users.append(user)

        # Start users with ramp-up
        self.start_time = datetime.now()
        ramp_up_delay = self.ramp_up_seconds / self.num_users if self.num_users > 0 else 0

        print(f"⏱️  Ramping up {self.num_users} users over {self.ramp_up_seconds}s...")

        for i, user in enumerate(self.users):
            thread = threading.Thread(target=user.run, name=f"User-{user.user_id}")
            self.threads.append(thread)
            thread.start()

            # Ramp-up delay
            if i < self.num_users - 1:
                time.sleep(ramp_up_delay)

            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"   Started {i + 1}/{self.num_users} users...")

        print(f"✅ All {self.num_users} users started")
        print(f"⏳ Running load test (this will take a few minutes)...")
        print()

        # Wait for all threads to complete
        for thread in self.threads:
            thread.join()

        self.end_time = datetime.now()

        print(f"✅ Load test complete!")
        print()

    def generate_report(self) -> str:
        """Generate a comprehensive report of test results."""
        if not self.start_time or not self.end_time:
            return "No test results available"

        # Collect all metrics
        all_operations = []
        for user in self.users:
            all_operations.extend(user.metrics.operations)

        total_ops = len(all_operations)
        successful_ops = sum(1 for op in all_operations if op.success)
        failed_ops = total_ops - successful_ops

        # Calculate statistics
        response_times = [op.duration_ms for op in all_operations if op.success]

        if not response_times:
            return "No successful operations recorded"

        avg_response = statistics.mean(response_times)
        median_response = statistics.median(response_times)
        p95_response = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        min_response = min(response_times)
        max_response = max(response_times)

        # Calculate throughput
        duration = (self.end_time - self.start_time).total_seconds()
        throughput_ops_per_sec = total_ops / duration if duration > 0 else 0

        # Operation breakdown
        op_counts = defaultdict(int)
        op_times = defaultdict(list)
        for op in all_operations:
            op_counts[op.operation] += 1
            if op.success:
                op_times[op.operation].append(op.duration_ms)

        # User pattern breakdown
        pattern_counts = defaultdict(int)
        for user in self.users:
            pattern_counts[user.pattern] += 1

        # Generate report
        report = []
        report.append("=" * 70)
        report.append("📊 LOAD TEST REPORT")
        report.append("=" * 70)
        report.append("")

        # Test Configuration
        report.append("⚙️  Test Configuration:")
        report.append(f"   Concurrent Users: {self.num_users}")
        report.append(f"   Operations per User: {self.operations_per_user}")
        report.append(f"   Think Time: {self.think_time_ms}ms")
        report.append(f"   Ramp-up Time: {self.ramp_up_seconds}s")
        report.append(f"   Test Duration: {duration:.2f}s")
        report.append("")

        # User Patterns
        report.append("👥 User Pattern Distribution:")
        for pattern, count in sorted(pattern_counts.items()):
            percentage = (count / self.num_users) * 100
            report.append(f"   {pattern}: {count} users ({percentage:.1f}%)")
        report.append("")

        # Overall Results
        report.append("📈 Overall Results:")
        report.append(f"   Total Operations: {total_ops:,}")
        report.append(f"   Successful: {successful_ops:,} ({(successful_ops/total_ops)*100:.2f}%)")
        report.append(f"   Failed: {failed_ops:,} ({(failed_ops/total_ops)*100:.2f}%)")
        report.append(f"   Throughput: {throughput_ops_per_sec:.2f} ops/sec")
        report.append("")

        # Response Times
        report.append("⏱️  Response Times (ms):")
        report.append(f"   Average: {avg_response:.2f}ms")
        report.append(f"   Median: {median_response:.2f}ms")
        report.append(f"   95th Percentile: {p95_response:.2f}ms")
        report.append(f"   99th Percentile: {p99_response:.2f}ms")
        report.append(f"   Min: {min_response:.2f}ms")
        report.append(f"   Max: {max_response:.2f}ms")
        report.append("")

        # Operation Breakdown
        report.append("🔍 Operation Breakdown:")
        for op_name, count in sorted(op_counts.items(), key=lambda x: x[1], reverse=True):
            if op_name in op_times and op_times[op_name]:
                avg_time = statistics.mean(op_times[op_name])
                report.append(f"   {op_name}: {count} ops, avg {avg_time:.2f}ms")
        report.append("")

        # Performance Assessment
        report.append("🎯 Performance Assessment:")
        if avg_response < 100:
            report.append("   ✅ Excellent: Average response time < 100ms")
        elif avg_response < 500:
            report.append("   ✅ Good: Average response time < 500ms")
        elif avg_response < 1000:
            report.append("   ⚠️  Fair: Average response time < 1000ms")
        else:
            report.append("   ❌ Poor: Average response time > 1000ms")

        if failed_ops == 0:
            report.append("   ✅ No failed operations")
        elif failed_ops < total_ops * 0.01:
            report.append(f"   ⚠️  Low failure rate: {(failed_ops/total_ops)*100:.2f}%")
        else:
            report.append(f"   ❌ High failure rate: {(failed_ops/total_ops)*100:.2f}%")

        if throughput_ops_per_sec > 100:
            report.append(f"   ✅ High throughput: {throughput_ops_per_sec:.2f} ops/sec")
        elif throughput_ops_per_sec > 50:
            report.append(f"   ✅ Good throughput: {throughput_ops_per_sec:.2f} ops/sec")
        else:
            report.append(f"   ⚠️  Low throughput: {throughput_ops_per_sec:.2f} ops/sec")

        report.append("")

        # Scaling Recommendations
        report.append("📊 Scaling to 4000 Users:")
        concurrent_capacity = self.num_users * (100 / max(avg_response, 1))
        estimated_4000_response = (4000 / concurrent_capacity) * avg_response if concurrent_capacity > 0 else float('inf')

        report.append(f"   Current capacity: ~{int(concurrent_capacity)} concurrent users")
        report.append(f"   Estimated response time at 4000 users: {estimated_4000_response:.0f}ms")

        if estimated_4000_response < 500:
            report.append("   ✅ System should handle 4000 users well")
        elif estimated_4000_response < 2000:
            report.append("   ⚠️  System may handle 4000 users with degraded performance")
            report.append("   💡 Recommendation: Add read replicas, optimize queries")
        else:
            report.append("   ❌ System will struggle with 4000 users")
            report.append("   💡 Recommendation: Horizontal scaling, caching, connection pooling")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)
