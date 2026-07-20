from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings
import os

DATABASE_URL = settings.DATABASE_URL

# QueuePool for PostgreSQL (production), NullPool for SQLite (dev)
use_queue_pool = DATABASE_URL.startswith("postgresql")
pool_kwargs = {}
if use_queue_pool:
    pool_kwargs["poolclass"] = QueuePool
    pool_kwargs["pool_size"] = 10
    pool_kwargs["max_overflow"] = 20
else:
    pool_kwargs["poolclass"] = NullPool

# SQLite needs check_same_thread=False for multi-threaded access
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    **pool_kwargs,
    connect_args=connect_args,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
