import asyncio
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.db.models import Base
from app.config import settings

# Alembic Config object
config = context.config

# Interpret the config file for logging
if config.config_file_name:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    """Include/exclude objects from migrations."""
    return True

def render_item(type_, obj, autogen_context):
    """Render items for autogeneration."""
    if type_ == "type" and hasattr(obj, "enums"):
        return obj
    return False

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    print(f"Running offline migration with DB: {url}")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Helper function to run migrations with a connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    """Run migrations in async mode."""
    url = config.get_main_option("sqlalchemy.url")
    print(f"Running async migration with DB: {url}")
    
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
        echo=False,
        future=True
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    url = config.get_main_option("sqlalchemy.url")
    if url and ("asyncpg" in url or "aiomysql" in url or "aiopg" in url):
        asyncio.run(run_async_migrations())
    else:
        print(f"Running sync migration with DB: {url}")
        connectable = create_engine(
            url,
            poolclass=pool.NullPool,
            echo=False,
            future=True
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()