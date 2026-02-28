from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.models import Job, JobStatus, User


def test_job_status_endpoint_returns_progress(client: TestClient, db_session, dev_user: User):
    job = Job(
        user_id=dev_user.id,
        type="parse_document",
        payload={"document_id": "abc"},
        status=JobStatus.running,
        progress={"stage": "CHUNKING", "percent": 42, "history": ["QUEUED", "PARSING", "CHUNKING"]},
        result={},
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    response = client.get(f"/api/jobs/{job.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["progress"]["stage"] == "CHUNKING"
    assert body["progress"]["percent"] == 42
