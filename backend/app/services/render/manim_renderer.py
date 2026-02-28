from __future__ import annotations

import py_compile
import shutil
import subprocess
from pathlib import Path

from app.services.storage import LocalStorage


def _quality_flag(quality: str) -> str:
    mapping = {
        "low": "l",
        "medium": "m",
        "high": "h",
        "production": "p",
        "4k": "k",
    }
    return mapping.get(quality.lower(), "m")


def render_module_video(
    *,
    module_id: str,
    code: str,
    scene_class_name: str,
    quality: str,
    storage: LocalStorage,
) -> tuple[Path, Path]:
    workdir = storage.manim_workdir(module_id)
    lesson_path = workdir / "lesson.py"
    lesson_path.write_text(code, encoding="utf-8")

    py_compile.compile(str(lesson_path), doraise=True)

    flag = _quality_flag(quality)
    output_name = "rendered"
    cmd = [
        "manim",
        f"-q{flag}",
        str(lesson_path),
        scene_class_name,
        "--media_dir",
        str(workdir / "media"),
        "-o",
        output_name,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Manim render failed:\n{result.stdout}\n{result.stderr}")

    rendered = list((workdir / "media").glob("videos/**/rendered.mp4"))
    if not rendered:
        raise RuntimeError("Manim render completed but output file was not found")

    dest = storage.video_path(module_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(rendered[0], dest)
    return dest, lesson_path
