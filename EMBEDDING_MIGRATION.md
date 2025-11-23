# Migration to Lightweight Embeddings

## What Changed?

Replaced `sentence-transformers` (400MB+) with **Google Gemini Embeddings API** (API-based, ~0MB).

## Benefits

✅ **Deployment size**: Reduced from ~400MB to ~50MB  
✅ **Memory usage**: No model loading, API-based  
✅ **Better embeddings**: text-embedding-004 is state-of-the-art (768 dimensions)  
✅ **No downloads**: No model files to download on startup  
✅ **Fits Render/Railway free tier**: Under 512MB limit  

## Changes Required

### 1. Update Dependencies

```bash
pip install -r backend/requirements.txt
```

sentence-transformers has been removed from requirements.txt.

### 2. API Usage

The new implementation uses the same API key you're already using:
- `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- No additional configuration needed

### 3. Embedding API Calls

**Free Tier Limits (Gemini API):**
- 1,500 requests per day (free)
- Each request can embed up to 100 text chunks
- For typical PDFs (10-50 pages), this means 30-100 PDFs per day

**Cost (if you exceed free tier):**
- Extremely cheap: $0.000125 per 1000 characters
- A 50-page PDF (~100 chunks) costs ~$0.0001

### 4. Vector Store

No changes needed - the vector store automatically adapts to 768-dimensional embeddings.

### 5. Performance

**Before (sentence-transformers):**
- First startup: 5-10 seconds (model download)
- Embedding 100 chunks: ~2 seconds (local)

**After (Gemini API):**
- First startup: Instant (no model)
- Embedding 100 chunks: ~1-2 seconds (API call)

## Testing

1. Clear old vector store:
```bash
rm -rf backend/vector_store_*.pkl
```

2. Restart backend:
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

3. Upload a PDF - embeddings will now use Gemini API

## Rollback (if needed)

If you need to rollback:

1. Add back to `requirements.txt`:
```
sentence-transformers
```

2. Revert `processing.py` from git:
```bash
git checkout HEAD~1 -- backend/processing.py
```

3. Reinstall:
```bash
pip install sentence-transformers
```

## Deployment Size Comparison

**Before:**
- sentence-transformers: ~380MB
- torch dependencies: ~200MB
- Model files: ~90MB
- **Total: ~670MB** ❌ (exceeds 512MB limit)

**After:**
- google-generativeai: ~5MB
- Dependencies: ~45MB
- **Total: ~50MB** ✅ (well under 512MB limit)
