from __future__ import annotations

from app.services.llm.script_agent import _expand_operator_abbreviations, _normalize_script


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
    assert "divided by" in narration or "20/4" in narration
    assert "plus" in narration
    assert "minus" in narration

    assert "multiplied by" in full
    assert "divided by" in full or "20/4" in full
    assert "plus" in full
    assert "minus" in full


def test_normalize_script_does_not_corrupt_regular_words():
    raw = {
        "module_title": "Word Safety",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Context",
                "narration_text": "In the next real-world example, we explore 4x5 and 9-1.",
                "on_screen_text": "",
                "math_expressions": [],
                "visual_instructions": "Narrate only.",
            }
        ],
        "full_narration_text": "In the next real-world example, we explore 4x5 and 9-1.",
    }

    out = _normalize_script(raw, "Word Safety")
    narration = out["scenes"][0]["narration_text"]
    full = out["full_narration_text"]

    assert "next" in narration
    assert "real-world" in narration
    assert "explore" in narration
    assert "multiplied by" in narration
    assert "minus" in narration
    assert "multiplied by" in full
    assert "minus" in full


def test_normalize_script_converts_latex_to_plain_math_text():
    raw = {
        "module_title": "Division of Whole Numbers by Fractions",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Core Example",
                "narration_text": "Solve 6 \\div \\frac{1}{3}.",
                "on_screen_text": "6 \\div \\frac{1}{3}",
                "math_expressions": ["6 \\div \\frac{1}{3}"],
                "visual_instructions": "Show equation.",
            }
        ],
        "full_narration_text": "Solve 6 \\div \\frac{1}{3}.",
    }

    normalized = _normalize_script(raw, "Division")
    scene = normalized["scenes"][0]

    assert "\\" not in scene["on_screen_text"]
    assert scene["math_expressions"][0] == "6 divided by 1/3"
    assert "\\" not in normalized["full_narration_text"]


def test_expand_operator_abbreviations_preserves_simple_fractions():
    text = "1 divided by 1/2 equals 2"
    expanded = _expand_operator_abbreviations(text)
    assert expanded == "1 divided by 1/2 equals 2"
