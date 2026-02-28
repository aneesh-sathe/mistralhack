from __future__ import annotations

from typing import Any

from app.services.llm.base import LLMProvider
from app.services.llm.prompts import script_generation_prompt


def _normalize_script(data: dict[str, Any], module_title: str) -> dict[str, Any]:
    scenes_raw = data.get("scenes") if isinstance(data, dict) else None
    if not isinstance(scenes_raw, list):
        scenes_raw = []

    scenes: list[dict[str, Any]] = []
    for idx, scene in enumerate(scenes_raw, start=1):
        if not isinstance(scene, dict):
            continue
        narration = str(scene.get("narration_text", "")).strip()
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
