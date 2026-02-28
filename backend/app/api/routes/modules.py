from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Document, Module, ModuleAsset, ModuleAssetStatus, ModuleStatus, User
from app.db.session import get_db
from app.services.pipeline.generate_module_assets_job import enqueue_generate_module_assets_job

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
