from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _bool_str(value: bool) -> str:
    return "true" if value else "false"


@pytest.fixture(scope="session", autouse=True)
def _test_env(tmp_path_factory):
    root = tmp_path_factory.mktemp("math_tutor_test")
    db_path = root / "test.db"
    data_dir = root / "data"

    os.environ["TESTING"] = "true"
    os.environ["DEV_AUTH_BYPASS"] = "true"
    os.environ["DISABLE_RQ_ENQUEUE"] = "true"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["STORAGE_DIR"] = str(data_dir)

    from app.core.config import clear_config_cache
    from app.core.settings import clear_settings_cache
    from app.db.session import reset_db_state

    clear_config_cache()
    clear_settings_cache()
    reset_db_state()

    yield


@pytest.fixture(autouse=True)
def _fresh_db(_test_env):
    from app.core.config import clear_config_cache
    from app.core.settings import clear_settings_cache
    from app.db.models import Base
    from app.db.session import get_engine, reset_db_state

    clear_config_cache()
    clear_settings_cache()
    reset_db_state()
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client(_test_env):
    from app.main import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture()
def db_session(_test_env):
    from app.db.session import get_session_maker

    session = get_session_maker()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def sample_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.fixture()
def dev_user(db_session):
    import uuid

    from app.api.deps import DEV_USER_ID
    from app.db.models import User

    user = db_session.get(User, DEV_USER_ID)
    if user is None:
        user = User(
            id=DEV_USER_ID,
            google_sub="dev-bypass",
            email="dev@example.com",
            name="Dev User",
            avatar_url=None,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture()
def set_bypass_mode(monkeypatch):
    def _set(enabled: bool):
        monkeypatch.setenv("DEV_AUTH_BYPASS", _bool_str(enabled))

        from app.core.config import clear_config_cache
        from app.core.settings import clear_settings_cache
        from app.db.session import reset_db_state

        clear_config_cache()
        clear_settings_cache()
        reset_db_state()

    return _set
