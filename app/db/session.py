from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config.settings import settings

# Database URL from settings
DATABASE_URL = settings.DATABASE_URL

# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# FastAPI dependency
def get_db() -> Session:
    """
    FastAPI dependency: yields a SQLAlchemy session and ensures proper cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Optional helper for scripts (seeders, maintenance)
def get_db_session() -> Session:
    """
    Returns a standalone SQLAlchemy session for non-FastAPI scripts.
    """
    db = SessionLocal()
    try:
        return db
    except:
        db.close()
        raise
