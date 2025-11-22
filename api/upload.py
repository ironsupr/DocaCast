from http.server import BaseHTTPRequestHandler
import json
import os
from typing import Dict, Any
import tempfile
import shutil

# Import your existing modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.processing import process_pdf
    from backend.vector_store import VectorStore
except ImportError:
    # Fallback imports for serverless environment
    process_pdf = None
    VectorStore = None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse the request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Handle CORS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Parse JSON data
            data = json.loads(post_data.decode('utf-8'))
            
            # Basic response for now
            response = {
                "message": "Upload endpoint - Vercel serverless function",
                "status": "success",
                "note": "File upload in serverless environment requires special handling"
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "message": "Upload failed"
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
