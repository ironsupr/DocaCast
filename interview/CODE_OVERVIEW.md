# DocaCast CODE OVERVIEW — Key Files & Functions Explained

Quick reference guide to the most important files, functions, and their responsibilities.

---

## Backend (`backend/main.py`) — Orchestration & Endpoints

### Key endpoints

#### `POST /upload`
**What it does**: Accepts multiple PDF files, saves them, and indexes their content.

```python
@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
```

**Flow**:
1. Receive multipart/form-data with PDF files.
2. Iterate over files; validate filename (prevent path traversal).
3. Save to `backend/document_library/` with a safe name.
4. Call `process_pdf(filepath)` to extract, chunk, embed.
5. Call `store.add_documents(chunks, filename=safe_name)` to index into VectorStore.
6. Return `{"saved": [filename1, filename2, ...]}`

**Error handling**: If `process_pdf` fails for a file, log and skip; continue with remaining files.

---

#### `POST /generate-audio`
**What it does**: Generates audio (narration or podcast) from text or a PDF page.

```python
@app.post("/generate-audio")
async def generate_audio(req: GenerateAudioRequest):
```

**Request model**:
```python
class GenerateAudioRequest(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None
    podcast: Optional[bool] = False       # narrative style?
    two_speakers: Optional[bool] = None   # dual dialogue?
    accent: Optional[str] = None          # e.g. en-US, en-GB
    style: Optional[str] = None           # voice style
    speakers: Optional[Dict[str, str]] = None  # custom voice mapping
    entire_pdf: Optional[bool] = False    # all pages?
```

**Key flow** (simplified):
1. Extract text from request or file/page.
2. **Cache key**: hash of (text[:1000], podcast, two_speakers, accent, style, expressiveness).
3. Fetch cached script if exists; else call `_gemini_script(...)`.
4. **If not two-speaker**: single TTS call → one audio file → return URL.
5. **If two-speaker**: 
   - Parse script into lines (regex: "Speaker 1: [text]", "Speaker 2: [text]").
   - For each line, call `_synthesize_with_fallback(...)` to synthesize per-line audio.
   - Concatenate clips using `ffmpeg concat`.
   - Compute chapter metadata using `ffprobe`.
   - Return full podcast URL + parts + chapters.

**Caching layers**:
- In-memory `_script_cache`: keyed by script hash.
- In-memory `_audio_cache`: keyed by (script hash, voice, provider).
- Disk cache: if `/audio/{basename}.mp3` exists, reuse without re-synthesis.

**Error handling**: 
- Return 400 if no extractable text.
- Return 503 if TTS provider is overloaded.
- Return 500 if all TTS providers fail.

---

#### `POST /recommendations`
**What it does**: Find related content across all PDFs based on a query.

```python
@app.post("/recommendations")
async def recommendations(req: RecommendationRequest):
```

**Request**:
```python
class RecommendationRequest(BaseModel):
    text: Optional[str] = None        # explicit query
    filename: Optional[str] = None    # or query from a file
    page_number: Optional[int] = None
    k: int = 5                        # top-k results
    fetch_k: Optional[int] = None     # internal retrieval pool size
    min_score: Optional[float] = None # relevance threshold
    exclude_self: bool = True         # exclude same page from results?
```

**Flow**:
1. Determine query text (from explicit text, or aggregate chunks from filename+page).
2. Embed query using sentence-transformer.
3. Search `VectorStore` for top `fetch_k` results (default k×3).
4. De-duplicate by (filename, page_number) to ensure diverse results.
5. For each result, extract a 2–4 sentence snippet using the `_snippet_2to4_sentences` helper.
6. Return list of snippets with metadata: `{"snippet": str, "filename": str, "page_number": int, "distance": float, "score": float}`.

**Smart deduplication**: Avoid returning 5 snippets all from the same page; aim for cross-document diversity.

---

#### `POST /insights`
**What it does**: Generate high-level insights (key takeaways, facts, examples, inspirations, counterpoints) from a text or page.

```python
@app.post("/insights")
async def insights(req: InsightsRequest):
```

**Request**:
```python
class InsightsRequest(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None
    k: int = 5                  # context chunks to retrieve
    web: Optional[bool] = False # augment with web search?
    web_k: int = 3              # web sources
```

**Flow**:
1. Extract or retrieve text.
2. Retrieve top-k related chunks from the VectorStore for citations/grounding.
3. Optionally, call `_web_search(text[:300])` to fetch 3 web snippets (if `web=True`).
4. Call `_gemini_insights(text, citations, web_results)` to generate structured insights.
5. Return:
   ```json
   {
     "key_insights": [...],
     "did_you_know_facts": [...],
     "counterpoints": [...],
     "inspirations": [...],
     "examples": [...],
     "citations": [{filename, page_number, snippet}, ...],
     "web": [{title, url, snippet}, ...]
   }
   ```

**Key function**: `_gemini_insights(text, citations, web_results)` → calls Gemini with a structured prompt to extract insights and return JSON.

---

#### `POST /cross-insights`
**What it does**: Compare multiple PDFs to find agreements and contradictions.

```python
@app.post("/cross-insights")
async def cross_insights(req: CrossInsightsRequest):
```

**Request**:
```python
class CrossInsightsRequest(BaseModel):
    filenames: Optional[List[str]] = None  # if None, all PDFs
    max_per_doc: int = 6                   # max snippets per PDF
    deep: Optional[bool] = False           # use LLM to extract claims?
    force: Optional[bool] = False          # bypass caches?
    focus: Optional[str] = None            # optional topic focus
    include_claims: Optional[bool] = False # include extracted claims in response?
```

**Flow**:
1. Determine list of PDFs to analyze.
2. For each PDF, extract "claims" (key statements with page refs) using `_extract_doc_claims(filename, max_per_doc, deep)`.
   - If `deep=True`: use Gemini to extract factual claims.
   - If `deep=False`: return snippets from diverse pages.
3. Aggregate all claims.
4. Call `_gemini_cross_compare(all_claims, focus)` to identify:
   - Agreements: statements supported by 2+ PDFs.
   - Contradictions: conflicting statements.
5. Return:
   ```json
   {
     "agreements": [{statement, support: [{file, page}], quotes}, ...],
     "contradictions": [...],
     "notes": [...]
   }
   ```

---

### Key helper functions

#### `_gemini_script(text, podcast, accent, style, expressiveness, two_speakers) -> str`
**What it does**: Use Gemini to transform raw document text into a narration or two-speaker dialogue script.

**Logic**:
1. Build a dynamic prompt based on flags.
2. If `two_speakers=True`: ask for alternating "Speaker 1:" and "Speaker 2:" lines.
3. If `podcast=True` or `expressiveness` is set: ask for a more conversational, warm tone.
4. Include accent/style hints in the prompt to nudge the LLM (e.g., "Accent preference: en-GB.").
5. Call `genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)`.
6. Parse response and return the script text.

**Caching**: Script is cached by hash to avoid repeated LLM calls.

---

#### `_synthesize_with_fallback(text, base, voice, accent, style) -> (filename, url)`
**What it does**: Attempt TTS synthesis using an ordered fallback chain.

**Fallback order**:
1. Try `TTS_PROVIDER` if explicitly set (env var).
2. Else try: Gemini TTS → Google Cloud TTS → Edge-TTS → HF Dia → pyttsx3.
3. If all fail, raise an exception.

**For each provider**:
- Call `_synthesize_speech(...)` with `provider_override=provider`.
- If it succeeds, return (filename, url).
- If it fails, log and try next provider.

---

#### `_synthesize_speech(text, voice, fmt, accent, style, deterministic_basename, provider_override) -> (filename, url)`
**What it does**: Synthesize speech using a specific TTS provider.

**Key logic** (provider-specific):

**Gemini TTS** (preferred):
```python
client = genai_speech.Client(api_key=api_key)
contents = [genai_types.Content(...)]
# Build multi-speaker or single-speaker config
gen_cfg = genai_types.GenerateContentConfig(
    response_modalities=["audio"],
    speech_config=...
)
# Stream response and collect audio chunks
for chunk in client.models.generate_content_stream(model, contents, gen_cfg):
    # extract audio data and mime_type
```
- Supports multi-speaker via `MultiSpeakerVoiceConfig`.
- Returns audio in a MIME format (e.g., "audio/L16;rate=24000").
- Convert to WAV if needed using `_convert_to_wav(...)`.

**Google Cloud TTS**:
```python
client = google_tts.TextToSpeechClient()
response = client.synthesize_speech(input, voice, audio_config)
# response.audio_content contains MP3 bytes
```

**Edge-TTS**:
```python
communicate = edge_tts.Communicate(text, voice_name)
async for chunk in communicate.stream():
    if chunk["type"] == "audio": f.write(chunk["data"])
```

**pyttsx3** (offline):
```python
engine = pyttsx3.init()
engine.save_to_file(text, output_path)
engine.runAndWait()
```

---

#### `_convert_to_wav(audio_data, mime_type) -> bytes`
**What it does**: Convert raw audio data (L16 PCM) to a WAV file by prepending a WAV header.

**Logic**: Parse mime_type to extract sample rate and bits-per-sample; use `struct.pack` to build a WAV header; prepend header to audio data.

---

### Startup & caching

#### `@app.on_event("startup")`
**What it does**: On server startup, re-index any PDFs already on disk.

```python
@app.on_event("startup")
async def _startup_index_existing_pdfs():
    # Collect already-indexed filenames from store.metadatas
    # Scan document_library/ for new PDFs
    # For each new PDF, call process_pdf and store.add_documents
```

This ensures recommendations/insights work correctly after a server restart.

---

## Backend (`backend/processing.py`) — PDF Processing

#### `process_pdf(file_path: str) -> List[Dict[str, Any]]`
**What it does**: Extract text from a PDF, chunk it, and prepare data for embedding + storage.

```python
def process_pdf(file_path: str) -> List[Dict[str, Any]]:
    doc = fitz.open(file_path)
    chunks = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        # Split into overlapping chunks (e.g., 500 tokens with 50-token overlap)
        page_chunks = _chunk_text(text, chunk_size=500, overlap=50)
        for i, chunk in enumerate(page_chunks):
            chunks.append({
                "text": chunk,
                "metadata": {
                    "filename": Path(file_path).name,
                    "page_number": page_num + 1,
                    "section_index": i,
                    "section_title": extract_title(text) or f"Section {i+1}"
                }
            })
    doc.close()
    return chunks
```

**Chunk strategy**: 
- Split by sentence boundaries to avoid breaking mid-sentence.
- Overlap (e.g., last 50 tokens of chunk N = first 50 tokens of chunk N+1) to preserve context at boundaries.
- Typical chunk: 200–800 tokens (depends on `chunk_size` param).

**Why chunking?** Large documents wouldn't fit in a single embedding, and we want to support granular retrieval (find the most relevant section, not the whole PDF).

---

#### `_get_embedder() -> SentenceTransformer`
**What it does**: Load or return a cached embedder model.

```python
def _get_embedder():
    global _embedder_cache
    if _embedder_cache is None:
        _embedder_cache = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder_cache
```

**Model choice**: `all-MiniLM-L6-v2` is fast and lightweight (22M params), trained on semantic similarity. For better quality, use `all-mpnet-base-v2` (109M params) or newer models like `e5-base`.

---

## Backend (`backend/vector_store.py`) — Semantic Search

#### `class VectorStore`
**What it does**: In-memory storage of text chunks, metadata, and embeddings; supports similarity search.

```python
class VectorStore:
    def __init__(self):
        self.texts: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray = np.empty((0, embedding_dim))
    
    def add_documents(self, documents: List[Dict], filename: str = None):
        for doc in documents:
            self.texts.append(doc["text"])
            self.metadatas.append(doc["metadata"])
            # Embed and append to embeddings matrix
    
    def search(self, query_embedding, k=5, fetch_k=15):
        # Compute cosine similarity between query and all embeddings
        scores = np.dot(self.embeddings, query_embedding)  # inner product for normalized embeddings
        top_indices = np.argsort(scores)[::-1][:fetch_k]
        # Return top-k with text, metadata, score, distance
```

**Trade-offs**:
- In-memory: no I/O, but limited by RAM and not persistent.
- Uses FAISS-like approach (but simplified for hackathon).
- For production, replace with Pinecone, Weaviate, Qdrant, or FAISS with persistence.

---

## Frontend (`frontend/pdf-reader-ui/src/components/`)

### `PodcastStudio.tsx`
**What it does**: Main UI component that orchestrates the podcast generation workflow.

**Flow**:
1. Display file picker (via `<UploadPdfButton />`).
2. Display "Generate Podcast" button (via `<GenerateAudioButton />`).
3. Show audio player with chapters and transcript (custom player component).
4. Handle state: `isLoading`, `audioUrl`, `chapters`, `transcript`.
5. On generate-audio, call backend and display player.

---

### `GenerateAudioButton.tsx`
**What it does**: Button component that triggers `/generate-audio` POST request.

**Parameters**:
- `filename`: uploaded PDF filename.
- `pageNumber`: which page to generate (or all if entire_pdf=true).
- `podcastMode`: boolean for podcast style.
- `twoSpeakers`: boolean for two-speaker dialogue.

**On click**:
```typescript
const response = await fetch(`${API_BASE}/generate-audio`, {
  method: "POST",
  body: JSON.stringify({
    filename,
    page_number: pageNumber,
    podcast: podcastMode,
    two_speakers: twoSpeakers
  })
});
const { url, parts, chapters } = await response.json();
// Display audio player with chapters
```

---

### `UploadPdfButton.tsx`
**What it does**: File picker for uploading PDFs.

**On file select**:
```typescript
const formData = new FormData();
formData.append("files", file);
const response = await fetch(`${API_BASE}/upload`, {
  method: "POST",
  body: formData
});
const { saved } = await response.json();
setUploadedFile(saved[0]);
```

---

### `RecommendationsSidebar.tsx`
**What it does**: Display related content (recommendations) based on current page or selection.

**On mount or page change**:
```typescript
const response = await fetch(`${API_BASE}/recommendations`, {
  method: "POST",
  body: JSON.stringify({
    filename,
    page_number,
    k: 5
  })
});
const { results } = await response.json();
// Display list of snippets with file/page refs
```

---

## API Utilities (`api/generate-audio.py`)

#### `handler(request, response)`
**What it does**: Serverless handler for Vercel deployment; demonstrates how to adapt the FastAPI backend to a serverless environment.

**Key difference from FastAPI**:
- Single request-response cycle per invocation.
- No persistent connections or background tasks.
- Must explicitly handle CORS and headers.

**Simplified flow** (Vercel deployment):
```python
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Parse JSON from body
        # Call backend logic (or forward to a backend service)
        # Return response
```

---

## Configuration & Environment

### `.env` (backend)
```env
GOOGLE_API_KEY=<your-gemini-api-key>
GEMINI_API_KEY=<optional-separate-key>
ADOBE_CLIENT_ID=<your-adobe-embed-client-id>
TTS_PROVIDER=gemini  # or google, edge_tts, hf_dia, pyttsx3
GEMINI_VOICE_A=Charon    # speaker 1
GEMINI_VOICE_B=Aoede     # speaker 2
UVICORN_HOST=127.0.0.1
UVICORN_PORT=8001
```

### `.env` (frontend)
```env
VITE_ADOBE_CLIENT_ID=<your-adobe-embed-client-id>
VITE_API_BASE_URL=http://127.0.0.1:8001
```

---

## Dependencies & Imports

### Backend (`requirements.txt`)
```
fastapi
uvicorn[standard]
python-multipart
PyMuPDF  # fitz for PDF extraction
sentence-transformers  # embeddings
numpy
google-generativeai  # Gemini API
edge-tts  # free TTS
pyttsx3  # offline TTS
python-dotenv
```

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "react": "^19",
    "typescript": "^5",
    "vite": "^4"
  }
}
```

---

## Execution Flow Diagram

```
User uploads PDF
    ↓
POST /upload
    ↓
process_pdf()
    ├─ fitz.open() → extract text pages
    ├─ _chunk_text() → split into ~500-token chunks
    ├─ _get_embedder() → SentenceTransformer embed chunks
    └─ VectorStore.add_documents() → store text + metadata + vectors
    ↓
User clicks "Generate Podcast"
    ↓
POST /generate-audio (filename, page_number, podcast=true, two_speakers=true)
    ├─ Extract text from page
    ├─ _gemini_script() → LLM generates "Speaker 1: ... Speaker 2: ..." script
    ├─ Parse script → [(speaker, line), ...]
    ├─ For each line:
    │   └─ _synthesize_with_fallback() → TTS call → audio file
    ├─ ffmpeg concat → single podcast MP3
    ├─ ffprobe → compute chapter timestamps
    └─ Return {url, parts, chapters}
    ↓
Frontend receives audio URL
    ↓
Display audio player with chapters
    ↓
User clicks chapter → seek to timestamp in audio
```

---

## Key classes and data structures

### `GenerateAudioRequest`
```python
text: Optional[str]
filename: Optional[str]
page_number: Optional[int]
podcast: Optional[bool]
two_speakers: Optional[bool]
accent: Optional[str]
style: Optional[str]
speakers: Optional[Dict[str, str]]
entire_pdf: Optional[bool]
```

### `Chunk` (internal)
```python
{
    "text": "The document says...",
    "metadata": {
        "filename": "paper.pdf",
        "page_number": 5,
        "section_index": 2,
        "section_title": "Introduction"
    }
}
```

### `Chapter` (returned to frontend)
```python
{
    "index": 0,
    "speaker": "Speaker 1",
    "text": "Welcome to...",
    "start_ms": 0,
    "end_ms": 5000,
    "part_url": "/audio/tts_...part000.mp3"
}
```

---

For more details on any component, open the source file and search for the function name. Use `Ctrl+F` to jump to definitions.
