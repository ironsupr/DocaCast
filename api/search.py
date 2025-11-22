from http.server import BaseHTTPRequestHandler
import json
import os

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
            
            query = data.get('query', '')
            filename = data.get('filename', '')
            top_k = data.get('top_k', 5)
            
            # Mock search results for Vercel demo
            mock_results = [
                {
                    "text": f"This is a relevant excerpt from the document related to '{query}'...",
                    "similarity_score": 0.85,
                    "page_number": 1,
                    "filename": filename,
                    "context": "Additional context around this excerpt..."
                },
                {
                    "text": f"Another section discussing '{query}' and its implications...",
                    "similarity_score": 0.78,
                    "page_number": 3,
                    "filename": filename,
                    "context": "More context for this section..."
                }
            ]
            
            response = {
                "results": mock_results[:top_k],
                "total_results": len(mock_results),
                "query_time": 0.125,
                "note": "This is a demo response for Vercel deployment"
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "message": "Search failed"
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
