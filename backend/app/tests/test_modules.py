from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.db.models import Document, DocumentChunk, DocumentStatus, Module, ModuleStatus, User
from app.services.storage import LocalStorage


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


def test_module_chat_endpoint(client: TestClient, db_session, dev_user: User, monkeypatch):
    doc = Document(
        user_id=dev_user.id,
        title="Algebra",
        filename="alg.pdf",
        storage_path="/tmp/alg.pdf",
        status=DocumentStatus.PARSED,
    )
    db_session.add(doc)
    db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        page_start=1,
        page_end=1,
        text="To solve 2x + 3 = 11, subtract 3 then divide by 2.",
        meta={"char_count": 48},
    )
    db_session.add(chunk)
    db_session.flush()

    module = Module(
        document_id=doc.id,
        title="Linear Equations",
        summary="Solve one-variable equations",
        prerequisites=["Arithmetic"],
        chunk_refs=[str(chunk.id)],
        status=ModuleStatus.READY,
    )
    db_session.add(module)
    db_session.commit()

    class FakeProvider:
        chat_model = "mistral-small-latest"

        def generate_chat_text(self, messages):
            assert any("Module context:" in m["content"] for m in messages if m["role"] == "system")
            assert messages[-1]["role"] == "user"
            return "Subtract 3 from both sides, then divide by 2."

    monkeypatch.setattr("app.api.routes.modules.OpenAICompatibleProvider", FakeProvider)

    response = client.post(
        f"/api/modules/{module.id}/chat",
        json={
            "message": "How do I solve 2x + 3 = 11?",
            "history": [{"role": "user", "content": "Give me the steps"}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["module_id"] == str(module.id)
    assert body["model"] == "mistral-small-latest"
    assert "Subtract 3" in body["answer"]


def test_module_chat_stream_endpoint(client: TestClient, db_session, dev_user: User, monkeypatch):
    doc = Document(
        user_id=dev_user.id,
        title="Physics",
        filename="physics.pdf",
        storage_path="/tmp/physics.pdf",
        status=DocumentStatus.PARSED,
    )
    db_session.add(doc)
    db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        page_start=1,
        page_end=1,
        text="Velocity is displacement per unit time.",
        meta={"char_count": 39},
    )
    db_session.add(chunk)
    db_session.flush()

    module = Module(
        document_id=doc.id,
        title="Velocity Basics",
        summary="Intro to velocity",
        prerequisites=[],
        chunk_refs=[str(chunk.id)],
        status=ModuleStatus.READY,
    )
    db_session.add(module)
    db_session.commit()

    class FakeProvider:
        chat_model = "mistral-chat-test"

        def stream_chat_text(self, messages):
            assert messages[-1]["role"] == "user"
            yield "Velocity "
            yield "is displacement over time."

    monkeypatch.setattr("app.api.routes.modules.OpenAICompatibleProvider", FakeProvider)

    with client.stream(
        "POST",
        f"/api/modules/{module.id}/chat/stream",
        json={"message": "What is velocity?", "history": []},
    ) as response:
        assert response.status_code == 200
        lines = [line for line in response.iter_lines() if line]

    events = [json.loads(line) for line in lines]
    assert events[0]["type"] == "meta"
    assert events[0]["model"] == "mistral-chat-test"
    token_text = "".join(evt.get("delta", "") for evt in events if evt.get("type") == "token")
    assert token_text == "Velocity is displacement over time."
    assert events[-1]["type"] == "done"


def test_delete_module_deletes_assets(client: TestClient, db_session, dev_user: User):
    doc = Document(
        user_id=dev_user.id,
        title="Trigonometry",
        filename="trig.pdf",
        storage_path="/tmp/trig.pdf",
        status=DocumentStatus.PARSED,
    )
    db_session.add(doc)
    db_session.flush()

    module = Module(
        document_id=doc.id,
        title="Sine and Cosine",
        summary="Ratios on right triangles",
        prerequisites=[],
        chunk_refs=[],
        status=ModuleStatus.READY,
    )
    db_session.add(module)
    db_session.commit()

    storage = LocalStorage()
    module_id = str(module.id)
    module_paths = [
        storage.audio_path(module_id),
        storage.captions_path(module_id),
        storage.video_path(module_id),
        storage.final_path(module_id),
    ]
    for path in module_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
        assert path.exists()

    manim_workdir = storage.manim_workdir(module_id)
    marker = Path(manim_workdir) / "marker.txt"
    marker.write_text("artifact", encoding="utf-8")
    assert marker.exists()

    delete_res = client.delete(f"/api/modules/{module.id}")
    assert delete_res.status_code == 204

    get_res = client.get(f"/api/modules/{module.id}")
    assert get_res.status_code == 404

    for path in module_paths:
        assert not path.exists()
    assert not manim_workdir.exists()


def test_delete_module_enforces_ownership(client: TestClient, db_session, dev_user: User):
    other_user = User(
        id=uuid.uuid4(),
        google_sub="other-delete-sub",
        email="other-delete@example.com",
        name="Other Delete User",
        avatar_url=None,
    )
    db_session.add(other_user)
    db_session.flush()

    doc = Document(
        user_id=other_user.id,
        title="Private Geometry",
        filename="private.pdf",
        storage_path="/tmp/private.pdf",
        status=DocumentStatus.PARSED,
    )
    db_session.add(doc)
    db_session.flush()

    module = Module(
        document_id=doc.id,
        title="Private Triangles",
        summary="Only owner can delete",
        prerequisites=[],
        chunk_refs=[],
        status=ModuleStatus.READY,
    )
    db_session.add(module)
    db_session.commit()

    delete_res = client.delete(f"/api/modules/{module.id}")
    assert delete_res.status_code == 404
