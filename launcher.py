"""Claude Pulse Launcher - runs API server and tray app together."""

import sys
import os
import threading
import time
import signal
import traceback

# Ensure we can import our modules
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

# Set up logging to file for debugging
LOG_FILE = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'ClaudePulse', 'launcher.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def log(message):
    """Log a message to file and stdout."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + '\n')
    except:
        pass


def run_api_server():
    """Run the FastAPI server in a thread."""
    try:
        import uvicorn
        from api.app import app

        log("API server starting...")

        # Custom log config to avoid sys.stdout.isatty() issue with pythonw.exe
        # When running windowless, sys.stdout is None
        # We must avoid uvicorn's DefaultFormatter entirely as it checks isatty() in __init__
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(levelname)s - %(message)s",
                    # Use standard logging.Formatter, not uvicorn's
                },
                "access": {
                    "format": "%(asctime)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.NullHandler",  # Discard logs since we have no console
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.NullHandler",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "WARNING", "propagate": False},
                "uvicorn.error": {"handlers": ["default"], "level": "WARNING", "propagate": False},
                "uvicorn.access": {"handlers": ["access"], "level": "WARNING", "propagate": False},
            },
        }

        # Run on localhost only for security
        uvicorn.run(app, host="127.0.0.1", port=5000, log_config=log_config)
    except Exception as e:
        log(f"API server error: {e}")
        log(traceback.format_exc())


def run_tray_app():
    """Run the system tray application."""
    try:
        from tray.main import ClaudePulseTray

        log("Tray app starting...")
        app = ClaudePulseTray()
        app.run()
    except Exception as e:
        log(f"Tray app error: {e}")
        log(traceback.format_exc())


def main():
    """Main entry point - starts both API and tray."""
    log("=" * 50)
    log("Claude Pulse starting...")
    log(f"BASE_DIR: {BASE_DIR}")
    log(f"Python: {sys.executable}")

    # Start API server in background thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()

    # Give API a moment to start
    time.sleep(2)

    # Verify API is running
    try:
        import requests
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.ok:
            log("API server verified running on http://localhost:5000")
        else:
            log(f"API server responded with status {response.status_code}")
    except Exception as e:
        log(f"WARNING: Could not verify API server: {e}")

    # Run tray app in main thread (it handles the event loop)
    log("Starting tray application...")
    try:
        run_tray_app()
    except KeyboardInterrupt:
        pass

    log("Claude Pulse stopped.")


if __name__ == "__main__":
    main()
