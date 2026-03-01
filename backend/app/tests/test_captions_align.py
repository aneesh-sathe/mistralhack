from __future__ import annotations

from app.services.captions.align import caption_segments_from_script


def test_caption_segments_from_script_uses_script_narration():
    script_json = {
        "scenes": [
            {
                "scene_id": 1,
                "title": "Example",
                "narration_text": "John cuts a 6 cm strip into one-third cm pieces. How many pieces does he get?",
            }
        ]
    }
    timing_alignment = [
        {
            "scene_id": 1,
            "start_seconds": 0.0,
            "end_seconds": 6.0,
            "duration_seconds": 6.0,
            "narration_text": "John cuts a 6 cm strip into one-third cm pieces. How many pieces does he get?",
        }
    ]

    segments = caption_segments_from_script(script_json, timing_alignment, max_chars=44)

    assert segments
    assert segments[0]["start"] == 0.0
    assert segments[-1]["end"] == 6.0
    joined_text = " ".join(seg["text"] for seg in segments)
    assert "John cuts a 6 cm strip" in joined_text
    assert "Simi Lorsi" not in joined_text


def test_caption_segments_from_script_returns_empty_without_timing():
    segments = caption_segments_from_script({"scenes": []}, [])
    assert segments == []

