from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.Auth.config import DATABASE_URL

# For SQLAlchemy 2.x with psycopg2-binary, use postgresql+psycopg2:// dialect
_database_url = DATABASE_URL
if _database_url.startswith("postgresql://"):
    _database_url = _database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
engine = create_engine(_database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

import app.models.db_models  # noqa: E402, F401


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
