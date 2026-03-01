"""Tests for Manim code validation functions."""

import ast

from app.services.llm.manim_agent import (
    _build_fallback_manim_code,
    _validate_frame_safety,
    _validate_math_expressions_present,
    _validate_spacing,
)


def test_validate_frame_safety_present():
    """Test that frame safety validation passes when checks are present."""
    code = """
from manim import *

class TestScene(Scene):
    def construct(self):
        safe_width = config.frame_width - 1.2
        text = Text("Hello")
        if text.width > safe_width:
            text.scale_to_fit_width(safe_width)
        self.play(Write(text))
"""
    errors = _validate_frame_safety(code)
    assert len(errors) == 0


def test_validate_frame_safety_with_scale_to_fit_width():
    """Test frame safety validation with scale_to_fit_width."""
    code = """
text = Text("Hello World")
text.scale_to_fit_width(config.frame_width - 1.2)
"""
    errors = _validate_frame_safety(code)
    assert len(errors) == 0


def test_validate_frame_safety_with_scale_to_fit_height():
    """Test frame safety validation with scale_to_fit_height."""
    code = """
text = Text("Hello World")
text.scale_to_fit_height(config.frame_height - 0.9)
"""
    errors = _validate_frame_safety(code)
    assert len(errors) == 0


def test_validate_frame_safety_missing():
    """Test that frame safety validation fails when checks are missing."""
    code = """
from manim import *

class TestScene(Scene):
    def construct(self):
        title = Text("Hello")
        self.play(Write(title))
"""
    errors = _validate_frame_safety(code)
    assert len(errors) > 0
    assert any("frame safety" in e.lower() for e in errors)


def test_validate_spacing_adequate():
    """Test spacing validation with adequate spacing."""
    code = """
line1 = Text("First")
line2 = Text("Second")
line2.next_to(line1, DOWN, buff=0.35)
"""
    errors = _validate_spacing(code)
    assert len(errors) == 0


def test_validate_spacing_multiple_adequate():
    """Test spacing validation with multiple adequate spacings."""
    code = """
line1 = Text("First")
line2 = Text("Second")
line2.next_to(line1, DOWN, buff=0.35)
line3 = Text("Third")
line3.next_to(line2, DOWN, buff=0.40)
"""
    errors = _validate_spacing(code)
    assert len(errors) == 0


def test_validate_spacing_too_tight():
    """Test spacing validation with spacing that's too tight."""
    code = """
line1 = Text("First")
line2 = Text("Second")
line2.next_to(line1, DOWN, buff=0.1)
"""
    errors = _validate_spacing(code)
    assert len(errors) > 0
    assert any("buff" in e.lower() or "spacing" in e.lower() for e in errors)


def test_validate_spacing_missing():
    """Test spacing validation when no buff parameters are found."""
    code = """
from manim import *

class TestScene(Scene):
    def construct(self):
        title = Text("Hello")
        self.play(Write(title))
"""
    errors = _validate_spacing(code)
    assert len(errors) > 0
    assert any("spacing" in e.lower() or "buff" in e.lower() for e in errors)


def test_validate_math_expressions_all_present():
    """Test math expression validation when all expressions are present."""
    code = """
from manim import *

class TestScene(Scene):
    def construct(self):
        expr1 = Text("5 plus 3 equals 8")
        expr2 = Text("8 minus 2 equals 6")
        self.play(Write(expr1))
        self.play(Write(expr2))
"""
    scene_contract = [
        {
            "scene_id": 1,
            "math_expressions": ["5 + 3 = 8", "8 - 2 = 6"],
        }
    ]
    errors = _validate_math_expressions_present(code, scene_contract)
    assert len(errors) == 0


def test_validate_math_expressions_missing():
    """Test math expression validation when expressions are missing."""
    code = """
from manim import *

class TestScene(Scene):
    def construct(self):
        title = Text("Math Lesson")
        self.play(Write(title))
"""
    scene_contract = [
        {
            "scene_id": 1,
            "math_expressions": ["5 + 3 = 8", "10 - 2 = 8"],
        }
    ]
    errors = _validate_math_expressions_present(code, scene_contract)
    assert len(errors) > 0
    assert any("math expression" in e.lower() for e in errors)


def test_validate_math_expressions_partial():
    """Test math expression validation when some expressions are missing."""
    code = """
from manim import *

class TestScene(Scene):
    def construct(self):
        expr1 = Text("5 plus 3 equals 8")
        self.play(Write(expr1))
"""
    scene_contract = [
        {
            "scene_id": 1,
            "math_expressions": ["5 + 3 = 8", "10 - 2 = 8"],
        }
    ]
    errors = _validate_math_expressions_present(code, scene_contract)
    assert len(errors) > 0
    # Should have error for the missing "10 - 2 = 8"
    assert any("10" in e and "2" in e for e in errors)


def test_validate_math_expressions_empty_contract():
    """Test math expression validation with empty scene contract."""
    code = """
from manim import *

class TestScene(Scene):
    def construct(self):
        title = Text("Hello")
        self.play(Write(title))
"""
    scene_contract = []
    errors = _validate_math_expressions_present(code, scene_contract)
    assert len(errors) == 0


def test_validate_math_expressions_no_expressions_in_scene():
    """Test math expression validation when scene has no expressions."""
    code = """
from manim import *

class TestScene(Scene):
    def construct(self):
        title = Text("Hello")
        self.play(Write(title))
"""
    scene_contract = [
        {
            "scene_id": 1,
            "math_expressions": [],  # No expressions required
        }
    ]
    errors = _validate_math_expressions_present(code, scene_contract)
    assert len(errors) == 0


def test_fallback_includes_math_expressions():
    """Test that fallback code includes math expressions."""
    scene_contract = [
        {
            "scene_id": 1,
            "title": "Addition",
            "narration_text": "Let's learn addition",
            "on_screen_text": "Addition basics",
            "math_expressions": ["2 + 2 = 4", "3 + 5 = 8"],
            "target_duration_seconds": 5.0,
        }
    ]
    code = _build_fallback_manim_code("LessonScene", scene_contract)

    # Check that math expressions are in the code
    assert "2 + 2 = 4" in code or "2plus2equals4" in code.replace(" ", "").lower()
    assert "3 + 5 = 8" in code or "3plus5equals8" in code.replace(" ", "").lower()


def test_fallback_uses_yellow_for_expressions():
    """Test that fallback code uses yellow color for math expressions."""
    scene_contract = [
        {
            "scene_id": 1,
            "title": "Math",
            "narration_text": "Math lesson",
            "on_screen_text": "Learn math",
            "math_expressions": ["x = 10"],
            "target_duration_seconds": 4.0,
        }
    ]
    code = _build_fallback_manim_code("LessonScene", scene_contract)

    # Check that expressions use yellow color
    assert "color=YELLOW" in code


def test_fallback_uses_addtextletterbyLetter():
    """Test that fallback code uses AddTextLetterByLetter."""
    scene_contract = [
        {
            "scene_id": 1,
            "title": "Test",
            "narration_text": "Test",
            "on_screen_text": "Test",
            "math_expressions": ["1 + 1 = 2"],
            "target_duration_seconds": 5.0,
        }
    ]
    code = _build_fallback_manim_code("LessonScene", scene_contract)

    assert "AddTextLetterByLetter" in code


def test_fallback_is_valid_python():
    """Test that fallback code is valid Python."""
    scene_contract = [
        {
            "scene_id": 1,
            "title": "Test Scene",
            "narration_text": "This is a test",
            "on_screen_text": "Test content",
            "math_expressions": ["a + b = c"],
            "target_duration_seconds": 5.0,
        }
    ]
    code = _build_fallback_manim_code("TestScene", scene_contract)

    # Should be valid Python
    try:
        ast.parse(code)
    except SyntaxError as e:
        raise AssertionError(f"Generated fallback code has invalid syntax: {e}")


def test_fallback_multiple_scenes():
    """Test fallback code with multiple scenes."""
    scene_contract = [
        {
            "scene_id": 1,
            "title": "Scene 1",
            "narration_text": "First scene",
            "on_screen_text": "Content 1",
            "math_expressions": ["1 + 1 = 2"],
            "target_duration_seconds": 4.0,
        },
        {
            "scene_id": 2,
            "title": "Scene 2",
            "narration_text": "Second scene",
            "on_screen_text": "Content 2",
            "math_expressions": ["2 + 2 = 4"],
            "target_duration_seconds": 4.0,
        },
    ]
    code = _build_fallback_manim_code("MultiScene", scene_contract)

    # Check both scenes are included
    assert "Scene 1" in code
    assert "Scene 2" in code
    assert "1 + 1 = 2" in code or "1plus1equals2" in code.replace(" ", "").lower()
    assert "2 + 2 = 4" in code or "2plus2equals4" in code.replace(" ", "").lower()

    # Should be valid Python
    ast.parse(code)
