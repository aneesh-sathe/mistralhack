from __future__ import annotations

import ast
import logging
import re
import time
from typing import Any

from app.core.settings import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.manim_docs import get_manim_docs_context
from app.services.llm.prompts import (
    manim_code_prompt,
    manim_code_prompt_mcp,
    manim_repair_prompt,
    manim_repair_prompt_mcp,
    manim_storyboard_prompt,
)

logger = logging.getLogger(__name__)

_LATEX_MOBJECT_NAMES = {"MathTex", "Tex", "SingleStringMathTex"}
_ALLOWED_TEXT_KWARGS = {"font_size", "color"}
_FORBIDDEN_MCP_METHOD_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\.clip_path\s*\([^)]*\)", "clip_path"),
    (r"\.set_clip_path\s*\([^)]*\)", "set_clip_path"),
)
_LATEX_INLINE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\\div", " divided by "),
    (r"\\times", " multiplied by "),
    (r"\\cdot", " multiplied by "),
    (r"\\pm", " plus or minus "),
    (r"\\left", " "),
    (r"\\right", " "),
)


def _is_mcp_backend() -> bool:
    try:
        settings = get_settings()
        backend = (settings.config.manim.render_backend or "local").strip().lower()
        return backend == "mcp"
    except Exception:
        return False


def _strip_code_fences(code: str) -> str:
    clean = code.strip()
    if clean.startswith("```"):
        clean = clean.strip("`")
        clean = clean.replace("python", "", 1).strip()
    return clean


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _rewrite_latex_calls(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    changed = False

    class LatexToTextTransformer(ast.NodeTransformer):
        def visit_Call(self, node: ast.Call):  # noqa: N802
            nonlocal changed
            node = self.generic_visit(node)
            name = _call_name(node)
            if name == "BulletedList":
                changed = True
                if not node.args:
                    return ast.Call(func=ast.Name(id="VGroup", ctx=ast.Load()), args=[], keywords=[])

                text_items: list[ast.expr] = []
                for arg in node.args:
                    bullet_text = ast.BinOp(
                        left=ast.Constant(value="• "),
                        op=ast.Add(),
                        right=ast.Call(func=ast.Name(id="str", ctx=ast.Load()), args=[arg], keywords=[]),
                    )
                    text_items.append(
                        ast.Call(
                            func=ast.Name(id="Text", ctx=ast.Load()),
                            args=[bullet_text],
                            keywords=[kw for kw in node.keywords if kw.arg in _ALLOWED_TEXT_KWARGS],
                        )
                    )
                return ast.Call(func=ast.Name(id="VGroup", ctx=ast.Load()), args=text_items, keywords=[])

            if name in {"DecimalNumber", "Integer"}:
                has_mob_class = any(kw.arg == "mob_class" for kw in node.keywords)
                if not has_mob_class:
                    node.keywords.append(ast.keyword(arg="mob_class", value=ast.Name(id="Text", ctx=ast.Load())))
                    changed = True
                return node

            if name not in _LATEX_MOBJECT_NAMES:
                return node

            changed = True
            node.func = ast.Name(id="Text", ctx=ast.Load())

            if not node.args:
                node.args = [ast.Constant(value="")]
            elif len(node.args) > 1:
                node.args = [node.args[0]]

            node.keywords = [kw for kw in node.keywords if kw.arg in _ALLOWED_TEXT_KWARGS]
            return node

    rewritten = LatexToTextTransformer().visit(tree)
    ast.fix_missing_locations(rewritten)
    if not changed:
        return code

    return ast.unparse(rewritten)


def _contains_latex_mobjects(code: str) -> bool:
    pattern = r"\b(?:MathTex|Tex|SingleStringMathTex)\s*\("
    return bool(re.search(pattern, code))


def _rewrite_numberline_calls(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    changed = False

    class NumberLineTransformer(ast.NodeTransformer):
        def visit_Call(self, node: ast.Call):  # noqa: N802
            nonlocal changed
            node = self.generic_visit(node)
            name = _call_name(node)
            if name == "add_numbers":
                changed = True
                return ast.Call(func=ast.Name(id="VGroup", ctx=ast.Load()), args=[], keywords=[])
            if name != "NumberLine":
                return node

            include_kw = None
            for kw in node.keywords:
                if kw.arg == "include_numbers":
                    include_kw = kw
                    break

            if include_kw is not None:
                if not (isinstance(include_kw.value, ast.Constant) and include_kw.value.value is False):
                    include_kw.value = ast.Constant(value=False)
                    changed = True
            else:
                node.keywords.append(ast.keyword(arg="include_numbers", value=ast.Constant(value=False)))
                changed = True
            return node

    rewritten = NumberLineTransformer().visit(tree)
    ast.fix_missing_locations(rewritten)
    if not changed:
        return code
    return ast.unparse(rewritten)


def _rewrite_sector_calls(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    changed = False

    class SectorTransformer(ast.NodeTransformer):
        def visit_Call(self, node: ast.Call):  # noqa: N802
            nonlocal changed
            node = self.generic_visit(node)
            name = _call_name(node)
            if name != "Sector":
                return node

            has_radius = any(kw.arg == "radius" for kw in node.keywords)
            for kw in node.keywords:
                if kw.arg == "outer_radius":
                    if not has_radius:
                        kw.arg = "radius"
                        has_radius = True
                    else:
                        kw.arg = None
                    changed = True

            if changed:
                node.keywords = [kw for kw in node.keywords if kw.arg is not None]
            return node

    rewritten = SectorTransformer().visit(tree)
    ast.fix_missing_locations(rewritten)
    if not changed:
        return code
    return ast.unparse(rewritten)


def _contains_latex_sensitive_numberline(code: str) -> bool:
    include_numbers_true = re.search(r"NumberLine\([^)]*include_numbers\s*=\s*True", code, flags=re.S)
    add_numbers_call = re.search(r"\.add_numbers\s*\(", code)
    return bool(include_numbers_true or add_numbers_call)


def _rewrite_unsupported_mobject_calls(code: str) -> str:
    rewritten = code
    for pattern, _ in _FORBIDDEN_MCP_METHOD_PATTERNS:
        rewritten = re.sub(pattern, "", rewritten)
    return rewritten


def _find_forbidden_mcp_calls(code: str) -> list[str]:
    found: list[str] = []
    for pattern, label in _FORBIDDEN_MCP_METHOD_PATTERNS:
        if re.search(pattern, code):
            found.append(label)
    return found


def _equation_key(text: str) -> str:
    value = (text or "").strip().lower()
    value = _latex_to_plain_text(value)
    replacements = (
        ("multiplied by", "*"),
        ("times", "*"),
        ("plus", "+"),
        ("minus", "-"),
        ("divided by", "/"),
        ("equal to", "="),
        ("equals", "="),
        ("×", "*"),
        ("÷", "/"),
    )
    for src, dest in replacements:
        value = value.replace(src, dest)
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[^a-z0-9+\-*/=().]", "", value)
    return value


def _latex_to_plain_text(text: str) -> str:
    value = (text or "").strip()
    if not value:
        return ""

    previous = ""
    while previous != value:
        previous = value
        value = re.sub(r"\\(?:d)?frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"\1/\2", value)
        value = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", value)

    for pattern, replacement in _LATEX_INLINE_REPLACEMENTS:
        value = re.sub(pattern, replacement, value)

    value = re.sub(r"\\[A-Za-z]+", " ", value)
    value = value.replace("{", " ").replace("}", " ").replace("$", " ")
    return re.sub(r"\s+", " ", value).strip()


def _normalize_display_text(text: str, max_chars: int | None = None) -> str:
    value = _latex_to_plain_text(text)
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"\s+", " ", value).strip()
    if max_chars is not None and len(value) > max_chars:
        value = value[: max_chars - 1].rstrip() + "..."
    return value


def _extract_scene_block(code: str, scene_id: int, next_scene_id: int | None) -> str | None:
    start_marker = f"scene_{scene_id}_group"
    start_idx = code.find(start_marker)
    if start_idx < 0:
        return None
    end_idx = len(code)
    if next_scene_id is not None:
        next_idx = code.find(f"scene_{next_scene_id}_group", start_idx + len(start_marker))
        if next_idx > start_idx:
            end_idx = next_idx
    return code[start_idx:end_idx]


def _build_scene_contract(script_json: dict[str, Any], timing_alignment: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timings_by_scene: dict[int, dict[str, Any]] = {}
    for item in timing_alignment:
        if not isinstance(item, dict):
            continue
        try:
            sid = int(item.get("scene_id"))
        except Exception:
            continue
        timings_by_scene[sid] = item

    scenes_raw = script_json.get("scenes", []) if isinstance(script_json, dict) else []
    scenes: list[dict[str, Any]] = []
    for index, scene in enumerate(scenes_raw, start=1):
        if not isinstance(scene, dict):
            continue
        scene_id = int(scene.get("scene_id", index))
        timing = timings_by_scene.get(scene_id, {})
        scenes.append(
            {
                "scene_id": scene_id,
                "title": _normalize_display_text(str(scene.get("title", f"Scene {scene_id}")).strip(), max_chars=90)
                or f"Scene {scene_id}",
                "narration_text": _normalize_display_text(str(scene.get("narration_text", "")).strip(), max_chars=500),
                "on_screen_text": _normalize_display_text(str(scene.get("on_screen_text", "")).strip(), max_chars=240),
                "math_expressions": [
                    _normalize_display_text(str(x).strip(), max_chars=120)
                    for x in scene.get("math_expressions", [])
                    if str(x).strip()
                ],
                "visual_instructions": _normalize_display_text(
                    str(scene.get("visual_instructions", "")).strip(),
                    max_chars=300,
                ),
                "target_duration_seconds": float(timing.get("duration_seconds", 0.0) or 0.0),
            }
        )

    if scenes:
        return scenes

    title = str(script_json.get("module_title", "Lesson")).strip() if isinstance(script_json, dict) else "Lesson"
    return [
        {
            "scene_id": 1,
            "title": title or "Lesson",
            "narration_text": _normalize_display_text(
                str(script_json.get("full_narration_text", "")).strip() if isinstance(script_json, dict) else "",
                max_chars=500,
            ),
            "on_screen_text": title or "Lesson",
            "math_expressions": [],
            "visual_instructions": "Explain the key idea with a visual diagram.",
            "target_duration_seconds": 4.0,
        }
    ]


_VISUAL_TYPE_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("number line", "numberline", "integers", "counting", "whole number"), "number_line"),
    (("coordinate", "graph", "axes", "axis", "plot", "function", "parabola", "slope"), "coordinate_plane"),
    (("fraction", "numerator", "denominator", "ratio", "proportion", "mixed number"), "fraction_bar"),
    (("angle", "triangle", "polygon", "circle", "rectangle", "square", "geometry", "perimeter", "area"), "geometry_shape"),
    (("factor tree", "prime factor", "hcf", "lcm", "divisor"), "tree_diagram"),
    (("venn", "union", "intersection", "subset", "set"), "venn_diagram"),
    (("block", "array", "grid", "area model", "group"), "blocks"),
    (("step", "procedure", "process", "flow", "algorithm", "method"), "flowchart"),
)


def _infer_diagram_type(scene: dict[str, Any]) -> str:
    combined = " ".join([
        str(scene.get("visual_instructions", "")),
        str(scene.get("on_screen_text", "")),
        str(scene.get("narration_text", "")),
        " ".join(str(e) for e in scene.get("math_expressions", [])),
        str(scene.get("title", "")),
    ]).lower()
    for keywords, dtype in _VISUAL_TYPE_KEYWORDS:
        if any(kw in combined for kw in keywords):
            return dtype
    return "equation_stack"


def _build_smart_storyboard(scene_contract: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a storyboard deterministically — no LLM call needed."""
    scenes: list[dict[str, Any]] = []
    for scene in scene_contract:
        scene_id = int(scene["scene_id"])
        title = scene.get("title", f"Scene {scene_id}")
        on_screen = scene.get("on_screen_text", "")
        expressions = scene.get("math_expressions", [])
        visual_instructions = scene.get("visual_instructions", "")
        diagram_type = _infer_diagram_type(scene)

        key_steps: list[str] = []
        if visual_instructions:
            key_steps.append(visual_instructions[:100])
        for line in on_screen.split("\n")[:2]:
            line = line.strip()
            if line:
                key_steps.append(f"Show: {line[:80]}")
        for expr in expressions[:2]:
            key_steps.append(f"Highlight: {str(expr)[:80]}")
        if len(key_steps) < 2:
            key_steps = [
                f"Introduce: {title}",
                "Present main concept visually",
                "Reinforce with worked example",
            ]

        scenes.append({
            "scene_id": scene_id,
            "teaching_goal": f"Teach {title} clearly using {diagram_type.replace('_', ' ')}.",
            "diagram_type": diagram_type,
            "key_steps": key_steps[:5],
            "emphasis_terms": [str(e)[:60] for e in expressions[:3]],
            "transition_style": "fade",
        })
    return {"scenes": scenes}


def _fallback_storyboard(scene_contract: list[dict[str, Any]]) -> dict[str, Any]:
    return _build_smart_storyboard(scene_contract)


def _normalize_storyboard(data: dict[str, Any], scene_contract: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return _fallback_storyboard(scene_contract)

    scene_ids = {int(item["scene_id"]) for item in scene_contract}
    raw = data.get("scenes")
    if not isinstance(raw, list):
        return _fallback_storyboard(scene_contract)

    normalized: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            scene_id = int(item.get("scene_id"))
        except Exception:
            continue
        if scene_id not in scene_ids:
            continue
        key_steps_raw = item.get("key_steps", [])
        key_steps = [str(step).strip() for step in key_steps_raw if str(step).strip()]
        if len(key_steps) < 2:
            key_steps = [
                "Introduce the core concept.",
                "Demonstrate a worked transformation visually.",
                "Summarize the takeaway.",
            ]
        normalized.append(
            {
                "scene_id": scene_id,
                "teaching_goal": str(item.get("teaching_goal", "")).strip() or "Teach the scene visually and clearly.",
                "diagram_type": str(item.get("diagram_type", "flowchart")).strip() or "flowchart",
                "key_steps": key_steps[:5],
                "emphasis_terms": [str(term).strip() for term in item.get("emphasis_terms", []) if str(term).strip()][:5],
                "transition_style": str(item.get("transition_style", "fade")).strip() or "fade",
            }
        )

    if not normalized:
        return _fallback_storyboard(scene_contract)

    normalized_by_id = {int(scene["scene_id"]): scene for scene in normalized}
    completed = []
    for scene in scene_contract:
        sid = int(scene["scene_id"])
        completed.append(normalized_by_id.get(sid) or _fallback_storyboard([scene])["scenes"][0])
    return {"scenes": completed}


def _generate_storyboard(
    script_json: dict[str, Any],
    timing_alignment: list[dict[str, Any]],
    scene_contract: list[dict[str, Any]],
    llm_provider: LLMProvider,
) -> dict[str, Any]:
    # Use deterministic storyboard — avoids one full LLM round-trip per attempt.
    # The scene_contract already contains visual_instructions from the script agent,
    # which is enough to infer diagram types and key steps without a separate LLM call.
    del llm_provider  # unused
    return _build_smart_storyboard(scene_contract)


def _validate_frame_safety(code: str) -> list[str]:
    """Check if code includes frame safety checks"""
    errors = []

    # Look for frame safety patterns
    has_frame_check = (
        "config.frame_width" in code
        or "config.frame_height" in code
        or "scale_to_fit_width" in code
        or "scale_to_fit_height" in code
    )

    if not has_frame_check:
        errors.append(
            "Code missing frame safety checks. Add: if obj.width > config.frame_width - 1.2: obj.scale_to_fit_width(...)"
        )

    return errors


def _validate_spacing(code: str) -> list[str]:
    """Check for proper spacing between elements"""
    errors = []

    # Look for buff parameter usage
    buff_matches = re.findall(r"buff\s*=\s*([\d.]+)", code)

    if buff_matches:
        min_buff = min(float(b) for b in buff_matches)
        if min_buff < 0.25:
            errors.append(
                f"Spacing too tight: found buff={min_buff}, use buff >= 0.3 to avoid overlaps"
            )
    else:
        # No buff found - warning
        errors.append(
            "No spacing (buff) parameters found. Use .next_to(..., buff=0.35) for vertical spacing"
        )

    return errors


def _validate_math_expressions_present(code: str, scene_contract: list[dict[str, Any]]) -> list[str]:
    """Validate that all required math expressions are present in the code"""
    errors = []
    code_lower = code.lower()

    for scene in scene_contract:
        scene_id = int(scene.get("scene_id", 0))
        expressions = scene.get("math_expressions", [])
        for expr in expressions:
            # Normalize expression for comparison
            expr_key = _equation_key(expr)
            code_key = _equation_key(code_lower)

            if expr_key not in code_key:
                errors.append(
                    f"Scene {scene_id}: Required math expression missing: '{expr}'"
                )

    return errors


def _collect_validation_errors(code: str, scene_class_name: str, scene_contract: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if f"class {scene_class_name}(Scene)" not in code:
        errors.append(f"Generated code must include class {scene_class_name}(Scene).")
    if "run_time=" not in code and ".wait(" not in code:
        errors.append("Generated code must include run_time/wait pacing.")
    if _contains_latex_mobjects(code):
        errors.append("Generated code must not use MathTex/Tex/SingleStringMathTex in this runtime.")
    if _contains_latex_sensitive_numberline(code):
        errors.append(
            "Generated code uses NumberLine labels that require TeX (include_numbers=True or add_numbers). "
            "Use NumberLine without numeric labels in this runtime."
        )
    forbidden_calls = _find_forbidden_mcp_calls(code)
    if forbidden_calls:
        errors.append(
            "Generated code uses unsupported Manim methods for this runtime: "
            + ", ".join(sorted(set(forbidden_calls)))
            + "."
        )
    if "AddTextLetterByLetter(" not in code:
        errors.append("Generated code must reveal instructional text character-by-character using AddTextLetterByLetter.")

    # NEW validations
    errors.extend(_validate_frame_safety(code))
    errors.extend(_validate_spacing(code))
    errors.extend(_validate_math_expressions_present(code, scene_contract))

    carry_forward_scenes = 0
    for index, scene in enumerate(scene_contract, start=1):
        if index > 1 and _scene_refers_previous(scene):
            carry_forward_scenes += 1

    # If script references prior context in multiple scenes, code must not clear everything every transition.
    if carry_forward_scenes > 0 and code.count("FadeOut(") >= max(1, len(scene_contract) - 1):
        errors.append(
            "Script references earlier context, but code appears to erase content on every scene transition. "
            "Keep prior context visible and build below it when appropriate."
        )

    try:
        ast.parse(code)
    except SyntaxError as exc:
        errors.append(f"Generated Manim code has invalid Python syntax: {exc}")
    return errors


def _validate_generated_code(code: str, scene_class_name: str, scene_contract: list[dict[str, Any]]) -> None:
    errors = _collect_validation_errors(code, scene_class_name, scene_contract)
    if errors:
        details = "\n".join(f"- {item}" for item in errors)
        raise ValueError(f"Generated Manim code failed quality validation:\n{details}")


def _validate_mcp_generated_code(code: str, scene_class_name: str, scene_contract: list[dict[str, Any]]) -> None:
    errors = _collect_validation_errors(code, scene_class_name, scene_contract)
    if errors:
        details = "\n".join(f"- {item}" for item in errors)
        raise ValueError(f"Generated MCP Manim code failed compatibility validation:\n{details}")


def _py_literal(text: str) -> str:
    return repr((text or "").strip())


def _clip_for_display(text: str, max_chars: int = 160) -> str:
    value = (text or "").strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "..."


def _scene_refers_previous(scene: dict[str, Any]) -> bool:
    blob = " ".join(
        [
            str(scene.get("title", "")),
            str(scene.get("narration_text", "")),
            str(scene.get("on_screen_text", "")),
            str(scene.get("visual_instructions", "")),
        ]
    ).lower()
    cues = (
        "earlier",
        "previous",
        "as we saw",
        "from above",
        "as above",
        "building on",
        "recall",
        "again",
        "using this",
        "therefore",
        "now that",
        "continue",
    )
    return any(cue in blob for cue in cues)


def _build_fallback_manim_code(scene_class_name: str, scene_contract: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("from manim import *")
    lines.append("")
    lines.append(f"class {scene_class_name}(Scene):")
    lines.append("    def construct(self):")
    lines.append("        safe_width = config.frame_width - 1.4")
    lines.append("        safe_height = config.frame_height - 1.0")
    lines.append("        safe_bottom = (-config.frame_height / 2) + 0.5")
    lines.append("        safe_top = (config.frame_height / 2) - 0.5")
    lines.append("")
    lines.append("        def fit_to_frame(mobj):")
    lines.append("            if mobj.width > safe_width:")
    lines.append("                mobj.scale_to_fit_width(safe_width)")
    lines.append("            if mobj.height > safe_height:")
    lines.append("                mobj.scale_to_fit_height(safe_height)")
    lines.append("            return mobj")
    lines.append("")
    lines.append("        stack_group = VGroup()")

    for index, scene in enumerate(scene_contract, start=1):
        scene_id = int(scene.get("scene_id", index))
        group = f"scene_{scene_id}_group"
        title_var = f"title_{scene_id}"
        title = _clip_for_display(str(scene.get("title", f"Scene {scene_id}")), 70) or f"Scene {scene_id}"
        narration = _clip_for_display(str(scene.get("narration_text", "")), 150)
        on_screen_text = _clip_for_display(str(scene.get("on_screen_text", "")), 100)
        expressions = [_clip_for_display(str(x), 84) for x in scene.get("math_expressions", []) if str(x).strip()]

        target_duration = float(scene.get("target_duration_seconds", 0.0) or 0.0)
        target_duration = max(2.5, target_duration)
        # Carry-forward disabled in fallback — stacking without total-height
        # budget tracking causes individual shift guards to fight each other,
        # producing overlapping or off-screen content.  Always clear.
        transition_rt = 0.28

        lines.append(f"        # Scene {scene_id}: {title}")
        if index > 1:
            lines.append("        if len(stack_group.submobjects) > 0:")
            lines.append(f"            self.play(FadeOut(stack_group), run_time={transition_rt:.2f})")
            lines.append("            stack_group = VGroup()")

        lines.append(f"        {group} = VGroup()")
        lines.append(f"        {title_var} = fit_to_frame(Text({_py_literal(title)}, font_size=34))")
        lines.append(f"        {group}.add({title_var})")
        lines.append("        if len(stack_group.submobjects) == 0:")
        lines.append(f"            {title_var}.to_edge(UP, buff=0.6)")
        lines.append("        else:")
        lines.append(f"            {title_var}.next_to(stack_group, DOWN, aligned_edge=LEFT, buff=0.42)")
        lines.append(f"        if {title_var}.get_bottom()[1] < safe_bottom:")
        lines.append(f"            {title_var}.shift(UP * (safe_bottom - {title_var}.get_bottom()[1]))")
        lines.append(f"        self.play(AddTextLetterByLetter({title_var}, time_per_char=0.02), run_time=0.6)")
        lines.append(f"        underline_width_{scene_id} = min(max(3.8, {title_var}.width + 0.5), safe_width)")
        lines.append(
            f"        underline_{scene_id} = Line(LEFT * (underline_width_{scene_id} / 2), RIGHT * (underline_width_{scene_id} / 2)).next_to({title_var}, DOWN, buff=0.32)"
        )
        lines.append(f"        {group}.add(underline_{scene_id})")
        lines.append(f"        self.play(Create(underline_{scene_id}), run_time=0.2)")

        line_var_prev = f"underline_{scene_id}"

        # Handle on-screen text
        text_rt = 0.8
        if on_screen_text:
            text_var = f"text_{scene_id}"
            on_screen_clean = on_screen_text.replace('"', '\\"').replace('\n', ' ')[:200]
            lines.append(f"        {text_var} = fit_to_frame(Text({_py_literal(on_screen_clean)}, font_size=28))")
            lines.append(f"        {text_var}.next_to({line_var_prev}, DOWN, aligned_edge=LEFT, buff=0.35)")
            lines.append(f"        if {text_var}.get_bottom()[1] < safe_bottom:")
            lines.append(f"            {text_var}.shift(UP * (safe_bottom - {text_var}.get_bottom()[1]))")
            lines.append(f"        {group}.add({text_var})")
            lines.append(f"        self.play(AddTextLetterByLetter({text_var}, time_per_char=0.014), run_time={text_rt:.2f})")
            line_var_prev = text_var
            lines.append("")

        # Handle math expressions explicitly (with yellow color)
        expr_rt = 0.7
        for expr_idx, expr in enumerate(expressions[:3]):  # Limit to 3 expressions
            expr_var = f"expr_{scene_id}_{expr_idx}"
            expr_clean = expr.replace('"', '\\"')
            lines.append(f"        {expr_var} = fit_to_frame(Text({_py_literal(expr_clean)}, font_size=32, color=YELLOW))")
            lines.append(f"        {expr_var}.next_to({line_var_prev}, DOWN, aligned_edge=LEFT, buff=0.35)")
            lines.append(f"        if {expr_var}.get_bottom()[1] < safe_bottom:")
            lines.append(f"            {expr_var}.shift(UP * (safe_bottom - {expr_var}.get_bottom()[1]))")
            lines.append(f"        {group}.add({expr_var})")
            lines.append(f"        self.play(AddTextLetterByLetter({expr_var}, time_per_char=0.014), run_time={expr_rt:.2f})")
            line_var_prev = expr_var
            lines.append("")

        # If no content, show narration
        if not on_screen_text and not expressions and narration:
            text_var = f"narr_{scene_id}"
            lines.append(f"        {text_var} = fit_to_frame(Text({_py_literal(narration)}, font_size=28))")
            lines.append(f"        {text_var}.next_to({line_var_prev}, DOWN, aligned_edge=LEFT, buff=0.35)")
            lines.append(f"        if {text_var}.get_bottom()[1] < safe_bottom:")
            lines.append(f"            {text_var}.shift(UP * (safe_bottom - {text_var}.get_bottom()[1]))")
            lines.append(f"        {group}.add({text_var})")
            lines.append(f"        self.play(AddTextLetterByLetter({text_var}, time_per_char=0.014), run_time={text_rt:.2f})")
            lines.append("")

        lines.append(f"        stack_group.add({group})")
        lines.append("        if len(stack_group.submobjects) > 0 and stack_group.get_bottom()[1] < safe_bottom:")
        lines.append("            _shift_amt = safe_bottom - stack_group.get_bottom()[1] + 0.08")
        lines.append("            if stack_group.get_top()[1] + _shift_amt > safe_top:")
        lines.append("                self.play(FadeOut(stack_group), run_time=0.2)")
        lines.append("                stack_group = VGroup()")
        lines.append("            else:")
        lines.append("                self.play(stack_group.animate.shift(UP * _shift_amt), run_time=0.2)")

        # Calculate consumed time: title (0.6) + underline (0.2) + text + math expressions
        text_time = 0.8 if on_screen_text else 0
        math_time = len(expressions[:3]) * 0.7
        consumed = 0.6 + 0.2 + text_time + math_time
        wait_rt = max(0.3, target_duration - consumed)
        lines.append(f"        self.wait({wait_rt:.2f})")

    lines.append("        if len(stack_group.submobjects) > 0:")
    lines.append("            self.play(FadeOut(stack_group), run_time=0.3)")
    return "\n".join(lines) + "\n"


def generate_manim_code(
    script_json: dict[str, Any],
    timing_alignment: list[dict[str, Any]],
    scene_class_name: str,
    llm_provider: LLMProvider,
) -> str:
    start_time = time.time()
    scene_contract = _build_scene_contract(script_json, timing_alignment)
    use_mcp_backend = _is_mcp_backend()

    logger.info(
        "manim_generation_started",
        extra={
            "scene_class": scene_class_name,
            "use_mcp": use_mcp_backend,
            "num_scenes": len(scene_contract),
        },
    )

    try:
        storyboard = _generate_storyboard(script_json, timing_alignment, scene_contract, llm_provider)
        if use_mcp_backend:
            prompt = manim_code_prompt_mcp(
                scene_class_name,
                script_json,
                timing_alignment,
                storyboard,
            )
        else:
            docs_context = get_manim_docs_context()
            prompt = manim_code_prompt(
                scene_class_name,
                script_json,
                docs_context,
                timing_alignment,
                scene_contract,
                storyboard,
            )

        code = _strip_code_fences(llm_provider.generate_code(prompt))
        if use_mcp_backend:
            code = _rewrite_latex_calls(code)
            code = _rewrite_numberline_calls(code)
            code = _rewrite_sector_calls(code)
            code = _rewrite_unsupported_mobject_calls(code)
            try:
                _validate_mcp_generated_code(code, scene_class_name, scene_contract)
                logger.info(
                    "manim_generation_success",
                    extra={
                        "scene_class": scene_class_name,
                        "code_lines": len(code.split("\n")),
                        "duration_ms": (time.time() - start_time) * 1000,
                    },
                )
                return code
            except ValueError as e:
                logger.warning(
                    "manim_validation_failed",
                    extra={
                        "scene_class": scene_class_name,
                        "error": str(e),
                        "duration_ms": (time.time() - start_time) * 1000,
                    },
                )
                logger.info("manim_fallback_used", extra={"scene_class": scene_class_name})
                return _build_fallback_manim_code(scene_class_name, scene_contract)

        code = _rewrite_latex_calls(code)
        code = _rewrite_numberline_calls(code)
        code = _rewrite_sector_calls(code)

        # Collect validation errors
        errors = _collect_validation_errors(code, scene_class_name, scene_contract)

        if errors:
            logger.warning(
                "manim_validation_failed",
                extra={
                    "scene_class": scene_class_name,
                    "error_count": len(errors),
                    "error_types": {
                        "missing_math": sum(1 for e in errors if "math expression" in e.lower()),
                        "missing_addtext": sum(1 for e in errors if "AddTextLetterByLetter" in e),
                        "frame_safety": sum(1 for e in errors if "frame safety" in e.lower()),
                        "spacing": sum(1 for e in errors if "spacing" in e.lower() or "buff" in e.lower()),
                    },
                    "duration_ms": (time.time() - start_time) * 1000,
                },
            )
            logger.info("manim_fallback_used", extra={"scene_class": scene_class_name})
            fallback = _build_fallback_manim_code(scene_class_name, scene_contract)
            _validate_generated_code(fallback, scene_class_name, scene_contract)
            return fallback

        logger.info(
            "manim_generation_success",
            extra={
                "scene_class": scene_class_name,
                "code_lines": len(code.split("\n")),
                "duration_ms": (time.time() - start_time) * 1000,
            },
        )
        return code

    except Exception as e:
        logger.error(
            "manim_generation_error",
            extra={
                "scene_class": scene_class_name,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000,
            },
        )
        raise


def repair_manim_code(
    script_json: dict[str, Any],
    timing_alignment: list[dict[str, Any]],
    current_code: str,
    error_log: str,
    scene_class_name: str,
    llm_provider: LLMProvider,
) -> str:
    scene_contract = _build_scene_contract(script_json, timing_alignment)
    storyboard = _generate_storyboard(script_json, timing_alignment, scene_contract, llm_provider)
    use_mcp_backend = _is_mcp_backend()
    if use_mcp_backend:
        prompt = manim_repair_prompt_mcp(
            scene_class_name,
            script_json,
            timing_alignment,
            storyboard,
            current_code,
            error_log,
        )
    else:
        validation_errors = _collect_validation_errors(current_code, scene_class_name, scene_contract)
        docs_context = get_manim_docs_context()
        prompt = manim_repair_prompt(
            scene_class_name,
            script_json,
            timing_alignment,
            scene_contract,
            storyboard,
            current_code,
            error_log,
            validation_errors,
            docs_context,
        )
    repaired = _strip_code_fences(llm_provider.generate_code(prompt))
    if use_mcp_backend:
        repaired = _rewrite_latex_calls(repaired)
        repaired = _rewrite_numberline_calls(repaired)
        repaired = _rewrite_sector_calls(repaired)
        repaired = _rewrite_unsupported_mobject_calls(repaired)
        try:
            _validate_mcp_generated_code(repaired, scene_class_name, scene_contract)
            return repaired
        except ValueError:
            return _build_fallback_manim_code(scene_class_name, scene_contract)

    repaired = _rewrite_latex_calls(repaired)
    repaired = _rewrite_numberline_calls(repaired)
    repaired = _rewrite_sector_calls(repaired)
    try:
        _validate_generated_code(repaired, scene_class_name, scene_contract)
        return repaired
    except ValueError:
        fallback = _build_fallback_manim_code(scene_class_name, scene_contract)
        _validate_generated_code(fallback, scene_class_name, scene_contract)
        return fallback
