from __future__ import annotations

import io
import logging
from pathlib import Path

import fitz
import pdfplumber
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


def extract_text_per_page(pdf_path: Path) -> list[str]:
    page_text: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            page_text.append((page.extract_text() or "").strip())
    return page_text


def text_density(text_pages: list[str]) -> float:
    if not text_pages:
        return 0.0
    all_text = "\n".join(text_pages)
    non_ws = sum(1 for ch in all_text if not ch.isspace())
    alpha = sum(1 for ch in all_text if ch.isalnum())
    if non_ws == 0:
        return 0.0
    return alpha / non_ws


def is_low_quality_text(text_pages: list[str]) -> bool:
    all_text = "\n".join(text_pages)
    dense = text_density(text_pages)
    return len(all_text) < 300 or dense < 0.45


def ocr_pdf_with_tesseract(pdf_path: Path) -> list[str]:
    doc = fitz.open(str(pdf_path))
    results: list[str] = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(image, lang="eng")
        results.append(text.strip())
    return results


def render_pages_for_vlm(pdf_path: Path, max_pages: int = 8) -> list[bytes]:
    doc = fitz.open(str(pdf_path))
    images: list[bytes] = []
    for idx, page in enumerate(doc):
        if idx >= max_pages:
            break
        pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
        images.append(pix.tobytes("png"))
    return images
