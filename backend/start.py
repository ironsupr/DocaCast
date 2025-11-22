#!/usr/bin/env python3
"""
Startup script for DocaCast backend on Render
Ensures proper port binding and environment validation
"""
import os
import sys

def check_environment():
    """Validate required environment variables"""
    required = ['GOOGLE_API_KEY', 'GEMINI_API_KEY']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("Please set them in Render dashboard → Environment")
        sys.exit(1)
    
    print("✅ All required environment variables are set")

def get_port():
    """Get port from environment or use default"""
    port = os.getenv('PORT', '8000')
    print(f"🔌 Port: {port}")
    return port

def main():
    print("🚀 Starting DocaCast Backend...")
    print(f"📦 Python version: {sys.version}")
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'production')}")
    
    # Check environment
    check_environment()
    
    # Get port
    port = get_port()
    
    # Start uvicorn
    print(f"🎯 Starting Uvicorn on 0.0.0.0:{port}")
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(port),
        workers=1,
        log_level="info"
    )

if __name__ == "__main__":
    main()
