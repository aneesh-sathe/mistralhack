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
  Text(str, font_size=...), MarkupText(str), VGroup(...), NumberPlane(), Axes(...), Line(...), Dot(...), Rectangle(...), Circle(...), Square(...)
- Layout helpers:
  mobject.next_to(other, DOWN), mobject.to_edge(UP), mobject.shift(RIGHT*...), mobject.scale(...), VGroup(...).arrange(DOWN, buff=...)
  Keep generous spacing between lines/elements to avoid overlap; prefer buff ~0.25 to 0.45.
- Animations with self.play:
  FadeIn(m), FadeOut(m), Write(m), Create(m), Transform(a, b), ReplacementTransform(a, b), Indicate(m), Circumscribe(m), AddTextLetterByLetter(text_mobject)
- Timing:
  self.play(..., run_time=1.0)
  self.wait(1.5)
- Transitions:
  Keep scene flow sequential and coherent.
  If a scene references earlier context, keep prior mobjects and place new content below existing content.
  If scene is independent, you can FadeOut prior content first.
  A safe pattern is:
    stack_group = VGroup()
    scene_group = VGroup(...)
    if independent_scene:
      self.play(FadeOut(stack_group), run_time=...)
      stack_group = VGroup()
    title.next_to(stack_group, DOWN)  # when carrying context
    self.play(AddTextLetterByLetter(title), run_time=...)
    stack_group.add(scene_group)
- Robustness rules:
  Avoid unsupported imports and external assets.
  Avoid relying on system-specific fonts.
  Prefer Text/MarkupText and geometric primitives.
  Do not use MathTex/Tex/SingleStringMathTex (LaTeX compiler is unavailable in runtime).
  Ensure each scene's total play/wait duration approximately matches audio timing for that scene.
  Ensure class is exactly named as requested and inherits Scene.
""".strip()


@lru_cache(maxsize=1)
def get_manim_docs_context() -> str:
    return _MANIM_CE_CONTEXT
