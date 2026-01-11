# PRD: Claude Pulse v2.0 (Windows Usage Tracker)

## 1. Product Overview

Claude Pulse is a lightweight Windows system tray utility that provides real-time visibility into Claude.ai rate limits. It uses direct API access via Claude Code's OAuth credentials to fetch usage data, eliminating the need for browser extensions or web scraping.

---

## 2. Architecture Change Summary

### Previous Architecture (v1.0)
| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Harvester | Chrome Extension (JS) | Scrapes `/settings/usage` and `POST`s JSON to localhost |
| Local API | Python (Flask/FastAPI) | Receives data and stores it in a temporary local cache |
| Tray Icon | Python (`pystray` + `PIL`) | Dynamically renders a percentage/graphic as the icon |
| Notifications | `win10toast` or `plyer` | Handles Windows Toast alerts |

### New Architecture (v2.0)
| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Tray App | Python (`pystray` + `PIL`) | Main application, renders icon, manages UI |
| API Client | Python (`requests`) | Reads OAuth token, calls Anthropic usage API directly |
| Notifications | `win10toast` or `plyer` | Handles Windows Toast alerts |

**Key Benefits:**
- No browser extension required
- No localhost Flask server required
- Single Python application
- More reliable data (direct from API)
- Works regardless of browser state

---

## 3. Data Source Specification

### 3.1 Credential Location

Claude Code stores OAuth credentials at:
```
~/.claude/.credentials.json
```

**File Structure:**
```json
{
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "sk-ant-ort01-...",
    "expiresAt": 1748658860401,
    "scopes": ["user:inference", "user:profile"]
  }
}
```

### 3.2 API Endpoint

```
GET https://api.anthropic.com/api/oauth/usage
```

**Required Headers:**
```
Accept: application/json
Content-Type: application/json
User-Agent: claude-code/2.0.32
Authorization: Bearer {accessToken}
anthropic-beta: oauth-2025-04-20
```

### 3.3 API Response Format

```json
{
  "five_hour": {
    "utilization": 8.0,
    "resets_at": "2025-01-11T05:17:29.000000+00:00"
  },
  "seven_day": {
    "utilization": 68.0,
    "resets_at": "2025-01-15T03:59:59.943679+00:00"
  },
  "seven_day_opus": {
    "utilization": 0.0,
    "resets_at": null
  },
  "seven_day_oauth_apps": null
}
```

**Field Mapping to UI:**

| API Field | UI Element |
|-----------|------------|
| `five_hour.utilization` | Session Usage gauge (orange arc) |
| `five_hour.resets_at` | "Resets in Xh Xm" countdown |
| `seven_day.utilization` | Weekly Pace bar and percentage |
| `seven_day.resets_at` | Weekly reset calculation |
| `seven_day_opus.utilization` | [Future] Opus-specific tracking |

---

## 4. Functional Requirements

### 4.1 Core Functionality

1. **Credential Reading:** On startup and periodically, read `~/.claude/.credentials.json` to obtain the OAuth access token.

2. **API Polling:** Call the usage API endpoint every 60 seconds (configurable) to fetch current utilization data.

3. **Token Refresh Handling:** If API returns 401/403, notify user to re-authenticate via Claude Code CLI.

4. **Tray Icon:** Display dynamic icon showing current 5-hour session utilization percentage.

5. **Deep Dive Window:** On click, show the full UI with:
   - Session Usage gauge (dual-ring: usage + time elapsed)
   - Weekly Pace bar with budget indicator
   - Limit Alerts toggle

### 4.2 Session Time Calculation

The "% of session" (blue arc) is calculated from the 5-hour window:

```python
from datetime import datetime, timezone

def calculate_session_time_percent(resets_at: str) -> float:
    """Calculate what percentage of the 5-hour session has elapsed."""
    reset_time = datetime.fromisoformat(resets_at.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    # Session is 5 hours (18000 seconds)
    session_duration = 5 * 60 * 60
    
    # Time remaining until reset
    time_remaining = (reset_time - now).total_seconds()
    
    # Time elapsed in current session
    time_elapsed = session_duration - time_remaining
    
    # Percentage elapsed
    return max(0, min(100, (time_elapsed / session_duration) * 100))
```

### 4.3 Weekly Pace Calculation

```python
def calculate_week_elapsed_percent(resets_at: str) -> float:
    """Calculate what percentage of the 7-day period has elapsed."""
    reset_time = datetime.fromisoformat(resets_at.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    # Week is 7 days (604800 seconds)
    week_duration = 7 * 24 * 60 * 60
    
    time_remaining = (reset_time - now).total_seconds()
    time_elapsed = week_duration - time_remaining
    
    return max(0, min(100, (time_elapsed / week_duration) * 100))

def is_over_budget(usage_percent: float, time_elapsed_percent: float) -> bool:
    """Pacing Ratio > 1.0 means over budget."""
    if time_elapsed_percent == 0:
        return usage_percent > 0
    return (usage_percent / time_elapsed_percent) > 1.0
```

### 4.4 Desktop Notification System (Windows Toasts)

Trigger native Windows notifications based on user-defined thresholds:

- **Threshold Alerts:** Toast when 5-hour usage hits 80%, 90%, and 95%
- **Reset Alerts:** Toast when session limit resets ("Session limit cleared – Full capacity restored")
- **Pace Warning:** Toast if weekly usage exceeds weekly time elapsed by more than 20%

### 4.5 Model-Specific Tracking (Future)

The API provides `seven_day_opus` for separate Opus tracking. Future UI update to include:
- Toggle between Sonnet/Opus/All views
- Stacked progress bars for multiple model limits

---

## 5. Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Credentials file missing | Show "Not authenticated" in UI, prompt to run `claude` CLI |
| Credentials file unreadable | Log error, retry on next poll cycle |
| API returns 401/403 | Token expired - show notification to re-authenticate |
| API returns 429 | Rate limited - back off to 5-minute polling interval |
| API returns 5xx | Server error - retry with exponential backoff |
| Network unavailable | Show "Offline" status, retry when network returns |

---

## 6. Configuration

Store in `~/.claude-pulse/config.json`:

```json
{
  "poll_interval_seconds": 60,
  "notifications_enabled": true,
  "notification_thresholds": [80, 90, 95],
  "show_opus_tracking": false
}
```

---

## 7. UI Specification (Unchanged)

The existing UI remains as implemented:

1. **Header:** Claude Pulse logo (speech bubble with heartbeat), title with "Claude" (white) + "Pulse" (orange)

2. **Session Usage Gauge:**
   - Outer ring (orange): Message utilization percentage
   - Inner ring (blue): Time elapsed in 5-hour window
   - Centre text: "X%" with "Resets in Xh Xm" below
   - Legend: Orange dot = Usage, Blue dot = Time

3. **Weekly Pace Section:**
   - Horizontal progress bar showing usage percentage
   - Floating marker indicating time elapsed position
   - Status pill: "Over Budget" (red) or "On Track" (green)
   - Labels: "X% used" and "X% of week elapsed"

4. **Footer:**
   - Limit Alerts toggle
   - Last refresh timestamp
   - "Refresh Claude" button (manual poll trigger)

---

## 8. File Structure

```
claude-pulse/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point, tray icon setup
│   ├── api_client.py        # Anthropic API calls
│   ├── credentials.py       # Read OAuth token from file
│   ├── calculations.py      # Pace/time calculations
│   ├── notifications.py     # Windows toast handling
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── deep_dive.py     # Main popup window
│   │   └── components.py    # Gauge, progress bar widgets
│   └── config.py            # Configuration management
├── assets/
│   └── logo.png
├── requirements.txt
├── README.md
└── setup.py
```

---

## 9. Dependencies

```
requests>=2.31.0
pystray>=0.19.4
Pillow>=10.0.0
win10toast>=0.9
```

---

## 10. Installation & Usage

### Prerequisites
- Windows 10+
- Python 3.10+
- Claude Code CLI installed and authenticated (`claude` command)

### Install
```powershell
pip install claude-pulse
```

### Run
```powershell
claude-pulse
```

The application will:
1. Read credentials from `~/.claude/.credentials.json`
2. Start polling the Anthropic usage API
3. Display tray icon with current utilization
4. Show Deep Dive window on click
