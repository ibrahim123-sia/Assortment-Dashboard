import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_config

config = get_config()

# If the database URL starts with postgres://, replace with postgresql:// for SQLAlchemy compatibility
db_url = config.SQLALCHEMY_DATABASE_URI
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Enable connection pooling and pre-ping for PostgreSQL robustness
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=10 if not db_url.startswith("sqlite") else None,
    max_overflow=20 if not db_url.startswith("sqlite") else None,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
