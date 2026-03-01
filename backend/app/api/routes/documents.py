from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Document, Module, User
from app.db.session import get_db
from app.services.pipeline.parse_document_job import enqueue_parse_document_job
from app.services.storage import LocalStorage

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _serialize_document(doc: Document) -> dict:
    return {
        "id": str(doc.id),
        "user_id": str(doc.user_id),
        "title": doc.title,
        "filename": doc.filename,
        "storage_path": doc.storage_path,
        "status": doc.status.value,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat(),
    }


def _serialize_module(module: Module) -> dict:
    return {
        "id": str(module.id),
        "document_id": str(module.document_id),
        "title": module.title,
        "summary": module.summary,
        "prerequisites": module.prerequisites,
        "chunk_refs": module.chunk_refs,
        "status": module.status.value,
        "created_at": module.created_at.isoformat(),
        "updated_at": module.updated_at.isoformat(),
    }


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    filename = file.filename
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    title = os.path.splitext(filename)[0]
    document = Document(
        user_id=user.id,
        title=title,
        filename=filename,
        storage_path="",
    )
    db.add(document)
    db.flush()

    storage = LocalStorage()
    saved_path = storage.save_pdf(str(document.id), payload)
    document.storage_path = str(saved_path)
    db.commit()
    db.refresh(document)

    job = enqueue_parse_document_job(db, user_id=user.id, document_id=document.id)

    return {
        "document_id": str(document.id),
        "job_id": str(job.id),
    }


@router.get("")
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).all()
    return {"documents": [_serialize_document(doc) for doc in docs]}


@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _serialize_document(doc)


@router.get("/{document_id}/modules")
def list_document_modules(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    modules = db.query(Module).filter(Module.document_id == doc.id).order_by(Module.created_at.asc()).all()
    return {"modules": [_serialize_module(module) for module in modules]}


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    module_ids = [str(item[0]) for item in db.query(Module.id).filter(Module.document_id == doc.id).all()]
    storage = LocalStorage()
    storage.delete_document_files(str(doc.id), module_ids)

    db.delete(doc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
