"""Alembic environment.

Resolves the DB URL from the same precedence as `database/connection.py`,
so migrations target the same DB as the app at runtime.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from database.connection import DATABASE_URL, Base
import database.models  # noqa: F401  ensure all models are registered
try:
    import database.auth.models  # noqa: F401
except ImportError:
    pass
try:
    import database.clinical.models  # noqa: F401
except ImportError:
    pass
try:
    import database.ops.models  # noqa: F401
except ImportError:
    pass
try:
    import database.v1_1.models  # noqa: F401
except ImportError:
    pass

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
