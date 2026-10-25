import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env.local (Neon) or .env
_env_local = Path(__file__).resolve().parents[2] / ".env.local"
_env_file = Path(__file__).resolve().parents[2] / ".env"
if _env_local.exists():
    load_dotenv(_env_local)
elif _env_file.exists():
    load_dotenv(_env_file)

# Default: local SQLite for development.
# Production PostgreSQL example:
#   DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/fishing_app
# Optional query params: ?sslmode=require
_raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./users.db")

# SQLAlchemy 2.x defaults to psycopg (v3) for "postgresql://" URLs.
# We use psycopg2-binary, so rewrite to "postgresql+psycopg2://" for Postgres.
if _raw_db_url.startswith("postgresql://"):
    DATABASE_URL = _raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
elif _raw_db_url.startswith("postgres://"):
    # Heroku-style URLs use "postgres://" which SQLAlchemy doesn't accept directly
    DATABASE_URL = _raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
else:
    DATABASE_URL = _raw_db_url
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))
