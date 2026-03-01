from __future__ import annotations

import os
import json
import re
import shlex
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


class GoogleConfig(BaseModel):
    client_id: str = Field(alias="CLIENT_ID")
    client_secret: str = Field(alias="CLIENT_SECRET")
    redirect_uri: str = Field(alias="REDIRECT_URI")
    scopes: list[str] = Field(alias="SCOPES")


class AuthConfig(BaseModel):
    jwt_secret: str = Field(alias="JWT_SECRET")
    google: GoogleConfig = Field(alias="GOOGLE")


class AppConfig(BaseModel):
    name: str = Field(alias="NAME")
    env: str = Field(alias="ENV")
    base_url: str = Field(alias="BASE_URL")
    frontend_url: str = Field(alias="FRONTEND_URL")
    storage_dir: str = Field(alias="STORAGE_DIR")
    dev_auth_bypass: bool = Field(default=False, alias="DEV_AUTH_BYPASS")

    @field_validator("dev_auth_bypass", mode="before")
    @classmethod
    def _coerce_dev_bypass(cls, value: Any) -> bool:
        if value in ("", None):
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)


class ProviderConfig(BaseModel):
    provider: str = Field(alias="PROVIDER")
    base_url: str = Field(default="", alias="BASE_URL")
    api_key: str = Field(default="", alias="API_KEY")
    model: str = Field(alias="MODEL")
    temperature: float = Field(default=0.2, alias="TEMPERATURE")
    max_tokens: int = Field(default=1500, alias="MAX_TOKENS")


class VLMConfig(ProviderConfig):
    enabled: bool = Field(default=False, alias="ENABLED")

    @field_validator("enabled", mode="before")
    @classmethod
    def _coerce_enabled(cls, value: Any) -> bool:
        if value in ("", None):
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)


class TTSConfig(BaseModel):
    provider: str = Field(alias="PROVIDER")
    api_key: str = Field(default="", alias="API_KEY")
    voice_id: str = Field(default="", alias="VOICE_ID")
    model_id: str = Field(default="", alias="MODEL_ID")
    output_format: str = Field(default="mp3", alias="OUTPUT_FORMAT")


class CaptionsConfig(BaseModel):
    method: str = Field(alias="METHOD")
    whisper_model: str = Field(default="small", alias="WHISPER_MODEL")


class ManimConfig(BaseModel):
    model: str = Field(alias="MODEL")
    quality: str = Field(default="medium", alias="QUALITY")
    scene_class_name: str = Field(default="LessonScene", alias="SCENE_CLASS_NAME")
    max_tokens: int = Field(default=6000, alias="MAX_TOKENS")
    render_backend: str = Field(default="local", alias="RENDER_BACKEND")
    mcp_command: str = Field(default="", alias="MCP_COMMAND")
    mcp_args: list[str] = Field(default_factory=list, alias="MCP_ARGS")
    mcp_media_dir: str = Field(default="", alias="MCP_MEDIA_DIR")
    mcp_timeout_seconds: int = Field(default=240, alias="MCP_TIMEOUT_SECONDS")

    @field_validator("render_backend", mode="before")
    @classmethod
    def _coerce_render_backend(cls, value: Any) -> str:
        if value in ("", None):
            return "local"
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"local", "mcp"}:
                return normalized
        raise ValueError("MANIM.RENDER_BACKEND must be 'local' or 'mcp'")

    @field_validator("mcp_args", mode="before")
    @classmethod
    def _coerce_mcp_args(cls, value: Any) -> list[str]:
        if value in ("", None):
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("[") and raw.endswith("]"):
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            return shlex.split(raw)
        return [str(value)]

    @field_validator("mcp_timeout_seconds", mode="before")
    @classmethod
    def _coerce_mcp_timeout(cls, value: Any) -> int:
        if value in ("", None):
            return 240
        return int(value)


class DatabaseConfig(BaseModel):
    url: str = Field(alias="URL")


class RedisConfig(BaseModel):
    url: str = Field(alias="URL")


class RootConfig(BaseModel):
    app: AppConfig = Field(alias="APP")
    auth: AuthConfig = Field(alias="AUTH")
    llm: ProviderConfig = Field(alias="LLM")
    chat: ProviderConfig = Field(alias="CHAT")
    vlm: VLMConfig = Field(alias="VLM")
    tts: TTSConfig = Field(alias="TTS")
    captions: CaptionsConfig = Field(alias="CAPTIONS")
    manim: ManimConfig = Field(alias="MANIM")
    database: DatabaseConfig = Field(alias="DATABASE")
    redis: RedisConfig = Field(alias="REDIS")


def _resolve_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(item) for item in value]
    if isinstance(value, str):
        def _replace(match: re.Match[str]) -> str:
            env_name = match.group(1)
            return os.environ.get(env_name, "")

        return _ENV_PATTERN.sub(_replace, value)
    return value


@lru_cache(maxsize=1)
def get_app_config() -> RootConfig:
    config_path = Path(__file__).with_name("config.yaml")
    raw = yaml.safe_load(config_path.read_text())
    resolved = _resolve_env(raw)
    return RootConfig.model_validate(resolved)


def clear_config_cache() -> None:
    get_app_config.cache_clear()  # type: ignore[attr-defined]
