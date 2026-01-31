# Getting Started with IP2A Development

This guide helps you set up a local development environment for IP2A Database.

## Prerequisites

- **Docker** and **Docker Compose** (for database and services)
- **Python 3.12+** (for backend development)
- **Git** (for version control)
- **VS Code** (recommended) with Python extension

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

# Edit .env with your local settings (defaults usually work)
```

### 3. Start Services

```bash
# Start PostgreSQL and other services
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

# Seed with test data (optional)
./ip2adb seed
```

### 6. Run the Application

```bash
# Start the FastAPI server
uvicorn src.main:app --reload

# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

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

### 7. Run Tests

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=term-missing
```

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Run tests: `pytest -v`
4. Run linting: `ruff check . --fix && ruff format .`
5. Commit with conventional commits: `git commit -m "feat(scope): description"`
6. Push and create PR

## Useful Commands

```bash
# Database CLI
./ip2adb seed              # Seed test data
./ip2adb integrity --repair # Check and fix data integrity
./ip2adb load --quick       # Quick load test

# Docker
docker-compose logs -f api  # Follow API logs
docker-compose down         # Stop all services
docker-compose up -d --build # Rebuild and start

# Database
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head        # Apply migrations
alembic downgrade -1        # Rollback one migration
```

## Project Structure

```
IP2A-Database-v2/
├── src/
│   ├── api/           # FastAPI routes
│   ├── db/            # Database models and enums
│   ├── services/      # Business logic layer
│   └── tests/         # Test files
├── docs/              # Documentation
├── alembic/           # Database migrations
└── docker-compose.yml # Service definitions
```

## Next Steps

- Read [System Overview](../architecture/SYSTEM_OVERVIEW.md) to understand the architecture
- Check [Architecture Decisions](../decisions/README.md) for context on design choices
- Review [Coding Standards](../standards/coding-standards.md) before contributing

## Troubleshooting

### Database won't start
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Fresh start
```

### Port already in use
Check for other services on ports 5432 (PostgreSQL) or 8000 (API).

### Import errors
Ensure you're in the virtual environment and have run `pip install -r requirements.txt`.

---

*Last updated: 2026-01-28*
