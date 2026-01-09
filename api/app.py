"""FastAPI application for Claude Pulse local API."""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import UsageData, UsageResponse, HealthResponse
from .storage import get_storage

# Track pending refresh requests
_pending_refresh: Optional[datetime] = None

app = FastAPI(
    title="Claude Pulse API",
    description="Local API for Claude.ai usage tracking",
    version="1.0.0"
)

# Allow CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "https://claude.ai"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@app.get("/api/health", response_model=HealthResponse)
async def api_health():
    """API health check."""
    return HealthResponse()


@app.post("/api/usage")
async def receive_usage(data: UsageData):
    """Receive usage data from Chrome extension."""
    storage = get_storage()
    storage.update(data)
    return {"status": "ok", "message": "Usage data received"}


@app.get("/api/usage", response_model=UsageResponse)
async def get_usage():
    """Get current usage data with calculated metrics."""
    storage = get_storage()
    return storage.get_response()


@app.post("/api/request-refresh")
async def request_refresh():
    """Request the browser extension to refresh the Claude.ai usage page."""
    global _pending_refresh
    _pending_refresh = datetime.now()
    return {"status": "ok", "message": "Refresh requested"}


@app.get("/api/check-refresh")
async def check_refresh():
    """Check if a refresh has been requested (called by browser extension)."""
    global _pending_refresh
    if _pending_refresh is not None:
        request_time = _pending_refresh
        _pending_refresh = None  # Clear the request
        return {"refresh_requested": True, "requested_at": request_time.isoformat()}
    return {"refresh_requested": False}


def run_server(host: str = "127.0.0.1", port: int = 5000):
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
