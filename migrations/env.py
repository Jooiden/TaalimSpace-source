from alembic import context

from app import models  # noqa: F401
from app.config import get_settings
from app.database import Base, get_engine

target_metadata = Base.metadata

if context.is_offline_mode():
    database_url = get_settings().database_url
    if not database_url:
        raise RuntimeError("Set DATABASE_URL before generating migration SQL")
    context.configure(url=database_url, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with get_engine().connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
