from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

import httpx

from app.core.settings import get_settings

logger = logging.getLogger(__name__)


def _resolve_output_format(raw: str) -> str:
    value = (raw or "").strip().lower()
    mapping = {
        "mp3": "mp3_44100_128",
        "mp3_44100_128": "mp3_44100_128",
        "mp3_22050_32": "mp3_22050_32",
        "mp3_44100_64": "mp3_44100_64",
        "pcm_16000": "pcm_16000",
        "pcm_22050": "pcm_22050",
        "pcm_24000": "pcm_24000",
        "pcm_44100": "pcm_44100",
        "ulaw_8000": "ulaw_8000",
    }
    return mapping.get(value, "mp3_44100_128")


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
    output = subprocess.check_output(cmd, text=True)
    payload = json.loads(output)
    return float(payload.get("format", {}).get("duration", 0.0))


class ElevenLabsClient:
    def __init__(self) -> None:
        settings = get_settings()
        cfg = settings.config.tts
        self.api_key = cfg.api_key
        self.voice_id = cfg.voice_id
        self.model_id = cfg.model_id or "eleven_multilingual_v2"
        self.output_format = _resolve_output_format(cfg.output_format)

    def _request_audio(self, narration: str) -> bytes:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
        payload = {
            "text": narration,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.75,
                "style": 0.2,
                "use_speaker_boost": True,
            },
        }

        with httpx.Client(timeout=120) as client:
            response = client.post(url, headers=headers, params={"output_format": self.output_format}, json=payload)

        if response.status_code >= 400:
            error_detail = response.text
            raise RuntimeError(f"ElevenLabs request failed ({response.status_code}): {error_detail}")

        content_type = response.headers.get("content-type", "").lower()
        if "audio" not in content_type and response.content.startswith(b"{"):
            raise RuntimeError(f"ElevenLabs returned non-audio payload: {response.text}")
        return response.content

    def _validate_audio_file(self, out_path: Path) -> float:
        if out_path.stat().st_size < 512:
            raise RuntimeError("ElevenLabs audio output is unexpectedly small")

        try:
            duration = _audio_duration_seconds(out_path)
        except Exception as exc:
            raise RuntimeError(f"Generated audio failed ffprobe validation: {exc}") from exc

        if duration <= 0.1:
            raise RuntimeError("Generated audio has near-zero duration")
        return duration

    def synthesize(self, text: str, out_path: Path) -> Path:
        narration = (text or "").strip()
        if not narration:
            raise RuntimeError("Narration text is empty; cannot synthesize voiceover")

        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is missing")
        if not self.voice_id:
            raise RuntimeError("ELEVENLABS_VOICE_ID is missing")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(self._request_audio(narration))
        duration = self._validate_audio_file(out_path)

        logger.info("Generated ElevenLabs audio: %s (%.2fs)", out_path, duration)
        return out_path

    def _concat_tracks(self, tracks: list[Path], out_path: Path) -> Path:
        if not tracks:
            raise RuntimeError("No audio scene tracks provided for concatenation")
        if len(tracks) == 1:
            out_path.write_bytes(tracks[0].read_bytes())
            return out_path

        manifest = out_path.with_suffix(".concat.txt")
        manifest_lines = [f"file '{track.as_posix()}'" for track in tracks]
        manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(manifest),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to concatenate scene audio tracks:\n{result.stdout}\n{result.stderr}")
        return out_path

    def synthesize_with_timing(
        self,
        *,
        script_json: dict[str, Any],
        out_path: Path,
        workdir: Path,
    ) -> tuple[Path, list[dict[str, Any]]]:
        scenes = script_json.get("scenes", []) if isinstance(script_json, dict) else []
        if not isinstance(scenes, list) or not scenes:
            audio = self.synthesize(str(script_json.get("full_narration_text", "")).strip(), out_path)
            duration = _audio_duration_seconds(audio)
            return audio, [
                {
                    "scene_id": 1,
                    "title": "Full narration",
                    "start_seconds": 0.0,
                    "end_seconds": duration,
                    "duration_seconds": duration,
                }
            ]

        workdir.mkdir(parents=True, exist_ok=True)
        scene_tracks: list[Path] = []
        timing: list[dict[str, Any]] = []
        cursor = 0.0

        for index, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                continue
            narration = str(scene.get("narration_text", "")).strip()
            if not narration:
                continue
            scene_id = int(scene.get("scene_id", index))
            title = str(scene.get("title", f"Scene {scene_id}")).strip() or f"Scene {scene_id}"
            scene_audio_path = workdir / f"scene_{scene_id:03d}.mp3"
            self.synthesize(narration, scene_audio_path)
            duration = _audio_duration_seconds(scene_audio_path)
            scene_tracks.append(scene_audio_path)
            timing.append(
                {
                    "scene_id": scene_id,
                    "title": title,
                    "start_seconds": round(cursor, 3),
                    "end_seconds": round(cursor + duration, 3),
                    "duration_seconds": round(duration, 3),
                    "narration_text": narration,
                }
            )
            cursor += duration

        if not scene_tracks:
            audio = self.synthesize(str(script_json.get("full_narration_text", "")).strip(), out_path)
            duration = _audio_duration_seconds(audio)
            return audio, [
                {
                    "scene_id": 1,
                    "title": "Full narration",
                    "start_seconds": 0.0,
                    "end_seconds": duration,
                    "duration_seconds": duration,
                }
            ]

        self._concat_tracks(scene_tracks, out_path)
        total_duration = self._validate_audio_file(out_path)
        logger.info("Generated timed narration with %d scene tracks (%.2fs total)", len(scene_tracks), total_duration)
        return out_path, timing
