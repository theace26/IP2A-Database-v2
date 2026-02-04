# Week 27 API Discovery Notes

**Created:** February 4, 2026
**Purpose:** Document backend API structure to guide frontend UI development

---

## Labor Request Endpoints

**Prefix:** `/api/v1/referral/requests`

| Method | Path | Purpose | Auth | Query Params |
|--------|------|---------|------|--------------|
| POST | `` | Create new labor request | Staff | - |
| GET | `` | List labor requests | Staff | book_id, employer_id, classification, include_filled |
| GET | `/morning` | Requests for morning referral (Rule 2) | Staff | target_date |
| GET | `/open` | All unfilled requests | Staff | book_id |
| GET | `/employer/{employer_id}` | Request history for employer | Staff | include_filled, limit |
| GET | `/{request_id}` | Get single request detail | Staff | - |
| PUT | `/{request_id}` | Update open request | Staff | - |
| POST | `/{request_id}/cancel` | Cancel request | Staff | reason |
| POST | `/{request_id}/expire` | Mark request as expired | Staff | - |
| GET | `/{request_id}/bidding-status` | Check if bidding open | Staff | - |
| GET | `/{request_id}/check-mark-status` | Check if generates check marks | Staff | - |

---

## Job Bid Endpoints

**Prefix:** `/api/v1/referral/bids`

| Method | Path | Purpose | Auth | Query Params |
|--------|------|---------|------|--------------|
| POST | `` | Place bid on request | User | - |
| GET | `/{bid_id}` | Get bid detail | Staff | - |
| POST | `/{bid_id}/withdraw` | Withdraw pending bid | User | reason |
| POST | `/{bid_id}/accept` | Accept bid (staff) | Staff | - |
| POST | `/{bid_id}/reject` | Reject bid (quit, Rule 8) | Staff | reason |
| GET | `/request/{labor_request_id}` | All bids for request | Staff | status |
| POST | `/request/{labor_request_id}/process` | Process all bids (FIFO) | Staff | - |
| GET | `/member/{member_id}` | Member bid history | Staff | limit, include_all |
| GET | `/member/{member_id}/pending` | Member's pending bids | Staff | - |
| GET | `/member/{member_id}/suspension` | Check suspension status | Staff | - |

---

## Dispatch Endpoints

**Prefix:** `/api/v1/referral`

| Method | Path | Purpose | Auth | Query Params |
|--------|------|---------|------|--------------|
| POST | `/dispatch` | Dispatch from queue (FIFO) | Staff | - |
| POST | `/dispatch/by-name` | Foreperson by-name (Rule 13) | Staff | - |
| GET | `/dispatch/{dispatch_id}` | Get dispatch detail | Staff | - |
| POST | `/dispatch/{dispatch_id}/check-in` | Record member check-in | Staff | - |
| POST | `/dispatch/{dispatch_id}/terminate` | Terminate dispatch (Rule 9,12) | Staff | - |
| GET | `/dispatch/active` | All active dispatches | Staff | book_id, employer_id |
| GET | `/dispatch/member/{member_id}` | Member dispatch history | Staff | limit |
| GET | `/dispatch/book/{book_id}/stats` | Book dispatch statistics | Staff | period_days |

---

## Queue Endpoints

**Prefix:** `/api/v1/referral/queue`

| Method | Path | Purpose | Auth | Query Params |
|--------|------|---------|------|--------------|
| GET | `/{book_id}` | Queue snapshot for book | Staff | include_exempt, limit |
| GET | `/{book_id}/depth` | Queue depth analytics | Staff | - |
| GET | `/{book_id}/dispatch-rate` | Dispatch rate for book | Staff | period (week/month) |
| GET | `/daily-activity` | All queue changes for day | Staff | target_date |

---

## Enforcement Endpoints

**Prefix:** `/api/v1/referral/admin`

| Method | Path | Purpose | Auth | Query Params |
|--------|------|---------|------|--------------|
| POST | `/enforcement/run` | Trigger daily enforcement | Admin | dry_run |
| GET | `/enforcement/preview` | Preview enforcement actions | Staff | - |
| GET | `/enforcement/pending` | Counts of pending enforcements | Staff | - |
| POST | `/enforcement/{enforcement_type}` | Run specific enforcement | Admin | dry_run |
| GET | `/re-sign-reminders` | Re-sign reminders list | Staff | - |

---

## Blackout Endpoints

**Prefix:** `/api/v1/referral`

| Method | Path | Purpose | Auth | Query Params |
|--------|------|---------|------|--------------|
| GET | `/blackout/check` | Check active blackout | Staff | member_id, employer_id |

---

## Business Rules Found in Code

| Rule | Implementation | Service | UI Implications |
|------|---------------|---------|-----------------|
| Rule 2 | Morning referral order by classification | `labor_request_service.get_requests_for_morning()` | Morning referral page shows ordered queue (Wire 8:30 AM → S&C 9:00 AM → Tradeshow 9:30 AM) |
| Rule 3 | 3 PM cutoff for next-morning dispatch | `labor_request_service.is_past_cutoff_for_tomorrow()` | Warning banner after 3 PM, requests go to next day |
| Rule 4 | Agreement type filtering (PLA/CWA/TERO) | `labor_request_service._determine_check_mark()` | Request detail shows agreement type badge, filters candidates |
| Rule 8 | Bidding window (5:30 PM – 7:00 AM) + 2 rejections = 1-year suspension | `job_bid_service.place_bid()`, `job_bid_service.check_suspension_status()` | Bidding window badge, rejection counter, suspension alert |
| Rule 9 | Short call ≤10 days → position restoration | `dispatch_service._process_short_call_end()` | "Short Call" badge, day counter, restore button |
| Rule 11 | Check mark determination (specialty, MOU, early start, etc.) | `labor_request_service.determine_check_mark()` | Check mark icons next to members, no-check-mark reason tooltips |
| Rule 12 | Quit/discharge → roll off ALL books + 2-week blackout | `dispatch_service._process_quit()`, `dispatch_service._process_discharge()` | Blackout section in enforcement, rolloff indicator |
| Rule 13 | By-name anti-collusion enforcement | `dispatch_service.dispatch_by_name()` | Warning banner on flagged requests, anti-collusion verification checkbox |

---

## Enum Values (for dropdowns/badges)

### LaborRequestStatus
- `open` → Badge: info (blue)
- `partially_filled` → Badge: warning (yellow)
- `filled` → Badge: success (green)
- `cancelled` → Badge: error (red)
- `expired` → Badge: ghost (gray)

### BidStatus
- `pending` → Badge: warning (yellow)
- `accepted` → Badge: success (green)
- `rejected` → Badge: error (red)
- `withdrawn` → Badge: ghost (gray)
- `expired` → Badge: ghost (gray)

### DispatchStatus
- `dispatched` → Badge: info (blue)
- `checked_in` → Badge: accent (purple)
- `working` → Badge: success (green)
- `completed` → Badge: info (blue)
- `terminated` → Badge: error (red)
- `rejected` → Badge: error (red)
- `no_show` → Badge: error (red)

### DispatchMethod
- `morning_referral` → Label: "Morning Referral"
- `internet_bid` → Label: "Internet Bid"
- `email_bid` → Label: "Email Bid"
- `in_person` → Label: "In Person"
- `by_name` → Label: "By Name"
- `emergency` → Label: "Emergency"

### TermReason
- `RIF` → Label: "RIF" (standard termination)
- `QUIT` → Label: "Quit" (Rule 12 penalty)
- `FIRED` → Label: "Fired" (Rule 12 penalty)
- `SHORT_CALL_END` → Label: "Short Call End" (Rule 9 restoration)
- `COMPLETED` → Label: "Completed"

### NoCheckMarkReason
- `specialty` → "Specialty skills"
- `mou_jobsite` → "MOU jobsite"
- `early_start` → "Early start (before 6 AM)"
- `under_scale` → "Under scale work"
- `various_location` → "Various location"
- `short_call` → "Short call"
- `employer_rejection` → "Employer rejection"

---

## Time-Sensitive Operations

| Operation | Window | Enforcement | Service Method |
|-----------|--------|-------------|----------------|
| Morning cutoff | 3:00 PM | Requests after 3 PM go to next day | `is_past_cutoff_for_tomorrow()` |
| Bidding opens | 5:30 PM | Members can submit online bids | `validate_bidding_window()` |
| Bidding closes | 7:00 AM | No more bids accepted | `validate_bidding_window()` |
| Morning referral | 8:30 AM – 9:30 AM | Staggered by classification | `get_requests_for_morning()` |
| Check-in deadline | 3:00 PM | Web dispatches must check in | `record_check_in()` |

---

## Key Service Methods for Frontend

### Labor Request Service
- `create_request()` - Create new request
- `get_open_requests()` - List unfilled requests
- `get_requests_for_morning()` - Morning referral queue (Rule 2)
- `get_employer_requests()` - Employer history
- `cancel_request()` - Cancel request
- `determine_check_mark()` - Check if generates check marks (Rule 11)
- `validate_bidding_window()` - Check if bidding open
- `is_past_cutoff_for_tomorrow()` - Check 3 PM cutoff (Rule 3)

### Job Bid Service
- `place_bid()` - Submit bid (Rule 8)
- `get_bids_for_request()` - All bids for request
- `process_bids()` - Auto-process bids in FIFO order
- `check_suspension_status()` - Check member suspension (Rule 8)

### Dispatch Service
- `dispatch_from_queue()` - FIFO dispatch from queue
- `dispatch_by_name()` - Foreperson by-name (Rule 13)
- `terminate_dispatch()` - Terminate with reason (Rules 9, 12)
- `get_active_dispatches()` - All active dispatches
- `has_active_blackout()` - Check 2-week blackout (Rule 12)

### Queue Service
- `get_queue_snapshot()` - Full queue ordered by APN
- `get_queue_depth()` - Queue analytics
- `get_dispatch_rate()` - Dispatch rate for book
- `get_daily_activity_log()` - Day's queue changes

### Enforcement Service
- `daily_enforcement_run()` - Run all enforcement
- `get_enforcement_report()` - Preview enforcement
- `get_pending_enforcements()` - Counts of pending actions
- `send_re_sign_reminders()` - Re-sign reminders

---

## Frontend Service Data Needs

Based on API discovery, the `DispatchFrontendService` will need to:

1. **Dashboard Stats:**
   - Count open requests: `labor_request_service.get_open_requests()`
   - Count active dispatches: `dispatch_service.get_active_dispatches()`
   - Count pending bids: `job_bid_service.get_bids_for_request()` (sum across all requests)
   - Queue sizes: `queue_service.get_queue_depth()` (sum across books)

2. **Time Context:**
   - Current time
   - Bidding window status: `labor_request_service.validate_bidding_window()`
   - Past 3 PM cutoff: `labor_request_service.is_past_cutoff_for_tomorrow()`
   - Next event calculation (local logic)

3. **Request Management:**
   - List requests with filters
   - Single request detail with employer, book, candidates
   - Matching candidates: Query registrations for book, filter by agreement type
   - Bid list for request

4. **Morning Referral:**
   - Ordered request queue by classification: `labor_request_service.get_requests_for_morning()`
   - Pending bids grouped by request
   - Process bids: `job_bid_service.process_bids()`

5. **Queue Display:**
   - Queue snapshot by book: `queue_service.get_queue_snapshot()`
   - Position, member name, registration date, check marks

6. **Enforcement:**
   - Suspension counts: `enforcement_service.get_pending_enforcements()`
   - Active blackouts: Query blackout_periods table
   - Violation history: Query enforcement logs

---

## Template Data Structure Patterns

### Labor Request Object
```python
{
    "id": 123,
    "request_number": "2026-02-04-001",
    "employer_id": 45,
    "employer_name": "ABC Electric",
    "book_id": 1,
    "classification": "inside_wireperson",
    "workers_requested": 3,
    "workers_dispatched": 1,
    "start_date": "2026-02-05",
    "start_time": "06:00:00",
    "worksite_address": "123 Main St, Seattle",
    "agreement_type": "PLA",
    "generates_check_mark": False,
    "no_check_mark_reason": "early_start",
    "status": "partially_filled",
    "allows_online_bidding": True,
    "bidding_opens_at": "2026-02-04T17:30:00",
    "bidding_closes_at": "2026-02-05T07:00:00",
}
```

### Dispatch Object
```python
{
    "id": 456,
    "labor_request_id": 123,
    "member_id": 789,
    "member_name": "Smith, John",
    "employer_name": "ABC Electric",
    "dispatch_date": "2026-02-05",
    "dispatch_method": "morning_referral",
    "status": "working",
    "days_worked": 3,
    "is_short_call": False,
}
```

### Queue Position Object
```python
{
    "registration_id": 234,
    "member_id": 789,
    "member_name": "Smith, John",
    "book_id": 1,
    "book_priority_number": 1,  # Book 1, 2, 3, or 4
    "applicant_priority_number": "45880.23",  # APN as DECIMAL
    "registration_date": "2026-01-15",
    "check_marks": 1,
    "status": "registered",
    "is_exempt": False,
}
```

---

## Notes for Frontend Implementation

1. **Time awareness is critical:** The UI must show current time, bidding window status, and 3 PM cutoff prominently.

2. **Business rule indicators:** Every place where a rule applies needs a visual indicator (badge, icon, tooltip).

3. **FIFO ordering:** Always display candidates/queue in APN order (DECIMAL sort).

4. **Multi-step workflows:** Request → Match → Bid → Dispatch has 4 distinct states to track.

5. **Error handling:** Backend raises `ValueError` with descriptive messages. Catch and display in HTMX partials.

6. **Pagination:** Large datasets (all requests, queue, history) need pagination. Use `limit` and `offset` params.

7. **Real-time updates:** Dashboard and morning referral page need HTMX polling (30-60 second intervals).

8. **Suspension tracking:** Always check suspension status before showing dispatch actions. Display rejection count if approaching 2-rejection threshold.

---

**Discovery Complete:** February 4, 2026
**Next:** Task 1 - Directory structure creation
