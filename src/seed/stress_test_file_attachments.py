"""Stress test seed for file attachments - realistic file sizes and types."""

from sqlalchemy.orm import Session
from faker import Faker
import random

from src.models.file_attachment import FileAttachment
from src.models.member import Member
from src.models.student import Student
from src.models.organization import Organization
from .base_seed import add_records

fake = Faker()


# File type configurations with realistic size ranges (in bytes)
FILE_TYPES = {
    # Photos (12MP camera: ~3-5 MB)
    "photo_id": {
        "extensions": [".jpg", ".jpeg"],
        "mime": "image/jpeg",
        "size_range": (2_500_000, 5_500_000),  # 2.5-5.5 MB
        "descriptions": [
            "Member ID photo",
            "Profile picture",
            "Identification document",
            "Headshot",
        ],
    },
    "photo_worksite": {
        "extensions": [".jpg", ".jpeg", ".png"],
        "mime": "image/jpeg",
        "size_range": (2_000_000, 6_000_000),  # 2-6 MB
        "descriptions": [
            "Worksite photo",
            "Job site documentation",
            "Project photo",
            "Work in progress",
            "Completed work",
        ],
    },
    # PDFs - Reports (0.5-5 MB)
    "pdf_report": {
        "extensions": [".pdf"],
        "mime": "application/pdf",
        "size_range": (500_000, 5_000_000),  # 0.5-5 MB
        "descriptions": [
            "Training completion certificate",
            "Safety certification",
            "Course completion report",
            "Inspection report",
            "Project report",
        ],
    },
    # PDFs - Scanned documents (0.2-2 MB)
    "pdf_scan": {
        "extensions": [".pdf"],
        "mime": "application/pdf",
        "size_range": (200_000, 2_000_000),  # 0.2-2 MB
        "descriptions": [
            "Scanned license",
            "Scanned certification",
            "Signed agreement",
            "Scanned application",
            "Membership form",
            "W-4 form",
            "Direct deposit form",
        ],
    },
    # PDFs - Forms (50-500 KB)
    "pdf_form": {
        "extensions": [".pdf"],
        "mime": "application/pdf",
        "size_range": (50_000, 500_000),  # 50-500 KB
        "descriptions": [
            "Membership application",
            "Benefits enrollment",
            "Tax form",
            "Emergency contact form",
            "Direct deposit authorization",
        ],
    },
    # Office documents (100 KB - 2 MB)
    "doc_word": {
        "extensions": [".docx", ".doc"],
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "size_range": (100_000, 2_000_000),  # 100 KB - 2 MB
        "descriptions": [
            "Resume",
            "Cover letter",
            "Work history",
            "Reference letter",
            "Performance review",
        ],
    },
    # Spreadsheets (50 KB - 1 MB)
    "doc_excel": {
        "extensions": [".xlsx", ".xls"],
        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "size_range": (50_000, 1_000_000),  # 50 KB - 1 MB
        "descriptions": [
            "Hours log",
            "Expense report",
            "Equipment inventory",
            "Time sheet",
        ],
    },
    # Small images (100 KB - 1 MB)
    "image_small": {
        "extensions": [".png", ".jpg"],
        "mime": "image/png",
        "size_range": (100_000, 1_000_000),  # 100 KB - 1 MB
        "descriptions": [
            "Signature scan",
            "Badge photo",
            "Document snippet",
            "Logo",
        ],
    },
}

# Grievance-specific files (can be any type, but more documents)
GRIEVANCE_FILE_TYPES = {
    "grievance_statement": {
        "extensions": [".pdf"],
        "mime": "application/pdf",
        "size_range": (200_000, 1_500_000),
        "descriptions": [
            "Grievance statement",
            "Witness statement",
            "Written complaint",
            "Union response",
        ],
    },
    "grievance_evidence": {
        "extensions": [".jpg", ".pdf", ".png"],
        "mime": "image/jpeg",
        "size_range": (500_000, 4_000_000),
        "descriptions": [
            "Evidence photo",
            "Email correspondence",
            "Time card copy",
            "Contract excerpt",
        ],
    },
    "grievance_doc": {
        "extensions": [".docx", ".pdf"],
        "mime": "application/pdf",
        "size_range": (100_000, 2_000_000),
        "descriptions": [
            "Meeting notes",
            "Resolution document",
            "Management response",
            "Union filing",
        ],
    },
}


def generate_file_attachment(
    record_type: str, record_id: int, file_category: str = None
):
    """Generate a single realistic file attachment."""

    # Choose file type category
    if file_category:
        file_config = FILE_TYPES.get(file_category) or GRIEVANCE_FILE_TYPES.get(
            file_category
        )
    else:
        file_config = random.choice(list(FILE_TYPES.values()))

    # Generate file metadata
    extension = random.choice(file_config["extensions"])
    file_size = random.randint(*file_config["size_range"])
    description = random.choice(file_config["descriptions"])

    # Generate realistic file path
    year = random.randint(2015, 2026)
    month = random.randint(1, 12)
    file_hash = fake.uuid4()[:16]
    original_name = f"{fake.word()}_{fake.word()}{extension}"
    file_path = f"uploads/{record_type}/{year}/{month:02d}/{file_hash}{extension}"

    return FileAttachment(
        record_type=record_type,
        record_id=record_id,
        file_name=f"{file_hash}{extension}",
        original_name=original_name,
        file_path=file_path,
        file_type=file_config["mime"],
        file_size=file_size,
        description=description,
    )


def stress_test_file_attachments(db: Session):
    """
    Generate file attachments for all entities.

    - Members: 1-20 documents each (certifications, IDs, forms, photos) - per user requirement
    - Students: 5-15 documents each (applications, photos, forms)
    - Organizations: 2-10 documents each (contracts, licenses)
    - Grievances: 1-50 files each (statements, evidence, correspondence)
    """

    # Get all entities
    members = db.query(Member).all()
    students = db.query(Student).all()
    organizations = db.query(Organization).all()

    if not members and not students and not organizations:
        print("   ⚠️  No entities found for file attachments")
        return []

    attachments = []
    total_size_bytes = 0
    member_file_count = 0
    student_file_count = 0
    org_file_count = 0

    print("   Generating file attachments for entities...")
    print("   This will take several minutes...")

    # === MEMBERS: 1-20 documents each ===
    if members:
        print(f"   Processing {len(members)} members (1-20 files each)...")

        for idx, member in enumerate(members):
            # Minimum 1 file, maximum 20 per member (user requirement)
            num_files = random.randint(1, 20)

            member_files = []

            # Common file types for members (weighted selection)
            common_types = [
                "photo_id",  # ID photo
                "pdf_scan",  # Scanned license
                "pdf_form",  # Membership form
                "pdf_report",  # Training certificate
                "doc_word",  # Resume or application
            ]

            # For members with fewer files, prioritize common types
            # For members with more files, add variety
            for file_idx in range(num_files):
                if file_idx < len(common_types) and file_idx < 5:
                    # First few files are common required types
                    file_type = common_types[file_idx]
                else:
                    # Additional files are random
                    file_type = random.choice(list(FILE_TYPES.keys()))
                attachment = generate_file_attachment("member", member.id, file_type)
                member_files.append(attachment)
                total_size_bytes += attachment.file_size

            attachments.extend(member_files)
            member_file_count += len(member_files)

            # Progress indicator
            if (idx + 1) % 1000 == 0:
                print(f"      {idx + 1}/{len(members)} members processed...")

        print(
            f"   ✅ Generated {member_file_count:,} files for members (avg {member_file_count / len(members):.1f} per member)"
        )

    # === STUDENTS: 5-15 documents each ===
    if students:
        print(f"   Processing {len(students)} students (5-15 files each)...")

        for student in students:
            num_files = random.randint(5, 15)

            for _ in range(num_files):
                # Students get mostly forms, photos, and reports
                file_type = random.choice(
                    [
                        "photo_id",
                        "pdf_form",
                        "pdf_scan",
                        "pdf_report",
                        "doc_word",
                        "image_small",
                    ]
                )
                attachment = generate_file_attachment("student", student.id, file_type)
                attachments.append(attachment)
                student_file_count += 1
                total_size_bytes += attachment.file_size

        print(
            f"   ✅ Generated {student_file_count:,} files for students (avg {student_file_count / len(students):.1f} per student)"
        )

    # === ORGANIZATIONS: 2-10 documents each ===
    if organizations:
        print(f"   Processing {len(organizations)} organizations (2-10 files each)...")

        for org in organizations:
            num_files = random.randint(2, 10)

            for _ in range(num_files):
                # Organizations get contracts, licenses, reports
                file_type = random.choice(
                    ["pdf_scan", "pdf_report", "doc_word", "doc_excel", "image_small"]
                )
                attachment = generate_file_attachment("organization", org.id, file_type)
                attachments.append(attachment)
                org_file_count += 1
                total_size_bytes += attachment.file_size

        print(
            f"   ✅ Generated {org_file_count:,} files for organizations (avg {org_file_count / len(organizations):.1f} per org)"
        )

    # === GRIEVANCES: 1-50 files each (simulate some grievances) ===
    # Note: We'll create grievance files even without a grievance table yet
    # This simulates future grievance functionality
    num_grievances = random.randint(50, 200)
    print(f"   Generating {num_grievances} simulated grievances (1-50 files each)...")

    for grievance_id in range(1, num_grievances + 1):
        # Most grievances have 5-15 files, but some have up to 50
        if random.random() < 0.1:  # 10% chance
            num_files = random.randint(20, 50)
        else:
            num_files = random.randint(1, 20)

        for _ in range(num_files):
            file_type = random.choice(list(GRIEVANCE_FILE_TYPES.keys()))
            attachment = generate_file_attachment("grievance", grievance_id, file_type)
            attachments.append(attachment)
            total_size_bytes += attachment.file_size

    print("   ✅ Generated grievance files")

    # Add all attachments to database
    print(f"   Adding {len(attachments):,} file attachments to database...")
    print(f"   Total simulated file size: {total_size_bytes / (1024**3):.2f} GB")

    add_records(db, attachments, batch_size=1000)

    print(f"   ✅ Seeded {len(attachments):,} file attachments")
    print("   📊 Storage breakdown:")
    print(f"      • Members: {member_file_count:,} files (1-20 per member)")
    print(f"      • Students: {student_file_count:,} files")
    print(f"      • Organizations: {org_file_count:,} files")
    print("      • Grievances: varies (1-50 per grievance)")
    print(f"      • Total size: {total_size_bytes / (1024**3):.2f} GB")

    return attachments
