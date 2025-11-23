from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re
import os
import numpy as np
import hashlib

import fitz  # PyMuPDF

try:
    import google.generativeai as genai
except ImportError:
    genai = None


# Cache for API client
_GENAI_CONFIGURED = False


def _ensure_genai_configured():
    """Ensure Gemini API is configured"""
    global _GENAI_CONFIGURED
    if not _GENAI_CONFIGURED and genai is not None:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            _GENAI_CONFIGURED = True


class SimpleTfidfEmbedder:
    """Ultra-lightweight TF-IDF based embedder (fallback when API unavailable)
    
    This is a simple hash-based embedding that:
    - Requires NO external models or APIs
    - Uses ~0MB memory
    - Fast and deterministic
    - Good enough for basic semantic search
    """
    
    def __init__(self, dim: int = 384):
        self.dim = dim
        
    def _hash_features(self, text: str) -> np.ndarray:
        """Create a simple feature vector using hashing trick"""
        # Tokenize
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Create sparse vector using hashing
        vector = np.zeros(self.dim, dtype=np.float32)
        for token in tokens:
            # Hash token to dimension
            hash_val = int(hashlib.md5(token.encode()).hexdigest(), 16)
            idx = hash_val % self.dim
            vector[idx] += 1.0
            
            # Also add bigrams for better context
            if len(token) > 3:
                for i in range(len(token) - 1):
                    bigram = token[i:i+2]
                    hash_val = int(hashlib.md5(bigram.encode()).hexdigest(), 16)
                    idx = hash_val % self.dim
                    vector[idx] += 0.5
        
        return vector
        
    def encode(self, texts: List[str], convert_to_numpy: bool = True, normalize_embeddings: bool = True, **kwargs) -> np.ndarray:
        """Encode texts into embeddings"""
        if not texts:
            return np.array([])
            
        embeddings = np.array([self._hash_features(text) for text in texts], dtype=np.float32)
        
        if normalize_embeddings:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            embeddings = embeddings / norms
            
        return embeddings


class GeminiEmbedder:
    """Lightweight embedder using Google's Gemini API with fallback"""
    
    def __init__(self, model_name: str = "models/text-embedding-004"):
        self.model_name = model_name
        self.fallback = SimpleTfidfEmbedder(dim=384)
        self.use_fallback = False
        _ensure_genai_configured()
        
    def encode(self, texts: List[str], convert_to_numpy: bool = True, normalize_embeddings: bool = True, batch_size: int = 100) -> np.ndarray:
        """Generate embeddings using Gemini API with automatic fallback
        
        Args:
            texts: List of text strings to embed
            convert_to_numpy: Return as numpy array
            normalize_embeddings: Normalize to unit vectors
            batch_size: Process in batches (Gemini supports up to 100)
        
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        # If we've already determined to use fallback, skip API attempt
        if self.use_fallback:
            return self.fallback.encode(texts, convert_to_numpy, normalize_embeddings)
        
        # Try Gemini API first
        if genai is not None:
            try:
                all_embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    result = genai.embed_content(
                        model=self.model_name,
                        content=batch,
                        task_type="retrieval_document"
                    )
                    
                    # Extract embeddings from response
                    if isinstance(result, dict) and 'embedding' in result:
                        embeddings_batch = result['embedding']
                        if not isinstance(embeddings_batch[0], list):
                            embeddings_batch = [embeddings_batch]
                        all_embeddings.extend(embeddings_batch)
                    else:
                        raise ValueError("Unexpected response format")
                
                embeddings = np.array(all_embeddings, dtype=np.float32)
                
                if normalize_embeddings:
                    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                    norms = np.where(norms == 0, 1, norms)
                    embeddings = embeddings / norms
                
                return embeddings
                
            except Exception as e:
                print(f"[INFO] Gemini embeddings not available ({type(e).__name__}), using lightweight fallback")
                self.use_fallback = True
                return self.fallback.encode(texts, convert_to_numpy, normalize_embeddings)
        
        # Use fallback if genai not available
        return self.fallback.encode(texts, convert_to_numpy, normalize_embeddings)


# Lazy-loaded global embedder
_EMBEDDER: Optional[GeminiEmbedder] = None


def _get_embedder(model_name: str = "models/text-embedding-004") -> GeminiEmbedder:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = GeminiEmbedder(model_name)
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


def _assemble_lines(page: fitz.Page) -> Tuple[List[Dict[str, Any]], float]:
    """Return ordered lines with average font size and the median font size for the page.
    Each line: { text: str, size: float }
    """
    data = page.get_text("dict")
    lines: List[Dict[str, Any]] = []
    sizes: List[float] = []
    for block in data.get("blocks", []) or []:
        for line in block.get("lines", []) or []:
            spans = line.get("spans", []) or []
            t = "".join([s.get("text", "") for s in spans]).strip()
            if not t:
                continue
            szs = [float(s.get("size", 0.0)) for s in spans if s.get("text")]
            avg = (sum(szs) / len(szs)) if szs else 0.0
            lines.append({"text": t, "size": avg})
            if avg > 0:
                sizes.append(avg)
    if sizes:
        sizes_sorted = sorted(sizes)
        mid = len(sizes_sorted) // 2
        median = sizes_sorted[mid] if len(sizes_sorted) % 2 == 1 else (sizes_sorted[mid-1] + sizes_sorted[mid]) / 2.0
    else:
        median = 0.0
    return lines, median


def _looks_like_heading(text: str, size: float, median_size: float) -> bool:
    t = (text or "").strip()
    if len(t) < 4:
        return False
    if t.endswith('.') or t.endswith('!') or t.endswith('?'):
        # headings rarely end with sentence punctuation
        return False
    # Size threshold: noticeably larger than median
    bigger = (median_size > 0 and (size >= median_size + 1.0 or size >= 1.15 * median_size))
    # Pattern hints: numbered headings or many capitalized words
    numbered = bool(re.match(r"^(\d+\.)+(\s|$)|^\d+\s+", t))
    letters = [c for c in t if c.isalpha()]
    uppers = [c for c in letters if c.isupper()]
    cap_ratio = (len(uppers) / len(letters)) if letters else 0.0
    capitalized = cap_ratio >= 0.35
    shortish = len(t) <= 120
    return shortish and (bigger or numbered or capitalized)


def _sections_from_toc(doc: fitz.Document) -> Optional[List[Dict[str, Any]]]:
    """Build sections from PDF TOC (table of contents) if available.
    Returns a list of sections [{title, page, text}] or None if TOC is absent/empty.
    """
    try:
        toc = doc.get_toc(simple=True)  # list of [level, title, page]
    except Exception:
        toc = None
    if not toc:
        return None

    # Normalize entries and ensure page numbers are valid (1-based)
    entries: List[Tuple[int, str, int]] = []
    for e in toc:
        try:
            level = int(e[0])
            title = str(e[1] or "").strip()
            page = int(e[2])
            if title and page >= 1 and page <= len(doc):
                entries.append((level, title, page))
        except Exception:
            continue
    if not entries:
        return None

    # Sort by page number to ensure reading order
    entries.sort(key=lambda x: x[2])

    # Build sections: each entry captures content from its page start up to next entry's page-1 (inclusive)
    sections: List[Dict[str, Any]] = []
    for i, (level, title, start_page) in enumerate(entries):
        end_page = (entries[i + 1][2] - 1) if (i + 1 < len(entries)) else len(doc)
        # Extract text across page range
        buf: List[str] = []
        for p in range(start_page - 1, end_page):  # doc is 0-based
            try:
                txt = doc[p].get_text("text") or ""
            except Exception:
                txt = ""
            if txt.strip():
                buf.append(txt.strip())
        body = "\n".join(buf).strip()
        if body:
            sections.append({
                "title": title,
                "text": body,
                "page": start_page,
            })
    return sections or None


def process_pdf(file_path: str, max_chars: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
    """Process a PDF into section embeddings when possible (heading + following content).

    Falls back to paragraph chunking if headings cannot be detected.

    Args:
        file_path: Path to a PDF file.
        max_chars: Not used for sectioning; used for fallback chunking.
        overlap: Overlap for fallback chunking.

    Returns:
        A list of dicts: { "text_chunk": str, "embedding": List[float], "page_number": int, "section_title"?: str, "section_index"?: int }
        page_number is 1-based (first page where section starts).
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    doc = fitz.open(path)
    try:
        # First pass: try to extract sections using TOC if present; else use heading heuristics
        sections: Optional[List[Dict[str, Any]]] = _sections_from_toc(doc)
        current: Optional[Dict[str, Any]] = None

        if sections is None:
            sections = []
            for page_index in range(len(doc)):
                page = doc[page_index]
                lines, median = _assemble_lines(page)
                if not lines:
                    continue
                for ln in lines:
                    t = (ln.get("text") or "").strip()
                    sz = float(ln.get("size") or 0.0)
                    if _looks_like_heading(t, sz, median):
                        # start a new section
                        current = {
                            "title": t,
                            "text": "",
                            "page": page_index + 1,
                        }
                        sections.append(current)
                    else:
                        if current is None:
                            # implicit intro section if content appears before any heading
                            current = {
                                "title": "Introduction",
                                "text": "",
                                "page": page_index + 1,
                            }
                            sections.append(current)
                        # append content line
                        if current["text"]:
                            current["text"] += "\n"
                        current["text"] += t

        # Prune empty or tiny sections
        sections = [s for s in sections if (s.get("text") or "").strip()]

        if not sections:
            # Fallback: paragraph chunking
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
                        meta.append({"page_number": page_index + 1})
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

        # Embed sections
        texts = [s.get("text", "") for s in sections]
        model = _get_embedder()
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        results: List[Dict[str, Any]] = []
        for idx, (sec, emb) in enumerate(zip(sections, embeddings)):
            results.append({
                "text_chunk": sec.get("text", ""),
                "embedding": emb.tolist(),
                "page_number": int(sec.get("page") or 1),
                "section_title": sec.get("title") or None,
                "section_index": idx,
            })
        return results
    finally:
        doc.close()
