from fastapi import FastAPI, UploadFile, File
from typing import List
from pathlib import Path
from backend.processing import process_pdf
from backend.vector_store import VectorStore
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Any, Dict, Tuple, Set
import os
import json
import fitz  # PyMuPDF
from fastapi import HTTPException
from dotenv import load_dotenv
try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore
from backend.processing import _get_embedder

# Load environment variables from .env at startup
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


@app.get("/config/public")
def public_config():
    """Return non-sensitive config usable by the frontend."""
    return {
        "adobeClientId": os.getenv("ADOBE_CLIENT_ID", "")
    }


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
    for r in results:
        md = r.get("metadata", {})
        fname = md.get("filename")
        pnum = md.get("page_number")
        key = (fname, pnum)
        if key in seen:
            continue
        if req.exclude_self and req.filename and fname == req.filename and req.page_number and pnum == req.page_number:
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
    return {"results": shaped}


class InsightsRequest(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None


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


def _gemini_insights(text: str) -> Dict[str, Any]:
    if genai is None:
        raise HTTPException(status_code=500, detail="google-generativeai not installed on server")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY not configured on server")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
You extract structured insights from the given context. Return strict JSON only with keys:
- "insights": array of 3-7 concise statements of key takeaways.
- "facts": array of factual statements supported by the text.
- "contradictions": array of potential inconsistencies or conflicts found in the text (empty if none).

Context:
{text}
Respond with JSON only.
"""
    try:
        resp = model.generate_content(prompt)
        raw = (getattr(resp, "text", None) or "").strip()
        data = json.loads(raw) if raw else {}
        return {
            "insights": data.get("insights", []) if isinstance(data, dict) else [],
            "facts": data.get("facts", []) if isinstance(data, dict) else [],
            "contradictions": data.get("contradictions", []) if isinstance(data, dict) else [],
        }
    except Exception:  # pragma: no cover
        return {"insights": [], "facts": [], "contradictions": []}


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
    result = _gemini_insights(text)
    return {
        "insights": result.get("insights", []),
        "facts": result.get("facts", []),
        "contradictions": result.get("contradictions", []),
    }

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
