"""Standalone dashboard runner - runs in its own process."""

import tkinter as tk
import requests
import sys
import os
import tempfile
import atexit

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tray.deep_dive import DeepDiveWindow

API_URL = "http://localhost:5000/api/usage"
REFRESH_URL = "http://localhost:5000/api/request-refresh"
LOCK_FILE = os.path.join(tempfile.gettempdir(), 'claude_pulse_dashboard.lock')


def fetch_usage():
    """Fetch usage data from the local API."""
    try:
        response = requests.get(API_URL, timeout=5)
        if response.ok:
            return response.json()
    except requests.RequestException:
        pass
    return None


def request_browser_refresh():
    """Request the browser extension to refresh the Claude.ai usage page."""
    try:
        response = requests.post(REFRESH_URL, timeout=5)
        return response.ok
    except requests.RequestException:
        pass
    return False


def cleanup_lock():
    """Remove lock file on exit."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass


def write_lock_file(hwnd):
    """Write the window handle to the lock file."""
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(hwnd))
    except Exception:
        pass


def main():
    """Run the dashboard as a standalone window."""
    # Register cleanup
    atexit.register(cleanup_lock)

    # Set AppUserModelID for proper taskbar grouping/icon on Windows
    if sys.platform == 'win32':
        try:
            import ctypes
            # This must be called BEFORE creating any windows
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ClaudePulse.Dashboard.1')
        except Exception:
            pass

    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Set icon on root window - this affects the taskbar icon
    if sys.platform == 'win32':
        try:
            from tray.icon_renderer import get_app_icon_path
            ico_path = get_app_icon_path()
            root.iconbitmap(ico_path)
        except Exception:
            pass

    # Create refresh callback for when window gets focus
    def on_focus_refresh():
        data = fetch_usage()
        if data:
            dashboard.update(data)

    # Create callback for manual browser refresh request
    def on_refresh_request():
        request_browser_refresh()

    dashboard = DeepDiveWindow(
        on_close=lambda: root.quit(),
        on_focus=on_focus_refresh,
        on_refresh_request=on_refresh_request
    )

    # Initial data fetch
    data = fetch_usage()
    dashboard.show(data)

    # Write lock file with window handle after window is created
    def write_hwnd():
        if dashboard.window and dashboard.window.winfo_exists():
            try:
                # For Windows, we need to get the actual HWND of the Toplevel window
                if sys.platform == 'win32':
                    import ctypes
                    # Get the HWND from the Toplevel window
                    # First update the window to ensure it's mapped
                    dashboard.window.update_idletasks()
                    # Get frame handle and find parent (actual window)
                    frame_id = dashboard.window.winfo_id()
                    # The winfo_id gives us a frame, we need the parent window
                    user32 = ctypes.windll.user32
                    # Get the actual top-level window handle
                    hwnd = user32.GetParent(frame_id)
                    if hwnd == 0:
                        hwnd = frame_id  # Fallback to frame_id if no parent
                    write_lock_file(hwnd)
                else:
                    hwnd = dashboard.window.winfo_id()
                    write_lock_file(hwnd)
            except Exception as e:
                print(f"Error writing hwnd: {e}", flush=True)

    root.after(100, write_hwnd)

    # Update loop
    def update_loop():
        if dashboard.is_visible():
            data = fetch_usage()
            if data:
                dashboard.update(data)
            root.after(5000, update_loop)  # Update every 5 seconds
        else:
            cleanup_lock()
            root.quit()

    root.after(1000, update_loop)

    try:
        root.mainloop()
    finally:
        cleanup_lock()


if __name__ == "__main__":
    main()
