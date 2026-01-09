"""Windows notification system for Claude Pulse."""

import json
import os
from pathlib import Path
from typing import Optional

# Try winotify first (better branding support), fall back to win10toast
HAS_WINOTIFY = False
HAS_TOAST = False

try:
    from winotify import Notification, audio
    HAS_WINOTIFY = True
except ImportError:
    try:
        from win10toast_click import ToastNotifier
        HAS_TOAST = True
    except ImportError:
        try:
            from win10toast import ToastNotifier
            HAS_TOAST = True
        except ImportError:
            pass


class NotificationSettings:
    """Manage notification preferences."""

    def __init__(self):
        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        self.settings_dir = Path(app_data) / 'ClaudePulse'
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.settings_dir / 'notification_settings.json'

        self.defaults = {
            'enabled': True,
            'threshold_90': True,
            'threshold_95': True,
            'reset_alert': True,
            'pace_warning': True,
            'pace_threshold': 20,  # Warn if usage exceeds time by this %
        }

        self._settings = self._load()

    def _load(self) -> dict:
        """Load settings from file."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r') as f:
                    return {**self.defaults, **json.load(f)}
            except (json.JSONDecodeError, ValueError):
                pass
        return self.defaults.copy()

    def save(self) -> None:
        """Save settings to file."""
        with open(self.settings_path, 'w') as f:
            json.dump(self._settings, f, indent=2)

    def get(self, key: str, default=None):
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a setting value."""
        self._settings[key] = value
        self.save()

    @property
    def enabled(self) -> bool:
        return self._settings.get('enabled', True)

    @enabled.setter
    def enabled(self, value: bool):
        self._settings['enabled'] = value
        self.save()


class NotificationManager:
    """Manage Windows toast notifications."""

    def __init__(self):
        self.settings = NotificationSettings()
        self._toaster = None
        self._last_notification_type: Optional[str] = None
        self._last_usage_percent: float = 0
        self._was_reset: bool = False
        self._icon_path: Optional[str] = None

        # Get icon path for notifications (use PNG for better quality)
        try:
            from .icon_renderer import get_app_icon_path
            self._icon_path = get_app_icon_path('png')
        except Exception:
            pass

        if HAS_TOAST and not HAS_WINOTIFY:
            try:
                self._toaster = ToastNotifier()
            except Exception:
                pass

    def _can_notify(self) -> bool:
        """Check if notifications are available and enabled."""
        if not self.settings.enabled:
            return False
        return HAS_WINOTIFY or (HAS_TOAST and self._toaster is not None)

    def _get_dashboard_script_path(self) -> str:
        """Get the path to the dashboard runner script."""
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, 'dashboard_runner.py')

    def _show_toast(self, title: str, message: str, duration: int = 5) -> None:
        """Show a Windows toast notification."""
        if not self._can_notify():
            return

        try:
            if HAS_WINOTIFY:
                import sys
                # Use winotify for better branding
                toast = Notification(
                    app_id="Claude Pulse",
                    title=title,
                    msg=message,
                    duration="short" if duration <= 5 else "long",
                    icon=self._icon_path if self._icon_path else ""
                )
                toast.set_audio(audio.Default, loop=False)

                # Add click action to open dashboard
                dashboard_script = self._get_dashboard_script_path()
                # Use launch parameter to open dashboard when clicked
                toast.add_actions(label="Open Dashboard", launch=f'"{sys.executable}" "{dashboard_script}"')

                toast.show()
            elif HAS_TOAST and self._toaster:
                # Fall back to win10toast
                self._toaster.show_toast(
                    title,
                    message,
                    icon_path=self._icon_path,
                    duration=duration,
                    threaded=True
                )
        except Exception as e:
            print(f"[Claude Pulse] Notification error: {e}")

    def check_and_notify(
        self,
        session_percent: float,
        pacing_ratio: Optional[float] = None
    ) -> None:
        """Check usage and send appropriate notifications.

        Args:
            session_percent: Current session usage percentage
            pacing_ratio: Current pacing ratio (usage% / time%)
        """
        if not self._can_notify():
            return

        # Check for reset (usage went from high to low)
        if self._last_usage_percent >= 50 and session_percent < 10:
            if self.settings.get('reset_alert'):
                self._show_toast(
                    "Claude Pulse",
                    "🔄 Session limit has been reset! You have full capacity again.",
                    duration=8
                )
                self._last_notification_type = 'reset'

        # Check 90% threshold
        elif session_percent >= 90 and self._last_usage_percent < 90:
            if self.settings.get('threshold_90'):
                self._show_toast(
                    "Claude Pulse - 90% Used",
                    "⚠️ You've used 90% of your session limit. Consider slowing down.",
                    duration=8
                )
                self._last_notification_type = 'threshold_90'

        # Check 95% threshold
        elif session_percent >= 95 and self._last_usage_percent < 95:
            if self.settings.get('threshold_95'):
                self._show_toast(
                    "Claude Pulse - 95% Used",
                    "🚨 You've used 95% of your session limit! Almost at capacity.",
                    duration=10
                )
                self._last_notification_type = 'threshold_95'

        # Check pacing (over budget warning)
        if pacing_ratio is not None and self.settings.get('pace_warning'):
            pace_threshold = 1 + (self.settings.get('pace_threshold', 20) / 100)
            if pacing_ratio >= pace_threshold and self._last_notification_type != 'pace':
                excess = int((pacing_ratio - 1) * 100)
                self._show_toast(
                    "Claude Pulse - Pace Warning",
                    f"📈 You're using messages {excess}% faster than your weekly pace.",
                    duration=8
                )
                self._last_notification_type = 'pace'

        self._last_usage_percent = session_percent

    def send_test_notification(self) -> bool:
        """Send a test notification to verify setup."""
        if not self._can_notify():
            return False

        self._show_toast(
            "Claude Pulse",
            "✅ Notifications are working correctly!",
            duration=5
        )
        return True
