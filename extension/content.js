/**
 * Claude Pulse Content Script
 * Scrapes usage data from Claude.ai and sends it to the background script
 */

(function() {
  'use strict';

  const API_URL = 'http://localhost:5000/api/usage';
  const SCRAPE_INTERVAL = 30000; // 30 seconds

  // Track when this page was loaded/refreshed
  const PAGE_LOAD_TIME = new Date().toISOString();

  /**
   * Parse time string like "1 hr 11 min" or "2 hr 30 min" to seconds
   */
  function parseTimeToSeconds(timeStr) {
    if (!timeStr) return null;

    let totalSeconds = 0;

    // Match "X hr" or "X hour" or "X hours"
    const hourMatch = timeStr.match(/(\d+)\s*(?:hr|hour)s?/i);
    // Match "X min" or "X minute" or "X minutes"
    const minMatch = timeStr.match(/(\d+)\s*(?:min|minute)s?/i);

    if (hourMatch) {
      totalSeconds += parseInt(hourMatch[1]) * 3600;
    }
    if (minMatch) {
      totalSeconds += parseInt(minMatch[1]) * 60;
    }

    return totalSeconds > 0 ? totalSeconds : null;
  }

  /**
   * Parse percentage from text like "75% used" or "75%"
   */
  function parsePercentage(text) {
    if (!text) return null;
    const match = text.match(/(\d+(?:\.\d+)?)\s*%/);
    return match ? parseFloat(match[1]) : null;
  }

  /**
   * Parse weekly reset time like "Resets Thu 8:00 AM" to a timestamp
   * Returns ISO string of the next reset time
   */
  function parseWeeklyResetTime(text) {
    // Match "Resets Thu 8:00 AM" or "Resets Monday 10:00 PM"
    const match = text.match(/Resets\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2}):(\d{2})\s*(AM|PM)/i);

    if (!match) return null;

    const dayNames = {
      'sun': 0, 'sunday': 0,
      'mon': 1, 'monday': 1,
      'tue': 2, 'tuesday': 2,
      'wed': 3, 'wednesday': 3,
      'thu': 4, 'thursday': 4,
      'fri': 5, 'friday': 5,
      'sat': 6, 'saturday': 6
    };

    const dayStr = match[1].toLowerCase();
    const targetDay = dayNames[dayStr];
    let hours = parseInt(match[2]);
    const minutes = parseInt(match[3]);
    const ampm = match[4].toUpperCase();

    // Convert to 24-hour format
    if (ampm === 'PM' && hours !== 12) {
      hours += 12;
    } else if (ampm === 'AM' && hours === 12) {
      hours = 0;
    }

    // Calculate the next occurrence of this day/time
    const now = new Date();
    const currentDay = now.getDay();

    // Days until target day
    let daysUntil = targetDay - currentDay;
    if (daysUntil <= 0) {
      daysUntil += 7; // Next week
    }

    // Check if it's today but later
    if (daysUntil === 7) {
      const todayReset = new Date(now);
      todayReset.setHours(hours, minutes, 0, 0);
      if (todayReset > now) {
        daysUntil = 0;
      }
    }

    const resetDate = new Date(now);
    resetDate.setDate(now.getDate() + daysUntil);
    resetDate.setHours(hours, minutes, 0, 0);

    return resetDate.toISOString();
  }

  /**
   * Scrape usage data from Claude.ai
   */
  function scrapeUsagePage() {
    const data = {
      session_usage_percent: 0,
      session_reset_seconds: null,
      weekly_usage_percent: null,
      weekly_reset_time: null,  // ISO string of when weekly resets
      model_limits: [],
      timestamp: new Date().toISOString(),
      page_load_time: PAGE_LOAD_TIME  // When the browser page was loaded/refreshed
    };

    const allText = document.body.innerText;

    // Debug: log the text we're searching (can be removed later)
    console.log('[Claude Pulse] Scanning page text...');

    // === CURRENT SESSION ===
    // Pattern: "Current session" followed by "Resets in X hr Y min" and "X% used"
    const sessionMatch = allText.match(/Current\s+session[\s\S]*?Resets\s+in\s+([\d\s\w]+?)[\s\S]*?(\d+)%\s*used/i);
    if (sessionMatch) {
      data.session_reset_seconds = parseTimeToSeconds(sessionMatch[1]);
      data.session_usage_percent = parseFloat(sessionMatch[2]);
      console.log('[Claude Pulse] Found session:', data.session_usage_percent + '%', 'resets in', sessionMatch[1]);
    }

    // === WEEKLY LIMITS - ALL MODELS ===
    // Pattern: "All models" followed by "Resets Thu 8:00 AM" and "X% used"
    const allModelsMatch = allText.match(/All\s+models[\s\S]*?(Resets\s+\w+\s+\d{1,2}:\d{2}\s*(?:AM|PM))[\s\S]*?(\d+)%\s*used/i);
    if (allModelsMatch) {
      const weeklyResetStr = allModelsMatch[1];
      data.weekly_usage_percent = parseFloat(allModelsMatch[2]);
      data.weekly_reset_time = parseWeeklyResetTime(weeklyResetStr);

      console.log('[Claude Pulse] Found weekly (all models):', data.weekly_usage_percent + '%', 'resets:', weeklyResetStr);

      data.model_limits.push({
        model_name: 'all',
        usage_percent: parseFloat(allModelsMatch[2]),
        reset_timestamp: data.weekly_reset_time,
        reset_seconds: null
      });
    }

    // === SONNET ONLY ===
    // Pattern: "Sonnet only" followed by "X% used" or "You haven't used Sonnet yet"
    const sonnetMatch = allText.match(/Sonnet\s+only[\s\S]*?(\d+)%\s*used/i);
    if (sonnetMatch) {
      const sonnetPercent = parseFloat(sonnetMatch[1]);
      console.log('[Claude Pulse] Found Sonnet:', sonnetPercent + '%');

      data.model_limits.push({
        model_name: 'sonnet',
        usage_percent: sonnetPercent,
        reset_timestamp: data.weekly_reset_time,
        reset_seconds: null
      });
    } else if (allText.includes("You haven't used Sonnet yet")) {
      console.log('[Claude Pulse] Found Sonnet: 0% (not used)');
      data.model_limits.push({
        model_name: 'sonnet',
        usage_percent: 0,
        reset_timestamp: data.weekly_reset_time,
        reset_seconds: null
      });
    }

    // === FALLBACK: Try simpler patterns if above didn't match ===
    if (data.session_usage_percent === 0) {
      // Simple pattern: just look for "X% used" anywhere
      const simpleMatches = allText.match(/(\d+)%\s*used/gi);
      if (simpleMatches && simpleMatches.length > 0) {
        const firstPercent = parsePercentage(simpleMatches[0]);
        if (firstPercent !== null) {
          data.session_usage_percent = firstPercent;
          console.log('[Claude Pulse] Fallback session:', firstPercent + '%');
        }
      }
    }

    // Look for reset time if not found
    if (data.session_reset_seconds === null) {
      const resetMatch = allText.match(/Resets\s+in\s+([\d\s\w]+?)(?:\n|$)/i);
      if (resetMatch) {
        data.session_reset_seconds = parseTimeToSeconds(resetMatch[1]);
        console.log('[Claude Pulse] Found reset time:', resetMatch[1]);
      }
    }

    return data;
  }

  /**
   * Send usage data to the local API
   */
  async function sendToAPI(data) {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        console.log('[Claude Pulse] Usage data sent successfully:', data);
        chrome.runtime.sendMessage({
          type: 'SYNC_SUCCESS',
          data: data
        });
      } else {
        console.error('[Claude Pulse] Failed to send usage data:', response.status);
        chrome.runtime.sendMessage({
          type: 'SYNC_ERROR',
          error: `HTTP ${response.status}`
        });
      }
    } catch (error) {
      console.error('[Claude Pulse] Error sending usage data:', error.message);
      chrome.runtime.sendMessage({
        type: 'SYNC_ERROR',
        error: error.message
      });
    }
  }

  /**
   * Main scrape and send function
   */
  function scrapeAndSend() {
    if (window.location.hostname !== 'claude.ai') {
      return;
    }

    const data = scrapeUsagePage();

    // Send if we got any meaningful data
    if (data.session_usage_percent > 0 || data.weekly_usage_percent > 0 || data.model_limits.length > 0) {
      sendToAPI(data);
    } else {
      console.log('[Claude Pulse] No usage data found on this page');
    }
  }

  /**
   * Initialize the content script
   */
  function init() {
    console.log('[Claude Pulse] Content script initialized on', window.location.href);

    // Initial scrape after page load
    setTimeout(scrapeAndSend, 2000);

    // Set up periodic scraping
    setInterval(scrapeAndSend, SCRAPE_INTERVAL);

    // Also scrape when visibility changes (user returns to tab)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        setTimeout(scrapeAndSend, 1000);
      }
    });

    // Listen for manual scrape requests from popup
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.type === 'MANUAL_SCRAPE') {
        scrapeAndSend();
        sendResponse({ status: 'ok' });
      }
    });
  }

  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
