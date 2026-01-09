/**
 * Claude Pulse Popup Script - Redesigned
 */

document.addEventListener('DOMContentLoaded', async () => {
  const apiDot = document.getElementById('apiDot');
  const apiStatus = document.getElementById('apiStatus');
  const usageContainer = document.getElementById('usageContainer');
  const syncBtn = document.getElementById('syncBtn');
  const lastSyncEl = document.getElementById('lastSync');
  const ambientGlow = document.getElementById('ambientGlow');

  const SESSION_DURATION_SECONDS = 5 * 60 * 60; // 5 hours

  /**
   * Format time ago string
   */
  function formatTimeAgo(isoString) {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return date.toLocaleDateString();
  }

  /**
   * Calculate session time elapsed percentage from reset seconds
   */
  function getSessionTimeElapsed(resetSeconds) {
    if (!resetSeconds || resetSeconds <= 0) return 0;
    const elapsed = SESSION_DURATION_SECONDS - resetSeconds;
    return Math.max(0, Math.min(100, (elapsed / SESSION_DURATION_SECONDS) * 100));
  }

  /**
   * Create the session gauge with dual rings
   */
  function createSessionGauge(usagePercent, timePercent, resetTime) {
    const outerRadius = 64;
    const innerRadius = 52;
    const outerCircum = 2 * Math.PI * outerRadius;
    const innerCircum = 2 * Math.PI * innerRadius;
    const outerOffset = outerCircum - (usagePercent / 100) * outerCircum;
    const innerOffset = innerCircum - (timePercent / 100) * innerCircum;
    const highUsage = usagePercent > 80;

    return `
      <div class="gauge-section">
        <div class="section-label">Session Usage</div>
        <div class="gauge-container">
          <div class="gauge-glow${highUsage ? ' high-usage' : ''}"></div>
          <div class="gauge">
            <svg width="160" height="160" viewBox="0 0 160 160">
              <defs>
                <linearGradient id="usageGradientPop" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#ff8c42" />
                  <stop offset="50%" stop-color="#ffa060" />
                  <stop offset="100%" stop-color="${highUsage ? '#FF6B6B' : '#ffb070'}" />
                </linearGradient>
                <linearGradient id="timeGradientPop" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#00b4ff" />
                  <stop offset="100%" stop-color="#0090dd" />
                </linearGradient>
              </defs>
              <!-- Outer Track -->
              <circle cx="80" cy="80" r="${outerRadius}" class="gauge-track" stroke-width="7"/>
              <!-- Outer Progress (Usage) -->
              <circle cx="80" cy="80" r="${outerRadius}"
                class="gauge-fill-usage"
                stroke="url(#usageGradientPop)"
                stroke-width="7"
                stroke-dasharray="${outerCircum}"
                stroke-dashoffset="${outerOffset}"/>
              <!-- Inner Track -->
              <circle cx="80" cy="80" r="${innerRadius}" class="gauge-track" stroke-width="5"/>
              <!-- Inner Progress (Time) -->
              <circle cx="80" cy="80" r="${innerRadius}"
                class="gauge-fill-time"
                stroke="url(#timeGradientPop)"
                stroke-width="5"
                stroke-dasharray="${innerCircum}"
                stroke-dashoffset="${innerOffset}"/>
            </svg>
          </div>
          <div class="gauge-text">
            <div class="gauge-percent">${Math.round(usagePercent)}<span>%</span></div>
            <div class="gauge-reset">Resets in ${resetTime}</div>
            <div class="gauge-time">${Math.round(timePercent)}% of session time</div>
          </div>
        </div>
        <div class="gauge-legend">
          <div class="legend-item">
            <div class="legend-dot usage"></div>
            <span class="legend-text">Usage</span>
          </div>
          <div class="legend-item">
            <div class="legend-dot time"></div>
            <span class="legend-text">Time</span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Create the weekly pace section
   */
  function createWeeklyPace(weeklyPercent, weekElapsed, budgetStatus) {
    const isOver = budgetStatus === 'over';
    const statusClass = isOver ? 'over' : 'under';
    const statusText = isOver ? 'Over Budget' : 'On Track';

    return `
      <div class="weekly-section">
        <div class="weekly-header">
          <div class="section-label">Weekly Pace</div>
          <div class="budget-badge ${statusClass}">
            <div class="budget-dot ${statusClass}"></div>
            <span class="budget-text ${statusClass}">${statusText}</span>
          </div>
        </div>
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill ${statusClass}" style="width: ${weeklyPercent}%"></div>
          </div>
          <div class="progress-marker" style="left: ${weekElapsed}%">
            <div class="marker-line"></div>
            <div class="marker-dot"></div>
          </div>
        </div>
        <div class="weekly-labels">
          <div class="weekly-usage">${Math.round(weeklyPercent)}%<span>used</span></div>
          <div class="weekly-elapsed">${Math.round(weekElapsed)}% of week elapsed</div>
        </div>
      </div>
    `;
  }

  /**
   * Render usage data
   */
  function renderUsage(data) {
    if (!data || data.session_usage_percent === 0) {
      usageContainer.innerHTML = `
        <div class="no-data">
          <p>No usage data yet</p>
          <p>Visit claude.ai to start tracking</p>
        </div>
      `;
      return;
    }

    const resetTime = data.session_reset_formatted || 'Unknown';
    const timeElapsed = getSessionTimeElapsed(data.session_reset_seconds);

    let html = '';

    // Session gauge with dual rings
    html += createSessionGauge(data.session_usage_percent, timeElapsed, resetTime);

    // Weekly pace section
    if (data.weekly_usage_percent !== null && data.weekly_usage_percent !== undefined) {
      const weekElapsed = data.week_elapsed_percent || 0;
      html += createWeeklyPace(data.weekly_usage_percent, weekElapsed, data.budget_status);

      // Update ambient glow based on budget status
      if (data.budget_status === 'over') {
        ambientGlow.classList.add('over-budget');
      } else {
        ambientGlow.classList.remove('over-budget');
      }
    }

    usageContainer.innerHTML = html;
  }

  /**
   * Update status display
   */
  function updateStatus(status) {
    if (status.apiConnected) {
      apiDot.className = 'status-dot connected';
      apiStatus.textContent = 'Connected';
    } else {
      apiDot.className = 'status-dot disconnected';
      apiStatus.textContent = 'Disconnected';
    }

    renderUsage(status.usageData);
    lastSyncEl.textContent = `Last sync: ${formatTimeAgo(status.lastSyncTime)}`;
  }

  /**
   * Fetch status from background script
   */
  async function fetchStatus() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (response) => {
        resolve(response || { apiConnected: false });
      });
    });
  }

  /**
   * Trigger manual sync
   */
  async function triggerSync() {
    syncBtn.disabled = true;
    syncBtn.textContent = 'Syncing...';

    chrome.runtime.sendMessage({ type: 'TRIGGER_SCRAPE' }, async (response) => {
      // Wait a moment for sync to complete
      await new Promise(r => setTimeout(r, 1500));
      const status = await fetchStatus();
      updateStatus(status);
      syncBtn.disabled = false;
      syncBtn.textContent = 'Sync Now';
    });
  }

  // Initial load
  const status = await fetchStatus();
  updateStatus(status);

  // Sync button handler
  syncBtn.addEventListener('click', triggerSync);
});
