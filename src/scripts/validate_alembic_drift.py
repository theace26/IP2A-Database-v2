"""
Fail if SQLAlchemy models and Alembic migrations are out of sync.
This does NOT generate or apply migrations.
"""

import sys
from pathlib import Path

from alembic import context
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.autogenerate import compare_metadata

from sqlalchemy import engine_from_config, pool

# -------------------------------------------------------------------
# Path bootstrap (same pattern as validate_imports)
# -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# -------------------------------------------------------------------
# Imports AFTER path setup
# -------------------------------------------------------------------
from src.db.base import Base  # noqa: E402

ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"

# -------------------------------------------------------------------
# Drift detection
# -------------------------------------------------------------------
def main() -> None:
    alembic_cfg = Config(str(ALEMBIC_INI))
    script = ScriptDirectory.from_config(alembic_cfg)

    connectable = engine_from_config(
        alembic_cfg.get_section(alembic_cfg.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=False,
        )

        with context.begin_transaction():
            diffs = compare_metadata(context, Base.metadata)

    if diffs:
        print("\n❌ ALEMBIC ↔ MODEL DRIFT DETECTED\n")
        for diff in diffs:
            print(diff)
        print("\n👉 Run:")
        print("   alembic revision --autogenerate -m \"describe change\"")
        sys.exit(1)

    print("✅ Alembic ↔ model schema in sync")


if __name__ == "__main__":
    main()
