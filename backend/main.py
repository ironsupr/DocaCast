from fastapi import FastAPI, UploadFile, File
from typing import List
from pathlib import Path
from backend.processing import process_pdf
from backend.vector_store import VectorStore
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
