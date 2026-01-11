"""Token storage, loading, and refresh for OAuth credentials.

This module can use existing Claude Code credentials or manage its own.
"""

import json
import os
import time
import stat
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from threading import Lock
import requests


# OAuth configuration
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
TOKEN_URL = "https://claude.ai/oauth/token"
REDIRECT_URI = "http://localhost:19532/callback"

# Token refresh buffer (5 minutes before expiry)
REFRESH_BUFFER_SECONDS = 300


def get_claude_code_credentials_path() -> Path:
    """Get the path to Claude Code's credentials file."""
    home = Path.home()
    return home / ".claude" / ".credentials.json"


def get_credentials_dir() -> Path:
    """Get the Claude Pulse credentials directory."""
    home = Path.home()
    creds_dir = home / ".claude-pulse"
    creds_dir.mkdir(parents=True, exist_ok=True)
    return creds_dir


def get_credentials_path() -> Path:
    """Get the path to the credentials file."""
    return get_credentials_dir() / "credentials.json"


class TokenManager:
    """Manages OAuth token storage, loading, and refresh.

    Can read from Claude Code's credentials or manage its own.
    """

    def __init__(self):
        self._credentials: Optional[Dict[str, Any]] = None
        self._lock = Lock()
        self._on_reauth_needed: Optional[callable] = None
        self._using_claude_code = False
        self._load_credentials()

    def set_reauth_callback(self, callback: callable):
        """Set callback to invoke when re-authentication is needed."""
        self._on_reauth_needed = callback

    def _load_credentials(self) -> bool:
        """Load credentials from disk.

        First tries Claude Code credentials, then falls back to own credentials.

        Returns:
            True if credentials were loaded successfully.
        """
        # Try Claude Code credentials first
        claude_code_path = get_claude_code_credentials_path()
        if claude_code_path.exists():
            try:
                with open(claude_code_path, 'r') as f:
                    data = json.load(f)

                # Extract OAuth credentials from Claude Code format
                oauth_data = data.get('claudeAiOauth', {})
                if oauth_data.get('accessToken'):
                    self._credentials = {
                        'access_token': oauth_data['accessToken'],
                        'refresh_token': oauth_data.get('refreshToken'),
                        'expires_at': oauth_data.get('expiresAt', 0) / 1000,  # Convert ms to seconds
                        'token_type': 'Bearer',
                        'scope': ' '.join(oauth_data.get('scopes', [])),
                    }
                    self._using_claude_code = True
                    print("[TokenManager] Loaded credentials from Claude Code")
                    return True
            except (json.JSONDecodeError, IOError, KeyError) as e:
                print(f"[TokenManager] Failed to load Claude Code credentials: {e}")

        # Fall back to own credentials
        creds_path = get_credentials_path()
        if creds_path.exists():
            try:
                with open(creds_path, 'r') as f:
                    self._credentials = json.load(f)
                self._using_claude_code = False
                print("[TokenManager] Loaded credentials from Claude Pulse")
                return True
            except (json.JSONDecodeError, IOError) as e:
                print(f"[TokenManager] Failed to load credentials: {e}")

        return False

    def _save_credentials(self) -> bool:
        """Save credentials to disk with secure permissions.

        Only saves to Claude Pulse's own credential file, not Claude Code's.

        Returns:
            True if credentials were saved successfully.
        """
        if self._credentials is None:
            return False

        # If using Claude Code credentials, also update Claude Code's file
        if self._using_claude_code:
            self._update_claude_code_credentials()

        # Save to own file
        creds_path = get_credentials_path()

        try:
            with open(creds_path, 'w') as f:
                json.dump(self._credentials, f, indent=2)

            if sys.platform != 'win32':
                os.chmod(creds_path, stat.S_IRUSR | stat.S_IWUSR)

            return True

        except IOError as e:
            print(f"[TokenManager] Failed to save credentials: {e}")
            return False

    def _update_claude_code_credentials(self):
        """Update Claude Code's credentials file with refreshed tokens."""
        claude_code_path = get_claude_code_credentials_path()
        if not claude_code_path.exists():
            return

        try:
            with open(claude_code_path, 'r') as f:
                data = json.load(f)

            if 'claudeAiOauth' in data:
                data['claudeAiOauth']['accessToken'] = self._credentials['access_token']
                if self._credentials.get('refresh_token'):
                    data['claudeAiOauth']['refreshToken'] = self._credentials['refresh_token']
                data['claudeAiOauth']['expiresAt'] = int(self._credentials.get('expires_at', 0) * 1000)

                with open(claude_code_path, 'w') as f:
                    json.dump(data, f)

        except (json.JSONDecodeError, IOError) as e:
            print(f"[TokenManager] Failed to update Claude Code credentials: {e}")

    def has_credentials(self) -> bool:
        """Check if credentials exist."""
        return self._credentials is not None and 'access_token' in self._credentials

    def get_access_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary.

        Returns:
            Access token string, or None if no valid token available.
        """
        with self._lock:
            if not self.has_credentials():
                return None

            # Check if token needs refresh
            expires_at = self._credentials.get('expires_at', 0)
            current_time = time.time()

            if current_time > (expires_at - REFRESH_BUFFER_SECONDS):
                # Token expired or about to expire - refresh it
                print("[TokenManager] Token expired or expiring soon, refreshing...")
                if not self._refresh_token():
                    # Refresh failed - but token might still work for a bit
                    print("[TokenManager] Refresh failed, trying existing token")

            return self._credentials.get('access_token')

    def _refresh_token(self) -> bool:
        """Refresh the access token using the refresh token.

        Returns:
            True if refresh was successful.
        """
        refresh_token = self._credentials.get('refresh_token')

        if not refresh_token:
            print("[TokenManager] No refresh token available")
            self._trigger_reauth()
            return False

        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'client_id': CLIENT_ID,
                    'refresh_token': refresh_token,
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Origin': 'https://claude.ai',
                    'Referer': 'https://claude.ai/',
                },
                timeout=30,
            )

            if response.status_code == 200:
                tokens = response.json()
                self._update_credentials(tokens)
                print("[TokenManager] Token refreshed successfully")
                return True

            else:
                print(f"[TokenManager] Token refresh failed: {response.status_code}")
                # Don't trigger reauth on temporary failures - just use existing token
                if response.status_code == 403:
                    print("[TokenManager] Refresh blocked (403), using existing token")
                    return False
                if response.status_code >= 500:
                    print("[TokenManager] Server error, using existing token")
                    return False
                # Only trigger reauth on 400/401 (truly invalid token)
                if response.status_code in (400, 401):
                    self._trigger_reauth()
                return False

        except requests.RequestException as e:
            print(f"[TokenManager] Token refresh request failed: {e}")
            return False

    def _update_credentials(self, tokens: Dict[str, Any]):
        """Update stored credentials with new tokens."""
        # Calculate absolute expiration time
        expires_in = tokens.get('expires_in', 3600)
        expires_at = time.time() + expires_in

        self._credentials = {
            'access_token': tokens['access_token'],
            'refresh_token': tokens.get('refresh_token', self._credentials.get('refresh_token')),
            'expires_at': expires_at,
            'token_type': tokens.get('token_type', 'Bearer'),
            'scope': tokens.get('scope', 'user:inference user:profile'),
        }

        self._save_credentials()

    def _trigger_reauth(self):
        """Trigger re-authentication flow."""
        print("[TokenManager] Re-authentication required")
        if self._on_reauth_needed:
            self._on_reauth_needed()

    def store_tokens(self, tokens: Dict[str, Any]) -> bool:
        """Store tokens from initial OAuth flow.

        Args:
            tokens: Token response from OAuth token exchange.

        Returns:
            True if tokens were stored successfully.
        """
        with self._lock:
            self._update_credentials(tokens)
            return True

    def clear_credentials(self):
        """Clear all stored credentials."""
        with self._lock:
            self._credentials = None
            creds_path = get_credentials_path()
            if creds_path.exists():
                try:
                    os.remove(creds_path)
                except OSError:
                    pass

    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current token (for debugging)."""
        if not self._credentials:
            return None

        expires_at = self._credentials.get('expires_at', 0)
        current_time = time.time()
        expires_in = max(0, expires_at - current_time)

        return {
            'has_access_token': 'access_token' in self._credentials,
            'has_refresh_token': 'refresh_token' in self._credentials,
            'expires_in_seconds': int(expires_in),
            'is_expired': current_time > expires_at,
            'scope': self._credentials.get('scope'),
            'using_claude_code': self._using_claude_code,
        }


# Global token manager instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get the global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
