from __future__ import annotations

from functools import lru_cache

# Compact Manim CE reference context injected into LLM prompts.
# This keeps generation grounded in valid APIs without hardcoding the animation itself.
_MANIM_CE_CONTEXT = """
Manim Community Edition quick reference:
- Base structure:
  from manim import *
  class LessonScene(Scene):
      def construct(self):
          ...
- Core mobjects:
  Text(str, font_size=...), MarkupText(str), MathTex(...), VGroup(...), NumberPlane(), Axes(...), Line(...), Dot(...), Rectangle(...), Circle(...), Square(...)
- Layout helpers:
  mobject.next_to(other, DOWN), mobject.to_edge(UP), mobject.shift(RIGHT*...), mobject.scale(...), VGroup(...).arrange(DOWN, buff=...)
- Animations with self.play:
  FadeIn(m), FadeOut(m), Write(m), Create(m), Transform(a, b), ReplacementTransform(a, b), Indicate(m), Circumscribe(m)
- Timing:
  self.play(..., run_time=1.0)
  self.wait(1.5)
- Transitions:
  Use FadeOut/ReplacementTransform between scenes and keep scene flow sequential.
  A safe pattern is:
    scene_group = VGroup(...)
    self.play(FadeIn(scene_group), run_time=...)
    self.wait(...)
    self.play(FadeOut(scene_group), run_time=...)
- Robustness rules:
  Avoid unsupported imports and external assets.
  Avoid relying on system-specific fonts.
  Prefer Text/MathTex and geometric primitives.
  Ensure each scene's total play/wait duration approximately matches audio timing for that scene.
  Ensure class is exactly named as requested and inherits Scene.
""".strip()


@lru_cache(maxsize=1)
def get_manim_docs_context() -> str:
    return _MANIM_CE_CONTEXT
