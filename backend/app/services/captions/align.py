from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


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


def _clean_caption_text(text: str) -> str:
    value = (text or "").strip()
    if not value:
        return ""
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _split_caption_units(text: str, max_chars: int = 72) -> list[str]:
    value = _clean_caption_text(text)
    if not value:
        return []

    sentence_chunks = re.split(r"(?<=[.!?])\s+", value)
    sentence_chunks = [chunk.strip() for chunk in sentence_chunks if chunk.strip()]
    if not sentence_chunks:
        sentence_chunks = [value]

    units: list[str] = []
    for sentence in sentence_chunks:
        words = sentence.split()
        if not words:
            continue
        current: list[str] = []
        for word in words:
            candidate = " ".join(current + [word]).strip()
            if current and len(candidate) > max_chars:
                units.append(" ".join(current).strip())
                current = [word]
            else:
                current.append(word)
        if current:
            units.append(" ".join(current).strip())
    return [unit for unit in units if unit]


def _duration_weight(text: str) -> float:
    return float(max(1, len(re.sub(r"\s+", "", text))))


def _scene_narration(scene_id: int, scene_by_id: dict[int, dict[str, Any]], timing_item: dict[str, Any]) -> str:
    from_timing = _clean_caption_text(str(timing_item.get("narration_text", "")).strip())
    if from_timing:
        return from_timing
    scene = scene_by_id.get(scene_id, {})
    return _clean_caption_text(str(scene.get("narration_text", "")).strip())


def caption_segments_from_script(
    script_json: dict[str, Any],
    timing_alignment: list[dict[str, Any]],
    max_chars: int = 72,
) -> list[dict[str, Any]]:
    scenes = script_json.get("scenes", []) if isinstance(script_json, dict) else []
    scene_by_id: dict[int, dict[str, Any]] = {}
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            continue
        try:
            sid = int(scene.get("scene_id", index))
        except Exception:
            sid = index
        scene_by_id[sid] = scene

    segments: list[dict[str, Any]] = []
    for index, timing in enumerate(timing_alignment, start=1):
        if not isinstance(timing, dict):
            continue
        try:
            scene_id = int(timing.get("scene_id", index))
            start = float(timing.get("start_seconds", 0.0))
            end = float(timing.get("end_seconds", start))
        except Exception:
            continue
        if end <= start + 0.05:
            continue

        narration = _scene_narration(scene_id, scene_by_id, timing)
        if not narration:
            continue
        units = _split_caption_units(narration, max_chars=max_chars)
        if not units:
            continue

        cursor = start
        weights = [_duration_weight(unit) for unit in units]
        for unit_index, unit in enumerate(units):
            if unit_index == len(units) - 1:
                seg_end = end
            else:
                remaining_weight = sum(weights[unit_index:])
                available = max(0.1, end - cursor)
                proportional = available * (weights[unit_index] / max(1.0, remaining_weight))
                min_remaining = 0.35 * (len(units) - unit_index - 1)
                seg_duration = max(0.35, min(proportional, available - min_remaining))
                seg_end = min(end, cursor + seg_duration)

            if seg_end <= cursor + 0.01:
                continue
            segments.append(
                {
                    "start": round(cursor, 3),
                    "end": round(seg_end, 3),
                    "text": unit,
                }
            )
            cursor = seg_end
    return segments


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
