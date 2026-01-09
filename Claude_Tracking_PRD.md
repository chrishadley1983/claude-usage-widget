# PRD: Claude Pulse (Windows Usage Tracker)

## 1. Product Overview

Claude Pulse is a lightweight Windows utility that provides real-time visibility into Claude.ai rate limits. It bridges the gap between the browser's data and the user's desktop environment, ensuring users can manage their "message budget" without constant manual checking.

---

## 2. Updated Functional Requirements

### 4.4 [V2] Model-Specific Tracking

Claude often provides different limits for specific models (e.g., "Sonnet only" vs "All models").

- **Toggle Interface:** The Deep Dive dashboard shall include a toggle or tabbed view to switch between general limits and model-specific limits.
- **Smart Selection:** The tray icon will, by default, display the limit for the model currently being used most frequently in the active session, as reported by the harvester.
- **Visualization:** If multiple limits are active, the UI will show stacked progress bars in the detail view.

### 4.5 [V2.1] Desktop Notification System (Windows Toasts)

To prevent "cutoff shock" during a productive flow, the app will push native Windows notifications based on user-defined triggers:

- **Threshold Alerts:** Trigger a toast notification when usage hits 90% and 95%.
- **Reset Alerts:** Trigger a notification when a limit has been reset (e.g., "Session limit cleared – You have full capacity again").
- **Pace Warning:** Trigger a notification if the "Weekly Usage" exceeds the "Weekly Time Elapsed" by more than 20% (e.g., "You are using messages faster than usual this week").

---

## 3. Core Logic: The "Pace" Comparison (Refined)

The standout feature of this app is the "Pace" indicator. This helps the user visualize whether they are "on budget" for the week.

### Data Logic

The application will calculate the Pacing Ratio using the following formula:

$$
\text{Pacing Ratio} = \frac{\text{Weekly Usage \%}}{\text{Percentage of Week Elapsed}}
$$

- **Result < 1.0:** You are "Under Budget" (The bar remains blue/green).
- **Result > 1.0:** You are "Over Budget" (The bar turns orange to warn of potential early lockout).

---

## 4. Technical Specifications Summary

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Harvester | Chrome Extension (JS) | Scrapes `/settings/usage` and `POST`s JSON to localhost. |
| Local API | Python (Flask/FastAPI) | Receives data and stores it in a temporary local cache. |
| Tray Icon | Python (`pystray` + `PIL`) | Dynamically renders a percentage/graphic as the icon. |
| Notifications | `win10toast` or `plyer` | Handles the V2.1 Windows Toast alerts. |

---

## 5. User Interface (The "Deep Dive" View)

When clicking the tray icon, a window shall appear containing:

1. **Session Gauge:** Large circular progress bar showing % used and "Resets in XX:XX".
2. **Weekly Pace Gauge:** A horizontal bar showing actual usage, with a vertical "time marker" indicating where the user should be in the week.
3. **Model Toggle (V2):** Buttons to switch between "Sonnet" and "All Models" data.
4. **Notification Settings (V2.1):** A simple checkbox to enable/disable "Near Limit" alerts.
