# DocaCast Interview Preparation — Master Index

Welcome to the comprehensive interview preparation guide for the DocaCast project. This folder contains everything you need to understand, explain, and defend the project in technical interviews.

---

## 📚 Document Overview

### Quick Start (5 minutes)
Start here if you have limited time:
- **[README.md](./README.md)** — High-level elevator pitch, architecture overview, and key interview Q&A (20 questions). Good for understanding the project at a glance.

### Deep Dives (30 minutes each)

#### 1. **[FAQ.md](./FAQ.md)** — Frequently Asked Interview Questions
   - **20+ detailed Q&A** covering architecture, tech stack, data flows, error handling, security, performance, and testing.
   - Best for: learning how to answer common technical questions.
   - Topics:
     - Architecture & high-level design
     - Tech stack rationale
     - Data flow & processing
     - TTS & audio synthesis
     - Vector search & embeddings
     - Error handling & edge cases
     - Security & privacy
     - Deployment & operations
     - Performance & optimization
     - Testing & QA
     - Interesting technical challenges
     - Metrics & KPIs

#### 2. **[CODE_OVERVIEW.md](./CODE_OVERVIEW.md)** — Key Files & Functions Explained
   - Detailed walkthrough of **every important file and function** in the codebase.
   - Best for: understanding code structure and being able to navigate the repo during a demo.
   - Includes:
     - Backend endpoints (POST /upload, /generate-audio, /recommendations, /insights, /cross-insights, etc.)
     - Helper functions (_gemini_script, _synthesize_speech, _convert_to_wav, etc.)
     - PDF processing pipeline (process_pdf, chunking strategy)
     - Vector store implementation
     - Frontend components (PodcastStudio, GenerateAudioButton, RecommendationsSidebar, etc.)
     - Execution flow diagram
     - Key data structures

#### 3. **[TECH_STACK.md](./TECH_STACK.md)** — Deep Dive into Technologies and Why
   - **Technology breakdown**: why each tool was chosen, trade-offs, and alternatives considered.
   - Best for: answering "Why did you use X instead of Y?" questions.
   - Covers:
     - Frontend: React 19, TypeScript, Vite, Adobe PDF Embed API
     - Backend: FastAPI, Uvicorn, Pydantic
     - AI/LLM: Google Generative AI (Gemini 1.5 Flash)
     - TTS: Gemini Speech, Google Cloud TTS, Edge-TTS, HuggingFace, pyttsx3
     - PDF processing: PyMuPDF (fitz)
     - Embeddings: Sentence-Transformers
     - Vector search: in-memory storage (FAISS-like)
     - Audio processing: ffmpeg, ffprobe
     - Deployment: Vercel
     - Caching strategy
     - Performance characteristics

#### 4. **[PROBLEMS_SOLUTIONS.md](./PROBLEMS_SOLUTIONS.md)** — Engineering Retrospective
   - **10 major challenges** encountered during development and how they were solved.
   - Best for: demonstrating problem-solving skills and resilience.
   - Challenges covered:
     1. Multi-speaker audio synthesis
     2. Script caching invalidation
     3. TTS provider failures & rate limiting
     4. ffmpeg concatenation with mixed audio formats
     5. Vector store scalability
     6. PDF extraction variability
     7. API key security
     8. Audio generation latency
     9. Handling concurrent TTS calls
     10. Debugging and observability

---

## 🎯 How to Use This Guide

### Before an Interview (2-3 hours preparation)

1. **Hour 1**: Read `README.md` for the big picture.
2. **Hour 2**: Skim `FAQ.md` and pick 5-10 questions to deep-dive on.
3. **Hour 3**: Review `TECH_STACK.md` to internalize why each tech choice was made.
4. Optional: glance at `PROBLEMS_SOLUTIONS.md` to prepare anecdotes about problem-solving.

### During an Interview

- **"Tell me about the project"** → Use README elevator pitch + architecture diagram.
- **"How does audio generation work?"** → Reference CODE_OVERVIEW.md's `/generate-audio` endpoint section.
- **"Why FastAPI instead of Flask?"** → Answer from TECH_STACK.md.
- **"What was the hardest problem?"** → Pick one from PROBLEMS_SOLUTIONS.md and explain the solution.
- **"What would you do differently?"** → See the "Future Challenges" section at the end of PROBLEMS_SOLUTIONS.md.

### Navigating the Code

If asked to show code:
1. Open `backend/main.py` and jump to the endpoint in question (Ctrl+F to search).
2. Reference `CODE_OVERVIEW.md` for function signatures and purposes.
3. Use `TECH_STACK.md` to explain design decisions.

---

## 🗂️ Quick Navigation by Topic

### Understanding the Project
- What is DocaCast? → [README.md - Elevator Pitch](./README.md)
- How does it work end-to-end? → [CODE_OVERVIEW.md - Execution Flow](./CODE_OVERVIEW.md#execution-flow-diagram)
- What are the key components? → [README.md - Architecture](./README.md#architecture-and-data-flow)

### Technology Decisions
- Why Python + FastAPI? → [TECH_STACK.md - FastAPI](./TECH_STACK.md#fastapi)
- Why Gemini instead of GPT? → [TECH_STACK.md - Gemini](./TECH_STACK.md#google-generative-ai-gemini-15-flash)
- Why multiple TTS providers? → [TECH_STACK.md - TTS Tier](./TECH_STACK.md#tts-text-to-speech-tier)
- What about PostgreSQL / MongoDB? → [TECH_STACK.md - Why not...](./TECH_STACK.md#why-not-alternatives-considered)

### Audio & Speech
- How is multi-speaker audio generated? → [FAQ.md - Q: How does multi-speaker audio synthesis work?](./FAQ.md#q-how-does-multi-speaker-audio-synthesis-work-under-the-hood)
- What if TTS fails? → [FAQ.md - Q: What happens if a TTS provider is down?](./FAQ.md#q-what-happens-if-a-tts-provider-is-down-or-returns-no-audio)
- Why ffmpeg? → [TECH_STACK.md - ffmpeg](./TECH_STACK.md#ffmpeg--ffprobe)
- How was this solved? → [PROBLEMS_SOLUTIONS.md - Problem 4](./PROBLEMS_SOLUTIONS.md#problem-4-ffmpeg-concatenation-with-mixed-audio-formats)

### Data Processing
- How does semantic search work? → [FAQ.md - Q: What is the role of semantic search?](./FAQ.md#q-what-is-the-role-of-semantic-search--vector-embeddings-in-this-project)
- Why embeddings? → [TECH_STACK.md - Embeddings](./TECH_STACK.md#embeddings-tier)
- How are PDFs processed? → [CODE_OVERVIEW.md - processing.py](./CODE_OVERVIEW.md#backend-backendprocessingpy--pdf-processing)
- What about scanned PDFs? → [PROBLEMS_SOLUTIONS.md - Problem 6](./PROBLEMS_SOLUTIONS.md#problem-6-pdf-extraction-variability)

### Caching & Performance
- Why caching? → [PROBLEMS_SOLUTIONS.md - Problem 2](./PROBLEMS_SOLUTIONS.md#problem-2-script-caching-invalidation) + [TECH_STACK.md - Caching](./TECH_STACK.md#caching-strategy)
- Typical latency? → [FAQ.md - Q: What is the typical latency?](./FAQ.md#q-what-is-the-typical-latency-for-generating-a-podcast-from-a-pdf-page)
- How to optimize? → [FAQ.md - Performance & Optimization](./FAQ.md#performance--optimization)

### Reliability & Security
- What if something fails? → [FAQ.md - Error Handling](./FAQ.md#error-handling--edge-cases)
- How is security handled? → [FAQ.md - Security & Privacy](./FAQ.md#security--privacy)
- API key protection? → [PROBLEMS_SOLUTIONS.md - Problem 7](./PROBLEMS_SOLUTIONS.md#problem-7-api-key-security)
- Prompt injection risks? → [FAQ.md - Q: Are there prompt injection risks?](./FAQ.md#q-are-there-prompt-injection-risks)

### Deployment & Operations
- How to run locally? → [README.md - Setup & how to run locally](./README.md#setup--how-to-run-locally-powershell-examples)
- How to deploy? → [FAQ.md - Q: How is DocaCast deployed to Vercel?](./FAQ.md#q-how-is-docacast-deployed-to-vercel)
- What to monitor? → [FAQ.md - Q: How do you monitor the app in production?](./FAQ.md#q-how-do-you-monitor-the-app-in-production)
- Environment variables? → [TECH_STACK.md - Configuration](./TECH_STACK.md#configuration--environment)

### Scaling & Production
- How to scale? → [README.md - Scaling & productionization notes](./README.md#scaling--productionization-notes)
- What about vector DBs? → [FAQ.md - Q: Why is the vector store in-memory?](./FAQ.md#q-why-is-the-vector-store-in-memory-instead-of-persistent)
- Production roadmap? → [TECH_STACK.md - Performance Characteristics](./TECH_STACK.md#performance-characteristics)

### Interview Anecdotes
- Problem-solving stories → [PROBLEMS_SOLUTIONS.md](./PROBLEMS_SOLUTIONS.md) (10 problems with solutions)
- Design trade-offs → [README.md - Design Decisions](./README.md#design-decisions--trade-offs-interview-talking-points)
- Failures & lessons → [PROBLEMS_SOLUTIONS.md - Summary](./PROBLEMS_SOLUTIONS.md#summary-key-learnings)

---

## 💡 Interview Tips

### 1. Lead with the problem, not the solution
**❌ Bad**: "We used Gemini TTS because it has multi-speaker support."
**✅ Good**: "We needed two-speaker podcast audio. Alternatives like OpenAI don't have native audio synthesis. Gemini was the only LLM with integrated multi-speaker TTS, so we chose it."

### 2. Be specific with numbers
**❌ Bad**: "FastAPI is faster than Flask."
**✅ Good**: "FastAPI handles async I/O natively via asyncio, which is critical for our TTS workload. Typical response latency is 500ms-2s (cached) vs. 10-20s (uncached). With Flask, we'd need to manage threading manually."

### 3. Admit trade-offs
**❌ Bad**: "Our architecture is perfect."
**✅ Good**: "The in-memory vector store works great for 1000s of documents, but doesn't scale to millions. For production, we'd migrate to Pinecone for persistence and horizontal scaling."

### 4. Show you've thought about production
**❌ Bad**: "We optimized for the hackathon."
**✅ Good**: "We optimized for the hackathon, but documented a clear upgrade path: in-memory → Pinecone for vector DB, Redis for caching, Celery for background jobs, and structured logging for observability."

### 5. Connect your choices to the problem you're solving
**❌ Bad**: "We used React because it's popular."
**✅ Good**: "React's component model made it easy to build reusable UI widgets (AudioPlayer, RecommendationsSidebar). Combined with Vite's fast dev iteration, we could iterate quickly during the hackathon."

---

## 📊 Key Metrics to Remember

- **Latency**: 7-20s (uncached), 100-500ms (cached).
- **Cache hit rate**: 50-70% scripts, 30-50% audio, 80%+ disk.
- **Storage**: ~150 MB for 50K vectors (1000 PDFs).
- **Cost**: ~$0.0008 per podcast (Gemini TTS), or free (Edge-TTS).
- **Throughput**: 10 concurrent requests per instance (TTS I/O bound).
- **Audio quality**: 160 kbps MP3 (good podcast quality).

---

## 🚀 Quick Demo Script (5 minutes)

If asked for a demo:

1. **Upload a PDF** (2 min)
   - Open frontend → Click "Upload PDF"
   - Select a short document (< 10 pages)
   - Show file appears in the list

2. **Generate a podcast** (1 min)
   - Select a page
   - Click "Generate Podcast"
   - Show the "Generating..." status
   - (If cached) Show result appears instantly

3. **Play and explore** (2 min)
   - Click play on the audio player
   - Show chapter navigation (each speaker turn is a chapter)
   - Expand "Recommendations" sidebar to show related content
   - Click a recommendation to jump to that file/page

---

## 🎓 Further Reading

- [Full project README](../README.md)
- [Backend code](../backend/main.py)
- [Frontend code](../frontend/pdf-reader-ui/src/)
- [API documentation](../API.md)
- [Installation guide](../INSTALLATION.md)

---

## 📝 Last-Minute Checklist

Before going into an interview, verify:

- [ ] I can explain the elevator pitch in 30 seconds.
- [ ] I can draw the architecture diagram on a whiteboard (input → PDF → chunks → embeddings → vector store → script → TTS → audio).
- [ ] I can name at least 3 design decisions and their trade-offs.
- [ ] I have 2-3 stories about problems I solved.
- [ ] I know the tech stack (React, FastAPI, Gemini, Sentence-Transformers, etc.).
- [ ] I can explain why in-memory vector store is acceptable for a hackathon but not production.
- [ ] I can show code (open `backend/main.py` and explain `/generate-audio` endpoint).
- [ ] I can discuss scaling (what would I change for 1M users?).
- [ ] I can talk about security (API keys, prompt injection, data privacy).
- [ ] I know my weaknesses and can discuss them honestly ("OCR for scanned PDFs is not implemented yet, but here's how I'd add it...").

---

## 🤝 Good Luck!

You're now ready to ace any technical interview on this project. Remember:
- Show enthusiasm for the problem you're solving.
- Be specific with examples and numbers.
- Admit trade-offs and limitations.
- Demonstrate you've thought about scaling and production readiness.
- Ask thoughtful questions about the role and team.

Good luck! 🚀

---

**Last updated**: November 6, 2025  
**Project**: DocaCast (Adobe Hackathon 2025)  
**Repository**: https://github.com/ironsupr/DocaCast
