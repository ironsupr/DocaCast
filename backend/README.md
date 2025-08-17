# Backend (FastAPI)

This backend powers PDF upload, chunking, semantic search, Gemini insights, and Text-to-Speech narration with providers: Gemini Speech (google-genai), Google Cloud TTS, Edge TTS (free), Hugging Face Dia-1.6B, or offline pyttsx3.

## Quick start

1. Create a virtual environment and install deps

- pip install -r requirements.txt

2. Configure env vars

- Copy `.env.example` to `.env` and fill in values as needed (at minimum choose a TTS provider below).

3. Run the full API (from repo root or backend folder)

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

Default preference is Gemini Speech for the most natural multi-speaker results. You can force a provider via env `TTS_PROVIDER` (when set, the backend will only use that provider and not silently fall back):

- hf_dia — Hugging Face Inference API for Dia-1.6B (requires HUGGINGFACE_API_TOKEN). Outputs MP3.
- pyttsx3 — Offline/local TTS. Outputs WAV.
- google — Google Cloud Text-to-Speech. Outputs MP3/OGG/WAV.
- gemini — Google AI Studio (google-genai) Speech. Outputs MP3/OGG/WAV depending on model.
- edge_tts — Microsoft Edge TTS (free). Outputs MP3.

Provider envs:

- HF_DIA_MODEL (default nari-labs/Dia-1.6B)
- GOOGLE_API_KEY (for Gemini insights and narration scripting)
- GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON) or GOOGLE_TTS_SERVICE_ACCOUNT_JSON (inline JSON)
- GOOGLE_TTS_VOICE_A, GOOGLE_TTS_VOICE_B (default voices for two-speaker podcasts)
- GOOGLE_TTS_AUDIO_ENCODING (MP3 | OGG_OPUS | LINEAR16; default MP3)
- EDGE_TTS_VOICE_A, EDGE_TTS_VOICE_B, EDGE_TTS_VOICE_DEFAULT (voice names)
- GEMINI_API_KEY (falls back to GOOGLE_API_KEY)
- GEMINI_TTS_MODEL (default gemini-2.5-pro-preview-tts)
- GEMINI_VOICE_A, GEMINI_VOICE_B (default Charon/Puck for dialogues)

See `.env.example` for a complete list.

## Two-person podcast mode

Use POST /generate-audio with `{ podcast: true, two_speakers: true }`. The server will:

- Summarize and script a natural Alex/Jordan dialogue with Gemini
- Synthesize each line with two distinct voices (Gemini recommended)
- Concatenate parts with ffmpeg and return:
  - `url`: merged audio file
  - `parts`: array of per-line clips (fallback)
  - `chapters`: metadata with speaker, text, and timestamps

## Gemini Speech (google-genai)

You can synthesize speech with Gemini's preview TTS model via `google-genai`.

Setup:

1) Install dependency (already in requirements.txt, otherwise):

   pip install google-genai

2) Environment variables:

- `TTS_PROVIDER=gemini`
- `GEMINI_API_KEY=...` (falls back to `GOOGLE_API_KEY` if set)
- Optional: `GEMINI_TTS_MODEL=gemini-2.5-pro-preview-tts`
- Optional default voices for multi-speaker:
  - `GEMINI_VOICE_A=Charon`
  - `GEMINI_VOICE_B=Aoede`

3) Restart the backend.

Notes:
- If your script text includes labeled lines like `Speaker 1:` and `Speaker 2:` (or `Alex:`/`Jordan:`), the backend will request multi-speaker synthesis when using Gemini.
- For single-speaker, provide plain text; for two-speaker podcasts, the server already generates labeled dialogue.
