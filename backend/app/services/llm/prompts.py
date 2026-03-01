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
        "For narration_text and full_narration_text: NEVER use symbolic operator abbreviations. "
        "Write operations in words (example: '4 multiplied by 5', '10 divided by 2', '7 plus 3', '9 minus 1'). "
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
    scene_contract: list[dict],
    storyboard: dict,
) -> str:
    return (
        "You write deterministic Python Manim Community Edition code. "
        f"Return ONLY Python code for a single class named {scene_class_name} inheriting Scene. "
        "Requirements: render scenes in order, avoid external assets, "
        "DO NOT use MathTex, Tex, or SingleStringMathTex because the runtime has no LaTeX binary, "
        "and ensure code runs in headless Linux container. Prefer Text/MarkupText and simple shapes. "
        "Primary rules:\n"
        "1) Script alignment: animate what the script says (title, on_screen_text, math_expressions).\n"
        "2) Reveal text/equations character-by-character using AddTextLetterByLetter.\n"
        "3) Coherence: if a scene references earlier context, keep prior content visible and build new content below it; "
        "otherwise transition cleanly.\n"
        "4) Keep ample spacing between visual elements and successive animations. "
        "Use clear vertical gaps (buff around 0.25-0.45) and avoid overlapping text/equations unless explicitly replacing one item.\n"
        "5) Use run_time/wait so each scene approximately matches timing_alignment.duration_seconds.\n"
        "No markdown.\n\n"
        f"Manim documentation context:\n{manim_docs_context}\n\n"
        f"Scene contract JSON (must be followed exactly):\n{json.dumps(scene_contract, indent=2)}\n\n"
        f"Storyboard JSON:\n{json.dumps(storyboard, indent=2)}\n\n"
        f"Timing alignment JSON (seconds):\n{json.dumps(timing_alignment, indent=2)}\n\n"
        f"Script JSON:\n{json.dumps(script_json, indent=2)}"
    )


def manim_repair_prompt(
    scene_class_name: str,
    script_json: dict,
    timing_alignment: list[dict],
    scene_contract: list[dict],
    storyboard: dict,
    current_code: str,
    error_log: str,
    validation_errors: list[str],
    manim_docs_context: str,
) -> str:
    return (
        "Repair the following Manim code so it compiles and renders successfully. "
        f"Return ONLY corrected Python code for class {scene_class_name}. "
        "Stay within Manim CE primitives documented below. "
        "Do not use MathTex, Tex, or SingleStringMathTex. Use Text/MarkupText equivalents for equations. "
        "Preserve scene-to-audio pacing from timing_alignment. "
        "Reveal instructional text character-by-character with AddTextLetterByLetter. "
        "If script scene references prior context, keep previous content and build below it. "
        "Increase spacing to avoid overlap: keep generous vertical gaps and do not place new objects on top of existing ones unless replacing.\n\n"
        f"Manim documentation context:\n{manim_docs_context}\n\n"
        f"Scene contract JSON:\n{json.dumps(scene_contract, indent=2)}\n\n"
        f"Storyboard JSON:\n{json.dumps(storyboard, indent=2)}\n\n"
        f"Timing alignment JSON (seconds):\n{json.dumps(timing_alignment, indent=2)}\n\n"
        f"Script JSON:\n{json.dumps(script_json, indent=2)}\n\n"
        f"Validation errors to fix:\n{json.dumps(validation_errors, indent=2)}\n\n"
        f"Current code:\n{current_code}\n\n"
        f"Error log:\n{error_log}"
    )


def manim_storyboard_prompt(
    script_json: dict,
    timing_alignment: list[dict],
    manim_docs_context: str,
) -> str:
    return (
        "You are planning educational animation choreography for Manim CE. "
        "Return STRICT JSON with key 'scenes' as an array. "
        "Each item must be: "
        "{scene_id:int, teaching_goal:string, diagram_type:string, key_steps:string[], "
        "emphasis_terms:string[], transition_style:string}. "
        "Rules: one item per script scene, keep same scene_id values, key_steps must have 2-5 entries, "
        "diagram_type should be specific and visual (e.g., number_line, coordinate_plane, blocks, flowchart, geometry_shape), "
        "and each scene should feel like a visual teacher explanation.\n\n"
        f"Manim documentation context:\n{manim_docs_context}\n\n"
        f"Timing alignment JSON:\n{json.dumps(timing_alignment, indent=2)}\n\n"
        f"Script JSON:\n{json.dumps(script_json, indent=2)}"
    )


def vlm_ocr_prompt() -> str:
    return (
        "Extract readable textbook text from these math page images. Preserve equations inline in plain text. "
        "Return only the extracted text."
    )


def module_chat_system_prompt() -> str:
    return (
        "You are a math tutor assistant answering questions about one uploaded learning module. "
        "Use only the provided module context and conversation history. "
        "Be concise and correct. If context is insufficient, say what is missing."
    )
