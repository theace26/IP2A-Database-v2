# Contributing to IP2A Database

Thank you for your interest in contributing to IP2A! This document provides guidelines for contributing.

## Getting Started

1. Clone the repository
2. Copy `.env.compose.example` to `.env.compose`
3. Run `docker-compose up -d`
4. Open in VS Code with Dev Containers extension

See [Getting Started Guide](docs/guides/getting-started.md) for detailed setup.

## Development Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation only

### Commit Messages
Use conventional commits:
- `feat: add member search endpoint`
- `fix: correct date validation in enrollment`
- `docs: update API reference`
- `test: add integration tests for members`
- `refactor: simplify organization service`

### Pull Request Process
1. Create feature branch from `main`
2. Make changes with tests
3. Run `pytest -v` (all tests must pass)
4. Run `ruff check . --fix && ruff format .`
5. Update documentation if needed
6. Submit PR with description of changes

## Code Standards

See [Coding Standards](docs/standards/coding-standards.md) for:
- Naming conventions
- File organization
- Service/Router patterns

## Testing

All PRs must include tests. See [Testing Strategy](docs/guides/testing-strategy.md).

### Running Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest src/tests/test_members.py -v

# Run with coverage
pytest --cov=src --cov-report=term-missing
```

### Test Requirements
- Unit tests for services
- Integration tests for routers
- Minimum 80% code coverage for new code
- All tests must pass before merge

## Documentation

### When to Update Documentation
- New feature → Update relevant guide or create new one
- Major decision → Create ADR (Architecture Decision Record)
- API change → Update reference docs
- Bug fix with lessons learned → Consider ADR or guide update

### Documentation Structure
- `docs/architecture/` - System design documents
- `docs/decisions/` - Architecture Decision Records
- `docs/guides/` - How-to guides
- `docs/reference/` - CLI and API reference
- `docs/reports/` - Test reports and assessments
- `docs/standards/` - Coding standards

## Development Tools

### Database CLI Tool

Use `ip2adb` for all database operations:

```bash
# Seed database
./ip2adb seed

# Check integrity
./ip2adb integrity --no-files

# Run load test
./ip2adb load --quick

# Full test suite
./ip2adb all --quick
```

### Code Quality

```bash
# Lint and format
ruff check . --fix
ruff format .

# Type checking (if using mypy)
mypy src/
```

## Project Structure

```
IP2A-Database-v2/
├── src/
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── routers/             # FastAPI endpoints
│   ├── db/                  # Database utilities
│   └── tests/               # pytest tests
├── docs/                    # Documentation
├── scripts/                 # Automation scripts
└── alembic/                 # Database migrations
```

## Coding Patterns

### Service Pattern

```python
# src/services/model_service.py
def create_model(db: Session, data: ModelCreate) -> Model:
    obj = Model(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_model(db: Session, model_id: int) -> Optional[Model]:
    return db.query(Model).filter(Model.id == model_id).first()
```

### Router Pattern

```python
# src/routers/models.py
@router.post("/", response_model=ModelRead)
def create(data: ModelCreate, db: Session = Depends(get_db)):
    return create_model(db, data)

@router.get("/{model_id}", response_model=ModelRead)
def read(model_id: int, db: Session = Depends(get_db)):
    obj = get_model(db, model_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj
```

### Schema Pattern

```python
# src/schemas/model.py
class ModelBase(BaseModel):
    name: str
    description: Optional[str] = None

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ModelRead(ModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add new table"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head
```

### Migration Guidelines
- Review auto-generated migrations carefully
- Test migrations on development data first
- Include both upgrade and downgrade paths
- Document complex migrations

## Questions?

Open an issue or contact the project maintainer.

---

*Last Updated: January 28, 2026*
