"""Run both the API server and tray application."""

import subprocess
import sys
import time
import threading


def run_api():
    """Run the API server in a subprocess."""
    subprocess.run([sys.executable, "run_api.py"])


def run_tray():
    """Run the tray app in a subprocess."""
    subprocess.run([sys.executable, "run_tray.py"])


def main():
    print("=" * 50)
    print("  Claude Pulse - Starting...")
    print("=" * 50)
    print()

    # Start API server in background thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    print("[✓] API server starting on http://localhost:5000")
    time.sleep(2)  # Give API time to start

    print("[✓] Starting tray application...")
    print()
    print("Claude Pulse is now running in your system tray!")
    print("Right-click the tray icon for options.")
    print()

    # Run tray app (this blocks)
    run_tray()


if __name__ == "__main__":
    main()
