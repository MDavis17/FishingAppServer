import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Load environment variables from .env.local (Neon) or .env
_env_local = Path(__file__).resolve().parents[1] / ".env.local"
_env_file = Path(__file__).resolve().parents[1] / ".env"
if _env_local.exists():
    load_dotenv(_env_local)
elif _env_file.exists():
    load_dotenv(_env_file)

from app.Auth.config import DATABASE_URL
from app.Auth.database import Base
import app.Auth.models  # noqa: F401
import app.models.db_models  # noqa: F401

# Use unpooled connection for migrations (best practice for Neon with PgBouncer)
# Falls back to DATABASE_URL if unpooled is not set
MIGRATION_DATABASE_URL = os.getenv("DATABASE_URL_UNPOOLED", DATABASE_URL)

# For SQLAlchemy 2.x with psycopg2-binary, use postgresql+psycopg2:// dialect
if MIGRATION_DATABASE_URL.startswith("postgresql://"):
    MIGRATION_DATABASE_URL = MIGRATION_DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg2://", 1
    )

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", MIGRATION_DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
