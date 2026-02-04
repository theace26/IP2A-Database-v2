# Getting Started with IP2A Development

> **Document Created:** January 27, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.1
> **Status:** Active — Developer Onboarding Guide
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Prerequisites

- **Docker** and **Docker Compose** (for local PostgreSQL)
- **Python 3.12+** (backend)
- **Git** (version control)
- **VS Code** (recommended) with Python extension

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/theace26/IP2A-Database-v2.git
cd IP2A-Database-v2
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your local settings (defaults usually work for development)
```

### 3. Start Services

```bash
# Start PostgreSQL via Docker
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 4. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 5. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Seed with test data (optional but recommended for development)
./ip2adb seed
```

### 6. Run the Application

```bash
# Start the Flask development server
flask run --debug

# Application available at http://localhost:5000
```

> **Note:** Production deployment is on Railway, which runs the application via Gunicorn. For local development, `flask run --debug` provides auto-reload on code changes.

### 7. First-Time Setup

When the database is seeded, a default admin account is created:

- Email: `admin@ibew46.com`
- Password: (see `src/seed/auth_seed.py`)

**Important:** On first access, you'll be redirected to `/setup`:

1. Create your own administrator account (cannot use `admin@ibew46.com`)
2. Optionally disable the default admin account (recommended for production)
3. Log in with your new credentials

The default admin account:

- Exists for system recovery purposes
- Cannot be deleted, only disabled
- Email/password cannot be changed via the setup page
- Can be re-enabled from Staff Management if needed

### 8. Run Tests

```bash
# Run all tests (~470 tests)
pytest -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest src/tests/test_dues.py -v
```

---

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Run tests: `pytest -v`
4. Run linting: `ruff check . --fix && ruff format .`
5. Commit with conventional commits: `git commit -m "feat(scope): description"`
6. Push and create PR against `develop` branch

### Branch Strategy

- **`main`** — Production-ready code (needs merge from `develop`)
- **`develop`** — Active development branch at v0.9.4-alpha (Railway deploys from here)
- **Feature branches** — Created from `develop` for new work

---

## Useful Commands

```bash
# Database CLI
./ip2adb seed              # Seed test data
./ip2adb integrity --repair # Check and fix data integrity
./ip2adb load --quick       # Quick load test

# Docker (local development)
docker-compose logs -f      # Follow service logs
docker-compose down         # Stop all services
docker-compose up -d --build # Rebuild and start

# Database migrations
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head        # Apply migrations
alembic downgrade -1        # Rollback one migration

# Code quality
ruff check . --fix          # Lint and auto-fix
ruff format .               # Format code
```

---

## Project Structure

```
IP2A-Database-v2/
├── src/
│   ├── api/              # Flask Blueprints (route handlers)
│   ├── db/               # Database models, enums, session management
│   │   └── enums.py      # Consolidated enum definitions
│   ├── services/         # Business logic layer
│   ├── templates/        # Jinja2 templates (HTMX + Alpine.js + DaisyUI)
│   ├── static/           # CSS, JS, images, service worker
│   ├── seed/             # Database seed scripts
│   └── tests/            # Test files (~470 tests)
├── docs/                 # Documentation
│   ├── architecture/     # System architecture docs
│   ├── decisions/        # Architecture Decision Records (14 ADRs)
│   ├── guides/           # How-to guides
│   ├── phase7/           # Phase 7 planning documents
│   ├── reference/        # API reference, stress/load testing
│   ├── reports/          # Session logs, analytics reports
│   └── standards/        # Coding standards, naming conventions
├── alembic/              # Database migrations
├── scripts/              # Utility scripts
├── docker-compose.yml    # Local service definitions
├── CLAUDE.md             # Project context for AI assistance
├── CHANGELOG.md          # Version history
└── requirements.txt      # Python dependencies
```

### Technical Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, Flask, SQLAlchemy 2.x |
| **Frontend** | Jinja2, HTMX, Alpine.js, DaisyUI (Tailwind CSS) |
| **Database** | PostgreSQL 16 |
| **Payments** | Stripe (Checkout Sessions + Webhooks) |
| **Monitoring** | Sentry |
| **PDF Export** | WeasyPrint |
| **Excel Export** | openpyxl |
| **Testing** | pytest (~470 tests) |
| **Linting** | ruff |
| **Deployment** | Railway (production) |

---

## Next Steps

- Read [System Overview](../architecture/SYSTEM_OVERVIEW.md) to understand the architecture
- Check [Architecture Decisions](../decisions/README.md) for context on design choices (14 ADRs)
- Review [Coding Standards](../standards/coding-standards.md) before contributing
- Review [Naming Conventions](../standards/naming-conventions.md) for consistent patterns
- Read [End-of-Session Documentation](../guides/END_OF_SESSION_DOCUMENTATION.md) for session documentation requirements

---

## Troubleshooting

### Database won't start

```bash
docker-compose down -v  # Remove volumes (WARNING: deletes data)
docker-compose up -d    # Fresh start
```

### Port already in use

Check for other services on ports 5432 (PostgreSQL) or 5000 (Flask).

### Import errors

Ensure you're in the virtual environment and have run `pip install -r requirements.txt`.

### Enum import errors

```python
# ✅ CORRECT — use consolidated enums
from src.db.enums import CohortStatus, MemberStatus

# ❌ WRONG — old location (deprecated)
from src.models.enums import CohortStatus
```

### Railway deployment issues

The production deployment runs on Railway with auto-deploy from the `develop` branch. If deployment fails, check the Railway dashboard for build logs and Sentry for runtime errors.

---

> **End-of-Session Rule:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

| Cross-Reference | Location |
|----------------|----------|
| System Overview | `/docs/architecture/SYSTEM_OVERVIEW.md` |
| ADR Index | `/docs/decisions/README.md` |
| Coding Standards | `/docs/standards/coding-standards.md` |
| Naming Conventions | `/docs/standards/naming-conventions.md` |
| Testing Strategy | `/docs/guides/testing-strategy.md` |
| End-of-Session Documentation | `/docs/guides/END_OF_SESSION_DOCUMENTATION.md` |
| CLAUDE.md | `/CLAUDE.md` |

---

*Document Version: 1.1*
*Last Updated: February 3, 2026*
