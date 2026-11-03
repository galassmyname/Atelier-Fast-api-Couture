"""Configuration d'Alembic : relie les migrations à nos modèles et au .env."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.config import settings  # lit DATABASE_URL depuis le .env
from app.database import Base  # classe mère des modèles
import app.models  # noqa: F401  -> importe tous les modèles pour qu'Alembic les détecte

# Objet de configuration Alembic (lit alembic.ini)
config = context.config

# On injecte l'URL de la base depuis le .env (et non depuis alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Active les logs définis dans alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnées de nos modèles : Alembic compare la base à ces tables
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
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
