from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _probe_duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    output = subprocess.check_output(cmd, text=True)
    payload = json.loads(output)
    return float(payload.get("format", {}).get("duration", 0.0))


def retime_video_to_duration(video_path: Path, target_duration_seconds: float) -> Path:
    if target_duration_seconds <= 0:
        raise RuntimeError("Target duration must be positive")

    source_duration = _probe_duration_seconds(video_path)
    if source_duration <= 0:
        raise RuntimeError("Unable to probe rendered video duration for retiming")

    ratio = target_duration_seconds / source_duration
    if abs(source_duration - target_duration_seconds) <= 0.25:
        return video_path

    temp_path = video_path.with_name(f"{video_path.stem}.retimed.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-an",
        "-filter:v",
        f"setpts={ratio:.8f}*PTS",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(temp_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg retime failed:\n{result.stdout}\n{result.stderr}")

    temp_path.replace(video_path)
    return video_path


def mux_video_audio(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg mux failed:\n{result.stdout}\n{result.stderr}")
    return output_path
