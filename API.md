# 📚 API Documentation

This document provides comprehensive API documentation for DocaCast's backend services.

## Base URL

```
http://127.0.0.1:8001
```

## Authentication

Most endpoints require a Google API key configured in the backend environment. No additional authentication headers are needed for client requests.

## Endpoints

### 📄 Document Management

#### Upload PDF Document

Upload a PDF document for processing and podcast generation.

**Endpoint:** `POST /upload`

**Content Type:** `multipart/form-data`

**Parameters:**
- `file` (required): PDF file to upload

**Response:**
```json
{
  "message": "File uploaded successfully",
  "filename": "document.pdf",
  "size": 1024000,
  "pages": 25
}
```

**Example:**
```bash
curl -X POST "http://127.0.0.1:8001/upload" \
  -F "file=@document.pdf"
```

#### List Uploaded Documents

Get a list of all uploaded PDF documents.

**Endpoint:** `GET /documents`

**Response:**
```json
{
  "documents": [
    {
      "filename": "document1.pdf",
      "upload_date": "2025-01-15T10:30:00Z",
      "size": 1024000,
      "pages": 25
    }
  ]
}
```

### 🎙️ Audio Generation

#### Generate Podcast Audio

Generate podcast-style audio from PDF content with AI-powered conversations.

**Endpoint:** `POST /generate-audio`

**Content Type:** `application/json`

**Parameters:**
- `filename` (required): Name of the uploaded PDF file
- `page_number` (optional): Specific page to process (default: processes entire document)
- `podcast` (optional): Enable podcast mode (default: `true`)
- `two_speakers` (optional): Enable two-speaker conversation (default: `true`)
- `tts_engine` (optional): TTS engine to use (default: `"edge-tts"`)
- `voice_alex` (optional): Voice for Alex (analytical host)
- `voice_jordan` (optional): Voice for Jordan (enthusiastic host)
- `content_style` (optional): Content generation style (`"conversational"`, `"academic"`, `"casual"`)

**TTS Engine Options:**
- `"edge-tts"` (recommended): Microsoft Edge TTS
- `"google-cloud"`: Google Cloud Text-to-Speech
- `"huggingface"`: Hugging Face TTS models
- `"pyttsx3"`: Offline TTS engine

**Request Body:**
```json
{
  "filename": "research_paper.pdf",
  "page_number": 1,
  "podcast": true,
  "two_speakers": true,
  "tts_engine": "edge-tts",
  "content_style": "conversational"
}
```

**Response:**
```json
{
  "audio_url": "/generated_audio/podcast_abc123.wav",
  "duration": 420.5,
  "chapters": [
    {
      "index": 0,
      "speaker": "Alex",
      "text": "Welcome to today's discussion about...",
      "start_ms": 0,
      "end_ms": 15000
    },
    {
      "index": 1,
      "speaker": "Jordan", 
      "text": "That's a fascinating topic, Alex...",
      "start_ms": 15000,
      "end_ms": 32000
    }
  ],
  "transcript": "Full conversation transcript...",
  "processing_time": 45.2
}
```

#### Generate Full PDF Podcast

Generate a comprehensive podcast covering the entire PDF document.

**Endpoint:** `POST /generate-full-podcast`

**Parameters:**
- `filename` (required): Name of the uploaded PDF file
- `max_duration` (optional): Maximum duration in minutes (default: 30)
- `summary_level` (optional): Level of detail (`"brief"`, `"detailed"`, `"comprehensive"`)

**Request Body:**
```json
{
  "filename": "research_paper.pdf",
  "max_duration": 45,
  "summary_level": "detailed"
}
```

### 🔍 Search and Analysis

#### Semantic Search

Perform semantic search on uploaded PDF documents.

**Endpoint:** `POST /search`

**Content Type:** `application/json`

**Parameters:**
- `query` (required): Search query text
- `filename` (optional): Specific file to search (searches all if omitted)
- `top_k` (optional): Number of results to return (default: 5)
- `similarity_threshold` (optional): Minimum similarity score (default: 0.3)

**Request Body:**
```json
{
  "query": "What are the main research findings?",
  "filename": "research_paper.pdf",
  "top_k": 10,
  "similarity_threshold": 0.4
}
```

**Response:**
```json
{
  "results": [
    {
      "text": "The main research findings indicate that...",
      "similarity_score": 0.85,
      "page_number": 5,
      "filename": "research_paper.pdf",
      "context": "surrounding text for context..."
    }
  ],
  "total_results": 10,
  "query_time": 0.245
}
```

#### Get Document Summary

Get an AI-generated summary of a PDF document.

**Endpoint:** `GET /summary/{filename}`

**Parameters:**
- `filename` (required): Name of the PDF file
- `summary_type` (optional): Type of summary (`"brief"`, `"detailed"`, `"outline"`)

**Response:**
```json
{
  "summary": "This document discusses...",
  "key_points": [
    "Key finding 1",
    "Key finding 2"
  ],
  "topics": ["AI", "Machine Learning", "Research"],
  "page_count": 25,
  "word_count": 8500
}
```

### 🎵 Audio Management

#### Get Audio File

Retrieve generated audio files.

**Endpoint:** `GET /generated_audio/{filename}`

**Parameters:**
- `filename` (required): Audio file name

**Response:** Audio file stream (WAV format)

#### List Generated Audio

Get a list of all generated audio files.

**Endpoint:** `GET /audio-files`

**Response:**
```json
{
  "audio_files": [
    {
      "filename": "podcast_abc123.wav",
      "source_pdf": "research_paper.pdf",
      "created_date": "2025-01-15T10:30:00Z",
      "duration": 420.5,
      "type": "two_speaker_podcast"
    }
  ]
}
```

### ⚙️ System Information

#### Health Check

Check system health and status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "ai_service": "available",
    "tts_service": "available",
    "vector_store": "available"
  },
  "uptime": 3600
}
```

#### Get System Info

Get system capabilities and configuration.

**Endpoint:** `GET /system-info`

**Response:**
```json
{
  "available_tts_engines": ["edge-tts", "google-cloud", "pyttsx3"],
  "supported_file_types": ["pdf"],
  "max_file_size": 52428800,
  "available_voices": {
    "edge-tts": [
      "en-GB-LibbyNeural",
      "en-US-AriaNeural"
    ]
  }
}
```

## Error Responses

All endpoints return standardized error responses:

```json
{
  "error": "Error description",
  "error_code": "ERROR_CODE",
  "details": "Additional error details",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: File or resource not found
- `413 Payload Too Large`: File size exceeds limit
- `422 Unprocessable Entity`: Invalid file format
- `500 Internal Server Error`: Server processing error
- `503 Service Unavailable`: AI service temporarily unavailable

## Rate Limiting

- **Upload endpoint**: 10 requests per minute
- **Audio generation**: 5 requests per minute
- **Search endpoint**: 100 requests per minute
- **Other endpoints**: 50 requests per minute

## WebSocket Support

For real-time updates during audio generation:

**Endpoint:** `ws://127.0.0.1:8001/ws/audio-generation`

**Messages:**
```json
{
  "type": "progress",
  "progress": 0.45,
  "stage": "Generating conversation",
  "estimated_time_remaining": 120
}
```

## SDK Examples

### Python
```python
import requests

# Upload file
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://127.0.0.1:8001/upload',
        files={'file': f}
    )

# Generate podcast
response = requests.post(
    'http://127.0.0.1:8001/generate-audio',
    json={
        'filename': 'document.pdf',
        'podcast': True,
        'two_speakers': True
    }
)
```

### JavaScript
```javascript
// Upload file
const formData = new FormData();
formData.append('file', file);

const uploadResponse = await fetch('http://127.0.0.1:8001/upload', {
    method: 'POST',
    body: formData
});

// Generate podcast
const audioResponse = await fetch('http://127.0.0.1:8001/generate-audio', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        filename: 'document.pdf',
        podcast: true,
        two_speakers: true
    })
});
```

### cURL
```bash
# Upload file
curl -X POST "http://127.0.0.1:8001/upload" \
  -F "file=@document.pdf"

# Generate podcast
curl -X POST "http://127.0.0.1:8001/generate-audio" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "document.pdf",
    "podcast": true,
    "two_speakers": true
  }'
```

## Best Practices

1. **File Management**: Keep filenames unique to avoid conflicts
2. **Error Handling**: Always check response status codes
3. **Rate Limiting**: Implement backoff strategies for rate-limited requests
4. **Large Files**: Use chunked uploads for files > 10MB
5. **Audio Generation**: Poll status endpoint for long-running generation tasks

## Changelog

### v1.0.0
- Initial API release
- Basic PDF upload and processing
- Two-speaker podcast generation
- Semantic search capabilities
