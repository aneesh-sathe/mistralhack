from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Document, Module, ModuleAsset, User
from app.db.session import get_db

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


CHUNK_SIZE = 1024 * 1024


def _owned_asset(db: Session, module_id: str, user_id: str) -> ModuleAsset:
    module = (
        db.query(Module)
        .join(Document, Module.document_id == Document.id)
        .filter(Module.id == module_id, Document.user_id == user_id)
        .first()
    )
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    asset = db.query(ModuleAsset).filter(ModuleAsset.module_id == module.id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Module assets not found")
    return asset


def _parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    try:
        units, values = range_header.strip().split("=", 1)
        if units != "bytes":
            raise ValueError("Unsupported range unit")
        start_str, end_str = values.split("-", 1)
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
    except Exception as exc:
        raise HTTPException(status_code=416, detail="Invalid range header") from exc

    if start < 0 or end >= file_size or start > end:
        raise HTTPException(status_code=416, detail="Requested range not satisfiable")
    return start, end


def _iter_file(path: Path, start: int, end: int):
    with path.open("rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk = f.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@router.get("/video/{module_id}")
def stream_video(
    module_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    asset = _owned_asset(db, module_id, str(user.id))
    if not asset.final_muxed_path:
        raise HTTPException(status_code=404, detail="Final video not available")

    path = Path(asset.final_muxed_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Final video file not found")

    file_size = path.stat().st_size
    range_header = request.headers.get("range")
    if range_header:
        start, end = _parse_range_header(range_header, file_size)
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(end - start + 1),
        }
        return StreamingResponse(
            _iter_file(path, start, end),
            media_type="video/mp4",
            headers=headers,
            status_code=status.HTTP_206_PARTIAL_CONTENT,
        )

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
    }
    return StreamingResponse(_iter_file(path, 0, file_size - 1), media_type="video/mp4", headers=headers)


@router.get("/captions/{module_id}")
def get_captions(module_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = _owned_asset(db, module_id, str(user.id))
    if not asset.captions_srt_path:
        raise HTTPException(status_code=404, detail="Captions not available")
    path = Path(asset.captions_srt_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Captions file not found")
    return PlainTextResponse(path.read_text(encoding="utf-8"), media_type="text/plain")


@router.get("/script/{module_id}")
def get_script(module_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = _owned_asset(db, module_id, str(user.id))
    return JSONResponse({"script_text": asset.script_text or "", "script_json": asset.script_json or {}})
