/**
 * Claude Pulse Background Service Worker
 * Manages state and coordinates between content script and popup
 */

const API_BASE = 'http://localhost:5000';

// State
let lastSyncTime = null;
let lastSyncStatus = 'unknown';
let lastUsageData = null;

/**
 * Check if the local API is running
 */
async function checkAPIHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Get current usage data from the API
 */
async function getUsageData() {
  try {
    const response = await fetch(`${API_BASE}/api/usage`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error('[Claude Pulse] Error fetching usage:', error);
  }
  return null;
}

/**
 * Handle messages from content script and popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'SYNC_SUCCESS':
      lastSyncTime = new Date().toISOString();
      lastSyncStatus = 'success';
      lastUsageData = message.data;
      // Update badge to show we're connected
      chrome.action.setBadgeText({ text: '✓' });
      chrome.action.setBadgeBackgroundColor({ color: '#22c55e' });
      break;

    case 'SYNC_ERROR':
      lastSyncStatus = 'error';
      chrome.action.setBadgeText({ text: '!' });
      chrome.action.setBadgeBackgroundColor({ color: '#ef4444' });
      break;

    case 'GET_STATUS':
      // Respond with current status for popup
      (async () => {
        const apiHealthy = await checkAPIHealth();
        const usageData = await getUsageData();
        sendResponse({
          apiConnected: apiHealthy,
          lastSyncTime: lastSyncTime,
          lastSyncStatus: lastSyncStatus,
          usageData: usageData
        });
      })();
      return true; // Keep channel open for async response

    case 'TRIGGER_SCRAPE':
      // Send scrape request to active Claude.ai tab
      chrome.tabs.query({ url: 'https://claude.ai/*' }, (tabs) => {
        if (tabs.length > 0) {
          chrome.tabs.sendMessage(tabs[0].id, { type: 'MANUAL_SCRAPE' });
          sendResponse({ status: 'ok', message: 'Scrape triggered' });
        } else {
          sendResponse({ status: 'error', message: 'No Claude.ai tab found' });
        }
      });
      return true;

    case 'TRIGGER_PAGE_REFRESH':
      // Refresh the Claude.ai usage page to get fresh data
      chrome.tabs.query({ url: 'https://claude.ai/settings/usage*' }, (tabs) => {
        if (tabs.length > 0) {
          // Refresh the existing usage tab
          chrome.tabs.reload(tabs[0].id);
          sendResponse({ status: 'ok', message: 'Usage page refreshed' });
        } else {
          // Check if any Claude.ai tab is open
          chrome.tabs.query({ url: 'https://claude.ai/*' }, (claudeTabs) => {
            if (claudeTabs.length > 0) {
              // Navigate the first Claude tab to usage page
              chrome.tabs.update(claudeTabs[0].id, { url: 'https://claude.ai/settings/usage' });
              sendResponse({ status: 'ok', message: 'Navigated to usage page' });
            } else {
              sendResponse({ status: 'error', message: 'No Claude.ai tab found. Please open Claude.ai first.' });
            }
          });
        }
      });
      return true;
  }
});

/**
 * Initialize on install/update
 */
chrome.runtime.onInstalled.addListener(() => {
  console.log('[Claude Pulse] Extension installed/updated');
  chrome.action.setBadgeText({ text: '' });
});

/**
 * Periodic health check
 */
setInterval(async () => {
  const healthy = await checkAPIHealth();
  if (!healthy && lastSyncStatus === 'success') {
    lastSyncStatus = 'disconnected';
    chrome.action.setBadgeText({ text: '?' });
    chrome.action.setBadgeBackgroundColor({ color: '#f59e0b' });
  }
}, 60000); // Check every minute

/**
 * Check for refresh requests from the tray app
 */
async function checkForRefreshRequest() {
  try {
    const response = await fetch(`${API_BASE}/api/check-refresh`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (response.ok) {
      const data = await response.json();
      if (data.refresh_requested) {
        console.log('[Claude Pulse] Refresh requested by tray app');
        refreshUsagePage();
      }
    }
  } catch {
    // API not available, ignore
  }
}

/**
 * Refresh the Claude.ai usage page
 */
function refreshUsagePage() {
  chrome.tabs.query({ url: 'https://claude.ai/settings/usage*' }, (tabs) => {
    if (tabs.length > 0) {
      chrome.tabs.reload(tabs[0].id);
      console.log('[Claude Pulse] Usage page refreshed');
    } else {
      // Check if any Claude.ai tab is open
      chrome.tabs.query({ url: 'https://claude.ai/*' }, (claudeTabs) => {
        if (claudeTabs.length > 0) {
          chrome.tabs.update(claudeTabs[0].id, { url: 'https://claude.ai/settings/usage' });
          console.log('[Claude Pulse] Navigated to usage page');
        }
      });
    }
  });
}

// Check for refresh requests every 3 seconds for faster response
setInterval(checkForRefreshRequest, 3000);

/**
 * Auto-refresh the usage page every 15 minutes
 */
const AUTO_REFRESH_INTERVAL = 15 * 60 * 1000; // 15 minutes in milliseconds
let lastAutoRefresh = Date.now();

setInterval(() => {
  const now = Date.now();
  if (now - lastAutoRefresh >= AUTO_REFRESH_INTERVAL) {
    console.log('[Claude Pulse] Auto-refreshing usage page (15 min interval)');
    refreshUsagePage();
    lastAutoRefresh = now;
  }
}, 60000); // Check every minute if it's time for auto-refresh
