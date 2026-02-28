from __future__ import annotations

from pathlib import Path


def _fmt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hrs = ms // 3_600_000
    ms %= 3_600_000
    mins = ms // 60_000
    ms %= 60_000
    secs = ms // 1000
    ms %= 1000
    return f"{hrs:02}:{mins:02}:{secs:02},{ms:03}"


def segments_to_srt(segments: list[dict]) -> str:
    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        start = _fmt_ts(float(seg["start"]))
        end = _fmt_ts(float(seg["end"]))
        text = str(seg["text"]).strip()
        lines.extend([str(i), f"{start} --> {end}", text, ""])
    return "\n".join(lines).strip() + "\n"


def write_srt(path: Path, segments: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(segments_to_srt(segments), encoding="utf-8")
    return path
