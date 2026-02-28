from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

from app.core.config import RootConfig, get_app_config


class RuntimeSettings(BaseModel):
    config: RootConfig
    storage_dir: Path
    database_url: str
    redis_url: str
    jwt_secret: str
    dev_auth_bypass: bool
    disable_rq_enqueue: bool
    testing: bool


_TRUE_VALUES = {"1", "true", "yes", "on"}


def _parse_bool(value: str | bool | None, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


@lru_cache(maxsize=1)
def get_settings() -> RuntimeSettings:
    cfg = get_app_config()
    storage_dir = Path(os.getenv("STORAGE_DIR", cfg.app.storage_dir)).resolve()
    database_url = os.getenv("DATABASE_URL", cfg.database.url)
    redis_url = os.getenv("REDIS_URL", cfg.redis.url)
    dev_auth_bypass = _parse_bool(os.getenv("DEV_AUTH_BYPASS"), cfg.app.dev_auth_bypass)
    disable_rq_enqueue = _parse_bool(os.getenv("DISABLE_RQ_ENQUEUE"), False)
    testing = _parse_bool(os.getenv("TESTING"), False)
    jwt_secret = os.getenv("JWT_SECRET", cfg.auth.jwt_secret or "dev-secret")

    return RuntimeSettings(
        config=cfg,
        storage_dir=storage_dir,
        database_url=database_url,
        redis_url=redis_url,
        jwt_secret=jwt_secret,
        dev_auth_bypass=dev_auth_bypass,
        disable_rq_enqueue=disable_rq_enqueue,
        testing=testing,
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()  # type: ignore[attr-defined]
