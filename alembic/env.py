import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# Ensure app is discoverable on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import models  # noqa: F401
from app.database import DATABASE_URL, Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Use config's sqlalchemy.url if overridden (e.g. by test suite), else application DATABASE_URL
url_from_config = config.get_main_option("sqlalchemy.url")
if not url_from_config or "driver://user:pass@localhost/dbname" in url_from_config:
    db_url = DATABASE_URL.render_as_string(hide_password=False)
    config.set_main_option("sqlalchemy.url", db_url)
else:
    db_url = url_from_config


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
