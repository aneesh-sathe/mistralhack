from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.db.models import Document, DocumentChunk, DocumentStatus, Job, JobStatus, Module, ModuleStatus
from app.db.session import get_session_maker
from app.services.chunking import chunk_pages
from app.services.llm.openai_provider import OpenAICompatibleProvider
from app.services.llm.prompts import vlm_ocr_prompt
from app.services.module_extraction import extract_modules_from_chunks
from app.services.pdf_parse import (
    extract_text_per_page,
    is_low_quality_text,
    ocr_pdf_with_tesseract,
    render_pages_for_vlm,
)
from app.services.pipeline.types import set_job_state

logger = logging.getLogger(__name__)


def _create_job(db: Session, *, user_id: uuid.UUID, job_type: str, payload: dict[str, Any]) -> Job:
    job = Job(
        user_id=user_id,
        type=job_type,
        payload=payload,
        status=JobStatus.queued,
        progress={"stage": "QUEUED", "percent": 0, "history": ["QUEUED"]},
        result={},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def enqueue_parse_document_job(db: Session, *, user_id: uuid.UUID, document_id: uuid.UUID) -> Job:
    settings = get_settings()
    job = _create_job(db, user_id=user_id, job_type="parse_document", payload={"document_id": str(document_id)})

    if not settings.disable_rq_enqueue:
        queue = Queue("default", connection=Redis.from_url(settings.redis_url))
        queue.enqueue(
            "app.services.pipeline.parse_document_job.parse_document_job_runner",
            str(job.id),
            str(document_id),
            job_timeout=1800,
        )
    return job


def _choose_best_text(pdf_path: Path, llm_provider: OpenAICompatibleProvider) -> list[str]:
    extracted = extract_text_per_page(pdf_path)
    if not is_low_quality_text(extracted):
        return extracted

    try:
        ocr_pages = ocr_pdf_with_tesseract(pdf_path)
        if not is_low_quality_text(ocr_pages):
            return ocr_pages
        extracted = ocr_pages
    except Exception as exc:
        logger.warning("Tesseract OCR failed: %s", exc)

    settings = get_settings()
    if settings.config.vlm.enabled:
        try:
            images = render_pages_for_vlm(pdf_path)
            vlm_text = llm_provider.vlm_extract_text(images, vlm_ocr_prompt())
            if len(vlm_text.strip()) > 200:
                return [vlm_text.strip()]
        except Exception as exc:
            logger.warning("Optional VLM OCR fallback failed: %s", exc)

    return extracted


def parse_document_job_runner(job_id: str, document_id: str) -> None:
    session_factory = get_session_maker()
    db = session_factory()
    document: Document | None = None
    job: Job | None = None

    try:
        job = db.get(Job, uuid.UUID(job_id))
        document = db.get(Document, uuid.UUID(document_id))
        if not job or not document:
            return

        set_job_state(job, status=JobStatus.running, stage="PARSING", percent=5)
        document.status = DocumentStatus.PARSING
        db.commit()

        llm_provider = OpenAICompatibleProvider()
        page_text = _choose_best_text(Path(document.storage_path), llm_provider)

        set_job_state(job, status=JobStatus.running, stage="CHUNKING", percent=35)
        db.commit()

        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
        db.query(Module).filter(Module.document_id == document.id).delete()

        chunk_rows: list[DocumentChunk] = []
        for chunk in chunk_pages(page_text):
            row = DocumentChunk(
                document_id=document.id,
                page_start=chunk["page_start"],
                page_end=chunk["page_end"],
                text=chunk["text"],
                meta=chunk["metadata"],
            )
            db.add(row)
            chunk_rows.append(row)
        db.flush()

        chunk_payload = [
            {
                "id": row.id,
                "page_start": row.page_start,
                "page_end": row.page_end,
                "text": row.text,
            }
            for row in chunk_rows
        ]

        set_job_state(job, status=JobStatus.running, stage="MODULE_EXTRACTION", percent=60)
        db.commit()

        modules_data = extract_modules_from_chunks(chunk_payload, llm_provider)
        all_chunk_ids = [str(row.id) for row in chunk_rows]
        for item in modules_data:
            chunk_refs = item.get("chunk_refs") or all_chunk_ids
            module = Module(
                document_id=document.id,
                title=item["title"],
                summary=item["summary"],
                prerequisites=item.get("prerequisites", []),
                chunk_refs=chunk_refs,
                status=ModuleStatus.READY,
            )
            db.add(module)

        document.status = DocumentStatus.PARSED
        set_job_state(
            job,
            status=JobStatus.succeeded,
            stage="PARSED",
            percent=100,
            result={"document_id": str(document.id), "module_count": len(modules_data)},
        )
        db.commit()
    except Exception as exc:
        logger.exception("parse_document_job failed")
        db.rollback()

        if job is None:
            job = db.get(Job, uuid.UUID(job_id))
        if document is None:
            document = db.get(Document, uuid.UUID(document_id))

        if document is not None:
            document.status = DocumentStatus.FAILED
        if job is not None:
            set_job_state(job, status=JobStatus.failed, stage="FAILED", percent=100, error=str(exc))
        db.commit()
    finally:
        db.close()
