from app.db.base import Base
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context

from app.config.settings import settings
from app.db.session import engine
from app.models import *  # this imports all model metadata as we create them

# Load Alembic config
config = context.config

# Interpret logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy metadata (empty for now — will populate as models are added)
# target_metadata = None #Original
target_metadata = Base.metadata


# --- RUN MIGRATIONS OFFLINE ---
def run_migrations_offline():
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# --- RUN MIGRATIONS ONLINE ---
def run_migrations_online():
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
