# Model Field Mapping - demo_seed.py Corrections

**Purpose:** Document all field name mismatches between demo_seed.py and actual models

**Status:** All issues identified, ready for batch fix

## Student Model Issues

### What demo_seed.py tries to use (WRONG):
```python
student_data = {
    "student_number": student_number,
    "first_name": first_name,           # ❌ WRONG - not on Student
    "last_name": last_name,             # ❌ WRONG - not on Student
    "email": email,                     # ❌ WRONG - not on Student
    "phone": phone,                     # ❌ WRONG - not on Student
    "status": status,
    "cohort_id": cohort.id,             # ❌ WRONG - should be cohort (string)
    "enrollment_date": cohort.start_date,
}
```

### Actual Student model fields:
```python
# Required fields
member_id: int                  # FK to members (REQUIRED - provides name/email/phone)
student_number: str             # Unique identifier
status: StudentStatus
application_date: date          # Required

# Optional fields
enrollment_date: date | None
cohort: str | None              # STRING field (e.g., "2026-Spring"), NOT FK
emergency_contact_name: str | None
emergency_contact_phone: str | None
notes: str | None
```

### How Student SHOULD be created:
```python
# Step 1: Create Member first (if not exists)
member_data = {
    "member_number": member_number,
    "first_name": first_name,
    "last_name": last_name,
    "email": email,
    "phone": phone,
    "classification": MemberClassification.APPRENTICE_1ST_YEAR,
    "status": MemberStatus.ACTIVE,
}
member, _ = get_or_create(db, Member, member_number=member_number, defaults=member_data)

# Step 2: Create Student linked to Member
student_data = {
    "member_id": member.id,              # ✅ Link to Member (provides name/email/phone)
    "student_number": student_number,
    "status": status,
    "application_date": cohort.start_date - timedelta(days=30),  # 30 days before enrollment
    "enrollment_date": cohort.start_date,
    "cohort": cohort.code,               # ✅ String field, not FK
}
student, _ = get_or_create(db, Student, student_number=student_number, defaults=student_data)
```

---

## FileAttachment Model Issues

### What demo_seed.py tries to use (WRONG):
```python
attachment_data = {
    "filename": filename,                # ❌ WRONG - should be file_name
    "file_size": file_size,
    "file_type": att_type,              # ⚠️  Should be MIME type, not category
    "uploaded_at": upload_date,         # ❌ WRONG - use created_at from mixin
    "uploaded_by": random.randint(1, 5), # ❌ WRONG - field doesn't exist
    "entity_type": entity_type,         # ❌ WRONG - should be record_type
    "entity_id": entity_id,             # ❌ WRONG - should be record_id
}
```

### Actual FileAttachment model fields:
```python
record_type: str               # ✅ e.g., "member", "student"
record_id: int                 # ✅ FK to the record
file_category: str             # ✅ e.g., "documents", "certifications"
file_name: str                 # ✅ Name of file
file_path: str                 # ✅ Required - path in storage
file_type: str                 # ✅ MIME type (e.g., "application/pdf")
file_size: int | None
created_at: datetime           # ✅ From TimestampMixin (auto-set)
```

### How FileAttachment SHOULD be created:
```python
attachment_data = {
    "record_type": entity_type.lower(),  # ✅ "member" or "student"
    "record_id": entity_id,              # ✅ ID of the member/student
    "file_category": att_type,           # ✅ "documents", "certifications", etc.
    "file_name": filename,
    "file_path": f"/uploads/{entity_type.lower()}s/{entity_id}/{filename}",  # ✅ Required
    "file_type": "application/pdf",      # ✅ MIME type
    "file_size": file_size,
    # created_at is auto-set by TimestampMixin
}
```

---

## Summary of Required Changes

### Student seed function (_seed_demo_students):
1. **Create Member first** with first_name, last_name, email, phone
2. **Link Student to Member** via `member_id`
3. **Use `cohort` as string** (not `cohort_id`)
4. **Add `application_date`** (required field)

### FileAttachment seed function (_seed_demo_attachments):
1. Rename `filename` → `file_name`
2. Rename `entity_type` → `record_type`
3. Rename `entity_id` → `record_id`
4. Add required `file_path` field
5. Remove `uploaded_at` (auto-set via created_at)
6. Remove `uploaded_by` (field doesn't exist)
7. Use MIME type for `file_type` (not category)

---

## Files to Modify

- `src/db/demo_seed.py`:
  - Lines 1012-1024: `_seed_demo_students()` function
  - Lines 1321-1338: `_seed_demo_attachments()` function
