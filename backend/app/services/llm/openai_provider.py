from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.core.settings import get_settings
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        cfg = settings.config

        self.llm_model = cfg.llm.model
        self.llm_temperature = cfg.llm.temperature
        self.llm_max_tokens = cfg.llm.max_tokens
        self.chat_model = cfg.chat.model
        self.chat_temperature = cfg.chat.temperature
        self.chat_max_tokens = cfg.chat.max_tokens
        self.manim_model = cfg.manim.model
        self.vlm_model = cfg.vlm.model
        self.vlm_temperature = cfg.vlm.temperature
        self.vlm_max_tokens = cfg.vlm.max_tokens
        self.vlm_enabled = bool(cfg.vlm.enabled)

        self.llm_client = OpenAI(
            api_key=cfg.llm.api_key or "",
            base_url=cfg.llm.base_url or None,
        )
        self.vlm_client = OpenAI(
            api_key=cfg.vlm.api_key or cfg.llm.api_key or "",
            base_url=cfg.vlm.base_url or cfg.llm.base_url or None,
        )
        self.chat_client = OpenAI(
            api_key=cfg.chat.api_key or cfg.llm.api_key or "",
            base_url=cfg.chat.base_url or cfg.llm.base_url or None,
        )

    def _chat(
        self,
        *,
        client: OpenAI,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        if isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
        return content or ""

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        candidate = text.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", candidate)
            candidate = re.sub(r"\n?```$", "", candidate)
        return candidate.strip()

    @staticmethod
    def _sanitize_json_text(text: str) -> str:
        out: list[str] = []
        in_string = False
        escaped = False

        for ch in text:
            code = ord(ch)
            if in_string:
                if escaped:
                    out.append(ch)
                    escaped = False
                    continue
                if ch == "\\":
                    out.append(ch)
                    escaped = True
                    continue
                if ch == '"':
                    out.append(ch)
                    in_string = False
                    continue
                if code < 0x20:
                    if ch == "\n":
                        out.append("\\n")
                    elif ch == "\r":
                        out.append("\\r")
                    elif ch == "\t":
                        out.append("\\t")
                    else:
                        out.append(" ")
                    continue
                out.append(ch)
                continue

            if ch == '"':
                in_string = True
                out.append(ch)
                continue
            if code < 0x20 and ch not in {"\n", "\r", "\t"}:
                continue
            out.append(ch)

        return "".join(out)

    @staticmethod
    def _extract_balanced_json_object(text: str) -> str | None:
        start = text.find("{")
        if start < 0:
            return None

        depth = 0
        in_string = False
        escaped = False

        for idx in range(start, len(text)):
            ch = text[idx]
            if in_string:
                if escaped:
                    escaped = False
                    continue
                if ch == "\\":
                    escaped = True
                    continue
                if ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]
        return None

    @staticmethod
    def _extract_json(text: str) -> dict:
        raw = OpenAICompatibleProvider._strip_markdown_fences(text)
        candidates = [raw]
        balanced = OpenAICompatibleProvider._extract_balanced_json_object(raw)
        if balanced:
            candidates.append(balanced)

        last_error: Exception | None = None
        for candidate in candidates:
            for parse_input in (candidate, OpenAICompatibleProvider._sanitize_json_text(candidate)):
                if not parse_input.strip():
                    continue
                try:
                    parsed = json.loads(parse_input)
                    if isinstance(parsed, dict):
                        return parsed
                    return {"data": parsed}
                except json.JSONDecodeError as exc:
                    last_error = exc

        if last_error is not None:
            raise last_error
        raise json.JSONDecodeError("No JSON object could be extracted", text, 0)

    def generate_json(self, prompt: str, max_retries: int = 2) -> dict:
        last_error: Exception | None = None
        for _ in range(max_retries + 1):
            try:
                text = self._chat(
                    client=self.llm_client,
                    model=self.llm_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Return valid JSON only. No markdown fences or prose.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.llm_temperature,
                    max_tokens=self.llm_max_tokens,
                )
                return self._extract_json(text)
            except Exception as exc:
                last_error = exc
                logger.warning("LLM JSON generation retry due to: %s", exc)
        raise RuntimeError(f"LLM JSON generation failed: {last_error}")

    def generate_text(self, prompt: str) -> str:
        return self._chat(
            client=self.llm_client,
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.llm_temperature,
            max_tokens=self.llm_max_tokens,
        ).strip()

    def generate_code(self, prompt: str) -> str:
        text = self._chat(
            client=self.llm_client,
            model=self.manim_model,
            messages=[
                {
                    "role": "system",
                    "content": "Return only Python code. Do not include markdown fences.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=self.llm_max_tokens,
        )
        return text.strip()

    def generate_chat_text(self, messages: list[dict[str, Any]]) -> str:
        return self._chat(
            client=self.chat_client,
            model=self.chat_model,
            messages=messages,
            temperature=self.chat_temperature,
            max_tokens=self.chat_max_tokens,
        ).strip()

    def stream_chat_text(self, messages: list[dict[str, Any]]):
        stream = self.chat_client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            temperature=self.chat_temperature,
            max_tokens=self.chat_max_tokens,
            stream=True,
        )

        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue

            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if isinstance(content, str):
                yield content
                continue

            if isinstance(content, list):
                parts: list[str] = []
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text")
                        if isinstance(text, str):
                            parts.append(text)
                    else:
                        text = getattr(item, "text", None)
                        if isinstance(text, str):
                            parts.append(text)
                if parts:
                    yield "".join(parts)

    def vlm_extract_text(self, images: list[bytes], prompt: str) -> str:
        if not self.vlm_enabled:
            return ""
        if not images:
            return ""

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for img in images:
            b64 = base64.b64encode(img).decode("utf-8")
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})

        try:
            return self._chat(
                client=self.vlm_client,
                model=self.vlm_model,
                messages=[{"role": "user", "content": content}],
                temperature=self.vlm_temperature,
                max_tokens=self.vlm_max_tokens,
            ).strip()
        except Exception as exc:
            logger.warning("VLM OCR call failed; skipping fallback: %s", exc)
            return ""
