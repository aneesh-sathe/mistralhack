from __future__ import annotations

import logging
from typing import Any

from app.services.llm.base import LLMProvider
from app.services.llm.prompts import module_extraction_prompt

logger = logging.getLogger(__name__)


def extract_modules_from_chunks(chunks: list[dict[str, Any]], llm_provider: LLMProvider) -> list[dict[str, Any]]:
    chunk_payload = []
    for chunk in chunks:
        chunk_payload.append(
            {
                "chunk_id": str(chunk["id"]),
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "text": chunk["text"][:1400],
            }
        )

    prompt = module_extraction_prompt(chunk_payload)
    try:
        data = llm_provider.generate_json(prompt)
    except Exception as exc:
        logger.warning("Module extraction via LLM failed, using fallback: %s", exc)
        data = {"modules": []}

    modules_raw = data.get("modules") if isinstance(data, dict) else data
    if not isinstance(modules_raw, list):
        modules_raw = []

    modules: list[dict[str, Any]] = []
    for i, item in enumerate(modules_raw, start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", f"Module {i}")).strip() or f"Module {i}"
        summary = str(item.get("summary", "")).strip() or "Core concept from the document."
        prerequisites = item.get("prerequisites") if isinstance(item.get("prerequisites"), list) else []
        chunk_refs = item.get("chunk_refs") if isinstance(item.get("chunk_refs"), list) else []
        modules.append(
            {
                "title": title,
                "summary": summary,
                "prerequisites": prerequisites,
                "chunk_refs": [str(ref) for ref in chunk_refs],
            }
        )

    if not modules:
        all_chunk_ids = [str(chunk["id"]) for chunk in chunks]
        modules = [
            {
                "title": "Overview of Uploaded Chapter",
                "summary": "A concise walkthrough of major ideas in the uploaded material.",
                "prerequisites": [],
                "chunk_refs": all_chunk_ids,
            }
        ]

    return modules
