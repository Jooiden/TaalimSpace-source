from collections.abc import Iterator
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if not url:
        raise HTTPException(status_code=503, detail="База данных ещё не настроена.")
    if not url.startswith("postgresql+psycopg://"):
        raise HTTPException(status_code=503, detail="Настройте PostgreSQL через драйвер psycopg.")
    return create_engine(url, pool_pre_ping=True)


def get_db() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
