from __future__ import annotations

import ast
import re
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

_LATEX_MOBJECT_NAMES = {"MathTex", "Tex", "SingleStringMathTex"}
_ALLOWED_TEXT_KWARGS = {"font_size", "color"}


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


def _contains_latex_sensitive_numberline(code: str) -> bool:
    include_numbers_true = re.search(r"NumberLine\([^)]*include_numbers\s*=\s*True", code, flags=re.S)
    add_numbers_call = re.search(r"\.add_numbers\s*\(", code)
    return bool(include_numbers_true or add_numbers_call)


def _equation_key(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())


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
                "title": str(scene.get("title", f"Scene {scene_id}")).strip() or f"Scene {scene_id}",
                "narration_text": str(scene.get("narration_text", "")).strip(),
                "on_screen_text": str(scene.get("on_screen_text", "")).strip(),
                "math_expressions": [str(x).strip() for x in scene.get("math_expressions", []) if str(x).strip()],
                "visual_instructions": str(scene.get("visual_instructions", "")).strip(),
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
            "narration_text": str(script_json.get("full_narration_text", "")).strip() if isinstance(script_json, dict) else "",
            "on_screen_text": title or "Lesson",
            "math_expressions": [],
            "visual_instructions": "Explain the key idea with a visual diagram.",
            "target_duration_seconds": 4.0,
        }
    ]


def _fallback_storyboard(scene_contract: list[dict[str, Any]]) -> dict[str, Any]:
    scenes = []
    for scene in scene_contract:
        scene_id = int(scene["scene_id"])
        scenes.append(
            {
                "scene_id": scene_id,
                "teaching_goal": f"Explain {scene['title']} with visuals and progressive emphasis.",
                "diagram_type": "flowchart",
                "key_steps": [
                    "Introduce the concept title and context.",
                    "Show the main statement or equation clearly.",
                    "Highlight the key transformation or conclusion.",
                ],
                "emphasis_terms": [scene["title"]],
                "transition_style": "fade",
            }
        )
    return {"scenes": scenes}


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
    docs_context = get_manim_docs_context()
    prompt = manim_storyboard_prompt(script_json, timing_alignment, docs_context)
    try:
        raw = llm_provider.generate_json(prompt, max_retries=1)
        return _normalize_storyboard(raw, scene_contract)
    except Exception:
        return _fallback_storyboard(scene_contract)


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
    if "AddTextLetterByLetter(" not in code:
        errors.append("Generated code must reveal instructional text character-by-character using AddTextLetterByLetter.")

    compact_code = _equation_key(code)
    carry_forward_scenes = 0
    for index, scene in enumerate(scene_contract, start=1):
        scene_id = int(scene.get("scene_id", index))
        expressions = [str(expr).strip() for expr in scene.get("math_expressions", []) if str(expr).strip()]
        if expressions:
            if not any(_equation_key(expr) in compact_code for expr in expressions if _equation_key(expr)):
                errors.append(f"Scene {scene_id} does not include script math_expressions.")
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
    lines.append("        safe_width = config.frame_width - 1.2")
    lines.append("        safe_height = config.frame_height - 0.9")
    lines.append("        safe_bottom = (-config.frame_height / 2) + 0.45")
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
        carry_forward = index > 1 and _scene_refers_previous(scene)
        transition_rt = 0.28

        lines.append(f"        # Scene {scene_id}: {title}")
        if index > 1 and not carry_forward:
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
            f"        underline_{scene_id} = Line(LEFT * (underline_width_{scene_id} / 2), RIGHT * (underline_width_{scene_id} / 2)).next_to({title_var}, DOWN, buff=0.18)"
        )
        lines.append(f"        {group}.add(underline_{scene_id})")
        lines.append(f"        self.play(Create(underline_{scene_id}), run_time=0.2)")

        line_var_prev = f"underline_{scene_id}"
        display_lines: list[str] = []
        if on_screen_text:
            display_lines.append(on_screen_text)
        if expressions:
            display_lines.extend(expressions)
        elif narration:
            display_lines.append(narration)
        if not display_lines:
            display_lines.append(title)
        if len(display_lines) > 3:
            display_lines = display_lines[:3]

        line_rt = max(0.42, min(0.95, target_duration / max(3, len(display_lines) + 2)))
        for line_idx, line_text in enumerate(display_lines):
            text_var = f"line_{scene_id}_{line_idx}"
            lines.append(f"        {text_var} = fit_to_frame(Text({_py_literal(line_text)}, font_size=28))")
            lines.append(f"        {text_var}.next_to({line_var_prev}, DOWN, aligned_edge=LEFT, buff=0.30)")
            lines.append(f"        if {text_var}.get_bottom()[1] < safe_bottom:")
            lines.append(f"            {text_var}.shift(UP * (safe_bottom - {text_var}.get_bottom()[1]))")
            lines.append(f"        {group}.add({text_var})")
            lines.append(f"        self.play(AddTextLetterByLetter({text_var}, time_per_char=0.014), run_time={line_rt:.2f})")
            line_var_prev = text_var

        lines.append(f"        stack_group.add({group})")
        lines.append("        if stack_group.get_bottom()[1] < safe_bottom:")
        lines.append("            overflow = safe_bottom - stack_group.get_bottom()[1]")
        lines.append("            self.play(stack_group.animate.shift(UP * (overflow + 0.08)), run_time=0.2)")

        consumed = 0.6 + 0.2 + (line_rt * len(display_lines))
        wait_rt = max(0.2, target_duration - consumed)
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
    scene_contract = _build_scene_contract(script_json, timing_alignment)
    storyboard = _generate_storyboard(script_json, timing_alignment, scene_contract, llm_provider)
    use_mcp_backend = _is_mcp_backend()
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
        return code

    code = _rewrite_latex_calls(code)
    code = _rewrite_numberline_calls(code)
    try:
        _validate_generated_code(code, scene_class_name, scene_contract)
        return code
    except ValueError:
        fallback = _build_fallback_manim_code(scene_class_name, scene_contract)
        _validate_generated_code(fallback, scene_class_name, scene_contract)
        return fallback


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
        return repaired

    repaired = _rewrite_latex_calls(repaired)
    repaired = _rewrite_numberline_calls(repaired)
    try:
        _validate_generated_code(repaired, scene_class_name, scene_contract)
        return repaired
    except ValueError:
        fallback = _build_fallback_manim_code(scene_class_name, scene_contract)
        _validate_generated_code(fallback, scene_class_name, scene_contract)
        return fallback
