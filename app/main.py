import uvicorn
import signal
import sys
from app.api import app
from app.config import settings

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        # Add graceful shutdown settings
        timeout_graceful_shutdown=30,
        timeout_keep_alive=5
    )
