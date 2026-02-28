from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate_json(self, prompt: str, max_retries: int = 2) -> dict:
        raise NotImplementedError

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_code(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def vlm_extract_text(self, images: list[bytes], prompt: str) -> str:
        raise NotImplementedError
