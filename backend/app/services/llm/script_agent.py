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
_LATEX_OPERATOR_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\\div", " divided by "),
    (r"\\times", " multiplied by "),
    (r"\\cdot", " multiplied by "),
    (r"\\pm", " plus or minus "),
    (r"\\left", " "),
    (r"\\right", " "),
)
_INVALID_TEXT_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_NOISY_WORD = re.compile(r"\b[bcdfghjklmnpqrstvwxyz]{6,}\b", flags=re.I)
_BROKEN_ENTITY = re.compile(r"\b[A-Z][a-z]{1,10}\s+[A-Z][a-z]{1,10}'s\s+[a-z]{2,8}\b")
_SHORT_NARRATION_WORDS = 4


def _expand_operator_abbreviations(text: str) -> str:
    value = (text or "").strip()
    if not value:
        return ""

    protected_fractions: dict[str, str] = {}

    def protect_fraction(match: re.Match[str]) -> str:
        key = f"__fraction_{len(protected_fractions)}__"
        protected_fractions[key] = re.sub(r"\s+", "", match.group(0))
        return key

    # Preserve explicit numeric fractions like 1/2 and 3 / 4.
    value = re.sub(
        r"(?<![A-Za-z0-9_])\d+\s*/\s*\d+(?![A-Za-z0-9_])",
        protect_fraction,
        value,
    )

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
    for key, fraction in protected_fractions.items():
        previous = previous.replace(key, fraction)
    return re.sub(r"\s+", " ", previous).strip()


def _latex_to_plain_text(text: str) -> str:
    value = (text or "").strip()
    if not value:
        return ""

    previous = ""
    while previous != value:
        previous = value
        value = re.sub(r"\\(?:d)?frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"\1/\2", value)
        value = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", value)

    for pattern, replacement in _LATEX_OPERATOR_REPLACEMENTS:
        value = re.sub(pattern, replacement, value)

    # Remove leftover TeX command markers and braces after conversion.
    value = re.sub(r"\\[A-Za-z]+", " ", value)
    value = value.replace("{", " ").replace("}", " ")
    value = value.replace("$", " ")
    return re.sub(r"\s+", " ", value).strip()


def _sanitize_text(text: str) -> str:
    value = _latex_to_plain_text(text)
    value = _INVALID_TEXT_CHARS.sub(" ", value)
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _looks_noisy(text: str) -> bool:
    value = (text or "").strip()
    if not value:
        return False
    if _BROKEN_ENTITY.search(value):
        return True
    words = re.findall(r"[A-Za-z]{3,}", value)
    if not words:
        return False
    noisy_words = sum(1 for word in words if _NOISY_WORD.fullmatch(word))
    return noisy_words >= 2


def _normalize_script(data: dict[str, Any], module_title: str) -> dict[str, Any]:
    scenes_raw = data.get("scenes") if isinstance(data, dict) else None
    if not isinstance(scenes_raw, list):
        scenes_raw = []

    scenes: list[dict[str, Any]] = []
    for idx, scene in enumerate(scenes_raw, start=1):
        if not isinstance(scene, dict):
            continue
        narration = _sanitize_text(_expand_operator_abbreviations(str(scene.get("narration_text", "")).strip()))
        on_screen = _sanitize_text(str(scene.get("on_screen_text", "")).strip())
        expressions = [
            _sanitize_text(str(x))
            for x in scene.get("math_expressions", [])
            if isinstance(x, (str, int, float))
        ]
        expressions = [expr for expr in expressions if expr]
        scenes.append(
            {
                "scene_id": int(scene.get("scene_id", idx)),
                "title": _sanitize_text(str(scene.get("title", f"Scene {idx}")).strip()) or f"Scene {idx}",
                "narration_text": narration,
                "on_screen_text": on_screen,
                "math_expressions": expressions,
                "visual_instructions": _sanitize_text(str(scene.get("visual_instructions", "")).strip()),
            }
        )

    if not scenes:
        scenes = [
            {
                "scene_id": 1,
                "title": module_title,
                "narration_text": "In this lesson, we summarize the key idea and a simple worked example.",
                "on_screen_text": _sanitize_text(module_title),
                "math_expressions": [],
                "visual_instructions": "Display title and short explanation text.",
            }
        ]

    full_narration = str(data.get("full_narration_text", "")).strip() if isinstance(data, dict) else ""
    if not full_narration:
        full_narration = " ".join(scene["narration_text"] for scene in scenes).strip()
    full_narration = _sanitize_text(_expand_operator_abbreviations(full_narration))

    return {
        "module_title": _sanitize_text(str(data.get("module_title", module_title)).strip())
        if isinstance(data, dict)
        else _sanitize_text(module_title),
        "scenes": scenes,
        "full_narration_text": full_narration,
    }


def _script_quality_issues(script: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    scenes = script.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) < 2:
        issues.append("need_at_least_two_scenes")
        return issues

    has_meaningful_math = False
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        narration = str(scene.get("narration_text", "")).strip()
        if len(re.findall(r"[A-Za-z0-9]+", narration)) < _SHORT_NARRATION_WORDS:
            issues.append("short_narration")
        if _looks_noisy(narration):
            issues.append("noisy_narration")
        if _looks_noisy(str(scene.get("on_screen_text", ""))):
            issues.append("noisy_onscreen")

        expressions = scene.get("math_expressions", [])
        if isinstance(expressions, list) and any(str(x).strip() for x in expressions):
            has_meaningful_math = True
        if any("\\" in str(x) for x in expressions):
            issues.append("latex_leak")

    full_narration = str(script.get("full_narration_text", "")).strip()
    if _looks_noisy(full_narration):
        issues.append("noisy_full_narration")

    if not has_meaningful_math:
        issues.append("missing_math_expressions")
    return sorted(set(issues))


def _fallback_script(module_title: str, module_summary: str) -> dict[str, Any]:
    return _normalize_script(
        {
            "module_title": module_title,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": module_title,
                    "narration_text": f"This module introduces {module_title}.",
                    "on_screen_text": module_summary,
                    "math_expressions": [],
                    "visual_instructions": "Show a title card and one short bullet list.",
                },
                {
                    "scene_id": 2,
                    "title": "Worked Example",
                    "narration_text": "Now we solve one short example step by step and summarize the method.",
                    "on_screen_text": "Example and takeaway",
                    "math_expressions": [],
                    "visual_instructions": "Show the worked steps one line at a time.",
                },
            ],
            "full_narration_text": (
                f"This module introduces {module_title}. "
                "Now we solve one short example step by step and summarize the method."
            ),
        },
        module_title,
    )


def generate_script(module_title: str, module_summary: str, chunk_text: str, llm_provider: LLMProvider) -> dict[str, Any]:
    prompt = script_generation_prompt(module_title, module_summary, chunk_text)
    best_candidate: dict[str, Any] | None = None
    best_issues: list[str] | None = None

    for _ in range(3):
        try:
            raw = llm_provider.generate_json(prompt, max_retries=1)
        except Exception:
            continue

        normalized = _normalize_script(raw, module_title)
        issues = _script_quality_issues(normalized)
        if not issues:
            return normalized

        if best_candidate is None or (best_issues is not None and len(issues) < len(best_issues)):
            best_candidate = normalized
            best_issues = issues

    if best_candidate is not None:
        return best_candidate
    return _fallback_script(module_title, module_summary)
