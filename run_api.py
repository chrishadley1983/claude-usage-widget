"""Run the Claude Pulse API server."""

import uvicorn
from api.app import app

if __name__ == "__main__":
    print("Starting Claude Pulse API server on http://localhost:5000")
    uvicorn.run(app, host="127.0.0.1", port=5000)
