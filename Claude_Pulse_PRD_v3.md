# PRD: Claude Pulse v3.0 (Windows Usage Tracker)

## 1. Product Overview

Claude Pulse is a fully standalone Windows system tray utility that provides real-time visibility into Claude.ai rate limits. It implements its own OAuth 2.0 authentication flow with PKCE, eliminating any dependency on Claude Code CLI or browser extensions.

**Key Principle:** Zero dependencies on external tools. Claude Pulse handles authentication, token refresh, and API access entirely on its own.

---

## 2. Architecture Summary

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Tray App | Python (`pystray` + `PIL`) | Main application, renders icon, manages UI |
| OAuth Module | Python (`requests`) | Handles full OAuth 2.0 + PKCE flow |
| Token Manager | Python | Automatic token refresh before expiry |
| API Client | Python (`requests`) | Calls Anthropic usage API |
| Notifications | `win10toast` or `plyer` | Windows Toast alerts |
| Local Server | Python (`http.server`) | Receives OAuth callback on localhost |

**Key Benefits:**
- No Claude Code CLI required
- No browser extension required  
- Fully self-contained authentication
- Automatic token refresh (no manual re-auth)
- Works on fresh Windows install with just Python

---

## 3. Authentication Specification

### 3.1 OAuth 2.0 + PKCE Flow

Claude Pulse implements the same OAuth flow that Claude Code and OpenCode use, with PKCE (Proof Key for Code Exchange) for security.

**OAuth Configuration:**
```python
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"  # Public client ID
REDIRECT_URI = "http://localhost:19532/callback"
SCOPES = "user:inference user:profile"
```

**Endpoints:**
| Purpose | URL |
|---------|-----|
| Authorization | `https://claude.ai/oauth/authorize` |
| Token Exchange | `https://claude.ai/oauth/token` |
| Token Refresh | `https://claude.ai/oauth/token` |
| Usage API | `https://api.anthropic.com/api/oauth/usage` |

### 3.2 PKCE Implementation

```python
import hashlib
import base64
import secrets

def generate_pkce():
    """Generate PKCE code verifier and challenge."""
    # Generate 32-byte random verifier
    code_verifier = secrets.token_urlsafe(32)
    
    # Create SHA-256 hash of verifier
    digest = hashlib.sha256(code_verifier.encode()).digest()
    
    # Base64url encode the hash (no padding)
    code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip('=')
    
    return code_verifier, code_challenge
```

### 3.3 Authorization Flow

**Step 1: Generate Authorization URL**
```python
def get_authorization_url():
    code_verifier, code_challenge = generate_pkce()
    
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    auth_url = f"https://claude.ai/oauth/authorize?{urlencode(params)}"
    
    # Store verifier for token exchange
    save_verifier(code_verifier)
    
    return auth_url
```

**Step 2: Start Local Callback Server**
```python
# Start temporary HTTP server on localhost:19532
# Listen for callback with authorization code
# Extract ?code= parameter from callback URL
```

**Step 3: Exchange Code for Tokens**
```python
def exchange_code_for_tokens(authorization_code: str, code_verifier: str):
    response = requests.post(
        "https://claude.ai/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code": authorization_code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    tokens = response.json()
    # Returns: access_token, refresh_token, expires_in
    return tokens
```

### 3.4 Automatic Token Refresh

```python
def refresh_access_token(refresh_token: str):
    """Refresh the access token before it expires."""
    response = requests.post(
        "https://claude.ai/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": refresh_token
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    if response.status_code == 200:
        tokens = response.json()
        save_credentials(tokens)
        return tokens
    else:
        # Refresh token invalid - need full re-auth
        return None
```

**Proactive Refresh Logic:**
```python
def ensure_valid_token():
    """Check token expiry and refresh if needed."""
    creds = load_credentials()
    
    # Refresh 5 minutes before expiry
    buffer_seconds = 300
    expires_at = creds.get("expires_at", 0)
    
    if time.time() > (expires_at - buffer_seconds):
        new_tokens = refresh_access_token(creds["refresh_token"])
        if new_tokens:
            return new_tokens["access_token"]
        else:
            # Trigger full re-auth flow
            trigger_oauth_flow()
            return None
    
    return creds["access_token"]
```

### 3.5 Credential Storage

Store credentials in `~/.claude-pulse/credentials.json`:

```json
{
  "access_token": "sk-ant-oat01-...",
  "refresh_token": "sk-ant-ort01-...",
  "expires_at": 1736582400,
  "token_type": "Bearer",
  "scope": "user:inference user:profile"
}
```

**Security Notes:**
- File permissions set to user-only read/write (600 on Unix, ACL on Windows)
- Tokens never logged or displayed in UI
- Refresh token allows indefinite access without re-login

---

## 4. Usage API Specification

### 4.1 Endpoint

```
GET https://api.anthropic.com/api/oauth/usage
```

### 4.2 Required Headers

```python
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "claude-pulse/1.0.0",
    "Authorization": f"Bearer {access_token}",
    "anthropic-beta": "oauth-2025-04-20"
}
```

### 4.3 Response Format

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
  }
}
```

### 4.4 Field Mapping

| API Field | UI Element |
|-----------|------------|
| `five_hour.utilization` | Session Usage gauge (orange arc) |
| `five_hour.resets_at` | "Resets in Xh Xm" countdown + session time calculation |
| `seven_day.utilization` | Weekly Pace bar percentage |
| `seven_day.resets_at` | Week elapsed calculation |
| `seven_day_opus.utilization` | [Future] Opus-specific tracking |

---

## 5. Functional Requirements

### 5.1 First-Run Experience

1. User launches Claude Pulse for the first time
2. App detects no credentials exist
3. App opens system browser to Anthropic OAuth page
4. User logs in with Claude.ai credentials (Pro/Max required)
5. Browser redirects to `localhost:19532/callback`
6. App exchanges code for tokens and stores them
7. App begins polling usage API
8. Tray icon appears with current usage

### 5.2 Normal Operation

1. On startup, load credentials from `~/.claude-pulse/credentials.json`
2. Check token expiry; refresh if needed
3. Poll usage API every 60 seconds
4. Update tray icon with current utilization percentage
5. On click, show Deep Dive window

### 5.3 Session Time Calculation

```python
def calculate_session_time_percent(resets_at: str) -> float:
    """Calculate what percentage of the 5-hour session has elapsed."""
    reset_time = datetime.fromisoformat(resets_at.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    session_duration = 5 * 60 * 60  # 5 hours
    time_remaining = (reset_time - now).total_seconds()
    time_elapsed = session_duration - time_remaining
    
    return max(0, min(100, (time_elapsed / session_duration) * 100))
```

### 5.4 Weekly Pace Calculation

```python
def calculate_week_elapsed_percent(resets_at: str) -> float:
    """Calculate what percentage of the 7-day period has elapsed."""
    reset_time = datetime.fromisoformat(resets_at.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    week_duration = 7 * 24 * 60 * 60  # 7 days
    time_remaining = (reset_time - now).total_seconds()
    time_elapsed = week_duration - time_remaining
    
    return max(0, min(100, (time_elapsed / week_duration) * 100))

def is_over_budget(usage_percent: float, time_elapsed_percent: float) -> bool:
    if time_elapsed_percent == 0:
        return usage_percent > 0
    return (usage_percent / time_elapsed_percent) > 1.0
```

### 5.5 Desktop Notifications

- **80% Threshold:** "You've used 80% of your session limit"
- **90% Threshold:** "Warning: 90% of session limit used"
- **95% Threshold:** "Critical: Almost at session limit"
- **Reset Alert:** "Session limit cleared – Full capacity restored"
- **Pace Warning:** "You're using messages faster than usual this week"

---

## 6. Error Handling

| Scenario | Behaviour |
|----------|-----------|
| No credentials file | Launch OAuth flow in browser |
| Token expired | Auto-refresh using refresh token |
| Refresh token invalid | Launch OAuth flow, show notification |
| API returns 401 | Attempt token refresh, then re-auth if needed |
| API returns 429 | Back off to 5-minute polling |
| API returns 5xx | Retry with exponential backoff |
| Network unavailable | Show "Offline" status, retry when available |
| OAuth callback timeout | Show error, offer retry button |

---

## 7. Configuration

Store in `~/.claude-pulse/config.json`:

```json
{
  "poll_interval_seconds": 60,
  "notifications_enabled": true,
  "notification_thresholds": [80, 90, 95],
  "show_opus_tracking": false,
  "start_with_windows": false,
  "callback_port": 19532
}
```

---

## 8. UI Specification

### 8.1 Header
- Claude Pulse logo (speech bubble with heartbeat)
- Title: "Claude" (white) + "Pulse" (orange)
- Subtitle: "USAGE MONITOR"

### 8.2 Session Usage Gauge
- Outer ring (orange): Message utilization %
- Inner ring (blue): Time elapsed in 5-hour window
- Centre: "X%" with "Resets in Xh Xm"
- Legend: Orange = Usage, Blue = Time

### 8.3 Weekly Pace Section
- Horizontal progress bar
- Floating marker for time elapsed
- Status: "Over Budget" (red) or "On Track" (green)
- Labels: "X% used" / "X% of week elapsed"

### 8.4 Footer
- Limit Alerts toggle
- Last refresh timestamp
- "Refresh Claude" button

---

## 9. File Structure

```
claude-pulse/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── oauth/
│   │   ├── __init__.py
│   │   ├── flow.py          # OAuth authorization flow
│   │   ├── pkce.py          # PKCE generation
│   │   ├── callback.py      # Local HTTP server for callback
│   │   └── tokens.py        # Token storage and refresh
│   ├── api_client.py        # Anthropic usage API calls
│   ├── calculations.py      # Pace/time calculations
│   ├── notifications.py     # Windows toast handling
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── deep_dive.py     # Main popup window
│   │   └── components.py    # Gauge widgets
│   └── config.py            # Configuration management
├── assets/
│   └── logo.png
├── requirements.txt
├── README.md
└── setup.py
```

---

## 10. Dependencies

```
requests>=2.31.0
pystray>=0.19.4
Pillow>=10.0.0
win10toast>=0.9
```

No external CLI tools or browser extensions required.

---

## 11. Installation & Usage

### Prerequisites
- Windows 10+
- Python 3.10+
- Claude Pro or Max subscription

### Install
```powershell
pip install claude-pulse
```

### Run
```powershell
claude-pulse
```

### First Run
1. Browser opens to Claude.ai login
2. Authorize Claude Pulse
3. Browser shows "Authentication successful"
4. Tray icon appears

### Subsequent Runs
- App loads saved credentials
- Tokens refresh automatically
- No manual login required

---

## 12. Security Considerations

1. **PKCE:** Prevents authorization code interception
2. **Localhost callback:** No external server receives tokens
3. **File permissions:** Credentials file restricted to current user
4. **No logging:** Tokens never written to logs
5. **Token rotation:** Refresh tokens may be rotated by Anthropic
6. **Proactive refresh:** Tokens refreshed before expiry to avoid gaps

---

## 13. Known Limitations

1. **Subscription required:** Only works with Claude Pro/Max (not API keys)
2. **Token lifetime:** Access tokens expire ~1 hour; refresh tokens may expire after extended periods of inactivity
3. **Single user:** Designed for single-user desktop use
4. **Windows only:** Current implementation targets Windows (cross-platform possible)
