from __future__ import annotations

from fastapi.testclient import TestClient


def test_upload_creates_document_and_job(client: TestClient, sample_pdf_bytes: bytes):
    response = client.post(
        "/api/documents",
        files={"file": ("algebra.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert "document_id" in body
    assert "job_id" in body

    docs_res = client.get("/api/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()["documents"]
    assert len(docs) == 1
    assert docs[0]["filename"] == "algebra.pdf"

    job_res = client.get(f"/api/jobs/{body['job_id']}")
    assert job_res.status_code == 200
    job = job_res.json()
    assert job["status"] == "queued"
    assert job["progress"]["stage"] == "QUEUED"


def test_delete_document(client: TestClient, sample_pdf_bytes: bytes):
    response = client.post(
        "/api/documents",
        files={"file": ("to-delete.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    document_id = response.json()["document_id"]

    delete_res = client.delete(f"/api/documents/{document_id}")
    assert delete_res.status_code == 204

    docs_res = client.get("/api/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()["documents"]
    assert all(doc["id"] != document_id for doc in docs)
