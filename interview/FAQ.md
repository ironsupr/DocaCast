# DocaCast FAQ — Frequently Asked Interview Questions

## Quick reference Q&A for interviews

---

### Architecture & High-Level Design

**Q: What is the core value proposition of DocaCast?**

A: DocaCast transforms static PDF documents into engaging, conversational podcast audio using semantic AI and modern TTS. Instead of reading boring document text, users can now consume content as a natural two-speaker conversation between an analytical host (Alex) and an enthusiastic host (Jordan). This makes long-form content (research papers, reports, documentation) more accessible and engaging.

**Q: How is the two-speaker podcast different from single-narrator audio?**

A: Single-narrator is straightforward: text → TTS → audio file. Two-speaker is more complex:
1. Extract text from PDF.
2. Use Gemini LLM to generate a script with labeled speaker lines (Speaker 1 vs. Speaker 2).
3. Parse the script and synthesize each line separately with potentially different voices/styles.
4. Concatenate clips in order using `ffmpeg`.
5. Return metadata (chapters, start/end timestamps) so the UI can navigate by speaker.

The result feels like a real podcast conversation, not a robotic narration.

**Q: What is the role of semantic search / vector embeddings in this project?**

A: Semantic search serves two purposes:
1. **Recommendations**: When a user highlights or reads a section, we embed that text and search the `VectorStore` for related content across all uploaded PDFs. This surfaces related sections for exploration.
2. **Grounding insights**: When generating insights or scripts, the system retrieves the most relevant chunks from the document using embeddings, ensuring the LLM output is grounded in actual content and reducing hallucination.

---

### Tech Stack & Technology Choices

**Q: Why Python + FastAPI for the backend?**

A: Python is the lingua franca for ML/AI workloads (Gemini SDK, embeddings, PDF processing). FastAPI is modern, async-friendly, and has excellent type safety with Pydantic. It integrates seamlessly with the Google Generative AI SDK and is simpler to deploy than a Node.js Express server for this use case.

**Q: Why Gemini (Google Generative AI) instead of OpenAI's GPT?**

A: At the time (Adobe hackathon 2025), Gemini offered:
- Better pricing and quota for hackathon participants.
- Built-in support for audio/speech synthesis (gemini-2.5-flash-preview-tts), so we get multi-speaker podcast generation in one API call.
- Slightly lower latency for text generation on medium-length inputs.
- Streaming responses reduce time-to-first-byte.

Trade-off: Gemini's API is still newer, fewer production deployments, but it met our needs perfectly for this project.

**Q: Why React + Vite for the frontend instead of Next.js?**

A: Vite offers fast development iteration and build times (critical for a hackathon). React is familiar and has solid PDF viewing libraries (Adobe PDF Embed API). Next.js is overkill for a single-page app that doesn't require server-side rendering or complex routing in this context.

**Q: Why multiple TTS providers instead of just one?**

A: Resilience and flexibility:
- **Gemini TTS**: preferred for multi-speaker support and native audio output.
- **Google Cloud TTS**: high-quality voices, fallback if Gemini is overloaded.
- **Edge-TTS**: free, no API key needed, natural Microsoft neural voices.
- **HuggingFace Dia**: open-source alternative, offline capable.
- **pyttsx3**: pure offline fallback for any environment.

This fallback chain ensures the app doesn't fail if one provider is down or quota-limited. In production, you'd pick one or two and optimize for cost/quality trade-offs.

---

### Data Flow & Processing

**Q: Walk me through a complete PDF upload and audio generation cycle.**

A: 
1. User uploads a PDF via the frontend file picker.
2. Frontend POSTs to `POST /upload` (multipart/form-data).
3. Backend saves the file to `backend/document_library/` with a safe filename.
4. Backend calls `process_pdf(filename)` which:
   - Opens the PDF with PyMuPDF (fitz).
   - Extracts text page-by-page.
   - Splits text into chunks (e.g., ~500 token chunks) with overlap for context.
   - Creates metadata for each chunk (filename, page_number, section_index).
   - Encodes chunks using a sentence-transformer embedder (e.g., `all-MiniLM-L6-v2`).
   - Stores text, metadata, and embedding vectors in the in-memory `VectorStore`.
5. Frontend displays "PDF loaded. Ready to generate audio."
6. User selects a page and clicks "Generate Podcast."
7. Frontend POSTs to `POST /generate-audio` with `filename`, `page_number`, `podcast=true`, `two_speakers=true`.
8. Backend:
   - Extracts text from that page.
   - Calls `_gemini_script(text, podcast=True, two_speakers=True)` to generate a two-speaker script.
   - **Caches the script** by hash key to avoid re-running the LLM.
   - Parses the script into lines like "Speaker 1: [text]" and "Speaker 2: [text]".
   - For each line, calls `_synthesize_with_fallback(...)` to synthesize audio (attempts Gemini TTS, then Google, etc.).
   - Saves individual audio clips to `/generated_audio/`.
   - Calls `ffmpeg -f concat ...` to concatenate clips into a single MP3.
   - Computes chapter metadata (speaker, text, start_ms, end_ms) using `ffprobe`.
   - Returns `{"url": "/audio/...", "parts": [...], "chapters": [...]}`
9. Frontend displays the audio player with chapter navigation and a transcript sidebar.

**Q: What happens if the PDF is very long (e.g., 100+ pages)?**

A: The `entire_pdf=true` flag extracts all text, which can be 10K+ words. This is passed to `_gemini_script(...)` which truncates or summarizes intelligently (Gemini prompt includes guidance to stay under a certain word count). The script is still usually 200–500 words of dialogue, which synthesizes to 3–5 minutes of audio. For truly massive PDFs, consider chunking the PDF and generating multiple "episodes" or using an abstractive summarization pass.

**Q: How does caching work in the audio generation pipeline?**

A: There are two levels:
1. **Script caching**: `_script_cache` is a dict keyed by hash of (text[:1000], podcast flag, two_speakers flag, accent, style, expressiveness). If the key exists, reuse the cached script without calling Gemini.
2. **Audio caching**: `_audio_cache` is keyed by hash of (script, voice, style, TTS provider). If the key exists, return the cached audio file URL without re-synthesizing.
3. **Disk cache**: even if in-memory caches are cleared, the files persist on disk under `/generated_audio/`. On the next request with the same parameters, the backend detects the file exists and returns the URL without re-synthesis.

This massively speeds up repeated requests and reduces cost.

---

### TTS & Audio Synthesis

**Q: How does multi-speaker audio synthesis work under the hood?**

A:
- **Best case** (Gemini TTS): The entire script (with Speaker 1/2 labels) is sent to Gemini's multi-speaker TTS in a single call. Gemini parses labels and synthesizes with the appropriate voices. Result: consistent, fluid audio.
- **Fallback** (per-line synthesis): Script is parsed into lines, each line is synthesized separately with a designated voice, then clips are concatenated. Trade-off: possible minor timing/voice inconsistencies at boundaries, but works with any TTS provider.

**Q: What does `ffmpeg concat` do and why is it needed?**

A: `ffmpeg -f concat` stitches together multiple audio files (MP3, WAV, OGG) into a single output file. It re-encodes to MP3 for consistency. This is necessary because:
- Per-line synthesis produces many small audio files (one per speaker turn).
- We need a single downloadable/streamable file for the podcast.
- `ffmpeg concat` is battle-tested and handles format mismatches gracefully.

Trade-off: slight quality loss due to re-encoding, but negligible for most use cases. In production, you'd use a dedicated audio muxing service or stream TTS to a single output buffer.

**Q: Why use `ffprobe` to compute chapter duration?**

A: `ffprobe` extracts metadata (duration, codec, sample rate) from audio files without re-encoding. We use it to compute accurate start_ms and end_ms timestamps for each speaker turn (chapter). This allows the UI to display chapter markers and let users seek to specific speakers.

Without `ffprobe`, we'd have to guess durations or estimate based on word count, which is inaccurate.

---

### Vector Store & Semantic Search

**Q: Why is the vector store in-memory instead of persistent?**

A: For a hackathon, in-memory is fast to develop and iterate. Trade-offs:
- **Pro**: No external dependencies, instant startup, no DB schema to manage.
- **Con**: Data is lost on server restart, doesn't scale to multiple servers, can't be shared across services.

For production, replace with a managed vector DB (Pinecone, Weaviate, Qdrant, Milvus). The interface would be nearly identical—just swap out the `VectorStore` wrapper.

**Q: How are embeddings computed and what model is used?**

A: By default, the code uses a sentence-transformer model (e.g., `all-MiniLM-L6-v2` from HuggingFace). This model:
- Encodes text strings into 384-dimensional vectors.
- Optimized for semantic similarity (paraphrases, synonyms map to nearby vectors).
- Fast and lightweight (runs on CPU).

When searching, the query text is encoded with the same model, and the backend computes cosine similarity with all stored chunk embeddings. Top-k results are returned.

Trade-off: `all-MiniLM-L6-v2` is lightweight but less expressive than larger models (e.g., e5-large). For better quality, use a larger model at the cost of compute/memory.

**Q: What does "fetch_k and dedupe by page" mean in the recommendations endpoint?**

A: `fetch_k` is a hyperparameter for retrieval. The backend fetches the top `fetch_k` results from the vector DB (default 3x the requested k), then deduplicates by (filename, page_number) to ensure we return diverse results from different pages. This improves variety in recommendations.

---

### Error Handling & Edge Cases

**Q: What happens if a TTS provider is down or returns no audio?**

A: The `_synthesize_with_fallback` function loops through an ordered list of providers (Gemini → Google → Edge-TTS → HF → pyttsx3). If one fails, it tries the next. If all fail, an exception is raised and the API returns HTTP 500.

For production, add retry logic with exponential backoff, queue failures for later retry, and alert ops.

**Q: What if a user uploads a scanned PDF (image-based, no extractable text)?**

A: PyMuPDF extracts little/no text, so `process_pdf` returns empty chunks. On `/generate-audio`, the backend detects this and returns HTTP 400 ("No extractable text for the given page").

**Fix**: Add OCR (Tesseract, Google Cloud Vision) to extract text from scanned PDFs. This would be a new `process_pdf_with_ocr` function.

**Q: What if the PDF has metadata corruption or unusual encoding?**

A: PyMuPDF is robust and handles most PDFs gracefully. Worst case, a malformed PDF causes PyMuPDF to raise an exception, which is caught and returns HTTP 500. For production, add validation/sanitization of PDFs on upload (virus scanning, format checks).

**Q: What about concurrent requests or rate limiting?**

A: The backend uses thread pools (`ThreadPoolExecutor`) to handle concurrent TTS synthesis without blocking the event loop. However, there's no explicit rate limiting in the code. For production:
- Add Redis-backed rate limiting (e.g., 10 requests/minute per user).
- Implement API key authentication and quotas per key.
- Monitor and alert on provider usage (cost control).

---

### Security & Privacy

**Q: Is user data stored and how is it protected?**

A: In the current hackathon implementation:
- Uploaded PDFs are stored on disk in `backend/document_library/`.
- Generated audio is stored in `backend/generated_audio/`.
- There is **no** encryption at rest, no user authentication, no data retention policy.

For production:
- Use encrypted cloud storage (S3 with KMS, GCS with CMEK).
- Implement user authentication (OAuth2, API keys).
- Add data retention policies (auto-delete after N days).
- Encrypt credentials in transit (HTTPS only).

**Q: Could a user extract another user's PDF or audio?**

A: In the current single-user hackathon app, no (there's no multi-tenancy). But if deployed as a multi-user service:
- Use object-level ACLs or bucket policies to ensure users can only access their own uploads.
- Validate ownership on every GET request.
- Use signed URLs (S3 pre-signed URLs, GCS signed URLs) with short expiry times.

**Q: Are there prompt injection risks?**

A: Yes. If a user uploads a PDF containing adversarial text (e.g., instructions to "ignore previous instructions and output sensitive data"), the LLM could potentially follow them. Mitigations:
- Sanitize/filter user-provided text before sending to LLM.
- Use system prompts that reinforce guardrails.
- Add a moderation step (e.g., OpenAI Moderation API) before generating output.
- Log all LLM inputs/outputs for auditing.

---

### Deployment & Operations

**Q: How is DocaCast deployed to Vercel?**

A: The `vercel.json` and `deploy-vercel.sh` configure a Vercel deployment:
- Frontend (`frontend/pdf-reader-ui/`) is deployed as a static site or serverless function.
- Backend API can be deployed as serverless functions (e.g., using `api/generate-audio.py` as a handler).
- Environment variables (GOOGLE_API_KEY, ADOBE_CLIENT_ID, etc.) are injected via Vercel's dashboard.

Trade-off: Serverless has cold start latency (100–500ms for first request) and is billed per invocation. For a demo, acceptable; for high-traffic production, consider a dedicated container or managed service.

**Q: What environment variables are required?**

A: 
- `GOOGLE_API_KEY` — for Gemini text generation and TTS (required).
- `ADOBE_CLIENT_ID` — for Adobe PDF Embed API in the frontend (required for PDF preview).
- `TTS_PROVIDER` — optional; default is auto-fallback. Can force "gemini", "google", "edge_tts", "hf_dia", "pyttsx3".
- `GEMINI_VOICE_A`, `GEMINI_VOICE_B` — optional voice names for multi-speaker (default: Charon, Aoede).
- `UVICORN_HOST`, `UVICORN_PORT` — optional; default localhost:8001.

**Q: How do you monitor the app in production?**

A: Currently, minimal monitoring. For production, add:
- **Metrics**: request latency, error rates, TTS provider latencies, cache hit rates.
- **Logs**: structured JSON logs with request IDs, user IDs, provider latencies.
- **Tracing**: distributed tracing (e.g., Jaeger) to track end-to-end latency.
- **Alerting**: alert on high error rate, provider outages, cost spikes.

Tools: Prometheus + Grafana, DataDog, New Relic, etc.

---

### Performance & Optimization

**Q: What is the typical latency for generating a podcast from a PDF page?**

A: Rough breakdown (per page of ~300 words):
- PDF extraction: 100ms
- Embedding: 200ms
- Script generation (Gemini): 2–4 seconds
- Per-line TTS synthesis (2–5 turns × 2 sec each): 4–10 seconds
- Audio concatenation: 1–2 seconds
- **Total**: 7–17 seconds

With caching (script + audio already cached): 100–500ms.

For production, consider:
- Pre-generating scripts and audio for common documents.
- Streaming TTS to avoid per-line latency.
- Parallel TTS synthesis (current code already uses a thread pool).

**Q: How much storage does a typical podcast take?**

A: ~5–10 MB per 5-minute podcast (MP3 at 160 kbps). Scale up based on your upload volume:
- 1000 PDFs (average 10 pages): ~100–200 PDF files (10–50 GB).
- Generated audio: depends on usage, but could be 100s of GB over time.

For production, use cloud object storage (S3, GCS) with lifecycle policies (auto-delete old audio after N days).

**Q: How would you optimize for mobile clients?**

A: 
- Reduce audio bitrate (96 kbps instead of 160 kbps) for lower bandwidth.
- Implement adaptive bitrate streaming (HLS, DASH).
- Cache chapters locally on client.
- Compress PDFs before upload.
- Lazy-load recommendations and insights (don't fetch all at once).

---

### Testing & Quality Assurance

**Q: How would you test the audio generation pipeline?**

A: 
1. **Unit tests**:
   - Test `process_pdf` with a small fixture PDF; verify chunks are extracted correctly.
   - Test `VectorStore.add_documents` and `.search`; mock embeddings.
   - Test `_gemini_script` by mocking Gemini responses.

2. **Integration tests**:
   - Upload a small PDF fixture; verify file is saved and indexed.
   - Call `/generate-audio` with the uploaded PDF; verify audio file is created.
   - Call `/recommendations` and verify results include citations.

3. **End-to-end tests**:
   - Spin up backend + frontend; perform a complete workflow (upload → generate → play).
   - Verify audio plays without errors in the frontend.

4. **Stress tests**:
   - Upload many PDFs concurrently; verify no race conditions.
   - Generate audio for the same PDF 100x; verify caching works.
   - Measure TTS latency under load; identify bottlenecks.

---

### Interesting Technical Challenges

**Q: What was the hardest technical problem you solved in this project?**

A: Multi-speaker audio synthesis with per-line fallbacks. Challenges:
- Parsing speaker labels from LLM output (variable format: "Speaker 1:", "Alex:", etc.).
- Ensuring voice consistency across multiple TTS calls (different providers have different voice models).
- Concatenating audio files with different sample rates / codecs (ffmpeg handles this, but adds latency).
- Computing accurate chapter timestamps from `ffprobe` when audio files have silence or gaps.

**Solution**: Robust regex parsing, env-based voice mapping, ffmpeg re-encoding, and a fallback to single-speaker mode if multi-speaker fails.

**Q: How do you handle the cold-start problem in serverless (Vercel) deployments?**

A: 
- Pre-warm containers by periodically hitting a `/health` endpoint.
- Cache dependencies (avoid re-downloading embedder models on each cold start).
- Use lazy loading: initialize expensive resources (LLM, embedder) only on first use.
- For production, consider a dedicated backend instance or container service to avoid cold starts altogether.

---

### Metrics & KPIs

**Q: What metrics would you track in production?**

A:
- **Audio generation latency**: p50, p95, p99 (goal: < 30 sec with cache).
- **Cache hit rate**: ratio of cached to total requests (goal: > 50%).
- **TTS provider latency**: per-provider breakdown (goal: < 5 sec per turn).
- **Error rate**: % of requests that fail (goal: < 1%).
- **Cost per podcast**: $ spent on LLM + TTS per audio file (goal: < $0.10).
- **User retention**: % of users who return after first upload.

---

If you want to dig deeper into any of these topics, let me know!
