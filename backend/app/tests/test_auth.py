from __future__ import annotations

from fastapi.testclient import TestClient


def test_me_works_in_dev_bypass(client: TestClient):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dev_auth_bypass"] is True
    assert payload["user"]["email"] == "dev@example.com"


def test_protected_requires_auth_when_bypass_disabled(set_bypass_mode):
    set_bypass_mode(False)

    from app.main import create_app

    client = TestClient(create_app())
    response = client.get("/api/documents")
    assert response.status_code == 401
