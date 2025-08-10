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


@app.get("/config/public")
def public_config():
    """Return non-sensitive config usable by the frontend."""
    return {
        "adobeClientId": os.getenv("ADOBE_CLIENT_ID", "")
    }


@app.get("/v1/health")
def health_check():
    return {"status": "ok"}


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


class GenerateAudioRequest(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None
    voice: Optional[str] = None  # optional, used best-effort for local pyttsx3
    format: Optional[str] = None  # mp3 or wav (hf_dia returns mp3; pyttsx3 outputs wav)


def _gemini_script(text: str) -> str:
    """Use Gemini to convert raw context into a short, engaging narration script."""
    if genai is None:
        # Fallback: return the text directly if Gemini isn't installed
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
    prompt = f"""
Transform the following content into a natural, spoken narration suitable for Text-To-Speech. 
Guidelines: conversational tone, clear and concise, 15-45 seconds spoken length, avoid lists/bullets, no URLs.

Content:
{text}
"""
    try:
        resp = model.generate_content(prompt)
        raw = (getattr(resp, "text", None) or "").strip()
        return raw or text[:1500]
    except Exception:
        return text[:1500]


def _synthesize_speech(text: str, voice: Optional[str] = None, fmt: Optional[str] = None) -> Tuple[str, str]:
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
        try:
            resp = requests.post(url, headers=headers, json={"inputs": text}, timeout=120)
        except Exception as e:  # pragma: no cover
            # Fall back to offline if network/model errors
            resp = None
        if resp is not None and resp.status_code == 503:
            # Model loading; surface a retryable error
            raise HTTPException(status_code=503, detail="TTS model loading, retry shortly")
        if resp is not None and resp.ok and resp.content:
            base = f"tts_{uuid.uuid4().hex[:8]}_dia.mp3"
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
    base = f"tts_{abs(hash(text))}_{(voice_name or 'default').replace(' ','_')}.{ext}"
    out_path = _audio_dir / base
    try:
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
    """Generate TTS audio from provided text or a specific page. Returns a public URL to the audio file."""
    text = (req.text or "").strip()
    if not text:
        if not (req.filename and req.page_number):
            raise HTTPException(status_code=400, detail="Provide text, or filename + page_number")
        file_path = str((_docs_dir / req.filename).absolute())
        text = _extract_page_text(file_path, req.page_number).strip()
        if not text:
            raise HTTPException(status_code=400, detail="No extractable text for the given page")

    script = _gemini_script(text)
    _, rel_url = _synthesize_speech(script, voice=req.voice, fmt=req.format)
    return {"url": rel_url}

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
