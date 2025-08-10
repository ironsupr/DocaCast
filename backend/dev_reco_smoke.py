from __future__ import annotations

from pathlib import Path
import uuid
from fastapi.testclient import TestClient


def main() -> int:
    try:
        # Import app from backend.main (works when run from repo root)
        from backend.main import app  # type: ignore
    except Exception:
        # Fallback if run from backend/ folder
        from main import app  # type: ignore

    client = TestClient(app)
    # access store for diagnostics
    try:
        from backend.main import store as VS  # type: ignore
    except Exception:
        from main import store as VS  # type: ignore

    here = Path(__file__).resolve().parent
    # Create a small synthetic PDF with text to ensure extraction works
    sample = here / f"smoke_{uuid.uuid4().hex[:8]}.pdf"
    try:
        import fitz  # PyMuPDF
        doc = fitz.open()
        page = doc.new_page()
        text = (
            "This is a smoke test document for the recommendation system.\n\n"
            "It contains some repeated keywords like machine learning, deep learning, and neural networks.\n"
            "We also mention transformers and embeddings for semantic search testing.\n\n"
            "The quick brown fox jumps over the lazy dog."
        )
        rect = page.rect
        margin = 72
        box = fitz.Rect(rect.x0 + margin, rect.y0 + margin, rect.x1 - margin, rect.y1 - margin)
        page.insert_textbox(box, text, fontsize=12)
        doc.save(str(sample))
        doc.close()
    except Exception as e:
        print("Failed to create synthetic PDF:", e)
        return 2

    # 1) Upload the sample PDF
    print(f"Store before upload: ntotal={(VS.index.ntotal if getattr(VS, 'index', None) else 0)} texts={len(VS.texts)}")
    with sample.open("rb") as f:
        files = {"files": (sample.name, f, "application/pdf")}
        r = client.post("/upload", files=files)
    if r.status_code != 200:
        print("Upload failed:", r.status_code, r.text)
        return 3
    data = r.json()
    saved = data.get("saved", [])
    if sample.name not in saved:
        print("Upload response missing filename:", data)
        return 4
    print("Uploaded:", saved)
    print(f"Store after upload: ntotal={(VS.index.ntotal if getattr(VS, 'index', None) else 0)} texts={len(VS.texts)}")

    # Diagnose process_pdf directly
    try:
        try:
            from backend.processing import process_pdf as _proc  # type: ignore
        except Exception:
            from processing import process_pdf as _proc  # type: ignore
        res = _proc(str(here / saved[0]))
        print(f"process_pdf returned {len(res)} chunks")
    except Exception as e:
        print("process_pdf raised:", repr(e))

    # 2) Query recommendations for page 1 of the uploaded file
    payload = {"filename": sample.name, "page_number": 1, "k": 5}
    r2 = client.post("/recommendations", json=payload)
    if r2.status_code != 200:
        print("Recommendations failed:", r2.status_code, r2.text)
        return 5
    recs = r2.json().get("results", [])
    print(f"Recommendations returned: {len(recs)} items")
    for i, rec in enumerate(recs[:3]):
        print(f"  {i+1}. {rec.get('filename')} p.{rec.get('page_number')} score={rec.get('score')}")
        snippet = (rec.get('snippet') or '')[:120].replace('\n', ' ')
        print("     ", snippet, "…" if len(rec.get('snippet') or '') > 120 else "")

    # 3) If empty, try a text-based query by extracting first page text via endpoint /insights pre-step
    if not recs:
        # use recommendations with an artificial text query derived from the sample
        try:
            # Load a little text from the pdf to simulate a query
            import fitz  # PyMuPDF
            doc = fitz.open(sample)
            try:
                text = (doc[0].get_text("text") or "").strip()
            finally:
                doc.close()
            if text:
                q = {"text": text[:1000], "k": 5}
                r3 = client.post("/recommendations", json=q)
                if r3.status_code == 200:
                    recs2 = r3.json().get("results", [])
                    print(f"Text-query recommendations: {len(recs2)} items")
                    for i, rec in enumerate(recs2[:3]):
                        print(f"  {i+1}. {rec.get('filename')} p.{rec.get('page_number')} score={rec.get('score')}")
        except Exception as e:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
