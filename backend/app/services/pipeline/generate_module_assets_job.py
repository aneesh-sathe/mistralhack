from __future__ import annotations

import json
import logging
import subprocess
import uuid

from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.db.models import (
    DocumentChunk,
    Job,
    JobStatus,
    Module,
    ModuleAsset,
    ModuleAssetStatus,
    ModuleStatus,
)
from app.db.session import get_session_maker
from app.services.captions.align import transcribe_segments
from app.services.captions.srt import write_srt
from app.services.llm.manim_agent import generate_manim_code, repair_manim_code
from app.services.llm.openai_provider import OpenAICompatibleProvider
from app.services.llm.script_agent import generate_script
from app.services.pipeline.parse_document_job import _create_job
from app.services.pipeline.types import set_job_state
from app.services.render.manim_mcp_renderer import render_module_video_via_mcp
from app.services.render.manim_renderer import render_module_video
from app.services.render.mux import mux_video_audio, retime_video_to_duration
from app.services.storage import LocalStorage
from app.services.tts.elevenlabs_client import ElevenLabsClient

logger = logging.getLogger(__name__)


def _media_duration_seconds(path: str) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        path,
    ]
    output = subprocess.check_output(cmd, text=True)
    payload = json.loads(output)
    return float(payload.get("format", {}).get("duration", 0.0))


def _render_video_for_backend(
    *,
    module_id: str,
    code: str,
    scene_class_name: str,
    quality: str,
    storage: LocalStorage,
):
    settings = get_settings()
    backend = (settings.config.manim.render_backend or "local").strip().lower()
    if backend == "mcp":
        return render_module_video_via_mcp(
            module_id=module_id,
            code=code,
            scene_class_name=scene_class_name,
            quality=quality,
            storage=storage,
        )
    return render_module_video(
        module_id=module_id,
        code=code,
        scene_class_name=scene_class_name,
        quality=quality,
        storage=storage,
    )


def enqueue_generate_module_assets_job(db: Session, *, user_id: uuid.UUID, module_id: uuid.UUID) -> Job:
    settings = get_settings()
    job = _create_job(
        db,
        user_id=user_id,
        job_type="generate_module_assets",
        payload={"module_id": str(module_id)},
    )

    if not settings.disable_rq_enqueue:
        queue = Queue("default", connection=Redis.from_url(settings.redis_url))
        queue.enqueue(
            "app.services.pipeline.generate_module_assets_job.generate_module_assets_job_runner",
            str(job.id),
            str(module_id),
            job_timeout=3600,
        )
    return job


def run_generate_module_assets(
    *,
    db: Session,
    module: Module,
    asset: ModuleAsset,
    llm_provider: OpenAICompatibleProvider,
    tts_client: ElevenLabsClient,
    job: Job | None,
) -> ModuleAsset:
    settings = get_settings()
    storage = LocalStorage()

    chunk_refs = module.chunk_refs if isinstance(module.chunk_refs, list) else []
    chunk_rows: list[DocumentChunk] = []
    if chunk_refs:
        try:
            ids = [uuid.UUID(str(item)) for item in chunk_refs]
            chunk_rows = db.query(DocumentChunk).filter(DocumentChunk.id.in_(ids)).all()
        except Exception:
            chunk_rows = []
    if not chunk_rows:
        chunk_rows = db.query(DocumentChunk).filter(DocumentChunk.document_id == module.document_id).all()

    source_text = "\n\n".join(chunk.text for chunk in chunk_rows)

    if job is not None:
        set_job_state(job, status=JobStatus.running, stage="SCRIPT", percent=15)
    script_json = generate_script(module.title, module.summary, source_text, llm_provider)
    asset.script_json = script_json
    asset.script_text = script_json.get("full_narration_text", "")
    asset.status = ModuleAssetStatus.SCRIPT_DONE
    if job is not None:
        set_job_state(job, status=JobStatus.running, stage="SCRIPT_DONE", percent=32)
    db.commit()

    audio_workdir = storage.manim_workdir(str(module.id)) / "audio_parts"
    audio_path, timing_alignment = tts_client.synthesize_with_timing(
        script_json=script_json,
        out_path=storage.audio_path(str(module.id)),
        workdir=audio_workdir,
    )
    asset.audio_path = str(audio_path)
    asset.status = ModuleAssetStatus.AUDIO_DONE
    script_with_timing = dict(script_json)
    script_with_timing["timing_alignment"] = timing_alignment
    asset.script_json = script_with_timing
    if job is not None:
        set_job_state(job, status=JobStatus.running, stage="AUDIO_DONE", percent=48)
    db.commit()

    scene_class_name = settings.config.manim.scene_class_name
    video_path = None
    manim_code = ""
    last_error = ""
    audio_duration = _media_duration_seconds(str(audio_path))
    for attempt in range(3):
        try:
            if attempt == 0:
                manim_code = generate_manim_code(script_json, timing_alignment, scene_class_name, llm_provider)
            else:
                current_code = manim_code or "# previous code generation failed"
                manim_code = repair_manim_code(
                    script_json,
                    timing_alignment,
                    current_code,
                    last_error,
                    scene_class_name,
                    llm_provider,
                )

            video_path, _ = _render_video_for_backend(
                module_id=str(module.id),
                code=manim_code,
                scene_class_name=scene_class_name,
                quality=settings.config.manim.quality,
                storage=storage,
            )

            video_duration = _media_duration_seconds(str(video_path))
            drift_seconds = abs(video_duration - audio_duration)
            if drift_seconds > 1.2:
                if attempt < 2:
                    raise RuntimeError(
                        f"Video/audio timing drift too high: video={video_duration:.3f}s, "
                        f"audio={audio_duration:.3f}s, drift={drift_seconds:.3f}s. "
                        "Adjust scene run_time and waits to match timing_alignment."
                    )

                logger.warning(
                    "Final Manim attempt still has drift (video=%.3fs, audio=%.3fs). "
                    "Applying automatic video retime to match audio duration.",
                    video_duration,
                    audio_duration,
                )
                retime_video_to_duration(video_path, audio_duration)
                adjusted_video_duration = _media_duration_seconds(str(video_path))
                adjusted_drift = abs(adjusted_video_duration - audio_duration)
                if adjusted_drift > 0.9:
                    raise RuntimeError(
                        f"Video/audio drift remains high after retime: "
                        f"video={adjusted_video_duration:.3f}s, audio={audio_duration:.3f}s, "
                        f"drift={adjusted_drift:.3f}s."
                    )
            break
        except Exception as exc:
            last_error = str(exc)
            if attempt >= 2:
                raise

    asset.manim_code = manim_code
    asset.status = ModuleAssetStatus.MANIM_DONE
    if job is not None:
        set_job_state(job, status=JobStatus.running, stage="MANIM_DONE", percent=52)
    db.commit()

    assert video_path is not None
    asset.video_path = str(video_path)
    asset.status = ModuleAssetStatus.VIDEO_DONE
    if job is not None:
        set_job_state(job, status=JobStatus.running, stage="VIDEO_DONE", percent=72)
    db.commit()

    segments = transcribe_segments(audio_path, settings.config.captions.whisper_model)
    captions_path = write_srt(storage.captions_path(str(module.id)), segments)
    asset.captions_srt_path = str(captions_path)
    asset.status = ModuleAssetStatus.CAPTIONS_DONE
    if job is not None:
        set_job_state(job, status=JobStatus.running, stage="CAPTIONS_DONE", percent=86)
    db.commit()

    final_path = mux_video_audio(video_path, audio_path, storage.final_path(str(module.id)))
    asset.final_muxed_path = str(final_path)
    asset.status = ModuleAssetStatus.MUXED_DONE
    module.status = ModuleStatus.DONE
    if job is not None:
        set_job_state(
            job,
            status=JobStatus.succeeded,
            stage="MUXED_DONE",
            percent=100,
            result={
                "module_id": str(module.id),
                "video_path": asset.video_path,
                "audio_path": asset.audio_path,
                "captions_path": asset.captions_srt_path,
                "final_path": asset.final_muxed_path,
            },
        )
    db.commit()
    return asset


def generate_module_assets_job_runner(job_id: str, module_id: str) -> None:
    session_factory = get_session_maker()
    db = session_factory()

    job: Job | None = None
    module: Module | None = None
    asset: ModuleAsset | None = None

    try:
        job = db.get(Job, uuid.UUID(job_id))
        module = db.get(Module, uuid.UUID(module_id))
        if not job or not module:
            return

        module.status = ModuleStatus.GENERATING
        asset = db.query(ModuleAsset).filter(ModuleAsset.module_id == module.id).first()
        if asset is None:
            asset = ModuleAsset(module_id=module.id, status=ModuleAssetStatus.QUEUED)
            db.add(asset)
            db.flush()

        asset.status = ModuleAssetStatus.RUNNING
        set_job_state(job, status=JobStatus.running, stage="RUNNING", percent=5)
        db.commit()

        llm_provider = OpenAICompatibleProvider()
        tts_client = ElevenLabsClient()
        run_generate_module_assets(
            db=db,
            module=module,
            asset=asset,
            llm_provider=llm_provider,
            tts_client=tts_client,
            job=job,
        )
    except Exception as exc:
        logger.exception("generate_module_assets_job failed")
        db.rollback()

        if job is None:
            job = db.get(Job, uuid.UUID(job_id))
        if module is None:
            module = db.get(Module, uuid.UUID(module_id))
        if asset is None and module is not None:
            asset = db.query(ModuleAsset).filter(ModuleAsset.module_id == module.id).first()

        if module is not None:
            module.status = ModuleStatus.FAILED
        if asset is not None:
            asset.status = ModuleAssetStatus.FAILED
            asset.error = str(exc)
        if job is not None:
            set_job_state(job, status=JobStatus.failed, stage="FAILED", percent=100, error=str(exc))
        db.commit()
        raise
    finally:
        db.close()
