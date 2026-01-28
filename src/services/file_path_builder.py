"""
File path builder for organized file storage.

Generates human-readable, collision-proof paths like:
    uploads/members/Smith_John_M7464416/grievances/2026/01-January/document.pdf

Path structure:
    uploads/{entity_type}/{owner_folder}/{category}/{year}/{MM-MonthName}/{filename}

Design decisions:
- Member number (or entity ID) in folder name prevents collisions
- Name prefix makes folders human-browsable without DB lookup
- Category subfolder groups files by business domain
- Year/month provides chronological organization
- Original filename preserved (sanitized) for recognition
"""

import os
import re
import unicodedata
from datetime import date, datetime

# Month names for folder labels
MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

UPLOAD_ROOT = "/app/uploads"

# Valid file categories by entity type
FILE_CATEGORIES = {
    "member": [
        "grievances",
        "benevolence",
        "salting",
        "dues",
        "employment",
        "certifications",
        "discipline",
        "correspondence",
        "general",
    ],
    "student": [
        "certifications",
        "applications",
        "progress",
        "attendance",
        "correspondence",
        "general",
    ],
    "organization": [
        "contracts",
        "correspondence",
        "salting",
        "grievances",
        "general",
    ],
    "grievance": [
        "statements",
        "evidence",
        "correspondence",
        "settlement",
        "general",
    ],
    "benevolence": [
        "applications",
        "supporting_docs",
        "correspondence",
        "general",
    ],
}

# Default category when none specified
DEFAULT_CATEGORY = "general"


def sanitize_name(name: str) -> str:
    """Sanitize a name for use in file paths.

    Handles unicode, special characters, spaces.
    Examples:
        "O'Brien" -> "OBrien"
        "Smith-Jones" -> "Smith-Jones"
        "María" -> "Maria"
        "Jean Claude" -> "Jean_Claude"
    """
    # Normalize unicode (é -> e, ñ -> n, etc.)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Keep only alphanumeric, underscore, hyphen
    name = re.sub(r"[^a-zA-Z0-9_\-]", "", name)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def build_owner_folder(
    entity_type: str,
    entity_id: str | int,
    last_name: str | None = None,
    first_name: str | None = None,
    entity_name: str | None = None,
) -> str:
    """Build the owner folder name.

    Members:       Smith_John_M7464416
    Students:      Doe_Jane_STU001
    Organizations: IBEW_Local_46_ORG042
    """
    if last_name and first_name:
        safe_last = sanitize_name(last_name)
        safe_first = sanitize_name(first_name)
        return f"{safe_last}_{safe_first}_{entity_id}"
    elif entity_name:
        safe_name = sanitize_name(entity_name)
        # Truncate long org names to keep paths reasonable
        if len(safe_name) > 40:
            safe_name = safe_name[:40].rstrip("_")
        return f"{safe_name}_{entity_id}"
    else:
        return str(entity_id)


def build_month_folder(ref_date: date | datetime | None = None) -> str:
    """Build month folder like '01-January'.

    Uses provided date or defaults to today.
    """
    if ref_date is None:
        ref_date = date.today()
    if isinstance(ref_date, datetime):
        ref_date = ref_date.date()
    month_num = ref_date.month
    return f"{month_num:02d}-{MONTH_NAMES[month_num]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename, preserving extension.

    "My Document (v2).pdf" -> "My_Document_v2.pdf"
    """
    name, ext = os.path.splitext(filename)
    safe_name = re.sub(r"[^a-zA-Z0-9_\-.]", "_", name)
    safe_name = re.sub(r"_+", "_", safe_name)
    safe_name = safe_name.strip("_")
    if not safe_name:
        safe_name = "file"
    return f"{safe_name}{ext.lower()}"


def build_file_path(
    entity_type: str,
    entity_id: str | int,
    filename: str,
    category: str | None = None,
    ref_date: date | datetime | None = None,
    last_name: str | None = None,
    first_name: str | None = None,
    entity_name: str | None = None,
) -> str:
    """Build the full organized file path.

    Args:
        entity_type: 'member', 'student', 'organization', etc.
        entity_id: Unique identifier (member_number, student ID, org ID)
        filename: Original filename
        category: Business category ('grievances', 'benevolence', etc.)
        ref_date: Date for year/month folder (defaults to today)
        last_name: Person's last name (for members/students)
        first_name: Person's first name (for members/students)
        entity_name: Entity name (for organizations)

    Returns:
        Full path like: /app/uploads/members/Smith_John_M7464416/grievances/2026/01-January/document.pdf
    """
    # Pluralize entity type for top-level folder
    type_folder = entity_type + "s" if not entity_type.endswith("s") else entity_type

    # Build owner folder
    owner = build_owner_folder(
        entity_type, entity_id,
        last_name=last_name,
        first_name=first_name,
        entity_name=entity_name,
    )

    # Validate and default category
    valid_categories = FILE_CATEGORIES.get(entity_type, [DEFAULT_CATEGORY])
    if category and category in valid_categories:
        cat_folder = category
    else:
        cat_folder = DEFAULT_CATEGORY

    # Date folders
    if ref_date is None:
        ref_date = date.today()
    if isinstance(ref_date, datetime):
        ref_date = ref_date.date()
    year_folder = str(ref_date.year)
    month_folder = build_month_folder(ref_date)

    # Sanitize filename
    safe_filename = sanitize_filename(filename)

    return os.path.join(
        UPLOAD_ROOT, type_folder, owner, cat_folder,
        year_folder, month_folder, safe_filename,
    )


def get_valid_categories(entity_type: str) -> list[str]:
    """Return valid file categories for an entity type."""
    return FILE_CATEGORIES.get(entity_type, [DEFAULT_CATEGORY])
