# Backend (FastAPI)

This backend powers PDF upload, chunking, semantic search, Gemini insights, and Text-to-Speech narration with providers: Hugging Face Dia-1.6B (preferred) or offline pyttsx3.

## Quick start

1) Create a virtual environment and install deps
- pip install -r requirements.txt

2) Configure env vars
- Copy `.env.example` to `.env` and fill in values as needed (at minimum choose a TTS provider below).

3) Run the full API (from repo root or backend folder)
- From repo root: uvicorn backend.main:app --reload --port 8001
- Or from backend folder: uvicorn main:app --reload --port 8001

Minimal health-only app (optional):
- uvicorn backend.app.main:app --reload

## Key endpoints
- POST /upload — upload PDFs; auto-chunks and indexes for semantic search
- POST /recommendations — query similar chunks by text or file/page
- POST /insights — Gemini-powered structured insights for text or a page
- POST /generate-audio — generate TTS narration; returns a public audio URL
- GET /document_library/... — static access to uploaded PDFs
- GET /audio/... — static access to generated audio files

## Text-to-Speech providers
Preference is Hugging Face Dia (if token is set); otherwise offline pyttsx3.
You can force a provider via env `TTS_PROVIDER`:
- hf_dia — Hugging Face Inference API for Dia-1.6B (requires HUGGINGFACE_API_TOKEN). Outputs MP3.
- pyttsx3 — Offline/local TTS. Outputs WAV.

Optional envs:
- HF_DIA_MODEL (default nari-labs/Dia-1.6B)
- GOOGLE_API_KEY (for Gemini insights and narration scripting)

See `.env.example` for a complete list.
