from __future__ import annotations

from app.services.llm.openai_provider import OpenAICompatibleProvider


def test_extract_json_recovers_unescaped_newline_in_string():
    raw = (
        '{\n'
        '  "module_title": "Integers",\n'
        '  "summary": "Line 1\n'
        "Line 2\"\n"
        "}"
    )
    parsed = OpenAICompatibleProvider._extract_json(raw)
    assert parsed["module_title"] == "Integers"
    assert "Line 1" in parsed["summary"]
    assert "Line 2" in parsed["summary"]


def test_extract_json_recovers_json_from_wrapped_text():
    raw = "Here is the JSON:\n```json\n{\"ok\": true, \"items\": [1, 2, 3]}\n```\nDone."
    parsed = OpenAICompatibleProvider._extract_json(raw)
    assert parsed["ok"] is True
    assert parsed["items"] == [1, 2, 3]
