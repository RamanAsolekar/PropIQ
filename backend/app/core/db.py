"""
Database configuration for PostgreSQL using SQLAlchemy.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# For local development we can fallback to SQLite if Postgres isn't provided yet
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./propiq_dev.db")

# Enterprise Connection Pooling settings
is_sqlite = "sqlite" in DATABASE_URL
connect_args = {"check_same_thread": False} if is_sqlite else {}
pool_kwargs = (
    {}
    if is_sqlite
    else {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_pre_ping": True,  # Enables transparent reconnection if DB drops
    }
)

engine = create_engine(DATABASE_URL, connect_args=connect_args, **pool_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
