# CalorieTracker Product Spec

## Purpose
CalorieTracker helps users log meals quickly, understand nutritional intake, and maintain healthy streaks across devices with a focus on mobile-first experiences.

## User Journeys
### 1. Onboarding
- **Entry**: User lands on welcome screen with brief value proposition.
- **Flow**:
  1. Create account (email/password or OAuth).
  2. Set profile basics (age range, height/weight, goals).
  3. Select dietary preferences/allergies.
  4. Grant optional camera permission for photo logging.
  5. See sample dashboard with first suggested log.
- **Exit**: User arrives at dashboard with a primary CTA to log a meal.

### 2. Manual Logging
- **Entry**: User taps “Log Meal.”
- **Flow**:
  1. Choose meal type (breakfast/lunch/dinner/snack).
  2. Search food database and/or enter custom item.
  3. Adjust serving size and confirm nutrition summary.
  4. Save entry and view updated daily totals.
- **Exit**: Log is saved with updated calorie/macronutrient totals and history.

### 3. Photo Logging
- **Entry**: User taps “Photo Log.”
- **Flow**:
  1. Capture or upload photo.
  2. Optionally add meal type/time and notes.
  3. Run on-device or server inference to estimate items/portion sizes.
  4. User reviews and edits suggested items before saving.
- **Exit**: Log is saved with photo attached and nutrition estimates.

### 4. Streaks & Progress
- **Entry**: User opens “Streaks/Progress” view from dashboard.
- **Flow**:
  1. See current streak, longest streak, and missed days.
  2. View daily/weekly goals and completion status.
  3. Receive reminders or nudge to log if at risk of breaking streak.
- **Exit**: User is encouraged to maintain streak and return to logging.

## Platform Constraints
### Android Web / PWA Capabilities
- **Installability**: Must support PWA install prompt on compatible Android browsers (Chrome, Samsung Internet).
- **Permissions**: Camera access limited to user gesture; no background camera access.
- **Storage**: Must respect storage quotas for IndexedDB/Cache Storage; avoid large offline photo caches by default.
- **Push Notifications**: Use Web Push; require user opt-in.

### Offline Caching
- **Critical paths**: Dashboard shell, recent logs, and food search cache should be available offline.
- **Sync**: Queue logs offline and sync when online (conflict resolution by timestamp).
- **Photo Handling**: Store compressed thumbnails offline; full-res photos only if user explicitly enables offline photo storage.

## Compliance Needs
### Data Privacy
- **Photos**: Treat meal photos as sensitive user content.
  - Encrypt in transit (TLS) and at rest.
  - Provide deletion controls (single photo and account-wide deletion).
- **Health Data**: Calorie and nutrition logs are health-adjacent data.
  - Minimize data collection to essentials.
  - Provide data export (CSV/JSON) and account deletion.
  - Show clear consent for data processing during onboarding.
- **Access Controls**: Enforce user-level authorization checks for all log/photo retrieval.

## Non-Functional Requirements
### Latency Targets
- App shell load: **< 2.5s** on 4G for first load.
- Food search results: **< 300ms** P95 with cached results; **< 800ms** P95 uncached.
- Photo upload: **< 5s** for 2MB image on 4G.

### Model Inference Limits
- Photo inference time: **< 2s** P95 on server.
- Maximum image size for inference: **5MB**; auto-compress above 2MB.
- Rate limit: **10 inferences/min/user** to protect capacity.

### Storage Quotas
- Local offline cache: **<= 50MB** by default.
- Photos offline: **<= 100MB** only if user enables offline photo storage.
- Log history cache: last **30 days** by default, with pagination for older data.

## Acceptance Criteria
- **Onboarding**
  - User can complete onboarding in < 2 minutes without errors.
  - Consent for data processing is explicitly captured before first log.
- **Manual Logging**
  - User can add a custom food entry and see updated totals immediately.
  - Offline logging queues and syncs within 30 seconds of reconnection.
- **Photo Logging**
  - User can review/edit model suggestions before saving.
  - Photos are encrypted in transit and at rest.
- **Streaks**
  - Streak updates within 10 seconds after log save.
  - Missed-day detection reflects user’s local time zone.
- **Platform Constraints**
  - PWA install prompt appears on eligible Android browsers.
  - Offline dashboard shell loads without network.
- **Compliance**
  - User can export data and delete account from settings.
  - Access to logs/photos is blocked for unauthorized users.
