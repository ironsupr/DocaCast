# DocaCast — Interview Guide

This document is intended to prepare you to explain, defend, and demo the DocaCast project in an interview. It consolidates the project's purpose, architecture, key components, data flows, deployment and ops notes, design decisions, edge cases, testing, scaling and security considerations, and a list of high-value interview questions with suggested answers.

---

## Quick elevator pitch

DocaCast converts PDF documents into engaging, podcast-style audio using semantic document understanding and modern text-to-speech (TTS) systems. It supports single-narrator and two-speaker podcast-style audio by extracting and summarizing page content, generating a natural dialogue script via an LLM (Gemini / Google Generative AI), synthesizing audio with multi-speaker support, and bundling the result into play-ready audio files with chapter metadata.

Key differentiators:
- Two-speaker, conversational podcast generation (Speaker 1 = analytical, Speaker 2 = enthusiastic).
- Semantic retrieval for grounding insights and citations (vector store + embeddings).
- Multiple TTS provider support with graceful fallbacks (Gemini TTS / Google / Edge-TTS / HF / pyttsx3).
- Frontend React UI with Adobe PDF Embed integration.

---

## Contract (short)
- Inputs: PDF uploads (multipart POST), or page/text input for /generate-audio, plus environment-configured API keys for AI and TTS.
- Outputs: audio file(s) served under `/audio/`, plus metadata for chapters/parts and transcript snippets.
- Error modes: 400 for invalid request inputs, 502/500 for provider failures, and graceful fallbacks if a TTS provider is not available.

---

## Repo structure (high-level, what to point at in an interview)
- `backend/` — FastAPI backend. Main entry point: `backend/main.py`.
  - `main.py` — API endpoints and orchestration (upload, generate-audio, search/recommendations, insights, diagnostics).
  - `processing.py` — PDF processing and chunking (extracting text from PDFs and preparing data to embed).
  - `vector_store.py` — in-memory vector store wrapper used for semantic search and recommendations.
  - `document_library/` — persisted uploaded PDFs.
  - `generated_audio/` — persisted audio outputs served by `/audio` static route.
- `api/` — example serverless microservice stubs used for Vercel (contains `generate-audio.py` demo handler used for deployments).
- `frontend/pdf-reader-ui/` — React + Vite app implementing the UI: file picker, podcast controls, recommendations sidebar, and audio player.
- `credentials/` — (gitignored) API key holders.
- Top-level tooling: `vercel.json`, `deploy-vercel.sh` / `.bat` for app deployment.

(When walking through the code, open `backend/main.py` to show the endpoints and the TTS orchestration: script creation, per-line synthesis, ffmpeg concat fallback, and caching behavior.)

---

## Architecture and data flow

1. Upload (or select) a PDF in the frontend.
2. Frontend posts file(s) to `POST /upload`.
3. Backend saves file to `backend/document_library/` and calls `process_pdf(...)` to:
   - extract page/chunk text (PyMuPDF / fitz),
   - produce chunks with metadata (filename, page_number, section_index),
   - embed chunks using an embedder (sentence-transformers or configured embedder),
   - store text + metadata + vectors in `VectorStore`.
4. For audio generation:
   - `POST /generate-audio` accepts text or filename+page or filename+entire_pdf.
   - Backend generates a narration script via `_gemini_script(...)` (Gemini LLM prompt transforms text into either narration or a two-speaker script).
   - Script is cached by a short hash key to avoid LLM re-runs.
   - For single-speaker: a single TTS call synthesizes an audio file.
   - For two-speaker podcast: the script is parsed into labeled lines, then per-line synthesis is attempted (or a multi-speaker Gemini TTS call if available). Clips are concatenated via `ffmpeg` into a single MP3; chapter metadata is computed via `ffprobe`.
   - Final audio and parts are stored under `generated_audio/` and served by `/audio`.
5. Semantic search and insights endpoints (`/recommendations`, `/insights`, `/cross-insights`) embed queries, search the `VectorStore`, and optionally call the LLM (Gemini) to produce higher-level insights.

---

## Important files and responsibilities (code walkthrough)
- `backend/main.py` — main FastAPI app; demonstrates:
  - endpoints: `/upload`, `/generate-audio`, `/recommendations`, `/insights`, `/cross-insights`, `/diagnostics`, `/documents`, `/reindex`.
  - TTS orchestration: `_synthesize_with_fallback`, `_synthesize_speech`, multi-provider logic and caching.
  - Script generation using Gemini: `_gemini_script`.
  - Podcast assembly: parsing speaker lines, per-line synthesis, `ffmpeg` concatenation, chapters creation.
- `backend/processing.py` — text extraction and chunking; explain how chunk size & metadata affect retrieval quality.
- `backend/vector_store.py` — wrapper for storage/search (FAISS-like behavior in-memory for demo).
- `api/generate-audio.py` — a simplified serverless handler used as a Vercel demo fallback (useful to show how to adapt to serverless environments).
- `frontend/pdf-reader-ui/src/components/` — React controls (FilePicker, GenerateAudioButton, PodcastStudio) showing UI wiring to backend endpoints.

When explaining code, open these files and point to concrete functions: e.g., `process_pdf` is called on upload, or `_synthesize_speech` is used to call Gemini TTS.

---

## Setup & how to run locally (PowerShell examples)

1. Backend (Python):

```powershell
cd backend
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# create .env in backend/ with keys: GOOGLE_API_KEY, GEMINI_API_KEY (optional), ADOBE_CLIENT_ID for frontend
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

2. Frontend (React + Vite):

```powershell
cd frontend\pdf-reader-ui
npm install
npm run dev
# open http://localhost:5173
```

Notes:
- If you don't have Gemini access, the code falls back to streaming providers if configured, or to demo behaviors.
- `api/generate-audio.py` is a tiny serverless demo used for Vercel deployment if you prefer serverless.

---

## Design decisions & trade-offs (interview talking points)

- Why LLM for script generation? LLMs (Gemini) provide flexible, human-like conversion from document text to spoken-style script with control tokens for two-speaker formatting. Trade-off: cost and dependency on API access; mitigated by short caching and fallback to simpler summarization.

- Vector store in-memory vs. product: For a hackathon demo, an in-memory VectorStore is fast to develop and easy to reset. In production, move to a managed vector DB (Pinecone, Weaviate, Qdrant) for persistence and multi-instance sharing.

- Multi-provider TTS with fallback: Improves resilience (Gemini TTS preferred), but adds complexity: voice mismatch across providers. Strategy: prefer single provider for a full podcast to avoid voice inconsistency; for per-line fallback, keep provider tags in filenames.

- Caching (script & audio): Keeps demo responsive. Production would need global cache (S3 + Redis) and proper eviction policies.

- Audio concatenation via `ffmpeg`: pragmatic, robust approach. If serverless or constrained env, consider streaming TTS that supports multi-speaker output or using a cloud audio assembly pipeline.

---

## Edge cases and how they are handled
- Empty or scanned PDFs: PyMuPDF extraction may return little text. The backend returns HTTP 400 when no extractable text exists. For scanned text, add OCR (Tesseract) in `processing.py`.
- Long documents (entire_pdf=true): Generation for many pages will be slow and costly. The system slices/limits script size and uses the embedder + retrieval to produce shorter, more useful scripts.
- Missing API keys: `/diagnostics` provides information about installed providers and availability; endpoints return 503 if required credentials are missing.
- ffmpeg missing: code falls back to returning first generated clip and informs the caller.
- Concurrency & rate limits: TTS providers may throttle; backend uses executors and thread pools (`_tts_executor`, `_bg_executor`) to keep the event loop responsive.

---

## Testing & quality gates
- Unit tests: add small tests for `processing.py` (text extraction), `vector_store.py` (add/search) and API endpoints using FastAPI TestClient.
- Integration tests: upload a small PDF fixture and call `/generate-audio` with `page_number=1` to ensure a file is written to `generated_audio/`.
- Linting & type checks: use `flake8`/`mypy` depending on project standards.
- CI: add pipeline to run tests and linting; gate merges on passing tests.

Suggested minimal test to add (pseudo):
- Test `process_pdf` returns non-empty chunks for a small known PDF.
- Test `POST /upload` saves the file and indexes chunks in the `VectorStore`.

---

## Scaling & productionization notes
- Vector DB: replace in-memory store with a managed vector DB for persistence and multi-AZ availability.
- Storage: move `document_library` and `generated_audio` to cloud object storage (S3, GCS) and serve via CDN.
- Audio pipeline: offload TTS jobs to background workers (Celery/RQ) with retries and job status endpoints.
- Observability: capture metrics for request latency, TTS provider latencies, cache hit rates; add structured logs and tracing.
- Security: ensure credentials are injected via environment with least privilege, rotate keys, and avoid storing secrets in repo.

---

## Security considerations
- Validate uploaded filenames (code already uses `Path(filename).name` to avoid path traversal).
- Rate-limit upload and generation endpoints to limit abuse and cost.
- Sanitize user-provided text before embedding or sending to LLM to avoid prompt injection-based data leaks.
- Store PII carefully; if storing user documents or outputs, provide retention policies and encryption at rest.

---

## Common interview questions and strong answers

Q: What does `POST /generate-audio` do? Walk me through it.
A: It accepts text or a file+page reference (or entire PDF). If entire PDF is requested, the server extracts the entire text. It uses `_gemini_script` to build a narration or two-speaker script and caches the script. For single-speaker it synthesizes one audio file. For two-speaker, it tries multi-speaker TTS where possible; otherwise it splits the script into labeled lines, synthesizes each line, optionally concatenates clips with `ffmpeg`, computes chapter metadata using `ffprobe`, caches the result, and returns the public `/audio/...` URL.

Q: How do you ensure the generated audio lines up with the source content and is not hallucinated?
A: The code uses semantic retrieval (`VectorStore`) to extract and supply the best-grounded snippets to the LLM for script/insights generation; we also design LLM prompts to ask for grounded outputs and use citations from retrieved snippets. For high-stakes cases, we'd restrict LLM generation to shorter, more conservative summarization and always include citations.

Q: How would you scale for production?
A: Replace in-memory vector store with a managed vector DB (Pinecone/Weaviate/Qdrant), move assets to cloud object storage and serve through a CDN, add background workers for TTS jobs with durable queues, add autoscaling and rate limiting, and implement better cost controls for LLM/TTS calls.

Q: What happens if Gemini TTS fails?
A: The backend implements `_synthesize_with_fallback` which tries a configured order of providers (gemini -> google -> edge_tts -> hf_dia -> pyttsx3). If all fail, an error is returned. For production, show fallback to hosted TTS or queue a retry.

Q: How would you test the end-to-end pipeline reliably?
A: Use small deterministic PDF fixtures and mock/stub TTS providers to return deterministic audio. Unit-test chunking, vector additions, and search. Add integration tests that use a local (or ephemeral) vector DB and a mocked LLM/TTS.

Q: What are the main risks and mitigations?
A:
- Cost: Guard LLM/TTS usage, cache script & audio, cap sizes. Use usage quotas and monitoring.
- Hallucination: Provide retrieval-grounded inputs, use conservative prompts, include citations.
- Availability: Multi-provider strategy and job queues for retries.
- Security: restrict file types, scanning, and implement rate limits.

---

## Example interview demo scenarios
- Demo 1: Upload a short research paper and generate a 3–5 minute two-speaker podcast.
  - Show the generated script (cached), show per-part audio URLs, and play audio in frontend player with chapter markers.
- Demo 2: Use `/insights` to show how the system produces 3–5 key takeaways and supporting citations.
- Demo 3: Show diagnostics (`/diagnostics`) to explain provider state and fallbacks.

---

## Shortlist of follow-ups / improvements (candidate action items)
- Add OCR pipeline for scanned PDFs (Tesseract or cloud OCR).
- Add durable job queue & worker pool for long-running TTS jobs.
- Add S3-backed storage with signed URLs and CDN.
- Replace in-memory vector store with managed vector DB for scale.
- Add role-based access control (RBAC) and quotas per user/org.
- Add integration tests & CI pipeline.

---

## Where to click in the repo during an interview
- `backend/main.py` — show the generate-audio orchestration and caching.
- `backend/processing.py` — show how PDFs are chunked and why chunk size matters.
- `frontend/pdf-reader-ui/src/components/PodcastStudio.tsx` — demo UI playback and chapter display.
- `api/generate-audio.py` — show a serverless example demonstrating adaptation to Vercel.

---

If you want, I can:
- Create a short slide deck summarizing these points for a 5–10 minute interview demo.
- Add minimal unit tests (upload + index + generate-audio mock) and a small CI workflow.

Files created:
- `interview/README.md` — this file (detailed interview guide and Q&A)

---

Completion summary: The `interview/README.md` is added to the repository with architecture, code walkthroughs, run instructions, design trade-offs, edge cases, and a set of interview Q&A that covers typical technical and product questions.
