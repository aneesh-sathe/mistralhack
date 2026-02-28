from __future__ import annotations

import asyncio
import logging
import py_compile
import shutil
import time
from pathlib import Path
from typing import Any

from app.core.settings import get_settings
from app.services.storage import LocalStorage

logger = logging.getLogger(__name__)


def _extract_mcp_text(result: Any) -> str:
    if result is None:
        return ""

    content = getattr(result, "content", None)
    if content is not None:
        chunks: list[str] = []
        for item in content:
            text = getattr(item, "text", None)
            if text is not None:
                chunks.append(str(text))
                continue
            if isinstance(item, dict) and "text" in item:
                chunks.append(str(item["text"]))
                continue
            chunks.append(str(item))
        return "\n".join(chunks).strip()

    if isinstance(result, dict):
        if "content" in result and isinstance(result["content"], list):
            chunks = []
            for item in result["content"]:
                if isinstance(item, dict):
                    chunks.append(str(item.get("text", item)))
                else:
                    chunks.append(str(item))
            return "\n".join(chunks).strip()
        return str(result)

    return str(result)


def _find_latest_mp4(media_dir: Path, started_after: float) -> Path | None:
    if not media_dir.exists():
        return None

    candidates = [
        path
        for path in media_dir.rglob("*.mp4")
        if path.is_file() and path.stat().st_size > 1024 and path.stat().st_mtime >= started_after
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0]


async def _call_mcp_execute(code: str, timeout_seconds: int) -> tuple[bool, str]:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except Exception as exc:
        raise RuntimeError("The 'mcp' Python package is required for MANIM_RENDER_BACKEND=mcp") from exc

    settings = get_settings()
    manim_cfg = settings.config.manim

    command = manim_cfg.mcp_command.strip() if manim_cfg.mcp_command else ""
    if not command:
        raise RuntimeError("MANIM_MCP_COMMAND is required when MANIM_RENDER_BACKEND=mcp")

    args = list(manim_cfg.mcp_args)
    server = StdioServerParameters(command=command, args=args)

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tool_result = await asyncio.wait_for(
                session.call_tool("execute_manim_code", {"code": code}),
                timeout=timeout_seconds,
            )

            text = _extract_mcp_text(tool_result)
            is_error = bool(getattr(tool_result, "isError", False))
            if not is_error and isinstance(tool_result, dict):
                is_error = bool(tool_result.get("isError"))

            if "execution failed" in text.lower():
                is_error = True
            return (not is_error), text


def render_module_video_via_mcp(
    *,
    module_id: str,
    code: str,
    scene_class_name: str,
    quality: str,
    storage: LocalStorage,
) -> tuple[Path, Path]:
    del scene_class_name
    del quality

    settings = get_settings()
    manim_cfg = settings.config.manim

    if not manim_cfg.mcp_media_dir:
        raise RuntimeError("MANIM_MCP_MEDIA_DIR must be configured when MANIM_RENDER_BACKEND=mcp")

    workdir = storage.manim_workdir(module_id)
    lesson_path = workdir / "lesson.py"
    lesson_path.write_text(code, encoding="utf-8")
    py_compile.compile(str(lesson_path), doraise=True)

    started_at = time.time()
    success, text = asyncio.run(_call_mcp_execute(code, manim_cfg.mcp_timeout_seconds))
    if not success:
        raise RuntimeError(f"manim-mcp-server execution failed:\n{text}")

    source = _find_latest_mp4(Path(manim_cfg.mcp_media_dir), started_after=started_at - 2.0)
    if source is None:
        raise RuntimeError(
            "manim-mcp-server did not produce a discoverable MP4 in MANIM_MCP_MEDIA_DIR. "
            "Verify MANIM_MCP_MEDIA_DIR points to the server's media output directory."
        )

    dest = storage.video_path(module_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    logger.info("MCP render succeeded for module %s: %s", module_id, source)
    return dest, lesson_path
