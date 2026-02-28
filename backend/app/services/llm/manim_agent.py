from __future__ import annotations

import ast
from typing import Any

from app.services.llm.base import LLMProvider
from app.services.llm.manim_docs import get_manim_docs_context
from app.services.llm.prompts import manim_code_prompt, manim_repair_prompt


def _strip_code_fences(code: str) -> str:
    clean = code.strip()
    if clean.startswith("```"):
        clean = clean.strip("`")
        clean = clean.replace("python", "", 1).strip()
    return clean


def _validate_generated_code(code: str, scene_class_name: str) -> None:
    if f"class {scene_class_name}(Scene)" not in code:
        raise ValueError(f"Generated code must include class {scene_class_name}(Scene)")
    if "run_time=" not in code and ".wait(" not in code:
        raise ValueError("Generated code must include run_time/wait for pacing")
    if "FadeOut(" not in code and "self.clear(" not in code:
        raise ValueError("Generated code must include cleanup transitions between scenes")
    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(f"Generated Manim code has invalid Python syntax: {exc}") from exc


def generate_manim_code(
    script_json: dict[str, Any],
    timing_alignment: list[dict[str, Any]],
    scene_class_name: str,
    llm_provider: LLMProvider,
) -> str:
    docs_context = get_manim_docs_context()
    prompt = manim_code_prompt(scene_class_name, script_json, docs_context, timing_alignment)

    code = _strip_code_fences(llm_provider.generate_code(prompt))
    _validate_generated_code(code, scene_class_name)
    return code


def repair_manim_code(
    script_json: dict[str, Any],
    timing_alignment: list[dict[str, Any]],
    current_code: str,
    error_log: str,
    scene_class_name: str,
    llm_provider: LLMProvider,
) -> str:
    docs_context = get_manim_docs_context()
    prompt = manim_repair_prompt(
        scene_class_name,
        script_json,
        timing_alignment,
        current_code,
        error_log,
        docs_context,
    )
    repaired = _strip_code_fences(llm_provider.generate_code(prompt))
    _validate_generated_code(repaired, scene_class_name)
    return repaired
