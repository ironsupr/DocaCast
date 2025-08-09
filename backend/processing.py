from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import re

import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer


# Lazy-loaded global embedder to avoid re-downloading/re-initializing on each call
_EMBEDDER: Optional[SentenceTransformer] = None


def _get_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer(model_name)
    return _EMBEDDER


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs using blank lines as separators."""
    # Normalize line breaks and split on blank lines
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    return paragraphs


def _chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
    """Chunk text into ~max_chars with a small overlap, trying to split at natural boundaries.

    - Cleans whitespace
    - Attempts to find a split point near the end of each chunk on punctuation/space
    """
    s = re.sub(r"\s+", " ", text).strip()
    if not s:
        return []

    chunks: List[str] = []
    n = len(s)
    start = 0
    while start < n:
        end = min(start + max_chars, n)
        if end < n:
            window = s[start:end]
            # Prefer split on sentence boundary, then space/comma
            candidates = [window.rfind(". "), window.rfind("? "), window.rfind("! "), window.rfind(", "), window.rfind(" ")]
            cut = max(candidates)
            if cut != -1 and cut > int(0.5 * max_chars):
                end = start + cut + 1  # include the split character
        chunk = s[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        # Overlap for context continuity
        start = max(0, end - overlap)
    return chunks


def process_pdf(file_path: str, max_chars: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
    """Process a PDF into chunk embeddings.

    Args:
        file_path: Path to a PDF file.
        max_chars: Target max characters per chunk.
        overlap: Character overlap between adjacent chunks.

    Returns:
        A list of dicts: { "text_chunk": str, "embedding": List[float], "page_number": int }
        page_number is 1-based.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    doc = fitz.open(path)
    try:
        # Collect chunks and metadata first, then embed in batch for speed
        texts: List[str] = []
        meta: List[Dict[str, Any]] = []

        for page_index in range(len(doc)):
            page = doc[page_index]
            text = page.get_text("text") or ""
            if not text.strip():
                continue

            for para in _split_paragraphs(text):
                for chunk in _chunk_text(para, max_chars=max_chars, overlap=overlap):
                    texts.append(chunk)
                    meta.append({"page_number": page_index + 1})  # 1-based

        if not texts:
            return []

        model = _get_embedder()
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

        results: List[Dict[str, Any]] = []
        for chunk, emb, m in zip(texts, embeddings, meta):
            results.append({
                "text_chunk": chunk,
                "embedding": emb.tolist(),
                "page_number": m["page_number"],
            })
        return results
    finally:
        doc.close()
