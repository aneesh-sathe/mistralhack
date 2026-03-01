"""Tests for prompt generation functions."""

from app.services.llm.prompts import (
    EXAMPLES,
    _inject_timing_guidance,
    manim_code_prompt,
    manim_code_prompt_mcp,
)


def test_examples_constant_exists():
    """Test that EXAMPLES constant is defined and contains expected content."""
    assert EXAMPLES is not None
    assert "EXAMPLE 1" in EXAMPLES
    assert "EXAMPLE 2" in EXAMPLES
    assert "EXAMPLE 3" in EXAMPLES
    assert "EXAMPLE 4" in EXAMPLES


def test_examples_contains_critical_patterns():
    """Test that EXAMPLES includes critical Manim patterns."""
    assert "AddTextLetterByLetter" in EXAMPLES
    assert "config.frame_width" in EXAMPLES
    assert "buff" in EXAMPLES
    assert "scale_to_fit_width" in EXAMPLES


def test_examples_contains_critical_rules():
    """Test that EXAMPLES includes the CRITICAL RULES section."""
    assert "CRITICAL RULES" in EXAMPLES
    assert "DO use AddTextLetterByLetter" in EXAMPLES
    assert "DO check frame bounds" in EXAMPLES
    assert "DO use buff >= 0.3" in EXAMPLES
    assert "DON'T use Write()" in EXAMPLES


def test_timing_guidance_injected():
    """Test that timing guidance is properly injected into prompts."""
    scene_contract = [
        {
            "scene_id": 1,
            "target_duration_seconds": 5.0,
            "on_screen_text": "First line\nSecond line",
            "math_expressions": ["2 + 2 = 4", "3 + 3 = 6"],
        }
    ]

    base_prompt = "Test prompt"
    result = _inject_timing_guidance(base_prompt, scene_contract)

    assert "TIMING GUIDANCE" in result
    assert "Scene 1" in result
    assert "target: 5.0s" in result
    assert "Title reveal" in result
    assert "Text lines" in result
    assert "Math expressions" in result
    assert "Recommended wait" in result


def test_timing_guidance_multiple_scenes():
    """Test timing guidance with multiple scenes."""
    scene_contract = [
        {
            "scene_id": 1,
            "target_duration_seconds": 4.0,
            "on_screen_text": "Line 1",
            "math_expressions": ["x = 5"],
        },
        {
            "scene_id": 2,
            "target_duration_seconds": 6.0,
            "on_screen_text": "Line 1\nLine 2\nLine 3",
            "math_expressions": [],
        },
    ]

    base_prompt = "Test prompt"
    result = _inject_timing_guidance(base_prompt, scene_contract)

    assert "Scene 1 (target: 4.0s)" in result
    assert "Scene 2 (target: 6.0s)" in result


def test_manim_code_prompt_includes_examples():
    """Test that manim_code_prompt includes EXAMPLES section."""
    script_json = {
        "module_title": "Test Module",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Introduction",
                "narration_text": "Welcome",
                "on_screen_text": "Welcome",
                "math_expressions": ["1 + 1 = 2"],
            }
        ],
    }
    timing_alignment = [{"scene_id": 1, "duration_seconds": 5.0}]
    scene_contract = [
        {
            "scene_id": 1,
            "title": "Introduction",
            "target_duration_seconds": 5.0,
            "on_screen_text": "Welcome",
            "math_expressions": ["1 + 1 = 2"],
        }
    ]

    prompt = manim_code_prompt(
        scene_class_name="TestScene",
        script_json=script_json,
        manim_docs_context="Test docs",
        timing_alignment=timing_alignment,
        scene_contract=scene_contract,
        storyboard={"scenes": []},
    )

    assert "EXAMPLE 1" in prompt
    assert "EXAMPLE 2" in prompt
    assert "CRITICAL RULES" in prompt
    assert "TIMING GUIDANCE" in prompt


def test_manim_code_prompt_mcp_includes_examples():
    """Test that manim_code_prompt_mcp includes EXAMPLES section."""
    script_json = {
        "module_title": "Test Module",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Introduction",
                "narration_text": "Welcome",
                "on_screen_text": "Welcome",
                "math_expressions": ["1 + 1 = 2"],
            }
        ],
    }
    timing_alignment = [{"scene_id": 1, "duration_seconds": 5.0}]

    prompt = manim_code_prompt_mcp(
        scene_class_name="TestScene",
        script_json=script_json,
        timing_alignment=timing_alignment,
        storyboard={"scenes": []},
    )

    assert "EXAMPLE 1" in prompt
    assert "EXAMPLE 2" in prompt
    assert "CRITICAL RULES" in prompt
    assert "TIMING GUIDANCE" in prompt


def test_timing_guidance_empty_scene_contract():
    """Test timing guidance with empty scene contract."""
    base_prompt = "Test prompt"
    result = _inject_timing_guidance(base_prompt, [])

    assert "TIMING GUIDANCE" in result
    # Should just have the header, no scenes


def test_timing_guidance_scene_with_no_duration():
    """Test timing guidance with scene missing target_duration_seconds."""
    scene_contract = [
        {
            "scene_id": 1,
            # Missing target_duration_seconds
            "on_screen_text": "Test",
            "math_expressions": [],
        }
    ]

    base_prompt = "Test prompt"
    result = _inject_timing_guidance(base_prompt, scene_contract)

    assert "TIMING GUIDANCE" in result
    assert "Scene 1 (target: 0.0s)" in result
