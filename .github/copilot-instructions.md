<!-- GitHub Copilot instructions for the IP2A-Database-v2 repository -->
# GitHub Copilot instructions — IP2A-Database-v2

Quick orientation (what matters): this repository is a FastAPI + SQLAlchemy backend
for the IP2A program. The runtime entry is `app.main:app` (see `app/main.py`).

Key directories and their responsibilities
- `app/main.py`: FastAPI app & router registration (CORS and health endpoints).
- `app/routers/`: HTTP route handlers. Routers are thin and delegate to `services`.
- `app/services/`: Business logic that uses SQLAlchemy sessions; services perform
  commits/refreshes and return ORM model instances.
- `app/models/`: SQLAlchemy ORM models (use `app/db/base.py` Declarative `Base`).
- `app/schemas/`: Pydantic v2 DTOs used for request/response validation. Note
  `from_attributes = True` in response models (Pydantic v2 replacement for orm_mode).
- `app/db/`: `session.py` exposes `get_db` dependency and `SessionLocal` factory;
  `base.py` defines `Base` for models.
- `app/seed/`: DB seeding helpers; run full seed with `python -m app.seed.run_seed`.
- `app/tests/`: project tests (run with `pytest`).
- migrations: Alembic config in `alembic.ini`, scripts in `app/db/migrations`.

Important conventions and patterns (do not override lightly)
- Router → Service pattern: add endpoints in `app/routers/<name>.py` that call
  functions from `app/services/<name>_service.py`. Routers use `Depends(get_db)`.
- Services operate on SQLAlchemy ORM objects and are responsible for committing
  and refreshing objects before returning them to the router.
- Pydantic v2: request models are simple `BaseModel` subclasses; response models
  set `class Config: from_attributes = True` so Pydantic reads attributes from ORM objects.
- DB lifecycle: use the `get_db` FastAPI dependency for request-scoped sessions;
  for scripts use `get_db_session()` from `app/db/session.py`.
- M2M & relationships: many-to-many associations are implemented in
  `app/models/associations.py` — when manipulating relationships, services append/remove
  objects and then `db.commit()` + `db.refresh()` the parent.

Common developer commands
- Dev server (hot reload): `./run_dev.sh` or
  `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Production server: `./run_prod.sh` (uses multiple workers)
- Run tests: `pytest -q` (this repository uses `pytest` and `pytest-asyncio`)
- Run DB seeds: `python -m app.seed.run_seed`
- Alembic migrations:
  - Create revision: `alembic revision --autogenerate -m "describe change"`
  - Apply migrations: `alembic upgrade head`
  - `alembic.ini` uses `script_location = app/db/migrations`
- Environment: `app/config/settings.py` reads `.env` (see `Settings`); set `DATABASE_URL`.

Examples / recipes
- Add a new resource `widgets` (high-level steps):
  1. Create `app/models/widget.py` (use `Base`, define columns and relationships).
  2. Create `app/schemas/widget.py` with `WidgetCreate`, `WidgetUpdate`, `WidgetRead`
     and set `from_attributes = True` on the read model.
  3. Implement `app/services/widget_service.py` — use the existing service files as templates.
  4. Add router `app/routers/widgets.py` exposing endpoints and use `Depends(get_db)`.
  5. Register the router in `app/main.py` (include it near the other routers).

Notes about tests and style
- Tests live under `app/tests/`. Use `pytest` to run them. The project lists `ruff` and
  `mypy` in `requirements.txt` for linting and static checks.
- Prefer reusing service functions instead of duplicating DB logic inside routers.

Pitfalls / gotchas
- Pydantic v2: do not use `orm_mode = True`; use `from_attributes = True` on response models.
- Services commit the DB session. If you need transactional composition across multiple
  service calls, be explicit about session handling (pass the same `db` session).
- Alembic: `alembic.ini` references the local `app` package; ensure `DATABASE_URL` is
  available to the alembic env (export `DATABASE_URL` or set in `.env`) before running migrations.

If anything here is unclear or you'd like examples expanded (tests, CI steps, or a
template PR checklist), tell me which area to expand and I'll iterate.
