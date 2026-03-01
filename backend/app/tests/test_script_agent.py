from __future__ import annotations

from app.services.llm.script_agent import _normalize_script


def test_normalize_script_expands_operator_abbreviations_in_narration():
    raw = {
        "module_title": "Ops",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Ops Scene",
                "narration_text": "Compute 4x5, then 20/4, then 7+3 and 9-1.",
                "on_screen_text": "4x5 = 20",
                "math_expressions": ["4x5=20", "20/4=5"],
                "visual_instructions": "Show steps.",
            }
        ],
        "full_narration_text": "4x5 then 20/4 then 7+3 then 9-1",
    }

    out = _normalize_script(raw, "Ops")
    narration = out["scenes"][0]["narration_text"]
    full = out["full_narration_text"]

    assert "multiplied by" in narration
    assert "divided by" in narration
    assert "plus" in narration
    assert "minus" in narration

    assert "multiplied by" in full
    assert "divided by" in full
    assert "plus" in full
    assert "minus" in full
