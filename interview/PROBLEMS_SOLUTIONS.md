# DocaCast PROBLEMS & SOLUTIONS — Engineering Retrospective

A real-world account of challenges encountered during development and how they were overcome.

---

## Problem 1: Multi-Speaker Audio Synthesis is Non-Trivial

### The Challenge
**Initial vision**: Convert a PDF into a podcast with two hosts having a natural conversation.

**Naive approach**:
1. Extract text from PDF.
2. Use TTS to read it aloud.
3. Done!

**Reality check**: 
- No TTS provider has native two-speaker support (besides Gemini).
- If we split the text and run TTS twice (female voice, male voice), concatenating clips is lossy (timing gaps, voice inconsistencies).
- Speaker labels need to be programmatically added to the text before TTS.

### Solution

**Multi-layer approach**:

1. **Step 1: LLM Script Generation**
   - Send raw PDF text to Gemini with a prompt requesting a two-speaker dialogue.
   - Gemini generates: `Speaker 1: [dialogue]\nSpeaker 2: [response]\nSpeaker 1: [reply]`
   - Script is cached to avoid re-running the LLM.

2. **Step 2: Speaker Line Parsing**
   - Use regex to parse the script: `^(?P<label>Speaker\s*[12]|Alex|Jordan):\s*(?P<text>.+)$`
   - Handle label variations (the LLM might say "Speaker A" or "Jordan" instead of "Speaker 1").
   - Build list of tuples: `[(speaker, dialogue_text), ...]`

3. **Step 3: Multi-Speaker TTS (Gemini Speech)**
   - If available, send the **entire script** with speaker labels to Gemini's multi-speaker TTS.
   - Gemini parses labels and assigns voices automatically.
   - Result: fluid, natural-sounding podcast with proper interruptions and timing.

4. **Step 4: Fallback Per-Line Synthesis**
   - If Gemini TTS unavailable, synthesize each line separately:
     - Speaker 1 line → call Google TTS with voice "en-US-Neural2-C" → save to `/audio/part_000.mp3`
     - Speaker 2 line → call Google TTS with voice "en-GB-Neural2-B" → save to `/audio/part_001.mp3`
     - Repeat for all lines.
   - Concatenate all clips using `ffmpeg concat`.

5. **Step 5: Chapter Metadata**
   - Use `ffprobe` to measure duration of each audio clip.
   - Compute start_ms and end_ms for each chapter.
   - Return chapters to frontend so users can seek by speaker.

### Code example

```python
# Step 1: Generate script
script = _gemini_script(text, podcast=True, two_speakers=True)
# Result: "Speaker 1: Welcome to this podcast.\nSpeaker 2: Excited to listen!\n..."

# Step 2: Parse script
lines = []
for raw_line in script.splitlines():
    m = re.match(r"^(?P<label>Speaker\s*[12]|Alex|Jordan):\s*(?P<text>.+)$", raw_line, re.IGNORECASE)
    if m:
        speaker = normalize_speaker_name(m.group("label"))
        text = m.group("text")
        lines.append((speaker, text))
# Result: [("Speaker 1", "Welcome to..."), ("Speaker 2", "Excited to listen!"), ...]

# Step 3: Try multi-speaker TTS first
try:
    filename, url = _synthesize_speech(
        script,
        provider_override="gemini",  # Use multi-speaker if available
        ...
    )
    return {"url": url}
except:
    pass

# Step 4: Fallback to per-line synthesis
filenames = []
for speaker, text in lines:
    voice = voice_map[speaker]  # Map speaker to voice (e.g., Speaker 1 → Charon)
    filename, _ = _synthesize_speech(text, voice=voice, ...)
    filenames.append(filename)

# Step 5: Concatenate and compute chapters
concatenate_with_ffmpeg(filenames, output="podcast.mp3")
chapters = compute_chapters_with_ffprobe(filenames)
return {"url": "/audio/podcast.mp3", "chapters": chapters}
```

### Trade-offs
- **Pro**: works reliably; multi-layer fallback ensures something always works.
- **Con**: per-line synthesis is slower (per-line latency adds up); possible voice inconsistencies at clip boundaries.

**Optimization** (future): stream TTS directly to a single output buffer (avoid per-line saves).

---

## Problem 2: Script Caching Invalidation

### The Challenge
**Observation**: Generating scripts is expensive (2-4 seconds per Gemini API call). If the same page is requested multiple times, we re-run Gemini each time.

**Initial attempt**: Store scripts in a global dict with a hash key.

**Problem**: How do we invalidate caches? 
- If the user re-uploads the PDF with changes, the script cache is stale.
- If a parameter changes (e.g., `two_speakers` flag flipped), should we regenerate?
- Hard to know when to clear the cache without manual intervention.

### Solution

**Signature-based cache key**:
```python
script_key = "|".join([
    _hash_short(text[:1000]),      # Only use first 1000 chars (long PDFs vary)
    f"p{1 if podcast else 0}",     # Podcast mode flag
    f"ts{1 if two_speakers else 0}",  # Two-speaker mode flag
    f"ep{1 if entire_pdf else 0}", # Entire PDF flag
    req.accent or "-",              # Accent (e.g., en-GB)
    req.style or "-",               # Style (e.g., male)
    req.expressiveness or "-",      # Expressiveness level
])
script = _script_cache.get(script_key)
if script is None:
    script = _gemini_script(...)    # Generate and cache
    _script_cache[script_key] = script
```

**Rationale**:
- **Text hash** (first 1000 chars): captures the content. If content changes significantly, hash changes → cache miss.
- **Flags**: each configuration change (podcast mode, accent, etc.) gets a unique key.
- **Lazy invalidation**: caches are never explicitly cleared; they're naturally replaced when parameters change.

### Trade-offs
- **Pro**: simple, works well for typical usage patterns.
- **Con**: caches grow unbounded if many unique (text, flag) combinations are requested; no TTL (cache persists until server restart).

**Production improvement**: add Redis with TTL (e.g., 1 hour expiry).

---

## Problem 3: TTS Provider Failures and Rate Limiting

### The Challenge
**Observation**: Each TTS provider has limitations:
- **Gemini**: might hit API rate limits (quota exceeded).
- **Google Cloud**: expensive; quota might be low in free tier.
- **Edge-TTS**: sometimes slow, occasional timeouts.
- **HF Dia**: model loading latency on first use.
- **pyttsx3**: lower quality, offline but slow.

**Real scenario**: 10 concurrent requests for audio generation, all hit Gemini TTS at the same time → rate limit error → all 10 requests fail.

### Solution

**Graceful fallback chain**:

```python
def _synthesize_with_fallback(text, base, voice, accent, style):
    pref = os.getenv("TTS_PROVIDER", "").lower().strip()
    
    # If provider is explicitly set, use ONLY that
    if pref in ["edge_tts", "hf_dia", "pyttsx3", "google", "gemini"]:
        order = [pref]
    else:
        # Default order: prioritize free & fast, fallback to paid
        order = ["gemini", "google", "edge_tts", "hf_dia", "pyttsx3"]
    
    last_err = None
    for provider in order:
        try:
            return _synthesize_speech(text, voice=voice, accent=accent, style=style,
                                     deterministic_basename=base, provider_override=provider)
        except Exception as e:
            last_err = e
            print(f"[TTS] Provider {provider} failed: {e}")
            continue
    
    # All providers failed
    if last_err:
        raise last_err
```

**Key behaviors**:

1. **Per-provider retry**: If Gemini fails, immediately try Google (no delay).
2. **Explicit provider selection**: Env var `TTS_PROVIDER=google` forces Google TTS (useful for load balancing across providers).
3. **Deterministic output**: the basename is tagged with the provider (e.g., `tts_hash_gemini.mp3`, `tts_hash_google.mp3`). This ensures we don't mix clips from different providers in a single podcast.

### Deployment configuration

**Example**: if Gemini is rate-limited during peak hours:
```bash
# Redirect to Google Cloud TTS
export TTS_PROVIDER=google
```

**Example**: to spread load across providers (requires some orchestration):
```python
# Load-balancer logic: alternate between providers
import hashlib
user_id = request.headers.get("X-User-ID", "default")
provider_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
provider = ["gemini", "google", "edge_tts"][provider_hash % 3]
os.environ["TTS_PROVIDER"] = provider
```

### Trade-offs
- **Pro**: maximal resilience; if one provider fails, the app still works.
- **Con**: potential voice inconsistency across fallbacks (Gemini voice ≠ Google voice).

---

## Problem 4: ffmpeg Concatenation with Mixed Audio Formats

### The Challenge
**Observation**: In the per-line synthesis fallback, each line might be synthesized by a different provider:
- Speaker 1 line → Gemini TTS → WAV file (sample rate 24 kHz)
- Speaker 2 line → Google TTS → MP3 file (sample rate 24 kHz)
- Speaker 1 line → Edge-TTS → MP3 file (sample rate 22.05 kHz)

Concatenating these directly results in audio artifacts (sample rate mismatches, codec issues).

### Solution

**Re-encode to uniform format**:

```python
import subprocess

filelist_path = _audio_dir / f"{deterministic_base}_files.txt"
with open(filelist_path, 'w', encoding='utf-8') as f:
    for clip_file in clip_files:
        f.write(f"file '{clip_file.name}'\n")

# Use ffmpeg to concatenate and re-encode to MP3 (uniform format)
ffmpeg_cmd = [
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
    '-i', str(filelist_path),
    '-c:a', 'libmp3lame',  # MP3 codec
    '-b:a', '160k',        # 160 kbps bitrate (good quality)
    '-ar', '44100',        # 44.1 kHz sample rate (standard)
    str(final_path)
]

result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, cwd=str(_audio_dir))
if result.returncode != 0:
    # ffmpeg failed; fallback to first clip
    return {"url": clip_urls[0], "note": "concatenation failed"}
```

**Key flags**:
- `-f concat`: use FFmpeg's concat demuxer (handles multiple input files).
- `-c:a libmp3lame`: specify MP3 encoder.
- `-b:a 160k`: bitrate (higher = better quality, larger file).
- `-ar 44100`: resample to 44.1 kHz (standard CD quality).

### Trade-offs
- **Pro**: robust, handles mixed input formats/sample rates gracefully.
- **Con**: re-encoding adds latency (~1-2 seconds); slight quality loss (negligible for podcasts).

**Optimization**: if all clips are already MP3 at the same sample rate, use `-acodec copy` (no re-encoding, instant).

---

## Problem 5: Vector Store Scalability

### The Challenge
**Observation**: In-memory `VectorStore` works great for 100s of documents, but what about 1000s?

**Concrete issue**:
- 1000 PDFs × 50 chunks/PDF = 50,000 vectors.
- Each vector: 384 dimensions × 8 bytes (float32) = 3 KB.
- Total: ~150 MB of embeddings (manageable).
- Search latency: O(50,000) = ~50 ms per search (acceptable).

**Future problem**:
- 100,000 PDFs = 5M chunks = 15 GB embeddings (still fits in RAM).
- Search: O(5M) = ~5 seconds per search (slow, unusable).
- Can't deploy on AWS Lambda (128 MB limit).

### Solution (for hackathon)

**Stay with in-memory** for now, but document the upgrade path:

```python
# Current: in-memory
class VectorStore:
    def __init__(self):
        self.embeddings = np.empty((0, 384))
        
    def search(self, query_emb, k=5):
        scores = np.dot(self.embeddings, query_emb)  # O(n)
        return top_k_results
```

**Production migration plan**:

```python
# Future: Pinecone (managed vector DB)
import pinecone

pinecone.init(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone.Index("docacast-index")

# Add documents
index.upsert(vectors=[
    (doc_id, embedding, {"text": chunk_text, "filename": ...})
    for doc_id, embedding in zip(ids, embeddings)
])

# Search
results = index.query(query_embedding, top_k=5)
```

**Why Pinecone?**
- Fully managed (no ops overhead).
- Serverless (pay per query).
- 10M+ vectors supported.
- Sub-100ms search latency.
- Supports hybrid search (text + semantic).

### Trade-offs
- **Current**: simple, sufficient for 1000s of PDFs.
- **Future**: move to Pinecone when document corpus grows.

---

## Problem 6: PDF Extraction Variability

### The Challenge
**Observation**: not all PDFs extract text equally well:
1. **Well-formatted PDFs** (e.g., academic papers): text extraction is perfect.
2. **Scanned PDFs** (images): PyMuPDF extracts nothing (need OCR).
3. **PDFs with unusual encodings**: extraction might produce mojibake or missing text.
4. **PDFs with embedded fonts**: occasional character replacement.

**Real scenario**: A user uploads a scanned PDF, `/generate-audio` is called, backend extracts 0 characters, returns HTTP 400 ("No extractable text").

### Solution

**Three-tier fallback approach**:

1. **Tier 1: Direct extraction** (current)
   ```python
   doc = fitz.open(filename)
   text = page.get_text("text")
   if text.strip():
       return process_chunks(text)
   ```

2. **Tier 2: Fallback to block extraction** (if needed)
   ```python
   blocks = page.get_text("blocks")  # Get text blocks
   text = "\n".join([b[4] for b in blocks if b[4]])  # Extract text from blocks
   ```

3. **Tier 3: OCR** (for scanned PDFs) - **not implemented in hackathon**
   ```python
   # Use Tesseract or Google Cloud Vision
   import pytesseract
   pil_image = convert_pdf_page_to_image(page)
   text = pytesseract.image_to_string(pil_image)
   ```

**Validation**:

```python
def process_pdf(file_path):
    doc = fitz.open(file_path)
    all_chunks = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Try direct extraction
        text = page.get_text("text").strip()
        if not text:
            # Fallback to block extraction
            blocks = page.get_text("blocks")
            text = "\n".join([b[4] for b in blocks if b[4]]).strip()
        
        # If still empty, skip page
        if not text:
            print(f"Warning: Page {page_num+1} extracted no text")
            continue
        
        # Process chunks
        chunks = _chunk_text(text)
        all_chunks.extend(chunks)
    
    if not all_chunks:
        raise ValueError("PDF extracted no text; may be scanned or corrupted")
    
    return all_chunks
```

### Trade-offs
- **Pro**: robust handling of various PDF formats.
- **Con**: OCR tier not yet implemented; need external service (cost, latency).

---

## Problem 7: API Key Security

### The Challenge
**Observation**: The project requires multiple API keys:
- `GOOGLE_API_KEY` (Gemini, TTS)
- `ADOBE_CLIENT_ID` (PDF Embed)
- `GEMINI_API_KEY` (optional separate key)
- `TAVILY_API_KEY` (web search, if enabled)
- `BING_SEARCH_API_KEY` (web search, if enabled)

**Risk**: keys hard-coded in code, checked into Git, leaked to GitHub.

### Solution

**Environment-based configuration**:

```python
# backend/main.py
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

# Load keys from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not set; exiting")

genai.configure(api_key=GOOGLE_API_KEY)
```

**.env file** (local development, **not committed**):
```env
GOOGLE_API_KEY=abc123...
ADOBE_CLIENT_ID=xyz789...
```

**.gitignore**:
```
.env
credentials/
__pycache__/
*.pyc
```

**Deployment** (Vercel):
```
Dashboard → Project → Settings → Environment Variables
[+] Add environment variable
Key: GOOGLE_API_KEY
Value: abc123... (Vercel encrypts at rest)
```

### Trade-offs
- **Pro**: keys not in code; separate per environment (dev, prod).
- **Con**: require manual setup on each deployment; risk of typos.

**Future improvement**: use a secrets management service (AWS Secrets Manager, HashiCorp Vault).

---

## Problem 8: Audio Generation Latency

### The Challenge
**Observation**: A typical audio generation request takes 7-20 seconds:
- PDF extraction: 100ms
- Embedding: 200ms
- Gemini script generation: 2-4s
- TTS synthesis (per line × 3-5 lines): 6-15s
- ffmpeg concat: 1-2s

**UX problem**: user waits 20 seconds, unclear if request is stuck or processing.

### Solution

**Progress indication + caching**:

1. **Client-side feedback**:
   ```typescript
   // Frontend (React)
   const [isLoading, setIsLoading] = useState(false);
   const [status, setStatus] = useState("");
   
   const generateAudio = async () => {
       setIsLoading(true);
       setStatus("Extracting text...");
       try {
           const response = await fetch(`${API}/generate-audio`, {
               method: "POST",
               body: JSON.stringify({...})
           });
           setStatus("Generating audio...");
           const { url } = await response.json();
           setStatus("Done!");
           setAudioUrl(url);
       } finally {
           setIsLoading(false);
       }
   };
   ```

2. **Server-side optimizations**:
   - **Script caching**: reduces 2-4s (Gemini) to ~0ms.
   - **Audio caching**: reduces per-line TTS to ~0ms if cached.
   - **Parallel TTS**: submit multiple per-line TTS calls concurrently (reduce 15s → 5s).

3. **Example with caching**:
   ```python
   # First request: 20 seconds (cold)
   POST /generate-audio {filename: "paper.pdf", page_number: 1}
   → Script cache miss, TTS cache miss → generate fresh → 20s
   
   # Second request (same page): <500ms (warm)
   POST /generate-audio {filename: "paper.pdf", page_number: 1}
   → Script cache hit, TTS cache hit → return cached URL → 0.5s
   ```

### Trade-offs
- **Pro**: caching makes repeated requests fast.
- **Con**: first request is still slow; need to set expectations (show "generating" spinner).

---

## Problem 9: Handling Concurrent TTS Calls

### The Challenge
**Observation**: If 10 users request audio generation simultaneously, the backend makes 30-50 concurrent TTS API calls. This risks:
1. Rate limiting from TTS provider.
2. Memory exhaustion (buffering all responses).
3. Event loop blocking (if not managed correctly).

### Solution

**Thread pool for I/O bound work**:

```python
from concurrent.futures import ThreadPoolExecutor

# Create thread pool
_tts_executor = ThreadPoolExecutor(max_workers=int(os.getenv("TTS_WORKERS", "2")))
_bg_executor = ThreadPoolExecutor(max_workers=int(os.getenv("BG_WORKERS", "4")))

# In async endpoint
@app.post("/generate-audio")
async def generate_audio(req: GenerateAudioRequest):
    loop = asyncio.get_running_loop()
    
    # Offload TTS to thread pool (non-blocking)
    filename, url = await loop.run_in_executor(
        _tts_executor,
        lambda: _synthesize_with_fallback(...)
    )
    return {"url": url}
```

**How it works**:
- Main event loop (FastAPI) stays responsive; handles new requests.
- TTS calls run in separate threads (ThreadPoolExecutor).
- Max workers = 2, so at most 2 concurrent TTS calls per instance.
- Additional requests queue up (FIFO).

### Trade-offs
- **Pro**: simple, effective; doesn't block the event loop.
- **Con**: limited concurrency per instance; for higher throughput, deploy multiple backend instances + load balancer.

---

## Problem 10: Debugging and Observability

### The Challenge
**Observation**: When something goes wrong (e.g., "TTS failed", "audio file not found"), it's hard to diagnose:
1. Which TTS provider was used?
2. What was the latency breakdown?
3. Was it a cache hit or miss?
4. What was the actual error?

### Solution

**Structured logging**:

```python
import logging
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

@app.post("/generate-audio")
async def generate_audio(req: GenerateAudioRequest):
    start_ts = time.time()
    try:
        log.info(f"[generate-audio] start podcast={req.podcast} two_speakers={req.two_speakers}")
        
        # ... processing ...
        
        elapsed = time.time() - start_ts
        log.info(f"[generate-audio] success url={url} elapsed={elapsed:.1f}s")
        return {"url": url}
    except Exception as e:
        elapsed = time.time() - start_ts
        log.error(f"[generate-audio] error={str(e)} elapsed={elapsed:.1f}s")
        raise

# Output
# [2025-11-06 10:30:45] [generate-audio] start podcast=true two_speakers=true
# [2025-11-06 10:30:47] [generate-audio] script ready len=450 two_speakers=true
# [2025-11-06 10:30:49] [generate-audio] single-speaker done provider=gemini url=/audio/tts_abc123_gem.mp3 elapsed=3.5s
```

**Diagnostics endpoint**:

```python
@app.get("/diagnostics")
def diagnostics():
    """Return info about TTS provider availability."""
    return {
        "provider": os.getenv("TTS_PROVIDER", "auto"),
        "gemini_available": genai is not None,
        "google_tts_available": google_tts is not None,
        "edge_tts_available": edge_tts is not None,
        "pyttsx3_available": pyttsx3 is not None,
        "ffmpeg": check_ffmpeg_available(),
        "ffprobe": check_ffprobe_available(),
    }
```

### Trade-offs
- **Pro**: easy to debug issues, identify bottlenecks.
- **Con**: logs can get verbose; need log aggregation service for production.

---

## Summary: Key Learnings

| Problem | Solution | Key Insight |
|---------|----------|-------------|
| Multi-speaker audio | LLM → script → per-line TTS → ffmpeg concat | Flexibility beats simplicity; fallbacks essential |
| Script caching | Signature-based keys | Lazy invalidation works better than explicit |
| TTS provider failures | Graceful fallback chain | Always have Plan B, C, D |
| Format mismatches | Re-encode with ffmpeg | Standardization > raw speed |
| Vector store scalability | In-memory for now, Pinecone for future | Good enough beats perfect |
| PDF extraction variability | Tier-1/2/3 fallback | Robustness requires optionality |
| API key security | Environment variables + .gitignore | Never check secrets into Git |
| Latency UX | Caching + progress feedback | Perception beats reality |
| Concurrency | Thread pool executor | I/O-bound tasks shouldn't block event loop |
| Debugging | Structured logging + diagnostics endpoint | Observability is a feature, not afterthought |

---

## Future Challenges (Beyond Hackathon)

1. **OCR for scanned PDFs**: add Tesseract or Google Vision API.
2. **Multi-language support**: localize prompts and voice selection.
3. **Persistent vector DB**: migrate from in-memory to Pinecone / Weaviate.
4. **Cost optimization**: implement request-level billing, metering per user.
5. **User authentication**: add OAuth2 or API key-based auth.
6. **Data privacy**: implement encryption at rest, PII filtering.
7. **Performance at scale**: load testing, CDN, auto-scaling.

---

For more details on implementation, see `CODE_OVERVIEW.md` and `TECH_STACK.md`.
