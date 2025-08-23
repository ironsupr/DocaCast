# ⚙️ Configuration Guide

This document explains all configuration options available in DocaCast.

## Environment Variables

### Backend Configuration

Create a `.env` file in the `backend/` directory:

```env
# Required Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Server Configuration
UVICORN_HOST=127.0.0.1
UVICORN_PORT=8001
UVICORN_WORKERS=1

# AI Model Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=8000

# TTS Configuration
DEFAULT_TTS_ENGINE=edge-tts
TTS_TIMEOUT=300
AUDIO_OUTPUT_FORMAT=wav
AUDIO_SAMPLE_RATE=22050

# Vector Store Configuration
VECTOR_STORE_TYPE=faiss
VECTOR_DIMENSION=384
SIMILARITY_THRESHOLD=0.3

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB in bytes
ALLOWED_FILE_TYPES=pdf
UPLOAD_DIRECTORY=document_library

# Audio Generation Configuration
MAX_AUDIO_DURATION=3600  # 1 hour in seconds
AUDIO_OUTPUT_DIRECTORY=generated_audio
ENABLE_BACKGROUND_PROCESSING=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/docastapp.log
ENABLE_REQUEST_LOGGING=true

# Cache Configuration
ENABLE_CACHING=true
CACHE_TTL=3600  # 1 hour
CACHE_DIRECTORY=cache

# Security Configuration
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ENABLE_CORS=true
```

### Frontend Configuration

Create a `.env` file in the `frontend/pdf-reader-ui/` directory:

```env
# Required Configuration
VITE_ADOBE_CLIENT_ID=your_adobe_embed_client_id
VITE_API_BASE_URL=http://127.0.0.1:8001

# Optional Frontend Configuration
VITE_APP_TITLE=DocaCast
VITE_MAX_FILE_SIZE=52428800
VITE_SUPPORTED_FORMATS=pdf
VITE_ENABLE_ANALYTICS=false

# UI Configuration
VITE_THEME=light
VITE_DEFAULT_LANGUAGE=en
VITE_SHOW_DEBUG_INFO=false

# Audio Player Configuration
VITE_DEFAULT_PLAYBACK_RATE=1.0
VITE_ENABLE_SUBTITLES=true
VITE_AUTO_PLAY=false
```

## Detailed Configuration Options

### AI Model Settings

#### Embedding Model
Controls the model used for text embeddings and semantic search.

```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**Options:**
- `sentence-transformers/all-MiniLM-L6-v2` (default, fast and lightweight)
- `sentence-transformers/all-mpnet-base-v2` (higher quality, slower)
- `sentence-transformers/multi-qa-mpnet-base-dot-v1` (optimized for Q&A)

#### Gemini Configuration
Settings for Google's Generative AI model.

```env
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=8000
GEMINI_TOP_P=0.9
GEMINI_TOP_K=40
```

**Temperature Values:**
- `0.0-0.3`: Conservative, factual responses
- `0.4-0.7`: Balanced creativity and accuracy (recommended)
- `0.8-1.0`: Creative, varied responses

### TTS Engine Configuration

#### Edge-TTS Settings
```env
DEFAULT_TTS_ENGINE=edge-tts
EDGE_TTS_VOICE_ALEX=en-GB-LibbyNeural
EDGE_TTS_VOICE_JORDAN=en-US-AriaNeural
EDGE_TTS_RATE=+0%
EDGE_TTS_PITCH=+0Hz
```

#### Google Cloud TTS Settings
```env
GOOGLE_TTS_PROJECT_ID=your_project_id
GOOGLE_TTS_VOICE_ALEX=en-GB-Neural2-A
GOOGLE_TTS_VOICE_JORDAN=en-US-Neural2-J
GOOGLE_TTS_SPEAKING_RATE=1.0
GOOGLE_TTS_PITCH=0.0
```

#### pyttsx3 Settings
```env
PYTTSX3_RATE=200
PYTTSX3_VOLUME=0.9
PYTTSX3_VOICE_ALEX=0  # Voice index
PYTTSX3_VOICE_JORDAN=1
```

### Audio Processing

#### Output Format Configuration
```env
AUDIO_OUTPUT_FORMAT=wav
AUDIO_SAMPLE_RATE=22050
AUDIO_CHANNELS=1  # Mono
AUDIO_BITRATE=128000  # For MP3 output
```

**Supported Formats:**
- `wav` (recommended for quality)
- `mp3` (smaller file size)
- `ogg` (open source alternative)

#### Podcast Generation Settings
```env
# Conversation parameters
PODCAST_MIN_SPEAKERS=2
PODCAST_MAX_SPEAKERS=2
CONVERSATION_STYLE=conversational
ENABLE_INTERRUPTIONS=true
ENABLE_REACTIONS=true

# Content processing
MAX_CONTENT_LENGTH=50000  # Characters
CONTENT_CHUNK_SIZE=2000
CONTENT_OVERLAP=200

# Timing settings
PAUSE_BETWEEN_SPEAKERS=0.5  # Seconds
INTRO_DURATION=10  # Seconds
OUTRO_DURATION=5   # Seconds
```

### Vector Store Configuration

#### FAISS Settings
```env
VECTOR_STORE_TYPE=faiss
VECTOR_DIMENSION=384
FAISS_INDEX_TYPE=IndexFlatIP  # Inner product similarity
ENABLE_GPU_ACCELERATION=false
```

#### Similarity Search
```env
DEFAULT_TOP_K=5
SIMILARITY_THRESHOLD=0.3
MAX_SEARCH_RESULTS=20
ENABLE_RERANKING=true
```

### File Processing

#### PDF Processing Settings
```env
# Text extraction
PDF_TEXT_EXTRACTION_METHOD=pymupdf
ENABLE_OCR=false
OCR_LANGUAGE=eng

# Content analysis
DETECT_HEADINGS=true
EXTRACT_TABLES=false
EXTRACT_IMAGES=false
MIN_TEXT_LENGTH=10

# Chunking strategy
CHUNK_SIZE=800
CHUNK_OVERLAP=100
CHUNK_METHOD=semantic  # or 'fixed'
```

#### Upload Restrictions
```env
MAX_FILE_SIZE=52428800  # 50MB
MAX_FILES_PER_USER=100
ALLOWED_FILE_EXTENSIONS=.pdf
SCAN_UPLOADED_FILES=true  # Virus scanning
```

### Performance Tuning

#### Server Performance
```env
UVICORN_WORKERS=1  # Increase for production
WORKER_TIMEOUT=300
MAX_CONCURRENT_REQUESTS=10
ENABLE_ASYNC_PROCESSING=true
```

#### Memory Management
```env
MAX_MEMORY_USAGE=4096  # MB
ENABLE_MEMORY_MONITORING=true
GARBAGE_COLLECTION_THRESHOLD=0.8
```

#### Caching
```env
ENABLE_CACHING=true
CACHE_TYPE=memory  # or 'redis', 'file'
CACHE_TTL=3600
CACHE_MAX_SIZE=1024  # MB
REDIS_URL=redis://localhost:6379  # If using Redis
```

### Security Configuration

#### CORS Settings
```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CORS_METHODS=GET,POST,PUT,DELETE
CORS_HEADERS=*
CORS_CREDENTIALS=false
```

#### Rate Limiting
```env
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600  # Seconds
RATE_LIMIT_STORAGE=memory  # or 'redis'
```

#### File Security
```env
SCAN_UPLOADS=true
QUARANTINE_SUSPICIOUS_FILES=true
ALLOWED_MIME_TYPES=application/pdf
MAX_SCAN_TIME=30  # Seconds
```

### Logging and Monitoring

#### Log Configuration
```env
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=logs/docastapp.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30
```

#### Monitoring
```env
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=60
PROMETHEUS_METRICS=true
```

### Development Settings

#### Debug Configuration
```env
DEBUG=false
ENABLE_AUTO_RELOAD=true  # Development only
SHOW_SQL_QUERIES=false
ENABLE_PROFILING=false
```

#### Testing Configuration
```env
TEST_DATABASE_URL=sqlite:///test.db
ENABLE_TEST_MODE=false
MOCK_AI_RESPONSES=false
SKIP_FILE_VALIDATION=false  # Testing only
```

## Production Configuration

### Recommended Production Settings

```env
# Security
DEBUG=false
ENABLE_AUTO_RELOAD=false
CORS_ORIGINS=https://yourdomain.com
SCAN_UPLOADS=true

# Performance
UVICORN_WORKERS=4
ENABLE_CACHING=true
CACHE_TYPE=redis
REDIS_URL=redis://redis-server:6379

# Monitoring
LOG_LEVEL=WARNING
ENABLE_METRICS=true
HEALTH_CHECK_INTERVAL=30

# Limits
MAX_FILE_SIZE=104857600  # 100MB
MAX_CONCURRENT_REQUESTS=20
RATE_LIMIT_REQUESTS=1000
```

### Docker Configuration

#### docker-compose.yml Environment
```yaml
environment:
  - GOOGLE_API_KEY=${GOOGLE_API_KEY}
  - REDIS_URL=redis://redis:6379
  - DATABASE_URL=postgresql://user:pass@db:5432/docastapp
  - CORS_ORIGINS=https://yourdomain.com
  - LOG_LEVEL=INFO
```

## Configuration Validation

The application validates configuration on startup. Common validation errors:

1. **Missing required variables**: Ensure `GOOGLE_API_KEY` is set
2. **Invalid file paths**: Check directory permissions
3. **Model download failures**: Verify internet connection
4. **Port conflicts**: Ensure ports are available

## Environment-Specific Configurations

### Development
- Enable debug logging
- Allow CORS from localhost
- Use local file caching
- Mock AI services for testing

### Staging
- Moderate logging
- Restricted CORS origins
- Redis caching
- Real AI services with limits

### Production
- Minimal logging
- Strict security settings
- Distributed caching
- Full AI capabilities
- Monitoring enabled

## Configuration Best Practices

1. **Security**: Never commit API keys to version control
2. **Performance**: Tune worker count based on CPU cores
3. **Monitoring**: Enable logging and metrics in production
4. **Backup**: Regularly backup configuration files
5. **Testing**: Validate configuration changes in staging first

## Troubleshooting Configuration Issues

### Common Problems
- **API key not working**: Check key format and permissions
- **High memory usage**: Reduce chunk sizes or enable caching
- **Slow audio generation**: Optimize TTS settings
- **File upload failures**: Check file size limits and permissions

### Diagnostic Commands
```bash
# Check configuration
python -c "from main import app; print('Config loaded successfully')"

# Test API key
python -c "import google.generativeai as genai; genai.configure(api_key='your_key'); print('API key valid')"

# Verify models
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```
