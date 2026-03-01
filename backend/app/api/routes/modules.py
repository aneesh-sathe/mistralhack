from __future__ import annotations

import json
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Document, DocumentChunk, Module, ModuleAsset, ModuleAssetStatus, ModuleStatus, User
from app.db.session import get_db
from app.services.llm.openai_provider import OpenAICompatibleProvider
from app.services.llm.prompts import module_chat_system_prompt
from app.services.pipeline.generate_module_assets_job import enqueue_generate_module_assets_job
from app.services.storage import LocalStorage

router = APIRouter(prefix="/api/modules", tags=["modules"])


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


def _serialize_assets(asset: ModuleAsset) -> dict:
    return {
        "id": str(asset.id),
        "module_id": str(asset.module_id),
        "script_text": asset.script_text,
        "script_json": asset.script_json,
        "manim_code": asset.manim_code,
        "audio_path": asset.audio_path,
        "captions_srt_path": asset.captions_srt_path,
        "video_path": asset.video_path,
        "final_muxed_path": asset.final_muxed_path,
        "status": asset.status.value,
        "error": asset.error,
        "created_at": asset.created_at.isoformat(),
        "updated_at": asset.updated_at.isoformat(),
    }


def _get_owned_module(db: Session, module_id: str, user_id: str):
    return (
        db.query(Module)
        .join(Document, Module.document_id == Document.id)
        .filter(Module.id == module_id, Document.user_id == user_id)
        .first()
    )


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ModuleChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatTurn] = Field(default_factory=list)


def _load_module_context(db: Session, module: Module) -> str:
    asset = db.query(ModuleAsset).filter(ModuleAsset.module_id == module.id).first()

    chunk_rows: list[DocumentChunk] = []
    chunk_refs = module.chunk_refs if isinstance(module.chunk_refs, list) else []
    if chunk_refs:
        try:
            chunk_ids = [uuid.UUID(str(item)) for item in chunk_refs]
            chunk_rows = db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
        except Exception:
            chunk_rows = []
    if not chunk_rows:
        chunk_rows = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == module.document_id)
            .order_by(DocumentChunk.page_start.asc())
            .limit(12)
            .all()
        )

    chunk_text = "\n\n".join(chunk.text for chunk in chunk_rows)
    chunk_text = chunk_text[:14000]
    script_text = (asset.script_text or "")[:7000] if asset else ""

    return (
        f"Module title: {module.title}\n"
        f"Module summary: {module.summary}\n"
        f"Prerequisites: {module.prerequisites}\n\n"
        f"Lesson script:\n{script_text}\n\n"
        f"Module source content:\n{chunk_text}"
    )


@router.get("/{module_id}")
def get_module(module_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module = _get_owned_module(db, module_id, str(user.id))
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    return _serialize_module(module)


@router.post("/{module_id}/generate")
def generate_module_assets(module_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module = _get_owned_module(db, module_id, str(user.id))
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    asset = db.query(ModuleAsset).filter(ModuleAsset.module_id == module.id).first()
    if asset is None:
        asset = ModuleAsset(module_id=module.id, status=ModuleAssetStatus.QUEUED)
        db.add(asset)
    else:
        asset.status = ModuleAssetStatus.QUEUED
        asset.error = None

    module.status = ModuleStatus.GENERATING
    db.commit()

    job = enqueue_generate_module_assets_job(db, user_id=user.id, module_id=module.id)
    return {"job_id": str(job.id)}


@router.get("/{module_id}/assets")
def get_module_assets(module_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module = _get_owned_module(db, module_id, str(user.id))
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    asset = db.query(ModuleAsset).filter(ModuleAsset.module_id == module.id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Module assets not found")

    return _serialize_assets(asset)


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(module_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module = _get_owned_module(db, module_id, str(user.id))
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    if module.status == ModuleStatus.GENERATING:
        raise HTTPException(status_code=409, detail="Cannot delete a module while generation is running")

    storage = LocalStorage()
    storage.delete_module_files(str(module.id))

    db.delete(module)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{module_id}/chat")
def chat_with_module(
    module_id: str,
    payload: ModuleChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    module = _get_owned_module(db, module_id, str(user.id))
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    context = _load_module_context(db, module)
    llm = OpenAICompatibleProvider()
    messages: list[dict[str, str]] = [
        {"role": "system", "content": module_chat_system_prompt()},
        {"role": "system", "content": f"Module context:\n{context}"},
    ]

    recent_history = payload.history[-8:]
    for turn in recent_history:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": payload.message})

    answer = llm.generate_chat_text(messages)
    return {
        "answer": answer,
        "model": llm.chat_model,
        "module_id": str(module.id),
    }


@router.post("/{module_id}/chat/stream")
def chat_with_module_stream(
    module_id: str,
    payload: ModuleChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    module = _get_owned_module(db, module_id, str(user.id))
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    context = _load_module_context(db, module)
    llm = OpenAICompatibleProvider()
    messages: list[dict[str, str]] = [
        {"role": "system", "content": module_chat_system_prompt()},
        {"role": "system", "content": f"Module context:\n{context}"},
    ]
    recent_history = payload.history[-8:]
    for turn in recent_history:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": payload.message})

    def event(obj: dict) -> str:
        return json.dumps(obj, ensure_ascii=False) + "\n"

    def stream():
        yield event({"type": "meta", "model": llm.chat_model, "module_id": str(module.id)})
        try:
            for delta in llm.stream_chat_text(messages):
                if delta:
                    yield event({"type": "token", "delta": delta})
            yield event({"type": "done"})
        except Exception as exc:
            yield event({"type": "error", "message": str(exc)})

    return StreamingResponse(stream(), media_type="application/x-ndjson")
