from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from alembic import context

# Импортируем Base и все модели для автогенерации
from settings import Base, SQL_URL

# Импортируем ВСЕ модели, чтобы Alembic их видел
from src.business.Click.click_table import Clicks
from src.business.Click.pageEvent_table import PageEvent, MicroConversion, CtaClick
from src.business.Contact.contact_table import Contact
from src.business.Works.works_table import Works
from src.business.Category.category_table import Category
from src.business.Users.user_table import Users
from src.business.Quiz.quiz_table import Quiz, QuizQuestion, QuizResult
from src.business.ManyToMany.works_category_association_ import works_category_association

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Устанавливаем URL из settings (конвертируем asyncpg → psycopg2 для sync-миграций)
if SQL_URL:
    sync_url = SQL_URL.replace('+asyncpg', '+psycopg2')
    config.set_main_option('sqlalchemy.url', sync_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


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


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
