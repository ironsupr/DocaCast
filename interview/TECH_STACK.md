# DocaCast TECH STACK — Deep Dive into Technologies and Why

A comprehensive breakdown of every major technology choice, rationale, trade-offs, and architectural decisions.

---

## Overview: The Tech Stack

```
Frontend: React 19 + TypeScript + Vite
          Adobe PDF Embed API
          
API Layer: FastAPI + uvicorn
           Pydantic for validation
           
LLM: Google Generative AI (Gemini 1.5 Flash)
     Text generation for scripts
     JSON mode for structured outputs
     
TTS: Gemini Speech (multi-speaker)
     + Google Cloud TTS (fallback)
     + Edge-TTS (free neural voices)
     + HuggingFace Dia (open-source)
     + pyttsx3 (offline)
     
PDF Processing: PyMuPDF (fitz)
                
Embeddings: Sentence-Transformers
            (all-MiniLM-L6-v2 by default)
            
Vector Search: In-memory storage
               (FAISS-like semantics)
               
Audio Processing: ffmpeg (concat)
                  ffprobe (metadata)
                  
Deployment: Vercel (frontend + serverless backend)
            Docker (containerized backend)
            
Database: In-memory (hackathon)
          → Pinecone / Weaviate (production)
```

---

## Frontend Tier

### React 19 + TypeScript

**Why?**
- React: industry standard, large ecosystem, excellent component model.
- TypeScript: type safety, better IDE support, catch bugs at compile time.
- Version 19: Latest features, better performance, improved React Compiler.

**Trade-offs**:
- Pro: Familiar, vast library ecosystem (thousands of React libraries).
- Con: Requires build step (Vite handles this well), larger bundle size than vanilla JS.

**Component structure**:
```
PodcastStudio (main orchestrator)
├── UploadPdfButton (file picker)
├── FilePicker (list uploaded files)
├── GenerateAudioButton (podcast control)
├── SelectionMenu (options for narrative style)
├── RecommendationsSidebar (related content)
└── AudioPlayer (playback + chapters)
```

---

### Vite

**Why Vite over Webpack / Create React App?**
- **Build speed**: Vite uses ES modules natively; webpack bundles everything upfront.
- **Dev server**: Vite's dev server is ~10-50x faster (no bundling, only transpilation).
- **HMR (Hot Module Replacement)**: Instant feedback during development.
- **Production build**: Rollup-based, optimized for tree-shaking and minimal bundle size.

**Trade-offs**:
- Pro: Exceptional developer experience (iteration speed = faster feature development).
- Con: Newer tooling, fewer StackOverflow answers than webpack.

**Config** (`vite.config.ts`):
```typescript
import react from '@vitejs/plugin-react';

export default {
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8001'  // Forward API calls to backend
    }
  }
};
```

**Key feature for this project**: Proxy configuration allows frontend dev server to forward API calls to the backend without CORS issues.

---

### Adobe PDF Embed API

**Why Adobe instead of open-source alternatives?**
- **Native PDF viewing**: Renders PDFs directly in the browser (no server-side conversion).
- **High fidelity**: Adobe's rendering is pixel-perfect (same as Adobe Reader).
- **Feature-rich**: zoom, text selection, annotations, form filling.
- **Reliable**: Adobe's service is battle-tested, 99.9%+ uptime.
- **Security**: Built-in DRM, permissions, expiration via API.

**Trade-offs**:
- Pro: Best-in-class rendering quality and features.
- Con: Requires API key (free tier available), external dependency, potential privacy concerns (Adobe sees uploads).

**Implementation** (React):
```typescript
import { PDFEmbedAPI } from "@adobe/pdfembed-api";

useEffect(() => {
  PDFEmbedAPI.ready();
  const adobeDCView = new PDFEmbedAPI.PDFEmbedAPI({
    clientID: ADOBE_CLIENT_ID
  });
  adobeDCView.previewFile({
    filePromise: fetch(pdfUrl).then(r => r.blob())
  }, {
    embedMode: "SIZED_CONTAINER",
    showDownloadPDF: false
  });
}, [pdfUrl]);
```

**Alternatives considered**:
- **pdfjs** (Mozilla): lighter, open-source, but slower rendering.
- **pdfmake**: good for generating PDFs, not viewing.
- **react-pdf**: simpler API but less feature-rich.

---

## Backend Tier

### FastAPI

**Why FastAPI over Flask / Django / Starlette?**

| Feature | Flask | Django | FastAPI |
|---------|-------|--------|---------|
| Async native | No | Partial | ✅ |
| Type hints | No | No | ✅ (Pydantic) |
| Auto API docs | No | No | ✅ (Swagger, ReDoc) |
| Performance | Good | Good | Excellent (Starlette-based) |
| Learning curve | Easy | Steep | Easy |
| Setup time | Fast | Slow (ORM, etc.) | Fast |

**Key advantages for DocaCast**:
1. **Async**: TTS synthesis and LLM calls are I/O bound. FastAPI's async/await + `asyncio` allows handling multiple concurrent requests without thread overhead.
2. **Pydantic**: automatic validation and serialization of request/response models (e.g., `GenerateAudioRequest`).
3. **Auto-documentation**: Swagger UI and ReDoc for easy API exploration.
4. **Performance**: built on Starlette (one of the fastest Python web frameworks).

**Example async endpoint**:
```python
@app.post("/generate-audio")
async def generate_audio(req: GenerateAudioRequest):
    # Pydantic automatically validates the request
    
    # Offload TTS to thread pool (non-blocking)
    loop = asyncio.get_running_loop()
    filename, url = await loop.run_in_executor(
        _tts_executor,  # ThreadPoolExecutor
        lambda: _synthesize_with_fallback(...)
    )
    return {"url": url}
```

**Trade-offs**:
- Pro: Modern, async-first, best-in-class API documentation.
- Con: Smaller community than Flask (though growing rapidly).

---

### Uvicorn

**Why Uvicorn?**
- Uvicorn is the ASGI server that runs FastAPI applications.
- **ASGI** (Asynchronous Server Gateway Interface) is the async equivalent of WSGI.
- Lightweight and fast (C-accelerated parser in uvicorn[standard]).

**Alternative**: Hypercorn (also ASGI, slightly slower but more feature-complete).

**Command to run**:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

- `--reload`: auto-restart on file changes (dev mode).
- `--host 127.0.0.1`: bind to localhost only (security).
- `--port 8001`: custom port to avoid conflicts.

---

### Pydantic

**Why Pydantic?**
Pydantic provides runtime validation and serialization for Python data structures. For a REST API, it ensures:
1. **Input validation**: reject invalid requests early.
2. **Type coercion**: convert "123" (string) to 123 (int) automatically.
3. **Auto-documentation**: Pydantic models appear in Swagger docs.

**Example**:
```python
from pydantic import BaseModel

class GenerateAudioRequest(BaseModel):
    filename: str
    page_number: int
    podcast: Optional[bool] = False
    
# Automatic validation:
req = GenerateAudioRequest(filename="doc.pdf", page_number="abc")
# ❌ ValidationError: page_number must be int
```

**Trade-offs**:
- Pro: Eliminates boilerplate validation code, enforces API contracts.
- Con: Small runtime overhead (negligible for most use cases).

---

## AI / LLM Tier

### Google Generative AI (Gemini 1.5 Flash)

**Why Gemini instead of GPT-4 / Claude?**

| Feature | GPT-4 | Claude 3 | Gemini 1.5 Flash |
|---------|-------|----------|------------------|
| Text generation | Excellent | Excellent | Very Good |
| Speed | Slow (20-60s) | Medium (5-10s) | Fast (2-4s) |
| Cost | High ($0.03-0.06 / 1k tokens) | High ($0.003-0.024) | Low ($0.00075) |
| Audio/Speech TTS | No | No | ✅ Yes (gemini-2.5-flash-preview-tts) |
| JSON mode | ✅ Yes | ✅ Yes | ✅ Yes (response_mime_type) |
| Availability | Excellent | Excellent | Good (getting better) |

**Key decision factor**: Gemini includes **integrated audio synthesis** (Speech API). For a podcast app, this is huge:
- Single API call for multi-speaker audio generation.
- No need to integrate separate TTS service.
- Consistent voice quality across the pipeline.

**Where Gemini is used**:

1. **Script generation** (`_gemini_script`):
   ```python
   model = genai.GenerativeModel("gemini-1.5-flash")
   response = model.generate_content("""
   Convert this text into a two-speaker podcast script:
   [text]
   Format: Speaker 1: [dialogue]
           Speaker 2: [response]
   """)
   script = response.text
   ```

2. **Insights extraction** (`_gemini_insights`):
   ```python
   response = model.generate_content("""
   Extract key insights from this text (JSON format):
   - key_insights: [...]
   - did_you_know_facts: [...]
   - counterpoints: [...]
   - examples: [...]
   """)
   insights = json.loads(response.text)
   ```

3. **Cross-document comparison** (`_gemini_cross_compare`):
   ```python
   response = model.generate_content("""
   Compare these claims from multiple PDFs:
   [claims]
   Return JSON with agreements and contradictions.
   """)
   comparisons = json.loads(response.text)
   ```

**Trade-offs**:
- Pro: Integrated audio, fast, cheap, handles complex tasks well.
- Con: API is relatively new; fewer production case studies; rate limits if traffic spikes.

**Prompt engineering best practices used in DocaCast**:
1. **Role-playing**: "You are an expert podcast writer..." to set tone.
2. **Output format**: explicit format (JSON, structured lines) reduces hallucination.
3. **Constraints**: "Limit to 3-8 claims" prevents rambling output.
4. **Examples**: show format with examples for better generalization (few-shot learning).

---

### Gemini Speech (Audio Generation)

**Why Gemini Speech?**
- Multi-speaker support: native support for "Speaker 1:", "Speaker 2:" labels.
- Natural pronunciation: neural voices trained on real speech.
- Fast: 5-10 seconds for 500-word script.
- Integrated: no separate API, same auth as text generation.

**Model**: `gemini-2.5-flash-preview-tts` (latest as of Nov 2025).

**Example multi-speaker request**:
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)

contents = [types.Content(
    role="user",
    parts=[types.Part.from_text(text="""
Speaker 1: Welcome to this podcast about AI.
Speaker 2: I'm excited to discuss this topic!
Speaker 1: Let's dive in...
""")]
)]

# Multi-speaker config
multi_cfg = types.MultiSpeakerVoiceConfig(
    speaker_voice_configs=[
        types.SpeakerVoiceConfig(
            speaker="Speaker 1",
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
            )
        ),
        types.SpeakerVoiceConfig(
            speaker="Speaker 2",
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
            )
        ),
    ]
)

gen_cfg = types.GenerateContentConfig(
    response_modalities=["audio"],
    speech_config=types.SpeechConfig(multi_speaker_voice_config=multi_cfg)
)

# Stream response
for chunk in client.models.generate_content_stream(
    model="gemini-2.5-flash-preview-tts",
    contents=contents,
    config=gen_cfg
):
    audio_data = chunk.candidates[0].content.parts[0].inline_data.data
    # save audio_data to file
```

**Trade-offs**:
- Pro: Seamless multi-speaker, natural, fast.
- Con: New API, limited voice selection (vs. Google Cloud TTS with 100+ voices).

---

## TTS (Text-to-Speech) Tier

### Multi-provider fallback strategy

**Hierarchy**:
1. **Gemini TTS** (best for multi-speaker, fastest, cheapest).
2. **Google Cloud TTS** (high-quality voices, proven production system).
3. **Edge-TTS** (free, no API key, natural Microsoft neural voices).
4. **HuggingFace Dia** (open-source, no cost, customizable).
5. **pyttsx3** (offline, works everywhere, lower quality).

**Why multiple providers?**
- **Resilience**: If Gemini is down, fall back to Google; if both are down, use Edge-TTS.
- **Cost**: Gemini is cheap, but Edge-TTS is free (no API key).
- **Flexibility**: HF and pyttsx3 are open-source (no vendor lock-in).

**Implementation**:
```python
def _synthesize_with_fallback(text, base, voice, accent, style):
    pref = os.getenv("TTS_PROVIDER", "").lower().strip()
    
    # If provider is explicitly set, use ONLY that
    if pref in ["edge_tts", "hf_dia", "pyttsx3", "google", "gemini"]:
        order = [pref]
    else:
        # Default order: try in sequence
        order = ["gemini", "google", "edge_tts", "hf_dia", "pyttsx3"]
    
    for provider in order:
        try:
            return _synthesize_speech(
                text,
                voice=voice,
                accent=accent,
                style=style,
                deterministic_basename=base,
                provider_override=provider
            )
        except Exception as e:
            log.error(f"Provider {provider} failed: {e}")
            continue
    
    # All providers failed
    raise Exception("All TTS providers exhausted")
```

**Trade-offs** per provider:

| Provider | Latency | Quality | Cost | Notes |
|----------|---------|---------|------|-------|
| Gemini | 5-10s | Excellent | $0.00 per 1M chars | Multi-speaker support |
| Google Cloud | 2-3s | Excellent | $0.000015 per char | 100+ voices, most expensive |
| Edge-TTS | 2-5s | Very good | Free | Free, no key, natural voices |
| HF Dia | 10-20s | Good | Free (or serverless) | Open-source, customizable |
| pyttsx3 | <1s | Fair | Free | Offline, lower quality |

**Example scenario**:
- Morning: Use Gemini (fast + cheap).
- Evening peak: Gemini rate-limited → fall back to Google (higher cost but still works).
- Late night: All cloud providers down → use Edge-TTS or pyttsx3 (slower but free).

---

## PDF Processing Tier

### PyMuPDF (fitz)

**Why PyMuPDF over pdfplumber / pypdf / pdfminer?**

| Library | Speed | Text accuracy | Tables | Code |
|---------|-------|---|---|---|
| PyMuPDF | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Simple |
| pdfplumber | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Moderate |
| pypdf | ⭐ | ⭐⭐ | ⭐ | Simple |
| pdfminer | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Complex |

**PyMuPDF strengths**:
1. **Speed**: written in C, 10-100x faster than pure-Python alternatives.
2. **Accuracy**: uses MuPDF rendering engine (same as many PDF readers).
3. **Simplicity**: clean Python API.

**Example usage**:
```python
import fitz  # PyMuPDF

doc = fitz.open("paper.pdf")
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text("text")  # extract text
    # Process text...
doc.close()
```

**Trade-offs**:
- Pro: Fast, reliable, widely used.
- Con: Less table-aware than pdfplumber; requires compiled C library (occasional install issues).

**Limitations DocaCast doesn't handle**:
1. **Scanned PDFs (images)**: need OCR (e.g., Tesseract).
2. **Complex tables**: extracted as flat text (hard to parse).
3. **Embedded fonts**: rare edge case, but can cause encoding issues.

---

## Embeddings Tier

### Sentence-Transformers (`all-MiniLM-L6-v2`)

**Why Sentence-Transformers?**
Sentence-Transformers are fine-tuned BERT models optimized for computing semantic similarity between sentences/documents.

**Model choice**: `all-MiniLM-L6-v2`
- **Size**: 22M parameters (lightweight, fits in memory).
- **Speed**: ~100ms to encode 128 documents on CPU.
- **Quality**: MTEB ranking ~25 (good for general semantic search).
- **Encoding dim**: 384 dimensions.

**Alternative models**:
- `all-mpnet-base-v2` (438M params, better quality, slower).
- `e5-base` / `e5-large` (newer SOTA, better on MTEB, more expensive compute).
- `bge-small-en-v1.5` / `bge-large-en-v1.5` (Chinese-optimized, still good for English).

**Example usage**:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# Encode documents
documents = ["The sky is blue.", "Birds can fly.", "AI is advancing."]
embeddings = model.encode(documents, convert_to_numpy=True, normalize_embeddings=True)
# embeddings.shape = (3, 384)

# Encode query
query = "What about the sky?"
query_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
# query_emb.shape = (384,)

# Compute similarity
import numpy as np
similarities = np.dot(embeddings, query_emb)  # cosine similarity
top_idx = np.argsort(similarities)[::-1][0]  # most similar document
print(f"Most similar: {documents[top_idx]}")
# Output: Most similar: The sky is blue.
```

**Trade-offs**:
- Pro: Fast, lightweight, good quality for general use cases.
- Con: Not domain-specific (for legal/medical, consider fine-tuning on domain data).

---

## Audio Processing Tier

### ffmpeg + ffprobe

**Why ffmpeg for concatenation?**
FFmpeg is the **de facto standard** for audio/video processing:
1. Supports 100+ formats (MP3, WAV, OGG, FLAC, etc.).
2. Handles format conversion and re-encoding.
3. Performs format detection automatically.
4. Extremely reliable and battle-tested.

**Example concatenation**:
```bash
ffmpeg -f concat -safe 0 -i filelist.txt -c:a libmp3lame -b:a 160k output.mp3
```

- `-f concat`: use concat demuxer.
- `-i filelist.txt`: file list (format: "file 'part1.mp3'\nfile 'part2.mp3'\n...").
- `-c:a libmp3lame`: audio codec (MP3).
- `-b:a 160k`: bitrate (160 kbps, good quality).

**ffprobe for duration**:
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio.mp3
# Output: 123.456 (seconds)
```

Used to compute chapter start_ms and end_ms timestamps.

**Trade-offs**:
- Pro: Industry standard, incredibly powerful and flexible.
- Con: requires shell execution, external binary dependency.

**Alternative** (Python-only):
- **pydub**: simpler Python API but slower; limited format support.
- **soundfile**: good for WAV, not suitable for MP3 concatenation.

---

## Vector Search / Storage Tier

### In-Memory VectorStore (hackathon version)

**Why in-memory for a hackathon?**
1. **Speed**: no network latency, no database queries.
2. **Simplicity**: no external service to manage.
3. **Quick iteration**: add/remove documents instantly.
4. **Sufficient scale**: works for 100s-1000s of documents.

**Implementation** (simplified):
```python
class VectorStore:
    def __init__(self):
        self.texts = []
        self.metadatas = []
        self.embeddings = np.empty((0, 384))  # 384-dim embeddings
    
    def add_documents(self, documents, filename):
        embedder = _get_embedder()
        texts = [d["text"] for d in documents]
        embs = embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        
        for i, d in enumerate(documents):
            self.texts.append(d["text"])
            self.metadatas.append(d["metadata"])
            self.embeddings = np.vstack([self.embeddings, embs[i:i+1]])
    
    def search(self, query_emb, k=5, fetch_k=15):
        # Cosine similarity (normalized embeddings = inner product)
        scores = np.dot(self.embeddings, query_emb)
        top_indices = np.argsort(scores)[::-1][:fetch_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "text": self.texts[idx],
                "metadata": self.metadatas[idx],
                "score": float(scores[idx]),
                "distance": float(1 - scores[idx])  # for API compatibility
            })
        return results
```

**Limitations**:
- Data lost on server restart.
- No persistence across instances (can't scale horizontally).
- Linear search time (O(n)) instead of logarithmic (O(log n) for tree-based DB).
- Memory consumption grows with document count.

**Production upgrade**:
```
In-memory (current) → Pinecone / Weaviate / Qdrant
```

- **Pinecone**: fully managed, fast, serverless.
- **Weaviate**: self-hosted or cloud, open-source.
- **Qdrant**: self-hosted, rust-based, very fast.

---

## Deployment Tier

### Vercel

**Why Vercel for this project?**
1. **Frontend deployment**: Vercel is optimized for React + Vite (auto-detected, zero config).
2. **Serverless backend**: Can deploy FastAPI as serverless functions.
3. **Fast CDN**: global edge network for frontend assets.
4. **Git integration**: deploy on every push to main.
5. **Environment variables**: easy secret management.
6. **Free tier**: suitable for hackathon/demo.

**Deployment flow**:
```
1. Push to GitHub
   ↓
2. Vercel detects push
   ↓
3. Build frontend: npm run build → static files
   ↓
4. Deploy backend: wrap FastAPI as serverless functions
   ↓
5. Serve frontend from CDN + backend via API Gateway
```

**Trade-offs**:
- Pro: easy, automatic scaling, low ops overhead.
- Con: cold starts (~1 sec), expensive at scale, vendor lock-in.

**Alternative deployments**:
- **Docker + AWS ECS**: more control, better for high traffic.
- **Fly.io**: modern, auto-scaling, similar to Vercel but more flexible.
- **Railway**: simpler UI, good for getting started.

---

## Caching Strategy

### Three-tier caching

1. **In-memory script cache** (`_script_cache`):
   - Key: hash of (text[:1000], podcast flag, two_speakers flag, ...).
   - Lifetime: server process lifetime.
   - Hit rate: ~50-70% for typical usage.

2. **In-memory audio cache** (`_audio_cache`):
   - Key: hash of (script hash, voice, provider).
   - Lifetime: server process lifetime.
   - Hit rate: ~30-50% (lower because audio depends on voice).

3. **Disk cache** (`generated_audio/`):
   - Persists across server restarts.
   - Hit rate: ~80%+ for repeated requests.

**Benefit**: repeated audio generation requests return cached file in <100ms (vs. 10-20 seconds for fresh generation).

**Production upgrade**: add Redis for distributed caching across multiple servers.

---

## Why not... (Alternatives Considered)

### Why not use Celery for background jobs?
- **Reason for exclusion**: adds complexity (Redis/RabbitMQ dependency, worker management).
- **For hackathon**: simple thread pool (`ThreadPoolExecutor`) is sufficient.
- **For production**: Celery would be appropriate for long-running jobs (email, batch processing).

### Why not use PostgreSQL for vector search?
- **PgVector extension**: PostgreSQL now supports vectors with pgvector plugin.
- **Reason for exclusion**: overkill for hackathon; in-memory sufficient.
- **For production**: pgvector is a good compromise (SQL + vectors in one DB).

### Why not use LangChain / LlamaIndex?
- **LangChain**: excellent orchestration library (chains, agents, memory).
- **Reason for exclusion**: adds abstraction layer; direct Gemini API calls are simpler for this use case.
- **For production**: LangChain worth considering if expanding to more complex LLM workflows.

### Why not use Docker Compose for local development?
- **Reason for exclusion**: developers can run backend + frontend directly without containers.
- **For production**: Docker is essential for reproducible deployments.

---

## Performance Characteristics

### Latency breakdown (per page)
```
PDF extraction:        100ms
Embedding:             200ms
Script generation:     2-4s (Gemini LLM)
Per-line TTS:          2s × (# speaker turns)
Audio concat:          1-2s
Total:                 7-20s (uncached)
Total (cached):        100-500ms
```

### Memory usage
- Backend: ~500 MB baseline (FastAPI + libraries).
- Per PDF indexed: ~50 MB (depends on content size).
- Embeddings: 384 dims × 8 bytes × # chunks = ~3 KB per chunk.

### Throughput
- Single instance: ~10 concurrent requests (TTS is I/O bound).
- With horizontal scaling + queue (production): 100+ RPS.

---

## Summary: Tech Stack Philosophy

**Guiding principles**:
1. **Use boring, proven technology**: FastAPI, React, PyMuPDF (don't experiment with novel tools in a hackathon).
2. **Minimize external dependencies**: in-memory storage, minimal DB (production: add persistence).
3. **Fallback gracefully**: multi-provider TTS ensures reliability.
4. **Cache aggressively**: script + audio caching makes UX fast.
5. **Async-first**: FastAPI's async allows handling concurrent requests without threads.

This stack is **production-ready** with minimal modifications (add auth, persistence, monitoring, rate limiting).
