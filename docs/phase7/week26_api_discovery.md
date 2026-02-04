# Week 26 API Discovery Notes

**Created:** February 4, 2026
**Purpose:** Document backend API contract for frontend implementation

---

## Referral Books Endpoints

| Method | Path | Purpose | Auth Required | Response |
|--------|------|---------|---------------|----------|
| GET | `/api/v1/referral/books` | List all books with filters | StaffUser | List[ReferralBookRead] |
| GET | `/api/v1/referral/books/summary` | All books with registration counts | StaffUser | List[dict] with stats |
| GET | `/api/v1/referral/books/classification-summary` | Cross-book summary by classification | StaffUser | dict |
| GET | `/api/v1/referral/books/{book_id}` | Get book detail | StaffUser | ReferralBookRead |
| GET | `/api/v1/referral/books/{book_id}/queue` | Get out-of-work queue (FIFO by APN) | StaffUser | List[QueuePosition] |
| GET | `/api/v1/referral/books/{book_id}/stats` | Registration statistics | StaffUser | ReferralBookStats |
| GET | `/api/v1/referral/books/{book_id}/depth` | Queue depth analytics | StaffUser | dict |
| GET | `/api/v1/referral/books/{book_id}/utilization` | Utilization statistics | StaffUser | dict |
| POST | `/api/v1/referral/books` | Create new book | AdminUser | ReferralBookRead |
| PUT | `/api/v1/referral/books/{book_id}` | Update book | AdminUser | ReferralBookRead |
| PATCH | `/api/v1/referral/books/{book_id}/activate` | Activate book | AdminUser | ReferralBookRead |
| PATCH | `/api/v1/referral/books/{book_id}/deactivate` | Deactivate book | AdminUser | ReferralBookRead |

### Query Parameters for List Books
- `classification` (optional): Filter by BookClassification enum
- `region` (optional): Filter by BookRegion enum
- `active_only` (default: true): Show only active books

---

## Registration Endpoints

| Method | Path | Purpose | Auth Required | Response |
|--------|------|---------|---------------|----------|
| POST | `/api/v1/referral/registrations` | Register member on book | get_current_user | BookRegistration |
| GET | `/api/v1/referral/registrations/{id}` | Get registration detail | StaffUser | BookRegistration |
| POST | `/api/v1/referral/registrations/{id}/re-sign` | Re-sign for 30-day cycle | get_current_user | BookRegistration |
| POST | `/api/v1/referral/registrations/{id}/resign` | Voluntary resignation | get_current_user | BookRegistration |
| POST | `/api/v1/referral/registrations/{id}/roll-off` | Staff rolls member off | get_current_user | BookRegistration |
| POST | `/api/v1/referral/registrations/{id}/exempt` | Grant exempt status | get_current_user | BookRegistration |
| DELETE | `/api/v1/referral/registrations/{id}/exempt` | Revoke exempt status | get_current_user | BookRegistration |
| POST | `/api/v1/referral/registrations/{id}/check-mark` | Record check mark | get_current_user | BookRegistration |
| GET | `/api/v1/referral/registrations/member/{member_id}` | All registrations for member | StaffUser | List[BookRegistration] |
| GET | `/api/v1/referral/registrations/member/{member_id}/status` | Member queue status all books | StaffUser | List[dict] |
| GET | `/api/v1/referral/registrations/member/{member_id}/wait-time` | Wait time estimates | StaffUser | List[dict] |
| GET | `/api/v1/referral/registrations/expiring` | Registrations approaching re-sign deadline | StaffUser | List[dict] |
| GET | `/api/v1/referral/registrations/reminders` | Re-sign reminder list | StaffUser | List[dict] |

### Query Parameters
- `active_only` (GET member registrations): Default true
- `days` (GET expiring): Days until expiration threshold, default 7
- `reason` (POST resign): Optional resignation reason

---

## Key Business Rules Found

1. **One Active Registration Per Book** — Member can be on multiple books, but only one REGISTERED status per book
2. **APN Assignment** — Automatic sequential assignment (DECIMAL(10,2))
3. **Re-sign Cycle** — Default 30 days, configurable per book
4. **Check Marks** — Max 2 allowed (configurable), 3rd triggers roll-off
5. **Exempt Status** — 7 reasons: military, medical, union_business, salting, jury_duty, training, other
6. **Status Transitions** — REGISTERED → DISPATCHED → (back to REGISTERED or RESIGNED/ROLLED_OFF)
7. **Activity Logging** — Every action creates RegistrationActivity record (audit trail)

---

## Service Methods Available

### ReferralBookService
- `get_by_id(db, book_id)` → ReferralBook | None
- `get_by_code(db, code)` → ReferralBook | None
- `get_all_active(db)` → List[ReferralBook]
- `get_all(db, include_inactive, skip, limit)` → List[ReferralBook]
- `get_by_classification(db, classification)` → List[ReferralBook]
- `get_by_region(db, region)` → List[ReferralBook]
- `get_by_classification_and_region(db, cls, reg)` → List[ReferralBook]
- `get_book_stats(db, book_id)` → ReferralBookStats | None
- `get_all_books_summary(db)` → List[dict] — **KEY METHOD FOR LANDING PAGE**

### BookRegistrationService
- `register_member(db, member_id, book_id, performed_by_id, method, notes)` → BookRegistration
- `re_sign_member(db, registration_id, performed_by_id)` → BookRegistration
- `resign_member(db, registration_id, performed_by_id, reason)` → BookRegistration
- `roll_off_member(db, registration_id, performed_by_id, reason, notes)` → BookRegistration
- `grant_exempt_status(db, registration_id, performed_by_id, reason, end_date, notes)` → BookRegistration
- `revoke_exempt_status(db, registration_id, performed_by_id, reason)` → BookRegistration
- `record_check_mark(db, registration_id, performed_by_id)` → BookRegistration
- `get_by_id(db, registration_id)` → BookRegistration | None
- `get_member_registrations(db, member_id, active_only)` → List[BookRegistration]
- `get_registrations_expiring_soon(db, days_threshold)` → List[dict]
- `get_re_sign_reminders(db)` → List[dict]

### QueueService
- `get_queue_snapshot(db, book_id, include_exempt, limit)` → List[QueuePosition]
- `get_queue_depth(db, book_id)` → dict
- `get_book_utilization(db, book_id, period_days)` → dict
- `get_classification_summary(db)` → dict
- `get_member_queue_status(db, member_id)` → List[dict]
- `estimate_wait_time(db, registration_id)` → dict

---

## Form Fields Required

### Register Member Form
- `member_id` (int, required) — via typeahead search
- `book_id` (int, required) — dropdown select from active books
- `registration_method` (str, optional, default: "in_person") — dropdown: in_person, online, phone, email
- `notes` (str, optional) — textarea

### Re-sign Confirmation
- `registration_id` (int, required) — from context
- No additional fields, simple POST

### Resign Form
- `registration_id` (int, required) — from context
- `reason` (str, optional) — dropdown or textarea

### Exempt Status Form
- `registration_id` (int, required)
- `exempt_reason` (ExemptReason enum, required) — dropdown: military, medical, union_business, salting, jury_duty, training, other
- `exempt_end_date` (date, optional) — date picker
- `notes` (str, optional) — textarea

---

## Pydantic Schemas

### ReferralBookRead
```python
id: int
name: str
code: str
classification: BookClassification
book_number: int (1-3)
region: BookRegion
referral_start_time: Optional[time]
re_sign_days: int (default 30)
max_check_marks: int (default 2)
grace_period_days: Optional[int]
max_days_on_book: Optional[int]
is_active: bool
internet_bidding_enabled: bool
created_at: datetime
updated_at: Optional[datetime]
```

### ReferralBookStats
```python
book_id: int
book_name: str
book_code: str
total_registered: int (all-time)
active_count: int (currently REGISTERED)
dispatched_count: int (currently DISPATCHED)
with_check_mark: int (active with check mark)
without_check_mark: int (active without check mark)
exempt_count: int (currently exempt)
```

### BookRegistrationRead
```python
id: int
member_id: int
book_id: int
registration_number: Decimal (APN)
registration_method: Optional[str]
status: RegistrationStatus
registration_date: datetime
last_re_sign_date: Optional[datetime]
re_sign_deadline: Optional[datetime]
check_marks: int
consecutive_missed_check_marks: int
has_check_mark: bool
last_check_mark_date: Optional[date]
last_check_mark_at: Optional[datetime]
short_call_restorations: int
is_exempt: bool
exempt_reason: Optional[ExemptReason]
exempt_start_date: Optional[date]
exempt_end_date: Optional[date]
roll_off_date: Optional[datetime]
roll_off_reason: Optional[RolloffReason]
notes: Optional[str]
created_at: datetime
updated_at: Optional[datetime]
```

### QueuePosition
```python
registration_id: int
member_id: int
member_name: str
member_number: str
registration_number: Decimal (APN)
position: int (1-indexed queue position)
status: RegistrationStatus
check_marks: int
is_exempt: bool
days_on_book: int
```

---

## Enums Reference

### RegistrationStatus
- REGISTERED — Active on book
- DISPATCHED — Currently working
- RESIGNED — Voluntarily resigned
- ROLLED_OFF — Removed by staff/system
- SUSPENDED — Temporarily suspended
- EXPIRED — Re-sign deadline passed

### ExemptReason
- military
- medical
- union_business
- salting
- jury_duty
- training
- other

### RolloffReason
- MAX_CHECK_MARKS — 3 check marks
- MANUAL — Staff action
- EXPIRED — Failed to re-sign
- DISCIPLINARY — Union discipline
- OTHER

### BookClassification
- inside_wireperson
- sound_comm
- residential
- installer_tech
- vdv_installer
- limited_energy
- traveler
- specialty

### BookRegion
- seattle
- bremerton
- port_angeles
- jurisdiction_wide

---

## Error Handling Patterns

From service layer, these raise `ValueError`:
- Member already registered on book
- Book not active
- Member not found
- Registration not found
- Invalid status transition

API routers catch `ValueError` and return `HTTPException(status_code=400, detail=str(e))`

Frontend should handle 400 responses and display error messages to user.

---

## Frontend Service Strategy

**Pattern from DuesFrontendService:**
1. Wrap backend service calls
2. Format data for templates (add computed fields)
3. Provide badge helper methods for status colors
4. Handle pagination formatting
5. Catch service errors and return user-friendly messages

**Key methods needed:**
- `get_books_overview()` → Call `referral_book_service.get_all_books_summary()`
- `get_book_detail(book_id)` → Combine `get_by_id()` + `get_book_stats()` + queue data
- `get_registrations(filters, page, per_page)` → Build filtered query, paginate
- `register_member(data)` → Wrap service call, return success/error dict
- Badge helpers for: book status, registration status, exempt reason, rolloff reason

**HTMX Patterns:**
- Landing stats: `/referral/partials/stats` → HTMX auto-refresh every 60s
- Books table: `/referral/partials/books-table?status=&search=` → Filter/search
- Registration table: `/referral/partials/registration-table?book_id=&status=&search=` → Filter/search
- Modals: Load forms via `/referral/partials/{action}-modal` → POST back to update tables

---

## Implementation Notes

1. **Direct API Calls** — Frontend service should call backend services directly (both are in same process)
2. **No Async** — All routes and service methods are synchronous (matching existing pattern)
3. **Template Context** — Always include `request` and `current_user` in template context
4. **Badge Colors** — Use DaisyUI badge classes: badge-success, badge-warning, badge-error, badge-info, badge-ghost
5. **HTMX Targets** — Use consistent ID patterns: `#books-table-container`, `#registration-table-container`, `#modal-container`
6. **Pagination** — Follow pattern from existing pages (members, dues): `page` query param, render page links

---

**Discovery Complete** — Ready to implement frontend service and templates
