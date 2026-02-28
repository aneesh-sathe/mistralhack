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
    def _extract_json(text: str) -> dict:
        candidate = text.strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            return {"data": parsed}
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.S)
            if not match:
                raise
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
            return {"data": parsed}

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
            model=self.llm_model,
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
