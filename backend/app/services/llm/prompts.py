from __future__ import annotations

import json


# Concrete examples showing correct Manim patterns
EXAMPLES = """
EXAMPLE 1 - Default scene start (ALWAYS clear screen first unless carry-forward):
```python
safe_w = config.frame_width - 1.4
safe_h = config.frame_height - 1.0

def fit(m):
    if m.width > safe_w:
        m.scale_to_fit_width(safe_w)
    if m.height > safe_h:
        m.scale_to_fit_height(safe_h)
    return m

self.play(FadeOut(*self.mobjects), run_time=0.3)
title = fit(Text("Understanding Division", font_size=34))
title.to_edge(UP, buff=0.6)
self.play(AddTextLetterByLetter(title, time_per_char=0.02), run_time=0.6)
self.wait(0.3)
```

EXAMPLE 2 - Stacking text and equations (fit on EVERY object):
```python
body = fit(Text("When we divide 25 by 5 we get 5.", font_size=28))
body.next_to(title, DOWN, buff=0.4)
self.play(AddTextLetterByLetter(body, time_per_char=0.014), run_time=0.8)

eq = fit(Text("25 divided by 5 equals 5", font_size=30, color=YELLOW))
eq.next_to(body, DOWN, buff=0.35)
self.play(AddTextLetterByLetter(eq, time_per_char=0.014), run_time=0.7)
```

EXAMPLE 3 - Proper spacing (NO overlaps, always use buff >= 0.35):
```python
stack = VGroup()
line1 = fit(Text("First concept", font_size=28))
line1.to_edge(UP, buff=0.6)
stack.add(line1)

line2 = fit(Text("Second concept", font_size=28))
line2.next_to(line1, DOWN, buff=0.35)
stack.add(line2)

equation = fit(Text("x = 10", font_size=30, color=YELLOW))
equation.next_to(line2, DOWN, buff=0.35)
stack.add(equation)
```

EXAMPLE 4 - Carry-forward (ONLY when narration says "recall"/"as we saw"/"therefore"):
```python
stack = VGroup(title, body, eq)
# MANDATORY height check before adding more content
if stack.height > config.frame_height * 0.72:
    self.play(FadeOut(stack), run_time=0.25)
    stack = VGroup()
    next_title = fit(Text("Continuing...", font_size=34))
    next_title.to_edge(UP, buff=0.6)
    self.play(AddTextLetterByLetter(next_title, time_per_char=0.02), run_time=0.6)
else:
    new_line = fit(Text("Building on this...", font_size=28))
    new_line.next_to(stack, DOWN, buff=0.4)
    self.play(AddTextLetterByLetter(new_line, time_per_char=0.014), run_time=0.6)
    stack.add(new_line)
```

CRITICAL RULES:
✓ CLEAR screen between scenes: self.play(FadeOut(*self.mobjects), run_time=0.3) — DEFAULT
✓ USE AddTextLetterByLetter for ALL instructional text
✓ CALL fit() on EVERY Text/mobject before placing or animating — never skip
✓ font_size <= 34 for titles, <= 30 for equations (color=YELLOW), <= 28 for body text
✓ buff >= 0.35 between stacked elements
✓ Include ALL math_expressions from script as YELLOW Text objects
✓ HEIGHT CHECK before stacking: if stack.height > config.frame_height * 0.72 → clear
✗ DON'T carry forward unless narration explicitly says "recall", "as we saw", "therefore", "earlier"
✗ DON'T use Write() or FadeIn() for instructional text
✗ DON'T use font_size > 34
✗ DON'T stack more content than fits in config.frame_height * 0.72
"""


def _inject_timing_guidance(prompt: str, scene_contract: list[dict]) -> str:
    """Add timing breakdown to help LLM pace animations"""

    guidance = "\n\nTIMING GUIDANCE:\n"
    for scene in scene_contract:
        target_dur = scene.get("target_duration_seconds", 0)

        # Estimate component durations
        title_time = 0.6
        text_lines = len(scene.get("on_screen_text", "").split("\n"))
        text_time = text_lines * 0.5
        math_time = len(scene.get("math_expressions", [])) * 0.7
        buffer_time = 0.5

        animation_time = title_time + text_time + math_time
        wait_time = max(0, target_dur - animation_time - buffer_time)

        guidance += f"Scene {scene['scene_id']} (target: {target_dur:.1f}s):\n"
        guidance += f"  - Title reveal: ~0.6s\n"
        guidance += f"  - Text lines ({text_lines}): ~{text_time:.1f}s\n"
        guidance += f"  - Math expressions: ~{math_time:.1f}s\n"
        guidance += f"  - Recommended wait: {wait_time:.1f}s\n"

    return prompt + guidance


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
        "For arithmetic expressions with numbers, write operators in words "
        "(example: '4 multiplied by 5', '10 divided by 2', '7 plus 3', '9 minus 1'). "
        "Write math in plain readable text only; do not use LaTeX commands (no \\frac, \\div, \\times, or backslashes). "
        "Use only entities and names present in source text; do not invent people/place names. "
        "Do not produce ASR-like gibberish or malformed phrases. "
        "Do not alter normal words that contain letters like x or hyphens (for example: 'next', 'real-world', 'explore'). "
        "visual_instructions must be specific and visual — describe exactly what diagram/shape/layout to draw "
        "(e.g. 'draw a number line from 0 to 10', 'show two rectangles side by side', 'display equation in centre'). "
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
    base_prompt = (
        "You write deterministic Python Manim Community Edition code. "
        f"Return ONLY Python code for a single class named {scene_class_name} inheriting Scene. "
        "Requirements: render scenes in order, avoid external assets, "
        "DO NOT use MathTex, Tex, or SingleStringMathTex because the runtime has no LaTeX binary, "
        "and ensure code runs in headless Linux container. Prefer Text/MarkupText and simple shapes. "
        "Primary rules:\n"
        "1) Script alignment: animate exactly what the script says — title, on_screen_text, "
        "math_expressions (as YELLOW Text), visual diagram from visual_instructions.\n"
        "2) Reveal text/equations character-by-character using AddTextLetterByLetter.\n"
        "3) Scene transitions: CLEAR the screen at the start of EVERY scene with "
        "self.play(FadeOut(*self.mobjects), run_time=0.3). EXCEPTION: only keep prior content "
        "if the scene's narration_text explicitly contains 'recall', 'as we saw', 'building on', "
        "'therefore', or 'earlier'. In carry-forward mode, always check "
        "stack.height > config.frame_height * 0.72 and clear if so.\n"
        "4) Frame safety: define fit(m) at the top of construct() — "
        "scale_to_fit_width(config.frame_width - 1.4), scale_to_fit_height(config.frame_height - 1.0). "
        "Call fit() on EVERY Text and diagram mobject before positioning. "
        "font_size <= 34 for titles, <= 30 for equations, <= 28 for body text.\n"
        "5) Spacing: buff >= 0.35 between stacked elements. "
        "Never place a new element without calling .next_to() or .to_edge().\n"
        "6) Use run_time/wait so each scene approximately matches timing_alignment.duration_seconds.\n"
        "No markdown.\n\n"
        f"{EXAMPLES}\n\n"
        f"Manim documentation context:\n{manim_docs_context}\n\n"
        f"Scene contract JSON (must be followed exactly):\n{json.dumps(scene_contract, indent=2)}\n\n"
        f"Storyboard JSON:\n{json.dumps(storyboard, indent=2)}\n\n"
        f"Timing alignment JSON (seconds):\n{json.dumps(timing_alignment, indent=2)}\n\n"
        f"Script JSON:\n{json.dumps(script_json, indent=2)}"
    )
    return _inject_timing_guidance(base_prompt, scene_contract)


def manim_code_prompt_mcp(
    scene_class_name: str,
    script_json: dict,
    timing_alignment: list[dict],
    storyboard: dict,
) -> str:
    # Extract scene_contract from timing_alignment for timing guidance
    scene_contract = []
    for i, timing in enumerate(timing_alignment):
        scene_id = timing.get("scene_id", i + 1)
        # Extract relevant scene data from script_json
        scene_data = next(
            (s for s in script_json.get("scenes", []) if s.get("scene_id") == scene_id),
            {}
        )
        scene_contract.append({
            "scene_id": scene_id,
            "target_duration_seconds": timing.get("duration_seconds", 5.0),
            "on_screen_text": scene_data.get("on_screen_text", ""),
            "math_expressions": scene_data.get("math_expressions", []),
        })

    base_prompt = (
        "You write deterministic Python Manim Community Edition code. "
        f"Return ONLY valid Python code — no markdown, no prose, no code fences — "
        f"for a single class named {scene_class_name} inheriting Scene. "
        "The code must be syntactically valid Python that can be parsed with ast.parse().\n\n"
        "Hard rules:\n"
        "1) Do NOT use MathTex, Tex, or SingleStringMathTex. Use Text() instead.\n"
        "2) Do NOT use clip_path or set_clip_path methods.\n"
        "3) For Sector, use keyword `radius` not `outer_radius`.\n"
        "4) Use only standard Manim CE mobjects: Text, VGroup, Circle, Square, Rectangle, Line, Dot, Arrow, Axes, NumberPlane, Polygon.\n"
        "5) Match scene timing to timing_alignment duration_seconds using self.play(run_time=...) and self.wait(...).\n"
        "6) Reveal text with AddTextLetterByLetter(text_mobject) for instructional text.\n"
        "7) CLEAR the screen at the start of each scene: self.play(FadeOut(*self.mobjects), run_time=0.3). "
        "Only skip clearing if narration explicitly says 'recall', 'as we saw', 'therefore', or 'earlier'.\n"
        "8) Define fit(m) helper at top of construct(): scale to config.frame_width - 1.4 and config.frame_height - 1.0. "
        "Call fit() on EVERY Text and diagram before placing. font_size <= 34 titles, <= 30 equations, <= 28 body.\n"
        "9) buff >= 0.35 between all stacked elements.\n"
        "10) If carrying forward content, check height > config.frame_height * 0.72 and clear if exceeded.\n\n"
        f"{EXAMPLES}\n\n"
        f"Storyboard JSON:\n{json.dumps(storyboard, indent=2)}\n\n"
        f"Timing alignment JSON (seconds):\n{json.dumps(timing_alignment, indent=2)}\n\n"
        f"Script JSON:\n{json.dumps(script_json, indent=2)}"
    )
    return _inject_timing_guidance(base_prompt, scene_contract)


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
        "CLEAR screen between scenes with FadeOut(*self.mobjects) — default behavior. "
        "Define fit(m) at top of construct() and call it on every mobject. "
        "font_size <= 34 titles, <= 30 equations, <= 28 body. buff >= 0.35 between elements. "
        "Keep all objects within frame bounds using fit().\n\n"
        f"Manim documentation context:\n{manim_docs_context}\n\n"
        f"Scene contract JSON:\n{json.dumps(scene_contract, indent=2)}\n\n"
        f"Storyboard JSON:\n{json.dumps(storyboard, indent=2)}\n\n"
        f"Timing alignment JSON (seconds):\n{json.dumps(timing_alignment, indent=2)}\n\n"
        f"Script JSON:\n{json.dumps(script_json, indent=2)}\n\n"
        f"Validation errors to fix:\n{json.dumps(validation_errors, indent=2)}\n\n"
        f"Current code:\n{current_code}\n\n"
        f"Error log:\n{error_log}"
    )


def manim_repair_prompt_mcp(
    scene_class_name: str,
    script_json: dict,
    timing_alignment: list[dict],
    storyboard: dict,
    current_code: str,
    error_log: str,
) -> str:
    return (
        "Repair this Manim code so it executes successfully in manim-mcp-server. "
        f"Return ONLY corrected Python code for class {scene_class_name}. "
        "Use your own best Manim choices for visuals and pacing. "
        "Do NOT use mobject clipping APIs such as clip_path or set_clip_path; they are unavailable in this runtime. "
        "For Sector, use keyword radius (not outer_radius). "
        "CLEAR screen between scenes with FadeOut(*self.mobjects). "
        "Define fit(m) helper; call fit() on every Text/mobject. font_size <= 34.\n\n"
        f"Storyboard JSON:\n{json.dumps(storyboard, indent=2)}\n\n"
        f"Timing alignment JSON (seconds):\n{json.dumps(timing_alignment, indent=2)}\n\n"
        f"Script JSON:\n{json.dumps(script_json, indent=2)}\n\n"
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
