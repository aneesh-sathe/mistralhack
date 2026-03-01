from __future__ import annotations

import pytest

from app.services.llm.manim_agent import _build_fallback_manim_code, _validate_mcp_generated_code


def _scene_contract() -> list[dict]:
    return [
        {
            "scene_id": 1,
            "title": "Division Example",
            "narration_text": "Solve 6 divided by 1/3.",
            "on_screen_text": "6 divided by 1/3",
            "math_expressions": ["6 divided by 1/3"],
            "visual_instructions": "Explain the reciprocal method.",
            "target_duration_seconds": 4.0,
        }
    ]


def test_mcp_validation_rejects_low_quality_code():
    low_quality = (
        "from manim import *\n"
        "class LessonScene(Scene):\n"
        "    def construct(self):\n"
        "        title = Text('Division')\n"
        "        self.play(Write(title))\n"
        "        self.wait(0.2)\n"
    )

    with pytest.raises(ValueError):
        _validate_mcp_generated_code(low_quality, "LessonScene", _scene_contract())


def test_mcp_validation_accepts_fallback_code():
    fallback = _build_fallback_manim_code("LessonScene", _scene_contract())
    _validate_mcp_generated_code(fallback, "LessonScene", _scene_contract())

