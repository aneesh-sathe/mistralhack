from __future__ import annotations

from app.services.llm.manim_agent import _rewrite_sector_calls, _rewrite_unsupported_mobject_calls


def test_rewrite_unsupported_clip_path_calls():
    code = (
        "from manim import *\n"
        "class LessonScene(Scene):\n"
        "    def construct(self):\n"
        "        apple_parts = VGroup(*[apple.copy().clip_path(line) for line in lines])\n"
        "        self.add(apple_parts)\n"
    )

    rewritten = _rewrite_unsupported_mobject_calls(code)
    assert ".clip_path(" not in rewritten
    assert "apple.copy()" in rewritten


def test_rewrite_sector_outer_radius_kwarg():
    code = (
        "from manim import *\n"
        "class LessonScene(Scene):\n"
        "    def construct(self):\n"
        "        part = Sector(outer_radius=1.5, angle=TAU / 5)\n"
        "        self.add(part)\n"
    )

    rewritten = _rewrite_sector_calls(code)
    assert "outer_radius=" not in rewritten
    assert "Sector(radius=1.5" in rewritten
