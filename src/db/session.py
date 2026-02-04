from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config.settings import settings

# Database URL from settings (uses property that handles Railway's postgres:// format)
DATABASE_URL = settings.database_url

# SQLAlchemy engine with production-ready pool settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DB_ECHO,
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
