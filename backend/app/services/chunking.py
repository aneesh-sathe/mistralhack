from __future__ import annotations


def chunk_pages(page_text: list[str], max_chars: int = 2200) -> list[dict]:
    chunks: list[dict] = []
    current_pages: list[int] = []
    current_text: list[str] = []
    current_len = 0

    for page_idx, text in enumerate(page_text, start=1):
        clean = text.strip()
        if not clean:
            continue

        if current_len + len(clean) > max_chars and current_text:
            chunks.append(
                {
                    "page_start": min(current_pages),
                    "page_end": max(current_pages),
                    "text": "\n\n".join(current_text),
                    "metadata": {"char_count": current_len},
                }
            )
            current_pages = []
            current_text = []
            current_len = 0

        current_pages.append(page_idx)
        current_text.append(clean)
        current_len += len(clean)

    if current_text:
        chunks.append(
            {
                "page_start": min(current_pages),
                "page_end": max(current_pages),
                "text": "\n\n".join(current_text),
                "metadata": {"char_count": current_len},
            }
        )

    if not chunks:
        chunks.append(
            {
                "page_start": 1,
                "page_end": max(1, len(page_text)),
                "text": "",
                "metadata": {"char_count": 0},
            }
        )

    return chunks
