# IP2A Database - Backend Development Roadmap

> **Purpose:** Master roadmap for backend development with timelines, milestones, and acceptance criteria.
> **Created:** January 27, 2026
> **For:** Claude Code implementation sessions
> **Time Budget:** 5-10 hours/week (estimates include 50% buffer)

---

## Executive Summary

| Phase | Focus | Duration | Hours | Status |
|-------|-------|----------|-------|--------|
| Phase 0 | Documentation & Structure | Week 1 | 5-8 hrs | 🟡 Ready to Start |
| Phase 1 | Foundation (Auth + Files) | Weeks 2-10 | 55-70 hrs | ⬜ Pending |
| Phase 2 | Pre-Apprenticeship System | Weeks 11-18 | 55-70 hrs | ⬜ Pending |
| Phase 3 | Market Recovery Module (Test Data) | Weeks 19-27 | 50-65 hrs | ⬜ Pending |
| Phase 4 | Integration & Polish | Weeks 28-30 | 35-45 hrs | ⬜ Pending |
| Phase 5 | Access DB Migration | Weeks 31-38 | 45-70 hrs | ⬜ Pending (Blocked) |

**Total Estimated Timeline:** 38 weeks (~9 months)
**Total Estimated Hours:** 245-330 hours

**Note on Phase 5:** This phase is intentionally blocked until the Access DB owner approves. Phases 1-4 serve as proof-of-concept. Phase 5 begins only after demo and approval.

---

## Technology Decisions (Confirmed)

| Component | Choice | ADR |
|-----------|--------|-----|
| Database | PostgreSQL 16 | ADR-001 |
| Backend Framework | FastAPI + SQLAlchemy | — |
| Frontend | Jinja2 + HTMX + Alpine.js | ADR-002 |
| Authentication | JWT (access + refresh tokens) | ADR-003 |
| File Storage | MinIO (dev) / B2 or S3 (prod) | ADR-004 |
| CSS Framework | Tailwind CSS | ADR-005 (create) |
| Background Jobs | Abstract TaskService (FastAPI now, Celery-ready) | ADR-006 (create) |
| Email | SendGrid | — |
| Observability | Grafana + Loki + Promtail (Docker) | ADR-007 (create) |
| Deployment | Union server (Phase 1-3) → Cloud (Phase 4+) | — |

### Background Jobs Strategy
We use an **abstract TaskService interface** that initially uses FastAPI BackgroundTasks but is designed for easy Celery migration:
- Phase 1-3: FastAPI BackgroundTasks (simple, no Redis needed)
- Phase 4+: Celery + Redis (when scheduling/monitoring needed)
- **Key:** Service code never changes, only the implementation swaps

### Observability Strategy
- Development: Console/file logs (structured JSON)
- Production: Grafana + Loki + Promtail stack (all Docker-based, portable)
- Error tracking: Sentry free tier (added in Phase 4)

---

## Phase 0: Documentation & Structure (Week 1)

**Goal:** Clean, organized project structure ready for feature development.

### Milestone 0.1: Documentation Reorganization
**Time Estimate:** 3-5 hours
**Dependency:** None

**Tasks:**
- [ ] Execute DOCS_REORGANIZATION_INSTRUCTIONS.md
- [ ] Create all ADRs (001-004)
- [ ] Create runbook templates
- [ ] Create CHANGELOG.md and CONTRIBUTING.md
- [ ] Update CLAUDE.md with new structure

**Acceptance Criteria:**
- [ ] No duplicate documentation files
- [ ] All folders lowercase
- [ ] ADRs explain key decisions
- [ ] Runbook templates exist (even if incomplete)
- [ ] Git history preserved for moved files

### Milestone 0.2: Frontend Scaffolding
**Time Estimate:** 3-4 hours
**Dependency:** 0.1

**Tasks:**
- [ ] Add Jinja2 template directory structure
- [ ] Add HTMX via CDN
- [ ] Add Alpine.js via CDN
- [ ] Set up Tailwind CSS (CLI or CDN for dev)
- [ ] Create base template with layout
- [ ] Create simple health check page (proves stack works)
- [ ] Add keyboard shortcuts scaffold (shortcuts.js)

**Tailwind Setup Options:**
```bash
# Option A: CDN (fastest for dev, not for prod)
<script src="https://cdn.tailwindcss.com"></script>

# Option B: Tailwind CLI (recommended)
npm init -y
npm install -D tailwindcss
npx tailwindcss init
# Add to package.json scripts:
# "build:css": "tailwindcss -i ./src/static/css/input.css -o ./src/static/css/output.css --watch"
```

**Directory Structure to Create:**
```
src/
├── templates/
│   ├── base.html           # Master layout (includes Tailwind)
│   ├── components/         # Reusable partials
│   │   ├── _navbar.html
│   │   ├── _flash.html     # Flash messages
│   │   ├── _modal.html     # Modal container for HTMX
│   │   └── _pagination.html
│   ├── auth/
│   │   ├── login.html
│   │   └── logout.html
│   ├── members/
│   │   ├── list.html
│   │   ├── detail.html
│   │   └── _search_results.html  # HTMX partial
│   └── errors/
│       ├── 404.html
│       └── 500.html
├── static/
│   ├── css/
│   │   ├── input.css       # Tailwind directives
│   │   └── output.css      # Compiled (gitignored in prod)
│   └── js/
│       └── shortcuts.js    # Keyboard shortcuts (Alpine.js)
```

**base.html Structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}IP2A{% endblock %}</title>
    
    <!-- Tailwind CSS -->
    <link href="{{ url_for('static', path='css/output.css') }}" rel="stylesheet">
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
    <!-- Alpine.js -->
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body class="bg-gray-50 min-h-screen" x-data="{ sidebarOpen: false }">
    {% include 'components/_navbar.html' %}
    
    <main class="container mx-auto px-4 py-8">
        {% include 'components/_flash.html' %}
        {% block content %}{% endblock %}
    </main>
    
    <!-- Modal container for HTMX -->
    <div id="modal" class="hidden"></div>
    
    <!-- Keyboard shortcuts -->
    <script src="{{ url_for('static', path='js/shortcuts.js') }}"></script>
</body>
</html>
```

**Acceptance Criteria:**
- [ ] `http://localhost:8000/` shows styled page
- [ ] Tailwind classes work (test with `bg-blue-500`)
- [ ] HTMX loaded (check browser console: `htmx.version`)
- [ ] Alpine.js loaded (check browser console: `Alpine.version`)
- [ ] No JavaScript errors in console

---

## Phase 1: Foundation (Weeks 2-9)

**Goal:** Authentication system and file storage operational.

### Milestone 1.1: Authentication Database Schema
**Time Estimate:** 4-6 hours
**Dependency:** Phase 0 complete
**Week:** 2

**Tasks:**
- [ ] Create User model
- [ ] Create Role model
- [ ] Create UserRole junction table
- [ ] Create RefreshToken model
- [ ] Create PasswordResetToken model
- [ ] Create Alembic migration
- [ ] Seed default roles (Admin, Officer, Staff, Organizer, Instructor)
- [ ] Seed initial admin user

**Models to Create:**
```python
# src/models/user.py
class User(Base):
    __tablename__ = "users"
    
    id: int (PK)
    email: str (unique, indexed)
    password_hash: str
    first_name: str
    last_name: str
    is_active: bool (default True)
    is_verified: bool (default False)
    member_id: int (FK, nullable)  # Link to Member if applicable
    last_login: datetime (nullable)
    failed_login_attempts: int (default 0)
    locked_until: datetime (nullable)
    created_at: datetime
    updated_at: datetime

# src/models/role.py
class Role(Base):
    __tablename__ = "roles"
    
    id: int (PK)
    name: str (unique)  # admin, officer, staff, organizer, instructor, member
    description: str
    permissions: JSON  # Flexible permission storage
    created_at: datetime

# src/models/user_role.py
class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id: int (FK, PK)
    role_id: int (FK, PK)
    granted_at: datetime
    granted_by: int (FK to User)

# src/models/refresh_token.py
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: int (PK)
    user_id: int (FK)
    token_hash: str (indexed)
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime (nullable)
    revoked_reason: str (nullable)
```

**Acceptance Criteria:**
- [ ] Migration runs without errors
- [ ] All tables created in database
- [ ] Foreign keys properly constrained
- [ ] Default roles seeded
- [ ] Admin user can be queried

### Milestone 1.2: Password Service
**Time Estimate:** 3-4 hours
**Dependency:** 1.1
**Week:** 3

**Tasks:**
- [ ] Install bcrypt (`pip install bcrypt`)
- [ ] Create PasswordService class
- [ ] Implement hash_password()
- [ ] Implement verify_password()
- [ ] Implement check_password_strength()
- [ ] Write unit tests

**Service Interface:**
```python
# src/services/password_service.py
class PasswordService:
    def hash_password(self, password: str) -> str: ...
    def verify_password(self, password: str, hash: str) -> bool: ...
    def check_strength(self, password: str) -> tuple[bool, list[str]]: ...
    # Returns (is_valid, list_of_issues)
```

**Password Requirements:**
- Minimum 12 characters
- At least one uppercase
- At least one lowercase
- At least one number
- At least one special character
- Not in common password list (top 10,000)

**Acceptance Criteria:**
- [ ] Passwords hashed with bcrypt (cost factor 12)
- [ ] Verification works correctly
- [ ] Weak passwords rejected with specific feedback
- [ ] Unit tests pass (minimum 8 tests)

### Milestone 1.3: JWT Service
**Time Estimate:** 4-6 hours
**Dependency:** 1.2
**Week:** 3-4

**Tasks:**
- [ ] Install PyJWT (`pip install PyJWT`)
- [ ] Create JWTService class
- [ ] Implement create_access_token()
- [ ] Implement create_refresh_token()
- [ ] Implement verify_token()
- [ ] Implement refresh_access_token()
- [ ] Implement revoke_refresh_token()
- [ ] Add token configuration to settings
- [ ] Write unit tests

**Token Configuration:**
```python
# src/config/settings.py
JWT_SECRET_KEY: str  # From environment
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

**Token Payload Structure:**
```json
{
    "sub": "user_id",
    "email": "user@example.com",
    "roles": ["staff", "organizer"],
    "type": "access",
    "exp": 1234567890,
    "iat": 1234567890
}
```

**Acceptance Criteria:**
- [ ] Access tokens expire in 15 minutes
- [ ] Refresh tokens expire in 7 days
- [ ] Refresh tokens stored in database
- [ ] Token verification rejects expired/invalid tokens
- [ ] Refresh token rotation works
- [ ] Unit tests pass (minimum 10 tests)

### Milestone 1.4: Auth Endpoints
**Time Estimate:** 6-8 hours
**Dependency:** 1.3
**Week:** 4-5

**Tasks:**
- [ ] Create auth router
- [ ] Implement POST /auth/login
- [ ] Implement POST /auth/logout
- [ ] Implement POST /auth/refresh
- [ ] Implement POST /auth/password/reset-request
- [ ] Implement POST /auth/password/reset-confirm
- [ ] Implement GET /auth/me
- [ ] Add rate limiting to login endpoint
- [ ] Write integration tests

**Endpoints:**
| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | /auth/login | No | Email + password → tokens |
| POST | /auth/logout | Yes | Revoke refresh token |
| POST | /auth/refresh | No (refresh token) | Get new access token |
| POST | /auth/password/reset-request | No | Send reset email |
| POST | /auth/password/reset-confirm | No | Reset with token |
| GET | /auth/me | Yes | Get current user info |

**Security Measures:**
- [ ] Login rate limiting: 5 attempts per 15 minutes per email
- [ ] Account lockout after 10 failed attempts
- [ ] Password reset tokens expire in 1 hour
- [ ] Audit log all auth events

**Acceptance Criteria:**
- [ ] Login returns access + refresh tokens
- [ ] Invalid credentials return 401
- [ ] Rate limiting blocks rapid attempts
- [ ] Logout invalidates refresh token
- [ ] Token refresh works correctly
- [ ] Integration tests pass (minimum 12 tests)

### Milestone 1.5: Task Service Abstraction
**Time Estimate:** 2-3 hours
**Dependency:** 1.4
**Week:** 5

**Tasks:**
- [ ] Create TaskService abstract base class
- [ ] Create FastAPITaskService implementation
- [ ] Create task status tracking (in-memory for now)
- [ ] Add dependency injection for task service
- [ ] Write unit tests
- [ ] Document Celery migration path

**Why This Matters:**
Building an abstraction now means when you need Celery features (scheduled jobs, monitoring, retries), you swap the implementation without touching service code.

**Service Interface:**
```python
# src/services/tasks/base.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Any, Optional
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskResult:
    task_id: str
    status: TaskStatus
    result: Optional[Any]
    error: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

class TaskService(ABC):
    @abstractmethod
    def enqueue(self, func: Callable, *args, **kwargs) -> str:
        """Queue task for immediate background execution."""
        pass
    
    @abstractmethod
    def schedule(self, func: Callable, run_at: datetime, *args, **kwargs) -> str:
        """Schedule task for future execution."""
        pass
    
    @abstractmethod
    def get_status(self, task_id: str) -> TaskResult:
        """Get task execution status."""
        pass


# src/services/tasks/fastapi_tasks.py
class FastAPITaskService(TaskService):
    """
    Implementation using FastAPI BackgroundTasks.
    
    Limitations (documented for future migration):
    - No true scheduling (runs immediately with warning)
    - No persistence (status lost on restart)
    - No retries
    - No monitoring
    
    These limitations are acceptable for Phase 1-3.
    Migrate to CeleryTaskService when needed.
    """
    
    def __init__(self):
        self._status_store: Dict[str, TaskResult] = {}
    
    def enqueue(self, func: Callable, *args, **kwargs) -> str:
        task_id = str(uuid4())
        # Status tracking happens in wrapper
        return task_id
    
    def schedule(self, func: Callable, run_at: datetime, *args, **kwargs) -> str:
        logger.warning(
            f"Scheduling not supported in FastAPI implementation. "
            f"Task {func.__name__} will run immediately. "
            f"Migrate to CeleryTaskService for true scheduling."
        )
        return self.enqueue(func, *args, **kwargs)


# FUTURE: src/services/tasks/celery_tasks.py (not implemented yet)
# class CeleryTaskService(TaskService):
#     """Full-featured implementation with Redis backend."""
#     pass
```

**Dependency Injection:**
```python
# src/dependencies/tasks.py
from functools import lru_cache
from src.services.tasks.fastapi_tasks import FastAPITaskService

@lru_cache()
def get_task_service() -> TaskService:
    # Change this ONE line when migrating to Celery
    return FastAPITaskService()
```

**Usage Example (in password reset):**
```python
# This code NEVER changes when you switch to Celery
@router.post("/auth/password/reset-request")
def request_password_reset(
    email: str,
    task_service: TaskService = Depends(get_task_service)
):
    # ... validation ...
    task_service.enqueue(send_password_reset_email, user.email, token)
    return {"message": "If account exists, reset email sent"}
```

**Acceptance Criteria:**
- [ ] TaskService ABC defined with clear interface
- [ ] FastAPITaskService implements interface
- [ ] Limitations documented in code comments
- [ ] Dependency injection configured
- [ ] Unit tests pass
- [ ] Migration path documented in ADR-006

### Milestone 1.6: Auth Middleware & Dependencies
**Time Estimate:** 4-5 hours
**Dependency:** 1.5
**Week:** 5-6

**Tasks:**
- [ ] Create get_current_user dependency
- [ ] Create require_roles() dependency factory
- [ ] Create RoleChecker class
- [ ] Protect existing endpoints with auth
- [ ] Add user context to audit logs
- [ ] Write tests for protected endpoints

**Dependency Examples:**
```python
# src/dependencies/auth.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User: ...
def require_roles(*roles: str) -> Callable: ...

# Usage in routers
@router.get("/members")
def list_members(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_roles("staff", "admin"))
):
    ...
```

**Role Permissions Matrix:**
| Endpoint | Admin | Officer | Staff | Organizer | Instructor |
|----------|-------|---------|-------|-----------|------------|
| GET /members | ✅ | ✅ | ✅ | ❌ | ❌ |
| POST /members | ✅ | ✅ | ✅ | ❌ | ❌ |
| DELETE /members | ✅ | ✅ | ❌ | ❌ | ❌ |
| GET /students | ✅ | ✅ | ✅ | ❌ | ✅ |
| GET /salting/* | ✅ | ✅ | ❌ | ✅ | ❌ |

**Acceptance Criteria:**
- [ ] Unauthenticated requests return 401
- [ ] Unauthorized role requests return 403
- [ ] Audit logs include user_id
- [ ] Tests verify role enforcement

### Milestone 1.6: Login UI
**Time Estimate:** 4-5 hours
**Dependency:** 1.5
**Week:** 6-7

**Tasks:**
- [ ] Create login page template
- [ ] Create logout confirmation
- [ ] Create password reset request page
- [ ] Create password reset confirmation page
- [ ] Add flash messages for feedback
- [ ] Handle redirect after login
- [ ] Style with Pico CSS

**Pages:**
- `/login` - Email/password form
- `/logout` - Confirmation + redirect
- `/forgot-password` - Request reset email
- `/reset-password/{token}` - Set new password

**Acceptance Criteria:**
- [ ] User can log in via web form
- [ ] Failed login shows error message
- [ ] Successful login redirects to dashboard
- [ ] Logout clears session and redirects
- [ ] Password reset flow works end-to-end
- [ ] All pages styled consistently

### Milestone 1.7: File Storage Setup
**Time Estimate:** 5-7 hours
**Dependency:** 1.5
**Week:** 7-8

**Tasks:**
- [ ] Add MinIO to docker-compose.yml
- [ ] Create storage configuration
- [ ] Create FileStorageService class
- [ ] Implement upload_file()
- [ ] Implement download_file()
- [ ] Implement delete_file()
- [ ] Implement generate_presigned_url()
- [ ] Update FileAttachment model
- [ ] Write integration tests

**Docker Compose Addition:**
```yaml
minio:
  image: minio/minio
  ports:
    - "9000:9000"
    - "9001:9001"
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  command: server /data --console-address ":9001"
  volumes:
    - minio_data:/data
```

**Service Interface:**
```python
# src/services/file_storage_service.py
class FileStorageService:
    def upload_file(self, file: UploadFile, path: str) -> FileMetadata: ...
    def download_file(self, path: str) -> bytes: ...
    def delete_file(self, path: str) -> bool: ...
    def get_presigned_url(self, path: str, expires: int = 3600) -> str: ...
```

**Acceptance Criteria:**
- [ ] MinIO accessible at localhost:9001
- [ ] Files upload successfully
- [ ] Files download correctly
- [ ] Presigned URLs work
- [ ] File metadata saved to database
- [ ] Integration tests pass

### Milestone 1.8: File Upload UI
**Time Estimate:** 4-5 hours
**Dependency:** 1.7
**Week:** 8-9

**Tasks:**
- [ ] Create file upload component (HTMX)
- [ ] Add drag-and-drop support
- [ ] Show upload progress
- [ ] Display file list with download links
- [ ] Add delete confirmation
- [ ] Integrate with member/student detail pages

**Acceptance Criteria:**
- [ ] Users can upload files via form
- [ ] Drag-and-drop works
- [ ] Progress indicator shows during upload
- [ ] Files appear in list after upload
- [ ] Download links work
- [ ] Delete requires confirmation

### Milestone 1.9: Phase 1 Testing & Stabilization
**Time Estimate:** 5-7 hours
**Dependency:** 1.8
**Week:** 9

**Tasks:**
- [ ] Run full test suite
- [ ] Fix any failing tests
- [ ] Security review of auth implementation
- [ ] Load test auth endpoints
- [ ] Update documentation
- [ ] Create Phase 1 summary report
- [ ] Merge to main, tag v0.3.0

**Security Checklist:**
- [ ] No secrets in code or logs
- [ ] Passwords properly hashed
- [ ] Tokens properly validated
- [ ] SQL injection prevented (ORM)
- [ ] XSS prevented (template escaping)
- [ ] CSRF protection in place
- [ ] Rate limiting active

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] No critical security issues
- [ ] Documentation updated
- [ ] Tagged and merged to main

---

## Phase 2: Pre-Apprenticeship System (Weeks 10-18)

**Goal:** Complete student management and grant reporting system.

### Milestone 2.1: Enhanced Student Schema
**Time Estimate:** 5-7 hours
**Dependency:** Phase 1 complete
**Week:** 10-11

**Tasks:**
- [ ] Review existing Student model
- [ ] Add Grant model
- [ ] Add GrantEnrollment model
- [ ] Add StudentProgress model
- [ ] Add Attendance model
- [ ] Add Certification model (enhanced)
- [ ] Add Placement model
- [ ] Create migrations
- [ ] Seed sample data

**New Models:**
```python
# Grant tracking
class Grant(Base):
    id, name, funder, amount, start_date, end_date,
    reporting_frequency, status, created_at

# Student enrollment in specific grant
class GrantEnrollment(Base):
    id, student_id (FK), grant_id (FK), cohort_id (FK),
    enrollment_date, completion_date, status, exit_reason

# Progress tracking
class StudentProgress(Base):
    id, student_id (FK), cohort_id (FK), week_number,
    attendance_hours, grade, notes, recorded_by (FK), created_at

# Attendance records
class Attendance(Base):
    id, student_id (FK), cohort_id (FK), date,
    status (present/absent/excused), hours, notes

# Certification tracking
class Certification(Base):
    id, student_id (FK), type, name, issued_date,
    expiration_date, issuing_org, document_path, verified_by

# Job placement
class Placement(Base):
    id, student_id (FK), employer_id (FK), position,
    start_date, hourly_rate, is_union, notes, recorded_by
```

**Acceptance Criteria:**
- [ ] All models created with proper relationships
- [ ] Migrations run successfully
- [ ] Sample data seeds correctly
- [ ] Foreign keys properly constrained

### Milestone 2.2: Student CRUD Enhancement
**Time Estimate:** 6-8 hours
**Dependency:** 2.1
**Week:** 11-12

**Tasks:**
- [ ] Update StudentService with new operations
- [ ] Add GrantService
- [ ] Add ProgressService
- [ ] Add AttendanceService
- [ ] Add CertificationService
- [ ] Add PlacementService
- [ ] Update/create routers
- [ ] Write tests

**Acceptance Criteria:**
- [ ] Full CRUD for all new entities
- [ ] Proper authorization on all endpoints
- [ ] Audit logging for all changes
- [ ] Tests pass

### Milestone 2.3: Student Management UI
**Time Estimate:** 8-10 hours
**Dependency:** 2.2
**Week:** 12-14

**Tasks:**
- [ ] Student list page (search, filter, pagination)
- [ ] Student detail page
- [ ] Student intake form
- [ ] Progress entry form
- [ ] Attendance entry (batch)
- [ ] Certification upload/tracking
- [ ] Placement recording
- [ ] Dashboard with key metrics

**Pages:**
| Page | Description |
|------|-------------|
| /students | List with search/filter |
| /students/{id} | Full student profile |
| /students/new | Intake form |
| /students/{id}/progress | Progress history + entry |
| /students/{id}/attendance | Attendance records |
| /students/{id}/certifications | Cert tracking |
| /cohorts/{id}/attendance | Batch attendance entry |
| /dashboard | Key metrics overview |

**Acceptance Criteria:**
- [ ] All pages functional and styled
- [ ] HTMX provides smooth UX (no full page reloads)
- [ ] Forms validate input
- [ ] Keyboard shortcuts work (Ctrl+S to save, etc.)

### Milestone 2.4: Grant Reporting
**Time Estimate:** 8-10 hours
**Dependency:** 2.3
**Week:** 14-16

**Tasks:**
- [ ] Grant list/detail pages
- [ ] Enrollment tracking per grant
- [ ] Report generation service
- [ ] Demographic summary report
- [ ] Attendance summary report
- [ ] Outcome report (completion, placement)
- [ ] Export to CSV
- [ ] Export to PDF
- [ ] Data visualization (charts)

**Reports Needed:**
| Report | Contents | Format |
|--------|----------|--------|
| Enrollment Summary | Students by cohort, demographics | Web + CSV + PDF |
| Attendance Report | Hours by student, by week | Web + CSV |
| Progress Report | Grades, completion rates | Web + CSV + PDF |
| Outcome Report | Completions, placements, wages | Web + CSV + PDF |
| Funder Report | Combined metrics per grant | PDF |

**Acceptance Criteria:**
- [ ] All reports generate correctly
- [ ] CSV exports are properly formatted
- [ ] PDF exports are professional quality
- [ ] Charts display in web UI
- [ ] Reports filterable by date range, cohort, grant

### Milestone 2.5: Cohort Management
**Time Estimate:** 5-6 hours
**Dependency:** 2.3
**Week:** 16-17

**Tasks:**
- [ ] Cohort list page
- [ ] Cohort detail page (student roster)
- [ ] Cohort creation form
- [ ] Instructor assignment
- [ ] Schedule management
- [ ] Bulk student operations

**Acceptance Criteria:**
- [ ] Cohorts can be created and managed
- [ ] Students can be enrolled/unenrolled
- [ ] Instructors can be assigned
- [ ] Bulk operations work (e.g., mark all present)

### Milestone 2.6: Notification System (SendGrid)
**Time Estimate:** 5-6 hours
**Dependency:** 2.4
**Week:** 17-18

**Tasks:**
- [ ] Set up SendGrid account and verify domain
- [ ] Create EmailService with SendGrid integration
- [ ] Create email templates (HTML + plain text)
- [ ] Certification expiration alerts
- [ ] Missing attendance alerts
- [ ] Grant deadline reminders
- [ ] Integrate with TaskService for background sending
- [ ] Add daily check cron job

**SendGrid Configuration:**
```python
# src/config/settings.py
SENDGRID_API_KEY: str  # From environment
EMAIL_FROM_ADDRESS: str = "noreply@ibew46.org"
EMAIL_FROM_NAME: str = "IBEW Local 46"

# src/services/email_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailService:
    def __init__(self, task_service: TaskService):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.tasks = task_service
    
    def send_async(self, to: str, subject: str, template: str, data: dict):
        """Queue email for background sending."""
        self.tasks.enqueue(self._send, to, subject, template, data)
    
    def _send(self, to: str, subject: str, template: str, data: dict):
        """Actually send the email (called by task service)."""
        html_content = render_template(f"emails/{template}.html", **data)
        message = Mail(
            from_email=(settings.EMAIL_FROM_ADDRESS, settings.EMAIL_FROM_NAME),
            to_emails=to,
            subject=subject,
            html_content=html_content
        )
        self.client.send(message)
```

**Email Templates to Create:**
```
src/templates/emails/
├── base_email.html              # Master email layout
├── cert_expiring.html           # Certification expiring in X days
├── attendance_alert.html        # Student absent 3+ days
├── grant_deadline.html          # Grant report due reminder
├── password_reset.html          # Password reset link
└── welcome.html                 # New user welcome
```

**Scheduled Checks (via TaskService):**
```python
# Daily at 6 AM:
- Check certifications expiring in 30/14/7 days → send alerts
- Check students absent 3+ consecutive days → send alerts
- Check grant reports due in 14/7 days → send reminders
```

**Acceptance Criteria:**
- [ ] SendGrid sends emails successfully
- [ ] Templates render correctly (test with SendGrid preview)
- [ ] Background sending works (doesn't block requests)
- [ ] Daily checks run via scheduled task
- [ ] All email events logged in audit trail
- [ ] Unsubscribe handling (CAN-SPAM compliance)

### Milestone 2.7: Phase 2 Testing & Stabilization
**Time Estimate:** 6-8 hours
**Dependency:** 2.6
**Week:** 18

**Tasks:**
- [ ] Full regression testing
- [ ] User acceptance testing (if possible)
- [ ] Performance testing with realistic data
- [ ] Documentation update
- [ ] Phase 2 summary report
- [ ] Merge to main, tag v0.4.0

**Acceptance Criteria:**
- [ ] All Phase 2 features working
- [ ] Performance acceptable (<2s page loads)
- [ ] No critical bugs
- [ ] Documentation complete

---

## Phase 3: Market Recovery Module (Weeks 19-27)

**Goal:** Build fully functional Market Recovery system with test data. Prove the system works before requesting Access database.

**Important:** This phase is designed to work WITHOUT access to the existing Access database. We build everything with realistic test data, prove it works, then migrate real data in Phase 5.

### Milestone 3.1: Market Recovery Schema
**Time Estimate:** 5-6 hours
**Dependency:** Phase 2 complete
**Week:** 19

**Tasks:**
- [ ] Research Market Recovery program workflows (interviews, documentation)
- [ ] Create MarketRecoveryProgram model
- [ ] Create MRAssignment model
- [ ] Create MRHourSubmission model
- [ ] Create MRApproval model
- [ ] Create MRPayment model (tracks subsidy payments)
- [ ] Create migrations
- [ ] Document assumed schema (for later validation against Access)

**Schema Design (Best Guess - Validate Later):**
```python
class MarketRecoveryProgram(Base):
    id, name, description, start_date, end_date,
    budget, hourly_subsidy_rate, status, created_at

class MRAssignment(Base):
    id, program_id (FK), member_id (FK), contractor_id (FK),
    start_date, end_date, hourly_rate, status, notes, assigned_by

class MRHourSubmission(Base):
    id, assignment_id (FK), week_ending, regular_hours,
    overtime_hours, submitted_by, submitted_at, status,
    approved_by, approved_at, rejection_reason

class MRPayment(Base):
    id, assignment_id (FK), pay_period_start, pay_period_end,
    hours_paid, subsidy_amount, status, qb_reference, processed_at
```

**Acceptance Criteria:**
- [ ] Schema supports full workflow (assign → submit → approve → pay)
- [ ] Models created with proper relationships
- [ ] Migrations run successfully

### Milestone 3.2: Market Recovery Services
**Time Estimate:** 6-8 hours
**Dependency:** 3.1
**Week:** 20-21

**Tasks:**
- [ ] CRUD services for all MR models
- [ ] Assignment workflow service
- [ ] Hour submission service (with validation)
- [ ] Approval workflow service (approve/reject)
- [ ] Subsidy calculation service
- [ ] Payment generation service
- [ ] Routers and endpoints
- [ ] Tests with realistic scenarios

**Business Logic to Implement:**
```python
# Subsidy calculation example
def calculate_subsidy(assignment: MRAssignment, hours: float) -> Decimal:
    """
    Union subsidizes difference between contractor rate and journeyman scale.
    Example: Journeyman scale = $50/hr, Contractor pays $35/hr
    Subsidy = $15/hr × hours worked
    """
    journeyman_rate = get_current_journeyman_rate()
    contractor_rate = assignment.hourly_rate
    subsidy_per_hour = max(journeyman_rate - contractor_rate, 0)
    return Decimal(subsidy_per_hour * hours)
```

**Acceptance Criteria:**
- [ ] Full CRUD for all entities
- [ ] Workflow state transitions enforced
- [ ] Calculations match expected business logic
- [ ] All endpoints protected with proper roles
- [ ] Tests pass

### Milestone 3.3: Market Recovery Seed Data
**Time Estimate:** 3-4 hours
**Dependency:** 3.2
**Week:** 21

**Tasks:**
- [ ] Create realistic test data generator
- [ ] Generate 2-3 programs (active, completed, planned)
- [ ] Generate 50+ assignments across programs
- [ ] Generate 6 months of hour submissions
- [ ] Generate approval history
- [ ] Generate payment records
- [ ] Document test data for demo purposes

**Why This Matters:**
This test data is your **proof of concept**. When you demo to the Access DB owner, she'll see realistic workflows with believable data. This builds confidence before you ask for real data.

**Acceptance Criteria:**
- [ ] Test data covers all workflow states
- [ ] Data is realistic (real contractor names, reasonable hours)
- [ ] Can demonstrate full lifecycle in demo

### Milestone 3.4: Market Recovery UI
**Time Estimate:** 10-12 hours
**Dependency:** 3.3
**Week:** 22-24

**Tasks:**
- [ ] Dashboard (program overview, pending approvals, recent activity)
- [ ] Program management pages (list, detail, create/edit)
- [ ] Assignment management (assign member to contractor)
- [ ] Hour submission form (staff enters on behalf of member)
- [ ] Approval queue (list pending, approve/reject workflow)
- [ ] Member hour history view
- [ ] Contractor summary view
- [ ] Payment processing interface
- [ ] Keyboard shortcuts for common actions

**Pages:**
| Page | Role Access | Description |
|------|-------------|-------------|
| /market-recovery | Staff+ | Dashboard |
| /market-recovery/programs | Staff+ | Program list |
| /market-recovery/programs/{id} | Staff+ | Program detail + assignments |
| /market-recovery/assignments/new | Staff+ | Create assignment |
| /market-recovery/hours/submit | Staff+ | Submit hours |
| /market-recovery/approvals | Officer+ | Approval queue |
| /market-recovery/payments | Officer+ | Payment processing |
| /market-recovery/reports | Staff+ | Reports menu |

**Acceptance Criteria:**
- [ ] All pages functional with test data
- [ ] Workflow is intuitive (minimal training needed)
- [ ] HTMX provides smooth experience
- [ ] Mobile-friendly for field use

### Milestone 3.5: Market Recovery Reports
**Time Estimate:** 8-10 hours
**Dependency:** 3.4
**Week:** 24-26

**Tasks:**
- [ ] Identify required reports (interview Access DB owner)
- [ ] Weekly Hours by Contractor report
- [ ] Member Hours Summary report
- [ ] Program Budget vs Actual report
- [ ] Payment Summary report
- [ ] Subsidy Calculation Detail report
- [ ] Export to CSV for all reports
- [ ] Export to PDF for print distribution
- [ ] Date range filtering on all reports

**Report Template Structure:**
```
templates/reports/market_recovery/
├── _base_report.html          # Common report layout (header, footer, print CSS)
├── weekly_hours.html          # Hours by contractor
├── member_summary.html        # Individual member history
├── budget_actual.html         # Program financials
├── payment_summary.html       # Payment batches
└── subsidy_detail.html        # Line-item subsidy calculations
```

**Acceptance Criteria:**
- [ ] All reports generate correctly with test data
- [ ] PDF output is print-ready (proper margins, page breaks)
- [ ] CSV exports are clean (no HTML artifacts)
- [ ] Reports match business requirements
- [ ] **Can demo reports to Access DB owner**

### Milestone 3.6: Phase 3 Testing & Demo Prep
**Time Estimate:** 6-8 hours
**Dependency:** 3.5
**Week:** 26-27

**Tasks:**
- [ ] Full regression testing
- [ ] Performance testing with realistic data volume
- [ ] Security review (role enforcement)
- [ ] Create demo script/walkthrough
- [ ] Document system capabilities
- [ ] Prepare comparison: "Current Access Process vs New System"
- [ ] Merge to main, tag v0.5.0

**Demo Preparation:**
Create a side-by-side comparison document:

| Workflow | Current (Access) | New System |
|----------|------------------|------------|
| Submit hours | Manual entry in Access | Web form, mobile-friendly |
| Approve hours | ? | Queue with one-click approve |
| Generate reports | Print from Access | Web + PDF + CSV |
| Track payments | ? | Integrated, links to QB |
| Audit trail | ? | Complete history of all changes |
| Remote access | VPN + Remote Desktop? | Web browser anywhere |

**Acceptance Criteria:**
- [ ] System is demo-ready
- [ ] Test data tells a compelling story
- [ ] Comparison document highlights improvements
- [ ] All tests pass
- [ ] Documentation complete

---

## Phase 4: Integration & Polish (Weeks 25-30)

**Goal:** System ready for production use.

### Milestone 4.1: QuickBooks Integration
**Time Estimate:** 8-10 hours
**Week:** 25-26

**Tasks:**
- [ ] Research QuickBooks API (Desktop vs Online)
- [ ] Create sync service
- [ ] Export transactions to QB format
- [ ] Import payment status from QB
- [ ] Reconciliation reports

### Milestone 4.2: Dashboard & Analytics
**Time Estimate:** 6-8 hours
**Week:** 27-28

**Tasks:**
- [ ] Executive dashboard
- [ ] Role-specific dashboards
- [ ] Key performance indicators
- [ ] Trend visualizations
- [ ] Export capabilities

### Milestone 4.3: Observability Stack (Grafana + Loki)
**Time Estimate:** 6-8 hours
**Week:** 27-28

**Tasks:**
- [ ] Add Loki to docker-compose (log aggregation)
- [ ] Add Promtail to docker-compose (log shipping)
- [ ] Add Grafana to docker-compose (visualization)
- [ ] Configure structured JSON logging in FastAPI
- [ ] Create Grafana dashboards
- [ ] Set up alerting rules
- [ ] Document monitoring runbook

**Docker Compose Addition:**
```yaml
# Observability Stack
loki:
  image: grafana/loki:2.9.0
  ports:
    - "3100:3100"
  command: -config.file=/etc/loki/local-config.yaml
  volumes:
    - loki_data:/loki

promtail:
  image: grafana/promtail:2.9.0
  volumes:
    - /var/log:/var/log
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - ./promtail-config.yml:/etc/promtail/config.yml
  command: -config.file=/etc/promtail/config.yml

grafana:
  image: grafana/grafana:10.0.0
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin  # Change in production!
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning
```

**Structured Logging Configuration:**
```python
# src/config/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

# Usage in code:
logger = structlog.get_logger()
logger.info("user_login", user_id=123, ip_address="192.168.1.1")
# Output: {"event": "user_login", "user_id": 123, "ip_address": "192.168.1.1", "level": "info", "timestamp": "2026-01-27T10:30:00Z"}
```

**Grafana Dashboards to Create:**
| Dashboard | Metrics |
|-----------|---------|
| API Health | Request rate, error rate, latency (p50/p95/p99) |
| Authentication | Login attempts, failures, lockouts |
| Background Tasks | Queue depth, success/failure rate, duration |
| Database | Query count, slow queries, connection pool |
| Business | Active users, new students, certifications expiring |

**Alerting Rules:**
| Alert | Condition | Action |
|-------|-----------|--------|
| High Error Rate | >5% 5xx errors in 5 min | Email + Slack |
| Auth Failures | >10 failed logins in 1 min | Email |
| Slow Queries | >5 queries over 1s in 5 min | Log |
| Disk Space | <20% free | Email |

**Acceptance Criteria:**
- [ ] All containers logging to Loki
- [ ] Grafana accessible at localhost:3000
- [ ] Dashboards populated with data
- [ ] Alerts firing correctly (test with intentional errors)
- [ ] Stack portable (copy folder, run docker-compose up)

### Milestone 4.4: Production Hardening
**Time Estimate:** 6-8 hours
**Week:** 28-29

**Tasks:**
- [ ] Security audit (OWASP checklist)
- [ ] Performance optimization (indexes, query analysis)
- [ ] Error handling improvement (graceful degradation)
- [ ] Rate limiting on all public endpoints
- [ ] Backup automation (daily, tested restore)
- [ ] SSL/TLS configuration
- [ ] Add Sentry for error tracking

**Security Checklist:**
- [ ] All secrets in environment variables
- [ ] No debug mode in production
- [ ] CORS properly configured
- [ ] CSRF protection enabled
- [ ] SQL injection prevented (ORM)
- [ ] XSS prevented (template escaping)
- [ ] Password requirements enforced
- [ ] Rate limiting on auth endpoints
- [ ] Audit logging comprehensive

**Acceptance Criteria:**
- [ ] Security checklist complete
- [ ] Load test passes (50 concurrent users)
- [ ] Backup/restore tested
- [ ] SSL working (if applicable)

### Milestone 4.4: Documentation & Training
**Time Estimate:** 6-8 hours
**Week:** 29-30

**Tasks:**
- [ ] User manual
- [ ] Admin guide
- [ ] Complete runbooks
- [ ] Training materials
- [ ] Video walkthroughs (optional)

### Milestone 4.5: Production Launch Prep
**Time Estimate:** 5-6 hours
**Week:** 30

**Tasks:**
- [ ] Final testing
- [ ] Deployment to production
- [ ] DNS/SSL configuration
- [ ] User account creation
- [ ] Go-live checklist
- [ ] Merge to main, tag v1.0.0 🎉

---

## Phase 5: Access Database Migration (Weeks 31-38)

**Goal:** Migrate data from Access database and recreate all reports. This phase happens AFTER the system is proven and the Access DB owner grants access.

**Prerequisites:**
- [ ] Phase 1-4 complete and stable
- [ ] Demo completed for Access DB owner
- [ ] Access DB owner approves migration
- [ ] Access to .mdb/.accdb file granted

### Milestone 5.1: Access Database Analysis
**Time Estimate:** 6-8 hours
**Dependency:** Access file provided
**Week:** 31-32

**Tasks:**
- [ ] Obtain Access database file (.mdb or .accdb)
- [ ] Extract and document all table structures
- [ ] Extract and document all queries
- [ ] Extract report definitions (structure, not layout)
- [ ] Identify all VBA code/macros
- [ ] Create data dictionary
- [ ] Map Access tables → IP2A schema
- [ ] Identify gaps (fields we don't have)
- [ ] Document transformation rules

**Tools for Extraction:**
```bash
# Option A: mdbtools (Linux/Mac)
mdb-tables database.mdb           # List tables
mdb-schema database.mdb           # Get schema
mdb-export database.mdb TableName # Export to CSV

# Option B: Python with pyodbc (Windows)
# Requires Access Database Engine

# Option C: Access itself
# Export each table to CSV manually
# Save queries as SQL text files
```

**Deliverable: Data Dictionary**
| Access Table | Access Column | Type | IP2A Table | IP2A Column | Transform |
|--------------|---------------|------|------------|-------------|-----------|
| tblMembers | MemberID | AutoNumber | members | id | Direct |
| tblMembers | LastName | Text | members | last_name | Direct |
| tblMembers | SSN | Text | members | ssn_last_four | Last 4 only |
| tblHours | WeekEnd | Date | mr_hour_submissions | week_ending | Direct |
| ... | ... | ... | ... | ... | ... |

**Acceptance Criteria:**
- [ ] Complete inventory of Access objects
- [ ] Mapping document complete
- [ ] Transformation rules defined
- [ ] Gaps identified and addressed

### Milestone 5.2: Query Translation
**Time Estimate:** 8-12 hours
**Dependency:** 5.1
**Week:** 32-33

**Tasks:**
- [ ] Extract all Access queries
- [ ] Categorize by type (select, action, crosstab)
- [ ] Translate each to SQLAlchemy/PostgreSQL
- [ ] Test with exported sample data
- [ ] Document any logic changes
- [ ] Create equivalent service methods

**Query Translation Reference:**
| Access SQL | PostgreSQL/SQLAlchemy |
|------------|----------------------|
| `IIf(x, y, z)` | `case([(x, y)], else_=z)` |
| `Nz(value, 0)` | `coalesce(value, 0)` |
| `DateDiff("d", d1, d2)` | `d2 - d1` |
| `DateAdd("m", 1, d)` | `d + interval '1 month'` |
| `Left(s, n)` | `substr(s, 1, n)` |
| `Mid(s, start, len)` | `substr(s, start, len)` |
| `& (concat)` | `\|\|` or `concat()` |
| `TRANSFORM...PIVOT` | Requires manual crosstab logic |
| `Parameters [prompt]` | Function parameter |

**Acceptance Criteria:**
- [ ] All queries translated
- [ ] Queries produce same results as Access
- [ ] Complex queries documented with explanation

### Milestone 5.3: Report Recreation
**Time Estimate:** 15-25 hours (varies by report count/complexity)
**Dependency:** 5.2
**Week:** 33-36

**Tasks:**
- [ ] Obtain PDF printouts of all Access reports
- [ ] Create report inventory with priority
- [ ] Recreate each report in priority order
- [ ] Match layout as closely as practical
- [ ] Add improvements where sensible (web view, CSV export)
- [ ] Test with real data
- [ ] Get sign-off on each report from owner

**Report Recreation Process:**
```
For each report:
1. Review PDF printout (visual reference)
2. Identify source query/queries
3. Create SQLAlchemy query (from 5.2)
4. Create Jinja2 template matching layout
5. Add PDF export (WeasyPrint)
6. Add CSV export
7. Test with sample data
8. Review with owner
9. Iterate until approved
```

**Report Inventory Template:**
| # | Report Name | Frequency | Priority | Source Query | Status | Hours |
|---|-------------|-----------|----------|--------------|--------|-------|
| 1 | Weekly Hours by Contractor | Weekly | Critical | qryWeeklyHours | ⬜ | Est: 3 |
| 2 | Monthly Subsidy Summary | Monthly | Critical | qrySubsidy | ⬜ | Est: 4 |
| 3 | Member Year-to-Date | On demand | High | qryMemberYTD | ⬜ | Est: 2 |
| 4 | ... | ... | ... | ... | ⬜ | ... |

**Report Template Structure:**
```
templates/reports/market_recovery/
├── _base_report.html              # Shared layout, print CSS
├── weekly_hours_by_contractor.html
├── monthly_subsidy_summary.html
├── member_ytd.html
├── contractor_summary.html
├── payment_batch.html
└── [additional reports as needed]
```

**Enhancements Over Access:**
| Access Limitation | Our Improvement |
|-------------------|-----------------|
| Print only | Web view + PDF + CSV |
| Fixed parameters | Flexible date ranges, filters |
| Single format | Multiple export formats |
| Desktop only | Web accessible anywhere |
| No mobile | Mobile-responsive |

**Acceptance Criteria:**
- [ ] All critical reports recreated
- [ ] Reports produce same data as Access (validated)
- [ ] Owner signs off on each report
- [ ] PDF output matches print quality expectations

### Milestone 5.4: Data Migration Execution
**Time Estimate:** 8-12 hours
**Dependency:** 5.3
**Week:** 36-37

**Tasks:**
- [ ] Create migration script
- [ ] Export all Access tables to CSV
- [ ] Transform data per mapping rules
- [ ] Load into staging environment
- [ ] Validate row counts
- [ ] Validate data integrity (spot checks)
- [ ] Validate calculations match
- [ ] Run reports, compare to Access output
- [ ] Fix any discrepancies
- [ ] Document migration results

**Migration Script Structure:**
```python
# scripts/migrate_access_data.py

def migrate_all():
    """Master migration function."""
    print("Starting Access data migration...")
    
    # 1. Load CSV exports
    members_df = load_csv('access_exports/tblMembers.csv')
    hours_df = load_csv('access_exports/tblHours.csv')
    # ...
    
    # 2. Transform data
    members_transformed = transform_members(members_df)
    hours_transformed = transform_hours(hours_df)
    # ...
    
    # 3. Load into PostgreSQL
    load_members(members_transformed)
    load_hours(hours_transformed)
    # ...
    
    # 4. Validate
    validate_row_counts()
    validate_sample_records()
    validate_calculations()
    
    print("Migration complete!")
```

**Validation Checklist:**
- [ ] Row counts match (±0 for most tables)
- [ ] Sample records spot-checked (10 per table)
- [ ] Key calculations validated:
  - [ ] Total hours by member (random sample)
  - [ ] Total subsidy by contractor (random sample)
  - [ ] Payment totals by period (random sample)
- [ ] Reports produce identical results

**Acceptance Criteria:**
- [ ] All data migrated successfully
- [ ] Zero data loss
- [ ] Calculations match Access
- [ ] Owner validates sample records

### Milestone 5.5: Parallel Running Period
**Time Estimate:** 4-6 hours (setup) + ongoing monitoring
**Dependency:** 5.4
**Week:** 37-38

**Tasks:**
- [ ] Deploy migrated data to production
- [ ] Train users on new system
- [ ] Run both systems in parallel (2-4 weeks)
- [ ] Compare outputs weekly
- [ ] Document and resolve discrepancies
- [ ] Gather user feedback
- [ ] Make adjustments as needed
- [ ] Set cutover date

**Parallel Running Process:**
```
Week 1-2: Staff enters data in BOTH systems
         Compare reports at end of each week
         Fix any discrepancies found

Week 3-4: Primary entry in new system
         Spot-check against Access
         Users report any issues

Week 5:  Cutover decision
         If stable → retire Access
         If issues → extend parallel period
```

**Cutover Criteria:**
- [ ] Zero critical bugs for 2 weeks
- [ ] Reports match Access output
- [ ] Users comfortable with new system
- [ ] Owner approves cutover

**Acceptance Criteria:**
- [ ] Parallel period completed successfully
- [ ] User sign-off obtained
- [ ] Access database archived (not deleted!)
- [ ] New system is system of record

### Milestone 5.6: Access Retirement
**Time Estimate:** 2-3 hours
**Dependency:** 5.5
**Week:** 38

**Tasks:**
- [ ] Final backup of Access database
- [ ] Archive to secure storage (keep 7+ years)
- [ ] Document archive location
- [ ] Remove Access from daily workflow
- [ ] Update procedures/documentation
- [ ] Celebrate! 🎉

**Archive Checklist:**
- [ ] Access .mdb/.accdb file backed up
- [ ] All CSV exports preserved
- [ ] Migration scripts preserved
- [ ] Mapping documentation preserved
- [ ] Archive location documented in runbook

**Acceptance Criteria:**
- [ ] Access database safely archived
- [ ] New system fully operational
- [ ] Documentation updated
- [ ] Phase 5 complete, tag v1.1.0

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Time availability drops | Medium | High | Realistic estimates, flexible scope |
| Technical blockers | Low | Medium | Architecture docs, fallback options |
| Scope creep | Medium | Medium | Strict phase boundaries, defer to backlog |
| Data migration issues | Medium | High | Parallel testing, rollback plan |
| Integration API changes | Low | Medium | Version pinning, adapter pattern |
| Access DB approval delayed | Medium | Low | Phase 5 is independent; system works without it |
| Access DB schema surprises | Medium | Medium | Build flexible schema, validate early |
| Report complexity underestimated | Medium | Medium | Prioritize critical reports, defer others |
| User resistance to new system | Low | Medium | Involve users early, training, parallel period |

---

## Backlog (Future Phases)

Items explicitly deferred to maintain focus:

**Completed (Originally Backlogged):**
- [x] Dues tracking module - ✅ Phase 4 Complete (January 2026)
- [x] Grievance tracking - ✅ Phase 2 Complete (January 2026)
- [x] Benevolence fund - ✅ Phase 2 Complete (January 2026)
- [x] SALTing activities module - ✅ Phase 2 Complete (January 2026)

**Phase 6+ Candidates:**
- [ ] Member self-service portal (web + mobile)
- [ ] Referral/dispatch module
- [ ] Multi-local support (other IBEW locals)
- [ ] LaborPower data import (for unified reporting)
- [ ] LaborPower replacement (long-term)
- [ ] Mobile app (native iOS/Android)
- [ ] Celery + Redis upgrade (when scheduling needed)
- [ ] Kubernetes deployment (if scaling demands)

**Deliberately NOT Building:**
- LaborPower replacement (use their system, sync data)
- QuickBooks replacement (integrate, don't replace)
- Custom payment processing (use Stripe/Square)

---

## Session Handoff Notes

### For Claude Code Sessions

When starting a session, check:
1. Current milestone in progress
2. Last completed task
3. Any blockers documented
4. Branch status

Typical session goal: Complete 1-2 tasks from current milestone.

### Progress Tracking

Update this document after each session:
- Mark completed tasks with [x]
- Note actual time vs estimate
- Document any decisions made
- Flag any blockers

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-27 | Initial roadmap created |
| 1.1 | 2026-01-28 | Updated backlog - marked Phase 2 and Phase 4 items as complete |

---

*Document created: January 27, 2026*
*Last updated: January 28, 2026*
