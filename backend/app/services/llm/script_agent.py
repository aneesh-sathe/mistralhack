from __future__ import annotations

import re
from typing import Any

from app.services.llm.base import LLMProvider
from app.services.llm.prompts import script_generation_prompt


_TOKEN_PATTERN = r"(?:\(?-?\d+(?:\.\d+)?\)?)"
_BINARY_OP_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9_])({_TOKEN_PATTERN})\s*([+\-*/xX×÷])\s*({_TOKEN_PATTERN})(?![A-Za-z0-9_])"
)
_OP_WORDS = {
    "+": "plus",
    "-": "minus",
    "*": "multiplied by",
    "x": "multiplied by",
    "X": "multiplied by",
    "×": "multiplied by",
    "/": "divided by",
    "÷": "divided by",
}


def _expand_operator_abbreviations(text: str) -> str:
    value = (text or "").strip()
    if not value:
        return ""

    def repl(match: re.Match[str]) -> str:
        left, op, right = match.group(1), match.group(2), match.group(3)
        word = _OP_WORDS.get(op, op)
        return f"{left} {word} {right}"

    previous = value
    for _ in range(5):
        updated = _BINARY_OP_PATTERN.sub(repl, previous)
        if updated == previous:
            break
        previous = updated
    return re.sub(r"\s+", " ", previous).strip()


def _normalize_script(data: dict[str, Any], module_title: str) -> dict[str, Any]:
    scenes_raw = data.get("scenes") if isinstance(data, dict) else None
    if not isinstance(scenes_raw, list):
        scenes_raw = []

    scenes: list[dict[str, Any]] = []
    for idx, scene in enumerate(scenes_raw, start=1):
        if not isinstance(scene, dict):
            continue
        narration = _expand_operator_abbreviations(str(scene.get("narration_text", "")).strip())
        scenes.append(
            {
                "scene_id": int(scene.get("scene_id", idx)),
                "title": str(scene.get("title", f"Scene {idx}")).strip() or f"Scene {idx}",
                "narration_text": narration,
                "on_screen_text": str(scene.get("on_screen_text", "")).strip(),
                "math_expressions": [str(x) for x in scene.get("math_expressions", []) if isinstance(x, (str, int, float))],
                "visual_instructions": str(scene.get("visual_instructions", "")).strip(),
            }
        )

    if not scenes:
        scenes = [
            {
                "scene_id": 1,
                "title": module_title,
                "narration_text": "In this lesson, we summarize the key idea and a simple worked example.",
                "on_screen_text": module_title,
                "math_expressions": [],
                "visual_instructions": "Display title and short explanation text.",
            }
        ]

    full_narration = str(data.get("full_narration_text", "")).strip() if isinstance(data, dict) else ""
    if not full_narration:
        full_narration = " ".join(scene["narration_text"] for scene in scenes).strip()
    full_narration = _expand_operator_abbreviations(full_narration)

    return {
        "module_title": str(data.get("module_title", module_title)).strip() if isinstance(data, dict) else module_title,
        "scenes": scenes,
        "full_narration_text": full_narration,
    }


def generate_script(module_title: str, module_summary: str, chunk_text: str, llm_provider: LLMProvider) -> dict[str, Any]:
    prompt = script_generation_prompt(module_title, module_summary, chunk_text)
    try:
        raw = llm_provider.generate_json(prompt)
    except Exception:
        raw = {
            "module_title": module_title,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": module_title,
                    "narration_text": f"This module introduces {module_title}.",
                    "on_screen_text": module_summary,
                    "math_expressions": [],
                    "visual_instructions": "Show a title card and one short bullet list.",
                }
            ],
            "full_narration_text": f"This module introduces {module_title}.",
        }
    return _normalize_script(raw, module_title)
