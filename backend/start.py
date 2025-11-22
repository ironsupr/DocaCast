#!/usr/bin/env python3
"""
Startup script for DocaCast backend on Render
Ensures proper port binding and environment validation
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Validate required environment variables - warn but don't exit"""
    logger.info("Checking environment variables...")
    
    # Critical variables
    google_key = os.getenv('GOOGLE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    if not google_key:
        logger.warning("⚠️ GOOGLE_API_KEY not set - some features will be limited")
    else:
        logger.info("✅ GOOGLE_API_KEY is set")
    
    if not gemini_key:
        logger.warning("⚠️ GEMINI_API_KEY not set - using GOOGLE_API_KEY if available")
    else:
        logger.info("✅ GEMINI_API_KEY is set")
    
    # Set defaults if needed
    if not gemini_key and google_key:
        os.environ['GEMINI_API_KEY'] = google_key
        logger.info("✅ Set GEMINI_API_KEY from GOOGLE_API_KEY")
    
    logger.info("✅ Environment check complete")

def get_port():
    """Get port from environment or use default"""
    port = os.getenv('PORT', '8000')
    logger.info(f"🔌 Using port: {port}")
    return port

def main():
    try:
        logger.info("=" * 50)
        logger.info("🚀 Starting DocaCast Backend")
        logger.info("=" * 50)
        logger.info(f"📦 Python version: {sys.version}")
        logger.info(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'production')}")
        logger.info(f"📁 Working directory: {os.getcwd()}")
        
        # Check environment
        check_environment()
        
        # Get port
        port = get_port()
        
        # Import app to check for errors
        logger.info("📦 Importing FastAPI application...")
        try:
            from main import app
            logger.info("✅ FastAPI app imported successfully")
        except Exception as e:
            logger.error(f"❌ Failed to import app: {e}")
            logger.error("Attempting to continue anyway...")
        
        # Start uvicorn
        logger.info(f"🎯 Starting Uvicorn on 0.0.0.0:{port}")
        logger.info("=" * 50)
        
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=int(port),
            workers=1,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Fatal error during startup: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()
