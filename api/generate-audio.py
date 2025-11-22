from http.server import BaseHTTPRequestHandler
import json
import os
import tempfile
import uuid
import asyncio

# Import your existing modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import google.generativeai as genai
    from backend.processing import process_pdf
except ImportError:
    genai = None
    process_pdf = None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Handle CORS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Parse request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Configure Google AI
            api_key = os.environ.get('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not configured")
            
            if genai:
                genai.configure(api_key=api_key)
            
            # Generate audio response
            audio_id = str(uuid.uuid4())[:8]
            
            # For Vercel deployment, we'll return a simplified response
            # In a full implementation, you'd integrate with cloud storage
            response = {
                "audio_url": f"/api/audio/{audio_id}",
                "duration": 120.5,
                "chapters": [
                    {
                        "index": 0,
                        "speaker": "Alex",
                        "text": "Welcome to this discussion about the document content...",
                        "start_ms": 0,
                        "end_ms": 5000
                    },
                    {
                        "index": 1,
                        "speaker": "Jordan",
                        "text": "That's a great introduction, Alex. Let me add some insights...",
                        "start_ms": 5000,
                        "end_ms": 10000
                    }
                ],
                "transcript": "Full conversation transcript would appear here...",
                "processing_time": 15.2,
                "filename": data.get('filename', 'unknown.pdf'),
                "note": "This is a demo response for Vercel deployment"
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "message": "Audio generation failed"
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
