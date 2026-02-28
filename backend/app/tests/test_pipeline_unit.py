from __future__ import annotations

from pathlib import Path

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    Job,
    JobStatus,
    Module,
    ModuleAsset,
    ModuleAssetStatus,
    ModuleStatus,
    User,
)
from app.services.pipeline.generate_module_assets_job import run_generate_module_assets


class FakeLLMProvider:
    def generate_json(self, prompt: str, max_retries: int = 2):
        return {
            "module_title": "Linear Equations",
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Goal",
                    "narration_text": "We solve for x by isolating it.",
                    "on_screen_text": "2x + 3 = 11",
                    "math_expressions": ["2x + 3 = 11", "x = 4"],
                    "visual_instructions": "Show equation and transform line by line.",
                }
            ],
            "full_narration_text": "We solve for x by isolating it.",
        }

    def generate_text(self, prompt: str):
        return "text"

    def generate_code(self, prompt: str):
        return (
            "from manim import *\n"
            "class LessonScene(Scene):\n"
            "    def construct(self):\n"
            "        t = Text('Linear Equations')\n"
            "        self.play(FadeIn(t), run_time=1.0)\n"
            "        self.wait(0.8)\n"
            "        self.play(FadeOut(t), run_time=0.3)\n"
        )

    def vlm_extract_text(self, images, prompt: str):
        return ""


class FakeTTSClient:
    def synthesize(self, text: str, out_path: Path):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"fake-mp3")
        return out_path

    def synthesize_with_timing(self, *, script_json, out_path: Path, workdir: Path):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"fake-mp3")
        return out_path, [
            {
                "scene_id": 1,
                "title": "Goal",
                "start_seconds": 0.0,
                "end_seconds": 2.0,
                "duration_seconds": 2.0,
                "narration_text": "We solve for x by isolating it.",
            }
        ]


def test_pipeline_with_fakes_produces_assets(monkeypatch, db_session, dev_user: User):
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
        page_end=2,
        text="Solve linear equations by inverse operations.",
        meta={"char_count": 45},
    )
    db_session.add(chunk)
    db_session.flush()

    module = Module(
        document_id=doc.id,
        title="Linear Equations",
        summary="Intro to one-variable equations",
        prerequisites=["Arithmetic"],
        chunk_refs=[str(chunk.id)],
        status=ModuleStatus.GENERATING,
    )
    db_session.add(module)
    db_session.flush()

    asset = ModuleAsset(module_id=module.id, status=ModuleAssetStatus.RUNNING)
    db_session.add(asset)

    job = Job(
        user_id=dev_user.id,
        type="generate_module_assets",
        payload={"module_id": str(module.id)},
        status=JobStatus.running,
        progress={"stage": "RUNNING", "percent": 5, "history": ["QUEUED", "RUNNING"]},
        result={},
    )
    db_session.add(job)
    db_session.commit()

    def fake_render_module_video(*, module_id: str, code: str, scene_class_name: str, quality: str, storage):
        out = storage.video_path(module_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"fake-video")
        lesson = storage.manim_workdir(module_id) / "lesson.py"
        lesson.write_text(code, encoding="utf-8")
        return out, lesson

    def fake_transcribe_segments(audio_path: Path, model_name: str):
        return [
            {"start": 0.0, "end": 1.2, "text": "We solve for x by isolating it."},
            {"start": 1.2, "end": 2.4, "text": "Subtract three, then divide by two."},
        ]

    def fake_mux(video_path: Path, audio_path: Path, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-final")
        return output_path

    def fake_media_duration(path: str):
        if "audio" in path:
            return 2.0
        return 2.1

    monkeypatch.setattr("app.services.pipeline.generate_module_assets_job._render_video_for_backend", fake_render_module_video)
    monkeypatch.setattr("app.services.pipeline.generate_module_assets_job.transcribe_segments", fake_transcribe_segments)
    monkeypatch.setattr("app.services.pipeline.generate_module_assets_job.mux_video_audio", fake_mux)
    monkeypatch.setattr("app.services.pipeline.generate_module_assets_job._media_duration_seconds", fake_media_duration)

    out = run_generate_module_assets(
        db=db_session,
        module=module,
        asset=asset,
        llm_provider=FakeLLMProvider(),
        tts_client=FakeTTSClient(),
        job=job,
    )

    db_session.refresh(module)
    db_session.refresh(job)
    db_session.refresh(out)

    assert isinstance(out.script_json, dict)
    assert out.script_json["module_title"] == "Linear Equations"
    assert out.manim_code and "class LessonScene" in out.manim_code
    assert out.audio_path and Path(out.audio_path).exists()
    assert out.captions_srt_path and Path(out.captions_srt_path).exists()
    assert out.video_path and Path(out.video_path).exists()
    assert out.final_muxed_path and Path(out.final_muxed_path).exists()

    assert out.status == ModuleAssetStatus.MUXED_DONE
    assert module.status == ModuleStatus.DONE
    assert job.status == JobStatus.succeeded

    history = job.progress.get("history", [])
    assert "SCRIPT_DONE" in history
    assert "MANIM_DONE" in history
    assert "AUDIO_DONE" in history
    assert "CAPTIONS_DONE" in history
    assert "MUXED_DONE" in history
