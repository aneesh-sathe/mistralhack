from __future__ import annotations

import shutil
from pathlib import Path

from app.core.settings import get_settings


class LocalStorage:
    def __init__(self, base_dir: str | Path | None = None):
        settings = get_settings()
        self.base_dir = Path(base_dir or settings.storage_dir)
        self.pdf_dir = self.base_dir / "pdfs"
        self.audio_dir = self.base_dir / "audio"
        self.captions_dir = self.base_dir / "captions"
        self.video_dir = self.base_dir / "video"
        self.final_dir = self.base_dir / "final"
        self.manim_dir = self.base_dir / "manim"
        self.ensure_dirs()

    def ensure_dirs(self) -> None:
        for path in [
            self.base_dir,
            self.pdf_dir,
            self.audio_dir,
            self.captions_dir,
            self.video_dir,
            self.final_dir,
            self.manim_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def pdf_path(self, document_id: str) -> Path:
        return self.pdf_dir / f"{document_id}.pdf"

    def audio_path(self, module_id: str) -> Path:
        return self.audio_dir / f"{module_id}.mp3"

    def captions_path(self, module_id: str) -> Path:
        return self.captions_dir / f"{module_id}.srt"

    def video_path(self, module_id: str) -> Path:
        return self.video_dir / f"{module_id}.mp4"

    def final_path(self, module_id: str) -> Path:
        return self.final_dir / f"{module_id}.mp4"

    def manim_workdir(self, module_id: str) -> Path:
        workdir = self.manim_dir / str(module_id)
        workdir.mkdir(parents=True, exist_ok=True)
        return workdir

    def save_pdf(self, document_id: str, payload: bytes) -> Path:
        path = self.pdf_path(document_id)
        path.write_bytes(payload)
        return path

    def delete_document_files(self, document_id: str, module_ids: list[str]) -> None:
        pdf = self.pdf_path(document_id)
        if pdf.exists():
            pdf.unlink()

        for module_id in module_ids:
            for path in [
                self.audio_path(module_id),
                self.captions_path(module_id),
                self.video_path(module_id),
                self.final_path(module_id),
            ]:
                if path.exists():
                    path.unlink()

            manim_dir = self.manim_dir / module_id
            if manim_dir.exists():
                shutil.rmtree(manim_dir, ignore_errors=True)
