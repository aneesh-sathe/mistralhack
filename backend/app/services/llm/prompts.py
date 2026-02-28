from __future__ import annotations

import json


def module_extraction_prompt(chunks: list[dict]) -> str:
    return (
        "You are a curriculum extraction engine. Given chunk summaries from a math textbook, "
        "propose bite-sized learning modules. Return STRICT JSON with key 'modules' where value "
        "is an array of objects: {title, summary, prerequisites, chunk_refs}. chunk_refs must be "
        "an array of chunk_id strings only. No markdown, no prose outside JSON.\n\n"
        f"Chunks:\n{json.dumps(chunks, indent=2)}"
    )


def script_generation_prompt(module_title: str, module_summary: str, chunk_text: str) -> str:
    return (
        "Create a narrated lesson script from the given math content. "
        "Return STRICT JSON object with exactly these keys:\n"
        "- module_title: string\n"
        "- scenes: array of objects each containing {scene_id:int, title:string, narration_text:string, "
        "on_screen_text:string, math_expressions:string[], visual_instructions:string}\n"
        "- full_narration_text: string\n"
        "Rules: 3-6 scenes, concise and pedagogical, transitions explicit in narration. "
        "full_narration_text must concatenate scene narration in order.\n"
        "No markdown, only JSON.\n\n"
        f"Module title: {module_title}\n"
        f"Module summary: {module_summary}\n"
        f"Source text:\n{chunk_text[:12000]}"
    )


def manim_code_prompt(
    scene_class_name: str,
    script_json: dict,
    manim_docs_context: str,
    timing_alignment: list[dict],
) -> str:
    return (
        "You write deterministic Python Manim Community Edition code. "
        f"Return ONLY Python code for a single class named {scene_class_name} inheriting Scene. "
        "Requirements: render scenes in order, clear transitions, avoid external assets, avoid LaTeX dependencies when possible, "
        "and ensure code runs in headless Linux container. Prefer Text/MarkupText/NumberPlane/Axes and built-in animations. "
        "Hard constraints: each scene must have its own VGroup; remove prior-scene mobjects before next scene; "
        "use run_time/wait so each scene duration tracks provided timing_alignment.duration_seconds. "
        "Do not overlay multiple scene bodies at once unless explicitly required by a transition. "
        "No markdown.\n\n"
        f"Manim documentation context:\n{manim_docs_context}\n\n"
        f"Timing alignment JSON (seconds):\n{json.dumps(timing_alignment, indent=2)}\n\n"
        f"Script JSON:\n{json.dumps(script_json, indent=2)}"
    )


def manim_repair_prompt(
    scene_class_name: str,
    script_json: dict,
    timing_alignment: list[dict],
    current_code: str,
    error_log: str,
    manim_docs_context: str,
) -> str:
    return (
        "Repair the following Manim code so it compiles and renders successfully. "
        f"Return ONLY corrected Python code for class {scene_class_name}. "
        "Stay within Manim CE primitives documented below. "
        "Preserve scene-to-audio pacing from timing_alignment and enforce cleanup between scenes (no lingering overlays).\n\n"
        f"Manim documentation context:\n{manim_docs_context}\n\n"
        f"Timing alignment JSON (seconds):\n{json.dumps(timing_alignment, indent=2)}\n\n"
        f"Script JSON:\n{json.dumps(script_json, indent=2)}\n\n"
        f"Current code:\n{current_code}\n\n"
        f"Error log:\n{error_log}"
    )


def vlm_ocr_prompt() -> str:
    return (
        "Extract readable textbook text from these math page images. Preserve equations inline in plain text. "
        "Return only the extracted text."
    )
