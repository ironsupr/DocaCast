from fastapi import FastAPI, UploadFile, File
from typing import List
from pathlib import Path
# Support running as a package (uvicorn backend.main:app) or from within backend/ (uvicorn main:app)
try:  # Prefer absolute imports when launched from repo root
    from backend.processing import process_pdf, _get_embedder  # type: ignore
    from backend.vector_store import VectorStore  # type: ignore
except Exception:  # Fallback to local module imports when cwd is backend/
    from processing import process_pdf, _get_embedder  # type: ignore
    from vector_store import VectorStore  # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Any, Dict, Tuple, Set
import os
import json
import uuid
import fitz  # PyMuPDF
import asyncio
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np  # type: ignore
from fastapi import HTTPException
from dotenv import load_dotenv
try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore
try:
    import pyttsx3  # type: ignore
except ImportError:  # pragma: no cover
    pyttsx3 = None  # type: ignore
try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None  # type: ignore
# Load environment variables from backend/.env reliably regardless of cwd
_ENV_PATH = (Path(__file__).resolve().parent / ".env")
if _ENV_PATH.is_file():
    load_dotenv(dotenv_path=str(_ENV_PATH))
else:
    # Fallback to default lookup (cwd)
    load_dotenv()

app = FastAPI(title="Adobe Hackathon Finale API")

# Global in-memory vector store for this app instance
store = VectorStore()

# ---------------------------------------------------------------------------
# Performance / caching infrastructure
# ---------------------------------------------------------------------------
# Lightweight in-memory caches (non-persistent) to avoid recomputation during a
# single server session. For hackathon/demo scale this is sufficient; for
# production consider an external cache with TTL handling.
_script_cache: Dict[str, str] = {}
_audio_cache: Dict[str, Tuple[str, str]] = {}  # key -> (filename, rel_url)

_pyttsx3_lock = threading.Lock()  # pyttsx3 is not fully thread-safe
_tts_executor = ThreadPoolExecutor(max_workers=int(os.getenv("TTS_WORKERS", "2")))
_bg_executor = ThreadPoolExecutor(max_workers=int(os.getenv("BG_WORKERS", "4")))


def _hash_short(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]

# Cross-document analysis caches
_doc_claims_cache: Dict[str, List[Dict[str, Any]] ] = {}
_cross_insights_cache: Dict[str, Dict[str, Any]] = {}

def _file_signature(filename: str) -> str:
    """Return a short signature for a file based on mtime and size for cache invalidation."""
    try:
        p = (_docs_dir / filename)
        st = p.stat()
        return f"{filename}:{int(st.st_mtime)}:{st.st_size}"
    except Exception:
        return f"{filename}:na"

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded PDFs statically so the frontend can preview them
_docs_dir = (Path(__file__).resolve().parent / "document_library").absolute()
_docs_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/document_library",
    StaticFiles(directory=str(_docs_dir)),
    name="document_library",
)

# Serve generated audio files
_audio_dir = (Path(__file__).resolve().parent / "generated_audio").absolute()
_audio_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/audio",
    StaticFiles(directory=str(_audio_dir)),
    name="audio",
)


# ---------------------------------------------------------------------------
# Startup: index any PDFs already present so recommendations work after restart
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def _startup_index_existing_pdfs():
    try:
        # Collect already-indexed filenames from metadata
        indexed: Set[str] = set()
        for md in store.metadatas:
            fn = md.get("filename")
            if fn:
                indexed.add(fn)
        # Scan disk for PDFs
        to_add: List[Path] = []
        for p in _docs_dir.iterdir():
            if p.is_file() and p.suffix.lower() == ".pdf" and p.name not in indexed:
                to_add.append(p)
        # Process sequentially to avoid embedder concurrency issues
        for pdf_path in sorted(to_add):
            try:
                processed = process_pdf(str(pdf_path))
                if processed:
                    store.add_documents(processed, filename=pdf_path.name)
            except Exception:
                # Skip problematic files to keep startup resilient
                continue
    except Exception:
        # Never block server startup on indexing failures
        pass


@app.post("/reindex")
async def reindex():
    """Re-scan document_library and (re)index any missing PDFs.
    Returns list of (newly) indexed filenames.
    """
    newly: List[str] = []
    try:
        indexed: Set[str] = set()
        for md in store.metadatas:
            fn = md.get("filename")
            if fn:
                indexed.add(fn)
        for p in _docs_dir.iterdir():
            if p.is_file() and p.suffix.lower() == ".pdf" and p.name not in indexed:
                try:
                    processed = process_pdf(str(p))
                    if processed:
                        store.add_documents(processed, filename=p.name)
                        newly.append(p.name)
                except Exception:
                    continue
    except Exception:
        pass
    return {"indexed": newly}


@app.get("/config/public")
def public_config():
    """Return non-sensitive config usable by the frontend."""
    return {
        "adobeClientId": os.getenv("ADOBE_CLIENT_ID", "")
    }


@app.get("/v1/health")
def health_check():
    return {"status": "ok"}


@app.get("/documents")
def list_documents():
    """List uploaded PDF filenames in the document library."""
    try:
        files = []
        for p in _docs_dir.iterdir():
            if p.is_file() and p.suffix.lower() == ".pdf":
                files.append(p.name)
        files.sort()
        return {"files": files}
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {e}")


class RecommendationRequest(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None
    k: int = 5
    fetch_k: Optional[int] = None  # retrieve more for better de-dup
    min_score: Optional[float] = None  # filter low-relevance results
    exclude_self: bool = True  # if querying by filename/page, remove same page from results


@app.post("/recommendations")
async def recommendations(req: RecommendationRequest):
    # Determine query text
    query_text: Optional[str] = None
    if req.text and req.text.strip():
        query_text = req.text.strip()
    elif req.filename:
        # Aggregate chunks for the given page or entire file
        joined: List[str] = []
        for text, meta in zip(store.texts, store.metadatas):
            if meta.get("filename") == req.filename and (
                req.page_number is None or meta.get("page_number") == req.page_number
            ):
                joined.append(text)
        if joined:
            # Use a brief summary as query to avoid excessively long input
            query_text = "\n\n".join(joined)[:2000]

    if not query_text:
        return {"results": []}

    # Embed and search
    model = _get_embedder()
    q_emb = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)[0]
    results = store.search(q_emb, k=req.k, fetch_k=req.fetch_k)

    # De-dup and optional filtering
    seen: Set[Tuple[Optional[str], Optional[int]]] = set()
    shaped = []
    best_self = None  # hold best result from the same page if we end up empty
    for r in results:
        md = r.get("metadata", {})
        fname = md.get("filename")
        pnum = md.get("page_number")
        key = (fname, pnum)
        if key in seen:
            continue
        if req.exclude_self and req.filename and fname == req.filename and req.page_number and pnum == req.page_number:
            # Record the best self result in case everything else is filtered out
            if best_self is None:
                best_self = r
            continue
        score = r.get("score")
        if req.min_score is not None and score is not None and score < req.min_score:
            continue
        seen.add(key)
        shaped.append({
            "snippet": r.get("text", ""),
            "filename": fname,
            "page_number": pnum,
            "distance": r.get("distance"),
            "score": score,
        })
        if len(shaped) >= req.k:
            break
    # If nothing found and we filtered out the self page, return the best self match
    if not shaped and best_self is not None:
        md = best_self.get("metadata", {})
        shaped.append({
            "snippet": best_self.get("text", ""),
            "filename": md.get("filename"),
            "page_number": md.get("page_number"),
            "distance": best_self.get("distance"),
            "score": best_self.get("score"),
        })
    return {"results": shaped}


class InsightsRequest(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None
    k: int = 5  # retrieval size for context/citations


def _extract_page_text(file_path: str, page_number: int) -> str:
    if not Path(file_path).is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if page_number is None or page_number < 1:
        raise HTTPException(status_code=400, detail="page_number must be >= 1")
    try:
        doc = fitz.open(file_path)
        try:
            idx = page_number - 1
            if idx < 0 or idx >= len(doc):
                raise HTTPException(status_code=400, detail="page_number out of range")
            page = doc[idx]
            return page.get_text("text") or ""
        finally:
            doc.close()
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Failed to read PDF: {e}")


def _gemini_insights(text: str, citations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    if genai is None:
        raise HTTPException(status_code=500, detail="google-generativeai not installed on server")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY not configured on server")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "response_mime_type": "application/json"
        }
    )
    cites_str = "\n".join([
        f"[CITATION {i+1}] file={c.get('filename')} page={c.get('page_number')}: {c.get('snippet')}"
        for i, c in enumerate(citations or [])
    ])
    prompt = f"""
You are an assistant extracting structured insights from a document passage and optional retrieved references.
Return JSON with exactly these keys:
- "summary": short paragraph summarizing the context (60-120 words).
- "insights": array of 3-7 concise key takeaways.
- "facts": array of factual statements supported by the text.
- "contradictions": array of potential inconsistencies or conflicts (empty if none).

Primary Context:
{text}

Retrieved References (optional):
{cites_str or 'None'}
"""
    try:
        resp = model.generate_content(prompt)
        raw = (getattr(resp, "text", None) or "").strip()
        # In JSON mode, raw should be JSON; still guard parsing
        data = json.loads(raw) if raw else {}
        return {
            "summary": data.get("summary", "") if isinstance(data, dict) else "",
            "insights": data.get("insights", []) if isinstance(data, dict) else [],
            "facts": data.get("facts", []) if isinstance(data, dict) else [],
            "contradictions": data.get("contradictions", []) if isinstance(data, dict) else [],
        }
    except Exception:  # pragma: no cover
        return {"summary": "", "insights": [], "facts": [], "contradictions": []}


@app.post("/insights")
async def insights(req: InsightsRequest):
    """Generate insights using Gemini from provided text or a specific page of an uploaded PDF."""
    text = (req.text or "").strip()
    if not text:
        if not (req.filename and req.page_number):
            raise HTTPException(status_code=400, detail="Provide text, or filename + page_number")
        file_path = str((_docs_dir / req.filename).absolute())
        text = _extract_page_text(file_path, req.page_number).strip()
        if not text:
            raise HTTPException(status_code=400, detail="No extractable text for the given page")
    # Retrieve top-k related chunks for better grounded insights and citations
    citations: List[Dict[str, Any]] = []
    try:
        model = _get_embedder()
        q_emb = model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
        raw = store.search(q_emb, k=max(1, req.k or 5), fetch_k=max(10, (req.k or 5) * 2))
        seen: Set[Tuple[Optional[str], Optional[int]]] = set()
        for r in raw:
            md = r.get("metadata", {})
            fname = md.get("filename")
            pnum = md.get("page_number")
            key = (fname, pnum)
            if key in seen:
                continue
            seen.add(key)
            citations.append({
                "filename": fname,
                "page_number": pnum,
                "snippet": r.get("text", "")[:500]
            })
            if len(citations) >= (req.k or 5):
                break
    except Exception:
        citations = []

    result = _gemini_insights(text, citations)
    return {
        "summary": result.get("summary", ""),
        "insights": result.get("insights", []),
        "facts": result.get("facts", []),
        "contradictions": result.get("contradictions", []),
        "citations": citations,
    }


class CrossInsightsRequest(BaseModel):
    filenames: Optional[List[str]] = None  # if None, use all uploaded PDFs
    max_per_doc: int = 6  # max claims/snippets per document
    deep: Optional[bool] = False  # if true, use LLM to extract claims; else use fast snippet fallback
    force: Optional[bool] = False  # bypass caches when true


def _select_diverse_pages(page_texts: Dict[int, str], k: int) -> List[int]:
    """Select up to k pages maximizing diversity using cosine distances on embeddings.
    Start with longest page then greedy max-min. Falls back to length ranking if embedder unavailable.
    """
    items = [(p, t, len(t)) for p, t in page_texts.items() if (t or "").strip()]
    if not items:
        return []
    # If k >= pages, return all pages sorted by page number
    if k >= len(items):
        return [p for p, _, _ in sorted(items, key=lambda x: x[0])]
    # Candidate pool: top k*3 by length to cap compute
    cand = sorted(items, key=lambda x: x[2], reverse=True)[: max(1, min(len(items), k * 3))]
    pages = [p for p, _, _ in cand]
    texts = [t for _, t, _ in cand]
    try:
        model = _get_embedder()
        embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    except Exception:
        return [p for p, _, _ in cand[:k]]
    # Greedy max-min selection
    selected: List[int] = []
    selected_idx: List[int] = []
    # seed with the longest page (index 0 in cand)
    selected.append(pages[0])
    selected_idx.append(0)
    while len(selected) < k and len(selected) < len(pages):
        best_i = None
        best_score = -1.0
        for i in range(len(pages)):
            if i in selected_idx:
                continue
            # max-min distance (1 - cosine since embs normalized and search uses inner product)
            dmin = 1.0
            for si in selected_idx:
                sim = float(np.dot(embs[i], embs[si]))
                dist = 1.0 - sim
                if dist < dmin:
                    dmin = dist
            if dmin > best_score:
                best_score = dmin
                best_i = i
        if best_i is None:
            break
        selected_idx.append(best_i)
        selected.append(pages[best_i])
    return selected


def _extract_doc_claims(filename: str, max_per_doc: int = 6, deep: bool = False) -> List[Dict[str, Any]]:
    """Return a list of concise claims for a document with page refs.
    Strategy:
      1) Select up to max_per_doc pages with the most content.
      2) Ask Gemini to extract 3-8 factual claims with page refs and short quotes.
      3) Fallback to raw snippets if LLM isn't available.
    """
    # Gather chunks for this file
    chunks: List[Tuple[str, Dict[str, Any]]] = [
        (t, m) for t, m in zip(store.texts, store.metadatas) if m.get("filename") == filename
    ]
    if not chunks:
        return []
    # Group by page
    pages: Dict[int, List[str]] = {}
    for t, m in chunks:
        p = int(m.get("page_number") or 0)
        pages.setdefault(p, []).append(t)
    # Build per-page text and select a diverse subset of pages
    page_full: Dict[int, str] = {}
    for p, segs in pages.items():
        page_full[p] = "\n".join(segs)
    chosen_pages = _select_diverse_pages(page_full, max_per_doc) or [p for p in sorted(pages.keys())[:max_per_doc]]

    # Prepare sections for LLM with page markers
    sections = []
    for p in chosen_pages:
        joined = page_full.get(p, "")
        sections.append({"page_number": p, "text": joined[:900]})

    # If Gemini not available, fallback to snippets
    if (not deep) or genai is None or not os.getenv("GOOGLE_API_KEY"):
        fallback: List[Dict[str, Any]] = []
        for s in sections:
            fallback.append({
                "filename": filename,
                "page_number": s["page_number"],
                "snippet": s["text"],
            })
        return fallback

    # Call Gemini once per document to extract claims
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        sec_text = []
        for s in sections:
            sec_text.append(f"PAGE {s['page_number']}\n{s['text']}")
        sections_block = "\n\n".join(sec_text)
        prompt = f"""
You are extracting factual claims from a PDF. Read the page sections and return JSON with an array 'claims'.
Each claim item must include:
    statement: concise factual sentence.
    page_number: integer page number where it's supported.
    quotes: array of 1-2 short quotes (<=120 chars) from that page.
Limit to 3-8 high-value claims total. Do not invent facts.

Sections:

{sections_block}
"""
        resp = model.generate_content(prompt)
        raw = (getattr(resp, "text", None) or "").strip()
        data = json.loads(raw) if raw else {}
        items = data.get("claims", []) if isinstance(data, dict) else []
        claims: List[Dict[str, Any]] = []
        for it in items:
            try:
                claims.append({
                    "filename": filename,
                    "page_number": int(it.get("page_number") or (chosen_pages[0] if chosen_pages else 1)),
                    "statement": (it.get("statement") or "").strip(),
                    "quotes": it.get("quotes", []) or [],
                })
            except Exception:
                continue
        if claims:
            return claims[: max_per_doc]
    except Exception:
        pass

    # Fallback to snippets if JSON parsing or LLM fails
    claims: List[Dict[str, Any]] = []
    for p in chosen_pages:
        joined = page_full.get(p, "")
        claims.append({
            "filename": filename,
            "page_number": p,
            "snippet": joined[:800],
        })
    return claims


def _gemini_cross_compare(doc_claims: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Use Gemini to compare claims across documents, returning agreements and contradictions with references."""
    if genai is None:
        return {"agreements": [], "contradictions": [], "notes": []}
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"agreements": [], "contradictions": [], "notes": []}
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"}
    )

    refs: List[str] = []
    for i, c in enumerate(doc_claims):
        line = f"[{i+1}] file={c.get('filename')} page={c.get('page_number')}\n"
        if c.get("statement"):
            line += f"CLAIM: {c.get('statement')}\n"
        if c.get("quotes"):
            try:
                qs = c.get("quotes") or []
                for q in qs[:2]:
                    if isinstance(q, str) and q.strip():
                        line += f"QUOTE: {q.strip()}\n"
            except Exception:
                pass
        if c.get("snippet") and not c.get("statement"):
            line += c.get("snippet")
        refs.append(line.strip())
    refs_block = "\n\n".join(refs)

    prompt = f"""
You are comparing evidence across multiple PDFs. Read the references and identify:
- Agreements: statements that are supported by two or more sources (list each statement once).
- Contradictions: statements that are in tension or conflict between sources.

For each item, return JSON with these fields:
    statement: concise sentence.
    support: array of references like {{file, page_number}} that support it.
    quotes: array of 1-3 short quotes (<=120 chars) from those references.

If no clear items exist, return empty arrays.

References:

{refs_block}
"""

    try:
        resp = model.generate_content(prompt)
        raw = (getattr(resp, "text", None) or "").strip()
        data = json.loads(raw) if raw else {}
        return {
            "agreements": data.get("agreements", []) if isinstance(data, dict) else [],
            "contradictions": data.get("contradictions", []) if isinstance(data, dict) else [],
            "notes": data.get("notes", []) if isinstance(data, dict) else [],
        }
    except Exception:
        return {"agreements": [], "contradictions": [], "notes": []}


@app.post("/cross-insights")
async def cross_insights(req: CrossInsightsRequest):
    """Compare uploaded PDFs to find supporting and contradicting points.
    If req.filenames is not provided, all PDFs in document_library are used.
    Returns agreements and contradictions with references back to files/pages.
    """
    # Determine files to analyze
    if req.filenames:
        files = [f for f in req.filenames if (_docs_dir / f).is_file() and f.lower().endswith(".pdf")]
    else:
        try:
            files = [p.name for p in _docs_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]
        except Exception:
            files = []
    files.sort()
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least two PDFs are required for cross-insights")

    # Collect claims with simple per-file caching based on (mtime,size)
    all_claims: List[Dict[str, Any]] = []
    cache_key_parts = []
    loop = asyncio.get_running_loop()
    tasks = []
    for f in files:
        sig = _file_signature(f) + ("|deep" if req.deep else "|fast")
        cache_key_parts.append(sig)
        if (not req.force) and (sig in _doc_claims_cache):
            # Use cached directly
            all_claims.extend(_doc_claims_cache[sig])
            continue
        # Offload extraction to background thread
        def _job(file=f, signature=sig):
            c = _extract_doc_claims(file, max_per_doc=max(2, req.max_per_doc), deep=bool(req.deep))
            _doc_claims_cache[signature] = c
            return c
        tasks.append(loop.run_in_executor(_bg_executor, _job))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                continue
            all_claims.extend(r or [])

    if not all_claims:
        return {"agreements": [], "contradictions": [], "notes": []}

    cross_key = _hash_short("|".join(cache_key_parts) + f"|m{req.max_per_doc}")
    cached = _cross_insights_cache.get(cross_key)
    if (not req.force) and (cached is not None):
        return cached

    result = _gemini_cross_compare(all_claims)
    _cross_insights_cache[cross_key] = result
    return result


class GenerateAudioRequest(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None
    voice: Optional[str] = None  # optional, used best-effort for local pyttsx3
    format: Optional[str] = None  # mp3 or wav (hf_dia returns mp3; pyttsx3 outputs wav)
    podcast: Optional[bool] = False  # if true, use more human/podcast-like narration
    accent: Optional[str] = None  # e.g. en-US, en-GB, en-IN, es-ES
    style: Optional[str] = None   # e.g. "female", "male", or custom speaker id
    expressiveness: Optional[str] = None  # e.g. "high", "medium", "low"


def _gemini_script(text: str, podcast: bool = False, accent: Optional[str] = None, style: Optional[str] = None, expressiveness: Optional[str] = None) -> str:
    """Use Gemini to convert raw context into a narration script.
    When podcast=True or expressiveness is specified, produce a warmer, more natural script.
    Accent/style hints are woven subtly (no phonetic spellings) to encourage region-appropriate phrasing.
    """
    if genai is None:
        return text[:1500]
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return text[:1500]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "response_mime_type": "text/plain"
        }
    )
    # Build dynamic guidance
    accent_hint = f"Accent preference: {accent}." if accent else ""
    style_hint = f" Voice/style hint: {style}." if style else ""
    expr_level = (expressiveness or ("high" if podcast else "medium"))
    expr_hint = f" Target expressiveness: {expr_level}." if expr_level else ""

    if podcast or expressiveness:
        prompt = f"""
You are a professional podcast narrator. Rewrite the following content as a warm, highly natural spoken narration.
Guidelines:
- Conversational, human, fluid phrasing; no bullet lists.
- Vary rhythm & sentence length; insert implicit short pauses with commas (do NOT write stage directions).
- Avoid robotic repetition; add light connective tissue for flow if needed (do not invent facts).
- No URLs, no markdown, no list formatting.
- Keep within ~220 words.
{accent_hint}{style_hint}{expr_hint}

Content:
{text}
"""
    else:
        prompt = f"""
Rewrite the content into a concise, natural narration (15-60 seconds). Conversational tone, no lists, no URLs.
{accent_hint}{style_hint}{expr_hint}

Content:
{text}
"""
    try:
        resp = model.generate_content(prompt)
        raw = (getattr(resp, "text", None) or "").strip()
        return raw or text[:1500]
    except Exception:
        return text[:1500]


def _synthesize_speech(text: str, voice: Optional[str] = None, fmt: Optional[str] = None, accent: Optional[str] = None, style: Optional[str] = None, deterministic_basename: Optional[str] = None) -> Tuple[str, str]:
    """Synthesize speech from text into a file using the selected provider.
    Preference: Hugging Face (Dia-1.6B) when token is available; otherwise offline pyttsx3.
    You can force provider via env TTS_PROVIDER: 'hf_dia' or 'pyttsx3'.
    Returns (filename, public_relative_url).
    """
    provider = (os.getenv("TTS_PROVIDER") or "").lower().strip()
    hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
    hf_model = os.getenv("HF_DIA_MODEL", "nari-labs/Dia-1.6B")

    # Decide provider: default to HF if token exists and not explicitly forcing pyttsx3
    use_hf = (provider == "hf_dia") or (provider == "" and bool(hf_token))

    # Hugging Face Dia-1.6B via Inference API (mp3)
    if use_hf and hf_token:
        if requests is None:
            raise HTTPException(status_code=500, detail="requests library not installed on server")
        url = f"https://api-inference.huggingface.co/models/{hf_model}"
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Accept": "audio/mpeg",
        }
        parameters: Dict[str, Any] = {}
        # Provide multiple possible keys to maximize compatibility across models
        if accent:
            # Normalize accent to language base for lang field (e.g. en-US -> en)
            base_lang = accent.split('-')[0]
            parameters["language"] = accent
            parameters["lang"] = base_lang
        if style:
            # Some models expect speaker or speaker_id
            parameters["speaker_id"] = style
            parameters["speaker"] = style
        payload: Dict[str, Any] = {"inputs": text}
        if parameters:
            payload["parameters"] = parameters
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=180)
        except Exception as e:  # pragma: no cover
            # Fall back to offline if network/model errors
            resp = None
        if resp is not None and resp.status_code == 503:
            # Model loading; surface a retryable error
            raise HTTPException(status_code=503, detail="TTS model loading, retry shortly")
        if resp is not None and resp.ok and resp.content:
            # Include short label for accent/style in filename for caching clarity
            tag_parts = []
            if accent:
                tag_parts.append(accent.replace('-', '').lower())
            if style:
                tag_parts.append(style.lower())
            tag = ("_" + "_".join(tag_parts)) if tag_parts else ""
            if deterministic_basename:
                base = f"{deterministic_basename}.mp3"
            else:
                base = f"tts_{uuid.uuid4().hex[:8]}_hf{tag}.mp3"
            out_path = _audio_dir / base
            try:
                out_path.write_bytes(resp.content)
            except Exception as e:  # pragma: no cover
                raise HTTPException(status_code=500, detail=f"Failed to write audio: {e}")
            rel_url = f"/audio/{base}"
            return base, rel_url
        # Otherwise: fall through to offline pyttsx3

    # Offline provider: pyttsx3 (WAV)
    if pyttsx3 is None:
        raise HTTPException(status_code=500, detail="pyttsx3 not installed on server; install pyttsx3 or configure HUGGINGFACE_API_TOKEN")
    ext = "wav"
    voice_name = voice or os.getenv("PYTTSX3_VOICE") or ""
    if deterministic_basename:
        base = f"{deterministic_basename}.{ext}"
    else:
        base = f"tts_{abs(hash(text))}_{(voice_name or 'default').replace(' ','_')}.{ext}"
    out_path = _audio_dir / base
    try:
        # Guard engine usage with a lock for thread safety
        with _pyttsx3_lock:
            engine = pyttsx3.init()
            if voice_name:
                # Try to select a matching voice id by name substring
                for v in engine.getProperty('voices'):
                    if voice_name.lower() in (v.name or '').lower():
                        engine.setProperty('voice', v.id)
                        break
            engine.save_to_file(text, str(out_path))
            engine.runAndWait()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Local TTS failed: {e}")
    rel_url = f"/audio/{base}"
    return base, rel_url


@app.post("/generate-audio")
async def generate_audio(req: GenerateAudioRequest):
    """Generate (and cache) TTS audio from provided text or a specific page.
    Optimizations:
    - Script caching: repeated requests for same content + parameters reuse Gemini output.
    - Audio caching: identical script + voice/style/accent/provider returns existing file.
    - Offloaded synthesis to thread pool to avoid blocking event loop.
    """
    text = (req.text or "").strip()
    if not text:
        if not (req.filename and req.page_number):
            raise HTTPException(status_code=400, detail="Provide text, or filename + page_number")
        file_path = str((_docs_dir / req.filename).absolute())
        text = _extract_page_text(file_path, req.page_number).strip()
        if not text:
            raise HTTPException(status_code=400, detail="No extractable text for the given page")

    # --- Script caching ---
    script_key = "|".join([
        _hash_short(text),
        f"p{1 if req.podcast else 0}",
        req.accent or "-",
        req.style or "-",
        req.expressiveness or "-",
    ])
    script = _script_cache.get(script_key)
    if script is None:
        script = _gemini_script(
            text,
            podcast=bool(req.podcast),
            accent=req.accent,
            style=req.style,
            expressiveness=req.expressiveness,
        )
        _script_cache[script_key] = script

    provider = (os.getenv("TTS_PROVIDER") or "").lower().strip() or "auto"

    # Deterministic base name for caching (does not include random UUID)
    deterministic_base = "_".join([
        "tts",
        _hash_short(script),
        provider,
        (req.accent or "na").replace('-', ''),
        (req.style or "na"),
    ])

    audio_key = "|".join([
        deterministic_base,
        req.voice or "-",
    ])
    cached_audio = _audio_cache.get(audio_key)
    if cached_audio:
        return {"url": cached_audio[1], "cached": True}
    # Disk-backed cache: if file exists from a previous run, reuse it
    for ext in ("mp3", "wav"):
        candidate = _audio_dir / f"{deterministic_base}.{ext}"
        if candidate.is_file():
            rel_url = f"/audio/{candidate.name}"
            _audio_cache[audio_key] = (candidate.name, rel_url)
            return {"url": rel_url, "cached": True}

    loop = asyncio.get_running_loop()
    try:
        filename, rel_url = await loop.run_in_executor(
            _tts_executor,
            lambda: _synthesize_speech(
                script,
                voice=req.voice,
                fmt=req.format,
                accent=req.accent,
                style=req.style,
                deterministic_basename=deterministic_base,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {e}")

    _audio_cache[audio_key] = (filename, rel_url)
    return {"url": rel_url, "cached": False}

@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Accept multiple file uploads and save them to backend/document_library.
    Returns the list of saved filenames.
    """
    base_dir = Path(__file__).resolve().parent
    save_dir = base_dir / "document_library"
    save_dir.mkdir(parents=True, exist_ok=True)

    saved: List[str] = []
    for f in files:
        # Prevent path traversal by using only the name component
        safe_name = Path(f.filename).name if f.filename else "upload.bin"
        target = save_dir / safe_name
        content = await f.read()
        with open(target, "wb") as out:
            out.write(content)
        saved.append(safe_name)

        # Process the saved PDF into chunks + embeddings and add to the vector store
        try:
            processed = process_pdf(str(target))
            if processed:
                store.add_documents(processed, filename=safe_name)
        except Exception as e:
            # Skip processing errors per-file but continue others
            # Optionally, log e
            pass

    return {"saved": saved}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8001"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
