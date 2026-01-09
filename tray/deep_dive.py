"""Deep Dive Dashboard window for Claude Pulse - Matching JSX Design."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import math
import sys


class CircularGauge(tk.Canvas):
    """A circular progress gauge widget with dual rings - matching JSX design."""

    SESSION_DURATION_SECONDS = 5 * 60 * 60  # 5 hours in seconds
    BG_COLOR = '#161622'  # Lighter background for better contrast

    def __init__(self, parent, size=200, **kwargs):
        super().__init__(parent, width=size, height=size + 60, bg=self.BG_COLOR,
                        highlightthickness=0, **kwargs)
        self.size = size
        self.usage_percent = 0
        self.time_elapsed_percent = 0
        self.reset_hours = 0
        self.reset_minutes = 0
        self._draw()

    def _get_usage_color(self, percent: float) -> str:
        if percent > 80:
            return '#FF6B6B'
        return '#ff8c42'

    def _draw(self):
        self.delete('all')

        center_x = self.size // 2
        center_y = self.size // 2

        # Ring dimensions - make them larger with more space for text
        outer_radius = 85
        inner_radius = 68
        outer_ring_width = 10
        inner_ring_width = 8

        # Text area radius (inside inner ring)
        text_area_radius = inner_radius - inner_ring_width - 8

        # Bounding boxes for arcs
        outer_box = (
            center_x - outer_radius, center_y - outer_radius,
            center_x + outer_radius, center_y + outer_radius
        )
        inner_box = (
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius
        )

        # Dark center background for text
        self.create_oval(
            center_x - text_area_radius, center_y - text_area_radius,
            center_x + text_area_radius, center_y + text_area_radius,
            fill=self.BG_COLOR, outline=''
        )

        # === OUTER RING: Usage percentage ===
        # Background track
        self.create_arc(
            *outer_box,
            start=90, extent=-360,
            style='arc', outline='#1f1f2a', width=outer_ring_width
        )

        # Usage fill
        if self.usage_percent > 0:
            extent = -360 * (self.usage_percent / 100)
            color = self._get_usage_color(self.usage_percent)
            self.create_arc(
                *outer_box,
                start=90, extent=extent,
                style='arc', outline=color, width=outer_ring_width
            )

        # === INNER RING: Time elapsed ===
        # Background track
        self.create_arc(
            *inner_box,
            start=90, extent=-360,
            style='arc', outline='#1f1f2a', width=inner_ring_width
        )

        # Time elapsed fill (blue)
        if self.time_elapsed_percent > 0:
            extent = -360 * (self.time_elapsed_percent / 100)
            self.create_arc(
                *inner_box,
                start=90, extent=extent,
                style='arc', outline='#00b4ff', width=inner_ring_width
            )

        # === CENTER TEXT (inside the rings) ===
        # Large percentage number with % symbol
        percent_str = f"{int(self.usage_percent)}"
        self.create_text(
            center_x, center_y - 18,
            text=percent_str,
            fill='white', font=('Segoe UI', 32)
        )
        # Small % symbol next to number
        self.create_text(
            center_x + len(percent_str) * 12 + 5, center_y - 18,
            text="%",
            fill='#555555', font=('Segoe UI', 14), anchor='w'
        )

        # Reset time (smaller)
        self.create_text(
            center_x, center_y + 8,
            text=f"Resets in {self.reset_hours}h {self.reset_minutes}m",
            fill='#555555', font=('Segoe UI', 8)
        )

        # Time elapsed percentage (blue, smallest)
        self.create_text(
            center_x, center_y + 24,
            text=f"{int(self.time_elapsed_percent)}% of session",
            fill='#00b4ff', font=('Segoe UI', 7)
        )

        # === LEGEND (below gauge) ===
        legend_y = self.size + 25

        # Usage legend
        self.create_oval(center_x - 55, legend_y - 4, center_x - 47, legend_y + 4, fill='#ff8c42', outline='')
        self.create_text(center_x - 42, legend_y, text="Usage", fill='#666666', font=('Segoe UI', 9), anchor='w')

        # Time legend
        self.create_oval(center_x + 15, legend_y - 4, center_x + 23, legend_y + 4, fill='#00b4ff', outline='')
        self.create_text(center_x + 28, legend_y, text="Time", fill='#666666', font=('Segoe UI', 9), anchor='w')

    def set_value(self, usage_percent: float, reset_seconds: Optional[int] = None):
        """Set the gauge values."""
        self.usage_percent = min(100, max(0, usage_percent))

        if reset_seconds is not None and reset_seconds > 0:
            self.reset_hours = reset_seconds // 3600
            self.reset_minutes = (reset_seconds % 3600) // 60
            elapsed_seconds = self.SESSION_DURATION_SECONDS - reset_seconds
            self.time_elapsed_percent = (elapsed_seconds / self.SESSION_DURATION_SECONDS) * 100
            self.time_elapsed_percent = min(100, max(0, self.time_elapsed_percent))
        else:
            self.reset_hours = 0
            self.reset_minutes = 0
            self.time_elapsed_percent = 0

        self._draw()


class WeeklyPaceCard(tk.Canvas):
    """Weekly pace section matching JSX design."""

    BG_COLOR = '#161622'  # Lighter background for better contrast

    def __init__(self, parent, width=320, **kwargs):
        super().__init__(parent, width=width, height=140, bg=self.BG_COLOR,
                        highlightthickness=0, **kwargs)
        self.card_width = width
        self.usage_percent = 0
        self.time_percent = 0
        self._draw()

    def _draw(self):
        self.delete('all')

        padding = 20
        card_margin = 16

        # Card background (rounded rectangle simulation)
        self._round_rect(card_margin, 0, self.card_width - card_margin, 130, 16, fill='#1e1e2a')

        # Title
        self.create_text(
            padding + card_margin, 20,
            text="WEEKLY PACE",
            fill='#555555', font=('Consolas', 9), anchor='w'
        )

        # Budget status badge
        over_budget = self.usage_percent > self.time_percent if self.time_percent > 0 else False
        badge_text = "Over Budget" if over_budget else "On Track"
        badge_color = '#FF6B6B' if over_budget else '#50C896'
        badge_bg = '#1f1515' if over_budget else '#0f1f15'

        badge_x = self.card_width - padding - card_margin - 80
        self._round_rect(badge_x, 10, badge_x + 90, 30, 10, fill=badge_bg)
        self.create_oval(badge_x + 8, 16, badge_x + 14, 22, fill=badge_color, outline='')
        self.create_text(badge_x + 20, 20, text=badge_text, fill=badge_color, font=('Segoe UI', 9, 'bold'), anchor='w')

        # Progress bar
        bar_y = 55
        bar_h = 8
        bar_x1 = padding + card_margin
        bar_x2 = self.card_width - padding - card_margin

        # Track
        self._round_rect(bar_x1, bar_y, bar_x2, bar_y + bar_h, 4, fill='#1a1a24')

        # Fill
        if self.usage_percent > 0:
            fill_width = (bar_x2 - bar_x1) * (self.usage_percent / 100)
            fill_color = '#50C896' if not over_budget else '#ff8c42'
            self._round_rect(bar_x1, bar_y, bar_x1 + fill_width, bar_y + bar_h, 4, fill=fill_color)

        # Time marker
        if self.time_percent > 0:
            marker_x = bar_x1 + (bar_x2 - bar_x1) * (self.time_percent / 100)
            # Vertical line
            self.create_line(marker_x, bar_y - 4, marker_x, bar_y + bar_h + 4, fill='#ffffff', width=2)
            # Dot below
            self.create_oval(marker_x - 4, bar_y + bar_h + 6, marker_x + 4, bar_y + bar_h + 14, fill='white', outline='')

        # Usage value
        self.create_text(
            bar_x1, bar_y + bar_h + 35,
            text=f"{int(self.usage_percent)}%",
            fill='white', font=('Segoe UI', 18, 'bold'), anchor='w'
        )
        self.create_text(
            bar_x1 + 55, bar_y + bar_h + 38,
            text="used",
            fill='#555555', font=('Segoe UI', 10), anchor='w'
        )

        # Time elapsed
        self.create_text(
            bar_x2, bar_y + bar_h + 38,
            text=f"{int(self.time_percent)}% of week elapsed",
            fill='#555555', font=('Segoe UI', 10), anchor='e'
        )

    def _round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def set_values(self, usage_percent: float, time_percent: float):
        self.usage_percent = min(100, max(0, usage_percent))
        self.time_percent = min(100, max(0, time_percent))
        self._draw()


class DeepDiveWindow:
    """Main Deep Dive dashboard window - matching JSX design."""

    def __init__(self, on_close: Optional[Callable] = None, on_focus: Optional[Callable] = None,
                 on_refresh_request: Optional[Callable] = None):
        self.window: Optional[tk.Toplevel] = None
        self.on_close = on_close
        self.on_focus = on_focus  # Called when window gets focus
        self.on_refresh_request = on_refresh_request  # Called when user clicks refresh
        self._session_gauge: Optional[CircularGauge] = None
        self._pace_card: Optional[WeeklyPaceCard] = None
        self._page_refresh_label: Optional[tk.Label] = None  # When Claude.ai page was refreshed
        self._synced_label: Optional[tk.Label] = None  # When data was scraped
        self._hint_label: Optional[tk.Label] = None
        self._refresh_btn: Optional[tk.Button] = None

    def show(self, data: Optional[dict] = None):
        """Show or bring to front the Deep Dive window."""
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            if data:
                self.update(data)
            return

        self._create_window()
        if data:
            self.update(data)

    BG_COLOR = '#161622'  # Lighter background for better contrast

    def _create_window(self):
        """Create the Deep Dive window with JSX-matching design."""
        self.window = tk.Toplevel()
        self.window.title("Claude Pulse")
        self.window.geometry("380x720")
        self.window.configure(bg=self.BG_COLOR)
        self.window.resizable(False, False)

        # Set window icon
        try:
            if sys.platform == 'win32':
                from .icon_renderer import get_app_icon_path
                ico_path = get_app_icon_path()
                self.window.iconbitmap(ico_path)

                # Also set the taskbar icon using Windows API
                self._set_taskbar_icon(ico_path)
        except Exception:
            pass

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Bind focus event to refresh data
        self.window.bind("<FocusIn>", self._on_focus_in)

        # Main container
        main_frame = tk.Frame(self.window, bg=self.BG_COLOR)
        main_frame.pack(fill='both', expand=True)

        # === HEADER ===
        header_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        header_frame.pack(fill='x', padx=28, pady=(24, 0))

        # Logo area
        logo_frame = tk.Frame(header_frame, bg=self.BG_COLOR)
        logo_frame.pack(side='left')

        # Logo canvas (speech bubble with heartbeat)
        logo_canvas = tk.Canvas(logo_frame, width=42, height=42, bg=self.BG_COLOR, highlightthickness=0)
        logo_canvas.pack(side='left', padx=(0, 14))

        # Draw speech bubble
        logo_canvas.create_oval(5, 5, 37, 32, fill='#2a4060', outline='#3a5a80', width=1)
        logo_canvas.create_polygon(15, 28, 12, 40, 22, 28, fill='#2a4060', outline='')
        # Heartbeat line
        logo_canvas.create_line(10, 18, 16, 18, 20, 8, 26, 28, 32, 18, 36, 18,
                               fill='#ff8c42', width=2, smooth=True)

        # Title
        title_frame = tk.Frame(logo_frame, bg=self.BG_COLOR)
        title_frame.pack(side='left')

        title_container = tk.Frame(title_frame, bg=self.BG_COLOR)
        title_container.pack(anchor='w')

        tk.Label(title_container, text="Claude", font=('Segoe UI', 17, 'bold'),
                fg='white', bg=self.BG_COLOR).pack(side='left')
        tk.Label(title_container, text="Pulse", font=('Segoe UI', 17, 'bold'),
                fg='#ff8c42', bg=self.BG_COLOR).pack(side='left', padx=(6, 0))

        tk.Label(title_frame, text="USAGE MONITOR", font=('Segoe UI', 9),
                fg='#555555', bg=self.BG_COLOR).pack(anchor='w')

        # Divider
        divider = tk.Frame(main_frame, bg='#1a1a24', height=1)
        divider.pack(fill='x', padx=28, pady=(20, 0))

        # === SESSION USAGE SECTION ===
        session_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        session_frame.pack(fill='x', pady=(20, 0))

        tk.Label(session_frame, text="SESSION USAGE", font=('Consolas', 9),
                fg='#555555', bg=self.BG_COLOR).pack()

        # Gauge
        gauge_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        gauge_frame.pack(pady=(10, 0))

        self._session_gauge = CircularGauge(gauge_frame, size=200)
        self._session_gauge.pack()

        # === WEEKLY PACE SECTION ===
        self._pace_card = WeeklyPaceCard(main_frame, width=380)
        self._pace_card.pack(pady=(10, 0))

        # === LIMIT ALERTS TOGGLE ===
        alerts_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        alerts_frame.pack(fill='x', padx=28, pady=(20, 20))

        # Bell icon (simple representation)
        bell_canvas = tk.Canvas(alerts_frame, width=16, height=16, bg=self.BG_COLOR, highlightthickness=0)
        bell_canvas.pack(side='left')
        bell_canvas.create_oval(4, 2, 12, 10, outline='#666666', width=1)
        bell_canvas.create_line(8, 10, 8, 14, fill='#666666', width=1)
        bell_canvas.create_oval(6, 12, 10, 15, outline='#666666', width=1)

        tk.Label(alerts_frame, text="Limit Alerts", font=('Segoe UI', 11),
                fg='#666666', bg=self.BG_COLOR).pack(side='left', padx=(10, 0))

        # Toggle switch (visual only for now)
        toggle_canvas = tk.Canvas(alerts_frame, width=44, height=24, bg=self.BG_COLOR, highlightthickness=0)
        toggle_canvas.pack(side='right')
        # Draw toggle background
        toggle_canvas.create_oval(0, 0, 24, 24, fill='#ff8c42', outline='')
        toggle_canvas.create_rectangle(12, 0, 32, 24, fill='#ff8c42', outline='')
        toggle_canvas.create_oval(20, 0, 44, 24, fill='#ff8c42', outline='')
        # Draw toggle knob
        toggle_canvas.create_oval(22, 3, 40, 21, fill='white', outline='')

        # === TIMESTAMPS ===
        timestamp_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        timestamp_frame.pack(pady=(15, 10))

        # Page refresh timestamp (when Claude.ai page was loaded/refreshed in browser)
        self._page_refresh_label = tk.Label(
            timestamp_frame,
            text="Claude page refreshed: --:--:--",
            font=('Segoe UI', 8),
            fg='#555555',
            bg=self.BG_COLOR
        )
        self._page_refresh_label.pack()

        # Synced from Claude timestamp (when extension scraped the data)
        self._synced_label = tk.Label(
            timestamp_frame,
            text="Data scraped: --:--:--",
            font=('Segoe UI', 8),
            fg='#444444',
            bg=self.BG_COLOR
        )
        self._synced_label.pack()

        # Refresh button and hint in a row
        refresh_row = tk.Frame(timestamp_frame, bg=self.BG_COLOR)
        refresh_row.pack(pady=(5, 0))

        # Refresh button (styled to match the dark theme)
        self._refresh_btn = tk.Button(
            refresh_row,
            text="Refresh Claude",
            font=('Segoe UI', 8),
            fg='#888888',
            bg='#1e1e2a',
            activeforeground='#ffffff',
            activebackground='#2a2a3a',
            relief='flat',
            cursor='hand2',
            padx=10,
            pady=2,
            command=self._on_refresh_click
        )
        self._refresh_btn.pack()

        # Hint text
        self._hint_label = tk.Label(
            timestamp_frame,
            text="Auto-refreshes every 15 minutes",
            font=('Segoe UI', 7),
            fg='#333333',
            bg=self.BG_COLOR
        )
        self._hint_label.pack(pady=(3, 0))

        # Position window
        self._position_window()

    def _set_taskbar_icon(self, ico_path: str):
        """Set the taskbar icon using Windows API."""
        try:
            import ctypes
            from ctypes import wintypes

            # Wait for window to be fully created
            self.window.update_idletasks()

            # Get the window handle
            hwnd = ctypes.windll.user32.GetParent(self.window.winfo_id())
            if hwnd == 0:
                hwnd = self.window.winfo_id()

            # Load the icon
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x0010
            LR_DEFAULTSIZE = 0x0040

            # Load icon at different sizes for small (title bar) and big (taskbar/alt-tab)
            hicon_small = ctypes.windll.user32.LoadImageW(
                None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
            )
            hicon_big = ctypes.windll.user32.LoadImageW(
                None, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE
            )

            # Set the icons
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1

            if hicon_small:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
            if hicon_big:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)

        except Exception as e:
            print(f"Error setting taskbar icon: {e}", flush=True)

    def _position_window(self):
        """Position window near system tray area."""
        if not self.window:
            return

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        window_width = 380
        window_height = 720
        x = screen_width - window_width - 20
        y = screen_height - window_height - 60

        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def _on_close(self):
        """Handle window close."""
        if self.window:
            self.window.destroy()
            self.window = None
        if self.on_close:
            self.on_close()

    def _on_refresh_click(self):
        """Handle refresh button click."""
        if self.on_refresh_request:
            self.on_refresh_request()
        # Update button to show it was clicked
        if self._refresh_btn:
            self._refresh_btn.config(text="Refreshing...", fg='#ff8c42')
            # Schedule auto-refresh of dashboard data after browser has time to reload
            # Extension checks every 3s, then page loads ~2s, then scrape ~2s = ~7s total
            if self.window:
                self.window.after(8000, self._auto_refresh_after_browser)

    def _auto_refresh_after_browser(self):
        """Auto-refresh dashboard data after browser refresh completes."""
        # Reset button text
        if self._refresh_btn and self._refresh_btn.winfo_exists():
            self._refresh_btn.config(text="Refresh Claude", fg='#888888')
        # Trigger focus callback to fetch fresh data
        if self.on_focus:
            self.on_focus()

    def _on_focus_in(self, event):
        """Handle window gaining focus - refresh data."""
        # Only trigger for the main window, not child widgets
        if event.widget == self.window and self.on_focus:
            self.on_focus()

    def update(self, data: dict):
        """Update the dashboard with new data."""
        if not self.window or not self.window.winfo_exists():
            return

        # Update session gauge
        session_percent = data.get('session_usage_percent', 0)
        reset_seconds = data.get('session_reset_seconds')
        if self._session_gauge:
            self._session_gauge.set_value(session_percent, reset_seconds)

        # Update pace card
        weekly_percent = data.get('weekly_usage_percent', 0) or 0
        time_elapsed = data.get('week_elapsed_percent', 0)
        if self._pace_card:
            self._pace_card.set_values(weekly_percent, time_elapsed)

        # Update timestamps
        from datetime import datetime

        # Page refresh timestamp (when Claude.ai page was loaded/refreshed)
        if self._page_refresh_label:
            page_load_time = data.get('page_load_time')
            if page_load_time:
                try:
                    if isinstance(page_load_time, str):
                        dt = datetime.fromisoformat(page_load_time.replace('Z', '+00:00'))
                    else:
                        dt = page_load_time
                    time_str = dt.strftime("%H:%M:%S")
                    self._page_refresh_label.config(text=f"Claude page refreshed: {time_str}")
                except (ValueError, AttributeError):
                    self._page_refresh_label.config(text="Claude page refreshed: --:--:--")

        # Data scraped timestamp (when extension last scraped)
        if self._synced_label:
            last_updated = data.get('last_updated')
            if last_updated:
                try:
                    if isinstance(last_updated, str):
                        dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    else:
                        dt = last_updated
                    time_str = dt.strftime("%H:%M:%S")
                    self._synced_label.config(text=f"Data scraped: {time_str}")
                except (ValueError, AttributeError):
                    self._synced_label.config(text="Data scraped: --:--:--")

    def hide(self):
        """Hide the window."""
        if self.window and self.window.winfo_exists():
            self.window.withdraw()

    def is_visible(self) -> bool:
        """Check if window is visible."""
        return self.window is not None and self.window.winfo_exists()
