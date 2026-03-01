from __future__ import annotations

import asyncio
import logging
import py_compile
import shutil
import time
from pathlib import Path
from typing import Any

from app.core.settings import get_settings
from app.services.llm.manim_agent import (
    _rewrite_latex_calls,
    _rewrite_numberline_calls,
    _rewrite_sector_calls,
    _rewrite_unsupported_mobject_calls,
)
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


def _is_missing_latex_runtime(error_text: str) -> bool:
    text = (error_text or "").lower()
    if "no such file or directory: 'latex'" in text:
        return True
    if "filenotfounderror" in text and "latex" in text:
        return True
    if "tex_to_svg_file" in text and "latex" in text:
        return True
    return False


def _rewrite_for_latexless_runtime(code: str) -> str:
    rewritten = _rewrite_latex_calls(code)
    rewritten = _rewrite_numberline_calls(rewritten)
    rewritten = _rewrite_sector_calls(rewritten)
    rewritten = _rewrite_unsupported_mobject_calls(rewritten)
    return rewritten


def _is_unsupported_mobject_method(error_text: str) -> bool:
    text = (error_text or "").lower()
    return "has no attribute 'clip_path'" in text or "has no attribute 'set_clip_path'" in text


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
            # Support both common parameter names used by different MCP server variants.
            # `abhiemj/manim-mcp-server` expects `manim_code`, while some servers use `code`.
            tool_result = None
            call_errors: list[str] = []
            for payload in ({"manim_code": code}, {"code": code}):
                try:
                    tool_result = await asyncio.wait_for(
                        session.call_tool("execute_manim_code", payload),
                        timeout=timeout_seconds,
                    )
                    break
                except Exception as exc:
                    call_errors.append(str(exc))

            if tool_result is None:
                joined = "\n".join(call_errors)
                raise RuntimeError(f"Failed to call MCP tool execute_manim_code:\n{joined}")

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
    code_to_render = _rewrite_for_latexless_runtime(code)
    lesson_path.write_text(code_to_render, encoding="utf-8")
    py_compile.compile(str(lesson_path), doraise=True)

    started_at = time.time()
    success, text = asyncio.run(_call_mcp_execute(code_to_render, manim_cfg.mcp_timeout_seconds))
    if not success and (_is_missing_latex_runtime(text) or _is_unsupported_mobject_method(text)):
        rewritten = _rewrite_for_latexless_runtime(code_to_render)
        if rewritten != code_to_render:
            logger.warning(
                "MCP render failed due to runtime compatibility issue; retrying with compatibility rewrite for module %s.",
                module_id,
            )
            code_to_render = rewritten
            lesson_path.write_text(code_to_render, encoding="utf-8")
            py_compile.compile(str(lesson_path), doraise=True)
            success, text = asyncio.run(_call_mcp_execute(code_to_render, manim_cfg.mcp_timeout_seconds))
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
