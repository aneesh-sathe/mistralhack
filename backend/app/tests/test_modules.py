from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.db.models import Document, DocumentStatus, Module, ModuleStatus, User


def test_modules_list_shape_and_ownership(client: TestClient, db_session, dev_user: User):
    doc = Document(
        user_id=dev_user.id,
        title="Algebra",
        filename="alg.pdf",
        storage_path="/tmp/alg.pdf",
        status=DocumentStatus.PARSED,
    )
    db_session.add(doc)
    db_session.flush()

    module = Module(
        document_id=doc.id,
        title="Linear Equations",
        summary="Solve one-variable equations",
        prerequisites=["Arithmetic"],
        chunk_refs=[],
        status=ModuleStatus.READY,
    )
    db_session.add(module)

    other_user = User(
        id=uuid.uuid4(),
        google_sub="other-sub",
        email="other@example.com",
        name="Other User",
        avatar_url=None,
    )
    db_session.add(other_user)
    db_session.flush()

    other_doc = Document(
        user_id=other_user.id,
        title="Geometry",
        filename="geo.pdf",
        storage_path="/tmp/geo.pdf",
        status=DocumentStatus.PARSED,
    )
    db_session.add(other_doc)
    db_session.flush()

    other_module = Module(
        document_id=other_doc.id,
        title="Triangles",
        summary="Triangle basics",
        prerequisites=[],
        chunk_refs=[],
        status=ModuleStatus.READY,
    )
    db_session.add(other_module)
    db_session.commit()

    modules_res = client.get(f"/api/documents/{doc.id}/modules")
    assert modules_res.status_code == 200
    payload = modules_res.json()
    assert "modules" in payload
    assert payload["modules"][0]["title"] == "Linear Equations"

    own_module_res = client.get(f"/api/modules/{module.id}")
    assert own_module_res.status_code == 200

    forbidden_res = client.get(f"/api/modules/{other_module.id}")
    assert forbidden_res.status_code == 404
