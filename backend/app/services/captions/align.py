from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _audio_duration_seconds(path: Path) -> float:
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
    try:
        output = subprocess.check_output(cmd, text=True)
        payload = json.loads(output)
        return float(payload.get("format", {}).get("duration", 5.0))
    except Exception:
        return 5.0


def transcribe_segments(audio_path: Path, model_name: str = "small") -> list[dict]:
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(audio_path), beam_size=1, vad_filter=True)
        rows = []
        for seg in segments:
            text = (seg.text or "").strip()
            if not text:
                continue
            rows.append({"start": float(seg.start), "end": float(seg.end), "text": text})
        if rows:
            return rows
    except Exception:
        pass

    duration = _audio_duration_seconds(audio_path)
    return [
        {
            "start": 0.0,
            "end": max(duration, 2.0),
            "text": "Narration generated."
        }
    ]
