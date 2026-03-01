from __future__ import annotations

from app.services.llm.manim_agent import generate_manim_code, repair_manim_code


class _FakeLLM:
    def __init__(self, code: str) -> None:
        self._code = code

    def generate_code(self, prompt: str) -> str:
        return self._code


def _script_json() -> dict:
    return {
        "module_title": "Integers",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Example",
                "narration_text": "Ten minus negative five equals fifteen.",
                "on_screen_text": "10 - (-5) = 15",
                "math_expressions": ["10 - (-5) = 15"],
                "visual_instructions": "Show the equation.",
            }
        ],
        "full_narration_text": "Ten minus negative five equals fifteen.",
    }


def _timing() -> list[dict]:
    return [
        {
            "scene_id": 1,
            "title": "Example",
            "start_seconds": 0.0,
            "end_seconds": 2.0,
            "duration_seconds": 2.0,
        }
    ]


def test_generate_manim_code_rewrites_mathtex_to_text():
    llm = _FakeLLM(
        "from manim import *\n"
        "class LessonScene(Scene):\n"
        "    def construct(self):\n"
        "        active_group = VGroup()\n"
        "        # SCENE_START:1\n"
        "        scene_1_group = VGroup()\n"
        "        title = Text('Example')\n"
        "        number_line = NumberLine(x_range=[-6, 12, 1], length=8, include_numbers=True)\n"
        "        eq = MathTex('10 - (-5) = 15', font_size=36)\n"
        "        scene_1_group.add(title, number_line, eq)\n"
        "        self.play(FadeIn(scene_1_group), run_time=1.0)\n"
        "        self.play(Indicate(eq), run_time=0.4)\n"
        "        self.wait(0.5)\n"
        "        active_group = scene_1_group\n"
        "        # SCENE_END:1\n"
        "        self.play(FadeOut(active_group), run_time=0.5)\n"
    )

    code = generate_manim_code(_script_json(), _timing(), "LessonScene", llm)
    assert "MathTex(" not in code
    assert "Tex(" not in code
    assert "Text(" in code
    assert "include_numbers=True" not in code
    assert "add_numbers(" not in code


def test_repair_manim_code_rewrites_tex_to_text():
    llm = _FakeLLM(
        "from manim import *\n"
        "class LessonScene(Scene):\n"
        "    def construct(self):\n"
        "        active_group = VGroup()\n"
        "        # SCENE_START:1\n"
        "        scene_1_group = VGroup()\n"
        "        title = Text('Example')\n"
        "        axis = Axes(x_range=[0, 6, 1], y_range=[0, 6, 1], x_length=5, y_length=3)\n"
        "        label = Tex('10 - (-5) = 15')\n"
        "        scene_1_group.add(title, axis, label)\n"
        "        self.play(FadeIn(scene_1_group), run_time=1.0)\n"
        "        self.play(Circumscribe(label), run_time=0.4)\n"
        "        self.wait(0.5)\n"
        "        active_group = scene_1_group\n"
        "        # SCENE_END:1\n"
        "        self.play(FadeOut(active_group), run_time=0.5)\n"
    )

    code = repair_manim_code(
        _script_json(),
        _timing(),
        current_code="",
        error_log="FileNotFoundError: latex",
        scene_class_name="LessonScene",
        llm_provider=llm,
    )
    assert "MathTex(" not in code
    assert "Tex(" not in code
    assert "Text(" in code
