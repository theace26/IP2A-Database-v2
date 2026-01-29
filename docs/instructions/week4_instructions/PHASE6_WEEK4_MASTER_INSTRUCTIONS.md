# Phase 6 Week 4: Training Landing Page

**Created:** January 29, 2026
**Estimated Time:** 6-8 hours (3 sessions)
**Prerequisites:** Week 3 complete (Staff Management, 205 tests)

---

## Overview

Week 4 builds the Training module landing page with student management and course enrollment:

| Session | Focus | Time |
|---------|-------|------|
| A | Training overview + stats dashboard | 2-3 hrs |
| B | Student list with status indicators | 2-3 hrs |
| C | Course list + enrollment actions | 2-3 hrs |

---

## Week 4 Objectives

### Must Have (MVP)
- [ ] Training overview page with stats cards
- [ ] Student list with search and filters
- [ ] Student status indicators (active, graduated, dropped, etc.)
- [ ] Course list with enrollment counts
- [ ] Quick enrollment modal
- [ ] HTMX-powered dynamic updates
- [ ] 15+ new tests

### Nice to Have
- [ ] Student detail page
- [ ] Course detail page
- [ ] Attendance quick-entry
- [ ] Grade summary view

---

## Architecture Overview

### Page Structure

```
/training                    → Training overview (main landing)
/training/students           → Student list page
/training/students/search    → HTMX partial (table body)
/training/students/{id}      → Student detail page
/training/courses            → Course list page
/training/courses/{id}       → Course detail page
/training/enroll             → POST enrollment action
```

### Component Hierarchy

```
templates/
└── training/
    ├── index.html              # Training overview/landing
    ├── students/
    │   ├── index.html          # Student list
    │   ├── detail.html         # Student detail (nice to have)
    │   └── partials/
    │       ├── _table.html     # Student table
    │       ├── _row.html       # Single student row
    │       └── _filters.html   # Filter controls
    └── courses/
        ├── index.html          # Course list
        └── partials/
            ├── _card.html      # Course card
            └── _enroll_modal.html  # Enrollment modal
```

### New Files Summary

| File | Purpose |
|------|---------|
| `src/services/training_frontend_service.py` | Training stats, student/course queries |
| `src/routers/training_frontend.py` | Training page routes |
| `src/templates/training/index.html` | Training landing page |
| `src/templates/training/students/*.html` | Student pages |
| `src/templates/training/courses/*.html` | Course pages |
| `src/tests/test_training_frontend.py` | Training frontend tests |

---

## Data Model Reference

### Student Model (from Phase 2)

```python
class Student(Base):
    __tablename__ = "students"

    id: int
    student_number: str           # Auto-generated (e.g., "STU-2026-0001")
    first_name: str
    last_name: str
    email: str
    phone: str | None
    date_of_birth: date | None
    status: StudentStatus         # active, graduated, dropped, suspended, on_leave
    cohort_id: int | None         # FK to Cohort
    member_id: int | None         # FK to Member (if linked)
    enrollment_date: date
    expected_graduation: date | None
    actual_graduation: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # Relationships
    cohort: Cohort | None
    member: Member | None
    enrollments: list[Enrollment]
    grades: list[Grade]
    certifications: list[Certification]
```

### StudentStatus Enum

```python
class StudentStatus(str, Enum):
    ACTIVE = "active"
    GRADUATED = "graduated"
    DROPPED = "dropped"
    SUSPENDED = "suspended"
    ON_LEAVE = "on_leave"
```

### Course Model

```python
class Course(Base):
    __tablename__ = "courses"

    id: int
    code: str                     # e.g., "ELEC101"
    name: str
    description: str | None
    credits: int
    hours: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    # Relationships
    sessions: list[ClassSession]
    enrollments: list[Enrollment]
```

### Enrollment Model

```python
class Enrollment(Base):
    __tablename__ = "enrollments"

    id: int
    student_id: int               # FK to Student
    course_id: int                # FK to Course
    session_id: int | None        # FK to ClassSession
    status: EnrollmentStatus      # enrolled, completed, dropped, failed
    enrolled_at: datetime
    completed_at: datetime | None
    grade: str | None             # Final grade (A, B, C, etc.)

    # Relationships
    student: Student
    course: Course
    session: ClassSession | None
```

### EnrollmentStatus Enum

```python
class EnrollmentStatus(str, Enum):
    ENROLLED = "enrolled"
    COMPLETED = "completed"
    DROPPED = "dropped"
    FAILED = "failed"
```

---

## HTMX Patterns (Same as Week 3)

### Live Search
```html
<input
    type="search"
    name="q"
    hx-get="/training/students/search"
    hx-trigger="input changed delay:300ms, search"
    hx-target="#student-table-body"
    hx-include="[name='status'], [name='cohort']"
/>
```

### Enrollment Modal
```html
<button
    hx-get="/training/courses/{{ course.id }}/enroll"
    hx-target="#modal-content"
    hx-swap="innerHTML"
    onclick="document.getElementById('enroll-modal').showModal()"
>
    Enroll Student
</button>
```

---

## Session Breakdown

### Session A: Training Overview (Document 1)
1. Create `training_frontend_service.py` with stats queries
2. Create `training_frontend.py` router
3. Create `training/index.html` landing page
4. Stats cards: total students, active, courses, enrollments
5. Quick links to student/course lists
6. Recent activity section

### Session B: Student List (Document 2)
1. Create `training/students/index.html` list page
2. Create student table partials
3. Search by name, student number, email
4. Filter by status and cohort
5. Status badges with colors
6. Pagination component
7. Link to student detail

### Session C: Course List + Enrollment (Document 3)
1. Create `training/courses/index.html` list page
2. Create course card component
3. Show enrollment counts per course
4. Create enrollment modal
5. POST endpoint for enrollment
6. Comprehensive tests (15+)
7. Update documentation

---

## Success Criteria

Week 4 is complete when:
- [ ] Training landing shows real stats
- [ ] Student list displays with search/filter
- [ ] Student status badges show correctly
- [ ] Course list shows enrollment counts
- [ ] Enrollment modal works
- [ ] All actions use HTMX (no page reloads)
- [ ] All tests pass (220+ total)
- [ ] Browser testing confirms full flow

---

## Quick Reference

### DaisyUI Stats Cards
```html
<div class="stats shadow">
    <div class="stat">
        <div class="stat-figure text-primary">
            <svg>...</svg>
        </div>
        <div class="stat-title">Total Students</div>
        <div class="stat-value text-primary">42</div>
        <div class="stat-desc">↗︎ 5 this month</div>
    </div>
</div>
```

### DaisyUI Status Badge
```html
<span class="badge badge-success">Active</span>
<span class="badge badge-warning">On Leave</span>
<span class="badge badge-error">Dropped</span>
<span class="badge badge-info">Graduated</span>
```

### DaisyUI Card for Courses
```html
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">ELEC101</h2>
        <p>Basic Electrical Theory</p>
        <div class="card-actions justify-end">
            <button class="btn btn-primary btn-sm">View</button>
            <button class="btn btn-outline btn-sm">Enroll</button>
        </div>
    </div>
</div>
```

---

## Relationship to Existing Code

### Existing Training API Routers
The backend already has these routers (from Phase 2):
- `src/routers/students.py` - Student CRUD API
- `src/routers/courses.py` - Course CRUD API
- `src/routers/enrollments.py` - Enrollment API
- `src/routers/attendance.py` - Attendance API
- `src/routers/grades.py` - Grades API

Week 4 creates **frontend pages** that may call these APIs or query directly.

### Existing Services
Check if these exist and can be reused:
- `src/services/student_service.py`
- `src/services/course_service.py`
- `src/services/enrollment_service.py`

If not, create `training_frontend_service.py` to consolidate training queries.

---

*Proceed to Document 1 (Session A) to begin implementation.*
