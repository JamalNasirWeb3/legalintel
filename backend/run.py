"""
Start uvicorn with settings suited for long-running background investigations.
Use this instead of `uvicorn main:app --reload` during development.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # Keep connections alive longer — prevents ECONNRESET during heavy background tasks
        timeout_keep_alive=120,
        # Give background tasks time to finish before forceful shutdown
        timeout_graceful_shutdown=30,
    )
