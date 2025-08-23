# 🎙️ DocaCast - AI-Powered PDF to Podcast Generator

**Transform any PDF document into engaging, natural-sounding podcasts with AI-generated two-speaker conversations.**

DocaCast is an innovative application that combines semantic PDF analysis with advanced text-to-speech technology to create podcast-style conversations from document content. Inspired by Google NotebookLM, it features natural dialogue between two AI hosts who discuss and explain your documents in an engaging, conversational format.

## ✨ Key Features

### 🎧 **Natural Two-Speaker Podcasts**
- **Alex** (Analytical Host): UK English female voice, asks probing questions
- **Jordan** (Enthusiastic Host): US English male voice, provides vivid explanations
- Natural conversation flow with interruptions, reactions, and dynamic interactions
- Conversational elements like "Oh, that's fascinating!" and "Wait, so you're saying..."

### 📖 **Intelligent PDF Processing**
- Semantic search and analysis of entire PDF documents
- Smart content summarization and dialogue structuring
- Support for academic papers, reports, and lengthy documents
- Vector-based similarity search for relevant content retrieval

### 🎙️ **Advanced TTS Options**
1. **Edge-TTS** (Recommended): Microsoft's neural voices for natural speech
2. **Google Cloud TTS**: High-quality cloud-based text-to-speech
3. **Hugging Face TTS**: AI-powered voices with customization
4. **pyttsx3**: Offline fallback option

### 🔧 **Flexible Audio Generation Modes**
- **Single Narrator**: Traditional narration for quick content overview
- **Two-Speaker Podcast**: Conversational dialogue between AI hosts
- **Full PDF Podcast**: Complete document coverage with engaging discussions
- **Page-by-Page**: Generate audio for specific sections or pages

### 🎨 **Interactive Web Interface**
- Modern React-based UI with TypeScript
- Adobe PDF Embed API integration for document viewing
- Real-time audio playback with chapter navigation
- Transcript display with speaker identification
- Responsive design for desktop and mobile

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with uvicorn server
- **PDF Processing**: PyMuPDF for text extraction and analysis
- **AI Integration**: Google Generative AI (Gemini) for content generation
- **Vector Search**: FAISS with Sentence Transformers for semantic similarity
- **Audio Generation**: Multiple TTS engines with fallback support

### Frontend (React + Vite)
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite for fast development and building
- **PDF Viewer**: Adobe PDF Embed API integration
- **Audio Player**: Custom podcast-style player with chapters
- **State Management**: React hooks and context

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google API Key (for Gemini AI)
- Adobe PDF Embed API Client ID

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ironsupr/DocaCast.git
   cd DocaCast
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend/pdf-reader-ui
   npm install
   ```

### Environment Configuration

#### Backend Environment (.env in `backend/`)
```env
GOOGLE_API_KEY=your_google_api_key_here
# Optional: Custom server settings
# UVICORN_HOST=127.0.0.1
# UVICORN_PORT=8001
```

#### Frontend Environment (.env in `frontend/pdf-reader-ui/`)
```env
VITE_ADOBE_CLIENT_ID=your_adobe_embed_client_id
VITE_API_BASE_URL=http://127.0.0.1:8001
```

### Running the Application

1. **Start the Backend**
   ```bash
   cd backend
   uvicorn main:app --reload --host 127.0.0.1 --port 8001
   ```

2. **Start the Frontend**
   ```bash
   cd frontend/pdf-reader-ui
   npm run dev
   ```

3. **Access the Application**
   - Open your browser to `http://localhost:5173`
   - Upload a PDF document
   - Generate your podcast!

## 📋 Usage Guide

### Basic Workflow
1. **Upload PDF**: Use the file picker to select your document
2. **Choose Mode**: Select single narrator or two-speaker podcast
3. **Generate Audio**: Click generate and wait for AI processing
4. **Listen & Explore**: Use the podcast player with chapter navigation

### API Endpoints

#### Generate Audio
```bash
POST /generate-audio
{
  "filename": "document.pdf",
  "page_number": 1,
  "podcast": true,
  "two_speakers": true,
  "tts_engine": "edge-tts"
}
```

#### Semantic Search
```bash
POST /search
{
  "query": "What are the main findings?",
  "filename": "document.pdf",
  "top_k": 5
}
```

#### Upload Document
```bash
POST /upload
Content-Type: multipart/form-data
file: [PDF file]
```

## 🛠️ Development

### Project Structure
```
DocaCast/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application entry point
│   ├── processing.py       # PDF processing and text extraction
│   ├── vector_store.py     # Vector database operations
│   ├── requirements.txt    # Python dependencies
│   └── document_library/   # Uploaded PDFs storage
├── frontend/               # React frontend
│   └── pdf-reader-ui/      # Main UI application
│       ├── src/
│       │   ├── components/ # React components
│       │   ├── App.tsx     # Main application component
│       │   └── main.tsx    # Application entry point
│       └── package.json    # Node.js dependencies
└── credentials/            # API credentials (gitignored)
```

### Key Technologies
- **Backend**: FastAPI, PyMuPDF, FAISS, Sentence Transformers, Google AI
- **Frontend**: React, TypeScript, Vite, Adobe PDF Embed API
- **AI/ML**: Google Gemini, Multiple TTS engines, Vector embeddings
- **Audio**: Edge-TTS, Google Cloud TTS, pyttsx3, pydub

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Google NotebookLM's podcast generation
- Built for Adobe Hackathon 2025
- Thanks to the open-source community for amazing tools and libraries

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Contact: [Your contact information]

---

**Transform your documents into engaging audio experiences with DocaCast! 🎙️📚**
