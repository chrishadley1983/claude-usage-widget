"""Local storage/cache for usage data."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import UsageData, UsageResponse, ModelLimit


class UsageStorage:
    """File-based storage for usage data."""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            # Store in user's app data folder
            app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            storage_dir = Path(app_data) / 'ClaudePulse'
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_path = storage_dir / 'usage_data.json'
        else:
            self.storage_path = Path(storage_path)

        self._data: Optional[UsageData] = None
        self._load()

    def _load(self) -> None:
        """Load data from file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self._data = UsageData(**data)
            except (json.JSONDecodeError, ValueError):
                self._data = None

    def _save(self) -> None:
        """Save data to file."""
        if self._data:
            with open(self.storage_path, 'w') as f:
                json.dump(self._data.model_dump(mode='json'), f, default=str)

    def update(self, data: UsageData) -> None:
        """Update stored usage data."""
        self._data = data
        self._save()

    def get_current(self) -> Optional[UsageData]:
        """Get current usage data."""
        return self._data

    def get_response(self) -> UsageResponse:
        """Get usage response with calculated metrics."""
        # Get weekly reset time from data if available
        weekly_reset_time = None
        if self._data and self._data.weekly_reset_time:
            weekly_reset_time = self._data.weekly_reset_time

        week_elapsed = self._calculate_week_elapsed_percent(weekly_reset_time)

        if self._data is None:
            return UsageResponse(
                session_usage_percent=0,
                week_elapsed_percent=week_elapsed,
                budget_status="unknown"
            )

        # Get weekly usage from model_limits if not set directly
        weekly_percent = self._data.weekly_usage_percent
        if weekly_percent is None and self._data.model_limits:
            # Look for "all" model limit
            for limit in self._data.model_limits:
                if limit.model_name == 'all':
                    weekly_percent = limit.usage_percent
                    break

        # Calculate pacing ratio
        pacing_ratio = None
        budget_status = "unknown"

        if weekly_percent is not None and week_elapsed > 0:
            pacing_ratio = weekly_percent / week_elapsed
            budget_status = "under" if pacing_ratio < 1.0 else "over"

        # Format reset time
        reset_formatted = None
        if self._data.session_reset_seconds:
            hours = self._data.session_reset_seconds // 3600
            minutes = (self._data.session_reset_seconds % 3600) // 60
            reset_formatted = f"{hours}h {minutes}m"

        return UsageResponse(
            session_usage_percent=self._data.session_usage_percent,
            session_reset_seconds=self._data.session_reset_seconds,
            session_reset_formatted=reset_formatted,
            weekly_usage_percent=weekly_percent,
            weekly_reset_time=weekly_reset_time,
            week_elapsed_percent=week_elapsed,
            pacing_ratio=pacing_ratio,
            budget_status=budget_status,
            model_limits=self._data.model_limits,
            last_updated=self._data.timestamp,
            page_load_time=self._data.page_load_time
        )

    def _calculate_week_elapsed_percent(self, weekly_reset_time: Optional[datetime] = None) -> float:
        """Calculate what percentage of the week has elapsed.

        Uses the weekly_reset_time from Claude to determine the week boundary.
        If not available, falls back to Thursday 8am.
        """
        now = datetime.now()

        if weekly_reset_time:
            # weekly_reset_time is when the week ENDS (next reset)
            # So week started 7 days before that
            week_end = weekly_reset_time
            if isinstance(week_end, str):
                week_end = datetime.fromisoformat(week_end.replace('Z', '+00:00'))

            # Make sure we're comparing naive datetimes
            if week_end.tzinfo is not None:
                week_end = week_end.replace(tzinfo=None)

            week_start = week_end - timedelta(days=7)

            # Calculate elapsed time since week started
            elapsed = now - week_start
            total_week_seconds = 7 * 24 * 3600

            # Clamp to 0-100%
            percent = (elapsed.total_seconds() / total_week_seconds) * 100
            return max(0, min(100, percent))

        # Fallback: assume Thursday 8am reset (default for Claude)
        WEEK_START_DAY = 3  # Thursday
        WEEK_START_HOUR = 8

        days_since_thursday = (now.weekday() - WEEK_START_DAY) % 7
        week_start = now.replace(hour=WEEK_START_HOUR, minute=0, second=0, microsecond=0)
        week_start = week_start - timedelta(days=days_since_thursday)

        if now < week_start:
            week_start = week_start - timedelta(days=7)

        elapsed = now - week_start
        total_week_seconds = 7 * 24 * 3600

        return (elapsed.total_seconds() / total_week_seconds) * 100


# Global storage instance
_storage: Optional[UsageStorage] = None


def get_storage() -> UsageStorage:
    """Get the global storage instance."""
    global _storage
    if _storage is None:
        _storage = UsageStorage()
    return _storage
