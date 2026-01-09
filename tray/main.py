"""Main entry point for Claude Pulse tray application."""

import threading
import time
import sys
import os
import tempfile
import subprocess
from typing import Optional

import pystray
from PIL import Image
import requests

from .icon_renderer import create_percentage_icon, create_unknown_icon, create_progress_ring_icon
from .notifications import NotificationManager

# Lock file path (must match dashboard_runner.py)
DASHBOARD_LOCK_FILE = os.path.join(tempfile.gettempdir(), 'claude_pulse_dashboard.lock')


class ClaudePulseTray:
    """System tray application for Claude Pulse."""

    API_URL = "http://localhost:5000/api/usage"
    REFRESH_URL = "http://localhost:5000/api/request-refresh"
    POLL_INTERVAL = 30  # seconds

    def __init__(self):
        self._icon: Optional[pystray.Icon] = None
        self._running = False
        self._current_data: Optional[dict] = None
        self._notification_manager = NotificationManager()
        self._poll_thread: Optional[threading.Thread] = None
        self._dashboard_process: Optional[subprocess.Popen] = None

    def _fetch_usage(self) -> Optional[dict]:
        """Fetch usage data from the local API."""
        try:
            response = requests.get(self.API_URL, timeout=5)
            if response.ok:
                return response.json()
        except requests.RequestException:
            pass
        return None

    def _update_icon(self, percent: Optional[float] = None):
        """Update the tray icon."""
        if self._icon is None:
            return

        if percent is None:
            icon_image = create_unknown_icon(64)
        else:
            icon_image = create_progress_ring_icon(percent, 64)

        self._icon.icon = icon_image

    def _poll_api(self):
        """Background thread to poll the API periodically."""
        while self._running:
            data = self._fetch_usage()

            if data:
                self._current_data = data
                percent = data.get('session_usage_percent', 0)
                self._update_icon(percent)

                # Check for notifications
                pacing_ratio = data.get('pacing_ratio')
                self._notification_manager.check_and_notify(percent, pacing_ratio)
            else:
                self._update_icon(None)

            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.POLL_INTERVAL):
                if not self._running:
                    break
                time.sleep(1)

    def _on_open_dashboard(self, icon, item):
        """Open the Deep Dive dashboard in a separate process."""
        # Check if dashboard is already running
        if self._is_dashboard_running():
            self._bring_dashboard_to_front()
            return

        # Get the path to the dashboard script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dashboard_script = os.path.join(script_dir, 'dashboard_runner.py')

        # Launch dashboard as separate process
        self._dashboard_process = subprocess.Popen(
            [sys.executable, dashboard_script],
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )

    def _is_dashboard_running(self) -> bool:
        """Check if the dashboard process is still running."""
        # Check if our stored process is running
        if self._dashboard_process is not None:
            poll = self._dashboard_process.poll()
            if poll is None:
                # Process is still running, also verify lock file exists
                if os.path.exists(DASHBOARD_LOCK_FILE):
                    return True
            else:
                # Process has exited
                self._dashboard_process = None

        # Also check lock file in case dashboard was started externally
        if os.path.exists(DASHBOARD_LOCK_FILE):
            try:
                # Try to read the hwnd - if file exists, dashboard might be running
                with open(DASHBOARD_LOCK_FILE, 'r') as f:
                    hwnd_str = f.read().strip()
                    if hwnd_str:
                        return True
            except Exception:
                pass

        return False

    def _bring_dashboard_to_front(self):
        """Bring the existing dashboard window to front using Windows API."""
        if sys.platform != 'win32':
            return

        try:
            import ctypes
            from ctypes import wintypes

            # Read the window handle from lock file
            if not os.path.exists(DASHBOARD_LOCK_FILE):
                return

            with open(DASHBOARD_LOCK_FILE, 'r') as f:
                hwnd_str = f.read().strip()

            if not hwnd_str:
                return

            hwnd = int(hwnd_str)

            # Windows API functions
            user32 = ctypes.windll.user32

            # Constants
            SW_RESTORE = 9
            SW_SHOW = 5

            # Check if window is minimized
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, SW_RESTORE)
            else:
                user32.ShowWindow(hwnd, SW_SHOW)

            # Bring to front
            user32.SetForegroundWindow(hwnd)

        except Exception as e:
            # If we can't bring to front, launch a new instance
            # (lock file might be stale)
            try:
                os.remove(DASHBOARD_LOCK_FILE)
            except Exception:
                pass
            self._dashboard_process = None

    def _on_refresh(self, icon, item):
        """Manually refresh data from local cache."""
        data = self._fetch_usage()
        if data:
            self._current_data = data
            percent = data.get('session_usage_percent', 0)
            self._update_icon(percent)

    def _on_refresh_claude(self, icon, item):
        """Request browser to refresh Claude.ai usage page."""
        try:
            response = requests.post(self.REFRESH_URL, timeout=5)
            if response.ok:
                print("[Claude Pulse] Browser refresh requested")
        except requests.RequestException as e:
            print(f"[Claude Pulse] Failed to request browser refresh: {e}")

    def _on_test_notification(self, icon, item):
        """Send a test notification."""
        self._notification_manager.send_test_notification()

    def _on_exit(self, icon, item):
        """Exit the application."""
        self._running = False
        icon.stop()

    def _create_menu(self) -> pystray.Menu:
        """Create the tray icon menu."""
        return pystray.Menu(
            pystray.MenuItem("Open Dashboard", self._on_open_dashboard, default=True),
            pystray.MenuItem("Refresh Claude", self._on_refresh_claude),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Test Notification", self._on_test_notification),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._on_exit)
        )

    def run(self):
        """Run the tray application."""
        print("Creating initial icon...", flush=True)
        # Create initial icon
        initial_icon = create_unknown_icon(64)
        print("Icon created", flush=True)

        # Create tray icon
        print("Creating pystray Icon...", flush=True)
        self._icon = pystray.Icon(
            "claude_pulse",
            initial_icon,
            "Claude Pulse",
            menu=self._create_menu()
        )
        print("pystray Icon created", flush=True)

        self._running = True

        # Start polling thread
        print("Starting poll thread...", flush=True)
        self._poll_thread = threading.Thread(target=self._poll_api, daemon=True)
        self._poll_thread.start()
        print("Poll thread started", flush=True)

        # Initial fetch
        print("Initial fetch...", flush=True)
        data = self._fetch_usage()
        if data:
            self._current_data = data
            self._update_icon(data.get('session_usage_percent', 0))
        print("Running icon...", flush=True)

        # Run the icon (blocks until stopped)
        self._icon.run()


def main():
    """Main entry point."""
    app = ClaudePulseTray()
    try:
        app.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
