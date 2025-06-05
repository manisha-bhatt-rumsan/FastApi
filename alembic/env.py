import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context

# Import your engine and Base
from models import Base, engine
from schemas import User, Document, Quiz, Question  # <-- Force model registration


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = Base.metadata

def run_migrations_offline():
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


def run_migrations_online():
    """Run migrations in 'online' mode."""    
    async def run_migrations():
        async with engine.begin() as conn:
            context.configure(
                connection=conn,
                target_metadata=target_metadata,
                compare_type=True  # optional, useful for detecting column type changes
            )
            with context.begin_transaction():
                context.run_migrations()

    asyncio.run(run_migrations())



if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
