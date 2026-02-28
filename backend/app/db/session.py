from __future__ import annotations

import uuid
from functools import lru_cache

from sqlalchemy import CHAR, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql.type_api import TypeDecorator

from app.core.settings import get_settings

Base = declarative_base()


class GUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        return uuid.UUID(str(value))


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    url = settings.database_url
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False}, future=True)
    return create_engine(url, pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def get_session_maker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    session = get_session_maker()()
    try:
        yield session
    finally:
        session.close()


def reset_db_state() -> None:
    get_session_maker.cache_clear()  # type: ignore[attr-defined]
    get_engine.cache_clear()  # type: ignore[attr-defined]
