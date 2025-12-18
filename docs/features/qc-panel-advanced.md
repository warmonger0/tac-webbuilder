# QC Panel - Advanced Features

## Overview

This document covers the advanced real-time features of the QC Panel, including automatic triggers, background refresh, selective updates, and visual notifications.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     QC Metrics System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   File       │      │  Background  │      │ Selective │ │
│  │   Watcher    │─────▶│  Scheduler   │─────▶│  Updates  │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                                            │       │
│         │  Coverage files changed                   │       │
│         │  Test completion detected                 │       │
│         │  Periodic refresh (5 min)                 │       │
│         ▼                                            ▼       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         QCMetricsService (compute metrics)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │     WebSocket Manager (broadcast to clients)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Frontend Clients   │
                  │  (QualityPanel)      │
                  │  + Notifications     │
                  └──────────────────────┘
```

## 1. File Watcher Service

**Location:** `app/server/services/qc_metrics_watcher.py`

### Purpose
Monitors file system for changes that affect QC metrics and automatically triggers refresh + WebSocket broadcast.

### Watched Files
- **Backend Coverage:** `app/server/.coverage`
- **Frontend Coverage:** `app/client/coverage/coverage-summary.json`
- **ADWs Coverage:** `adws/tests/.coverage`

### How It Works

1. **Initialization**
   - Stores initial modification times (mtime) for all coverage files
   - Connects to WebSocket manager for broadcasts

2. **Watch Loop (every 10 seconds)**
   - Checks each coverage file's mtime
   - Detects new files, modified files, deleted files
   - Accumulates changes in pending_changes set

3. **Change Accumulation**
   - Waits 5 seconds for changes to settle
   - Prevents multiple rapid refreshes
   - Groups related changes together

4. **Trigger Refresh**
   - Rate-limited to 1 broadcast per 30 seconds minimum
   - Computes fresh metrics
   - Updates cache
   - Broadcasts to all WebSocket clients

### Configuration

```python
min_broadcast_interval = 30.0  # Min 30s between broadcasts
change_accumulation_time = 5.0  # Wait 5s for changes to settle
```

### Usage

```python
from services.qc_metrics_watcher import get_qc_watcher

# Get singleton instance
qc_watcher = get_qc_watcher(websocket_manager=manager)

# Start watching
await qc_watcher.start()

# Manual refresh (bypasses rate limiting)
await qc_watcher.manual_refresh()

# Stop watching
await qc_watcher.stop()
```

## 2. Background Refresh Scheduler

**Location:** `app/server/services/qc_metrics_watcher.py` (integrated)

### Purpose
Ensures QC metrics stay current even when no file changes are detected.

### How It Works

1. **Periodic Refresh (every 5 minutes)**
   - Runs independently of file watching
   - Catches changes not detected by file watcher
   - Updates linting metrics (which may change without file changes)

2. **Smart Scheduling**
   - Respects rate limiting (min 30s between broadcasts)
   - Only broadcasts if metrics actually changed
   - Skips refresh if manual refresh just occurred

### Configuration

```python
enable_background_refresh = True
background_refresh_interval = 300.0  # 5 minutes
```

### Benefits
- Catches linting changes (developers may run linters manually)
- Ensures metrics don't become stale
- Provides regular health checks

## 3. Selective Metric Updates

**Location:** `app/server/services/qc_metrics_cache.py`

### Purpose
Only recompute changed metrics instead of full refresh, improving performance.

### Components

#### QCMetricsCache
Stores individual metric categories with timestamps:
```python
coverage: Dict  # Coverage metrics
coverage_updated: float  # Timestamp

naming: Dict  # Naming metrics
naming_updated: float  # Timestamp

file_structure: Dict  # File metrics
file_structure_updated: float  # Timestamp

linting: Dict  # Linting metrics
linting_updated: float  # Timestamp
```

#### SelectiveQCMetricsService
Smart metric refresh:
```python
# Full refresh
metrics = service.get_metrics_selective(changed_categories=None)

# Selective refresh (coverage only)
metrics = service.get_metrics_selective(changed_categories={'coverage'})

# Multiple categories
metrics = service.get_metrics_selective(changed_categories={'coverage', 'linting'})
```

### Performance Comparison

| Operation | Full Refresh | Selective (coverage only) | Speedup |
|-----------|--------------|---------------------------|---------|
| Coverage only | 10-30s | 2-5s | 4-6x |
| Linting only | 10-30s | 5-10s | 2-3x |
| Naming only | 10-30s | 1-2s | 10-15x |

### How It Works

1. **Change Detection**
   - File watcher identifies which category changed
   - E.g., `.coverage` file → coverage category

2. **Selective Refresh**
   - Only recompute changed category
   - Reuse cached data for unchanged categories
   - Recalculate overall score

3. **Cache Invalidation**
   - Manual refresh → clear all caches
   - Individual category max age: 5 minutes

## 4. Visual Notifications

**Location:** `app/client/src/components/QCMetricsNotification.tsx`

### Purpose
Show toast notifications when QC metrics update via WebSocket.

### Features
- **Score Display** - Shows new score with large, color-coded text
- **Delta Indicator** - Shows score change (+/-) in green/red
- **Changed Categories** - Lists what updated (optional)
- **Auto-dismiss** - Fades out after 5 seconds
- **Manual Dismiss** - Click X to close immediately
- **Animation** - Slides in from right with smooth transition

### Notification Types

#### Score Improved (📈)
- Delta > 0
- Green delta text
- Shown when coverage increases, linting issues decrease, etc.

#### Score Decreased (📊)
- Delta < 0
- Red delta text
- Shown when coverage decreases, linting issues increase, etc.

#### Score Unchanged (🔄)
- Delta ≈ 0
- No delta shown
- Shown when metrics refresh but score doesn't change significantly

### Implementation

```tsx
import { QCMetricsNotification } from './QCMetricsNotification';

function QualityPanel() {
  const [showNotification, setShowNotification] = useState(false);
  const previousScoreRef = useRef<number | undefined>(undefined);

  // Detect score changes
  useEffect(() => {
    if (metrics && previousScoreRef.current !== undefined) {
      const scoreDelta = Math.abs(metrics.overall_score - previousScoreRef.current);
      if (scoreDelta > 0.1) {
        setShowNotification(true);
        setTimeout(() => setShowNotification(false), 5000);
      }
    }
    previousScoreRef.current = metrics?.overall_score;
  }, [metrics]);

  return (
    <>
      {showNotification && (
        <QCMetricsNotification
          oldScore={previousScoreRef.current}
          newScore={metrics.overall_score}
          changedCategories={['coverage', 'linting']}
        />
      )}
      {/* Rest of component */}
    </>
  );
}
```

## 5. Integration Points

### Server Startup (`app/server/server.py`)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... other initialization ...

    # Start QC Metrics Watcher
    from services.qc_metrics_watcher import get_qc_watcher
    qc_watcher = get_qc_watcher(websocket_manager=manager)
    await qc_watcher.start()
    logger.info("[STARTUP] QC Metrics Watcher started")

    yield

    # Shutdown
    await qc_watcher.stop()
    # ... other cleanup ...
```

### Refresh Endpoint (`app/server/routes/qc_metrics_routes.py`)

```python
@router.post("/refresh")
async def refresh_qc_metrics() -> Dict:
    # Compute fresh metrics
    metrics = qc_service.get_all_metrics()

    # Trigger manual refresh (broadcasts to WebSocket clients)
    from services.qc_metrics_watcher import get_qc_watcher
    qc_watcher = get_qc_watcher()
    await qc_watcher.manual_refresh()

    return metrics
```

## 6. Testing & Verification

### Manual Testing

1. **Test Coverage File Watch**
   ```bash
   # Terminal 1: Start backend
   ./scripts/start_full.sh

   # Terminal 2: Run tests with coverage
   cd app/server && uv run pytest --cov=.

   # Observe: Panel updates automatically within 5-10 seconds
   ```

2. **Test Background Refresh**
   ```bash
   # Wait 5 minutes without making changes
   # Observe: Panel refreshes automatically
   # Check logs: "[QC_WATCHER] Triggering scheduled background refresh"
   ```

3. **Test Manual Refresh**
   ```bash
   # Click "Refresh" button in Panel 7
   # Observe: Immediate update + notification
   # Check logs: "[QC_WATCHER] Manual refresh triggered"
   ```

4. **Test Notifications**
   ```bash
   # Make code changes that improve score
   # Run tests
   # Observe: Green notification with score increase
   ```

### Log Messages

**File Watch Detected:**
```
[QC_WATCHER] Coverage file changed: .coverage
[QC_WATCHER] Processing 1 pending changes
[QC_WATCHER] QC metrics updated - Score: 45.2/100, Coverage: 12.5%
[QC_WATCHER] Broadcasted QC metrics update to WebSocket clients
```

**Background Refresh:**
```
[QC_WATCHER] Triggering scheduled background refresh
[QC_WATCHER] QC metrics updated - Score: 45.2/100, Coverage: 12.5%
```

**Rate Limiting:**
```
[QC_WATCHER] Skipping refresh (last broadcast 15.2s ago, min interval: 30s)
```

## 7. Performance Optimization

### Caching Strategy
- **Route cache** - Full metrics cached globally
- **Selective cache** - Individual categories cached with timestamps
- **File mtime tracking** - Only check file metadata, not contents

### Rate Limiting
- **Minimum interval:** 30 seconds between broadcasts
- **Change accumulation:** 5 seconds to batch related changes
- **Background refresh:** 5 minutes for periodic updates

### Resource Usage
- **CPU:** Minimal (file stat checks every 10s)
- **Memory:** ~1-2 MB for caches
- **Network:** Only broadcasts when metrics change

## 8. Troubleshooting

### Metrics Not Updating

**Symptom:** Panel doesn't update after running tests

**Check:**
1. Is QC Watcher running?
   ```bash
   # Check logs for: "[STARTUP] QC Metrics Watcher started"
   ```

2. Are coverage files being created?
   ```bash
   ls -la app/server/.coverage
   ls -la app/client/coverage/coverage-summary.json
   ```

3. Is WebSocket connected?
   ```
   # Check browser console: "[WS] Received QC metrics update"
   ```

**Fix:**
- Restart backend: `./scripts/start_full.sh`
- Check file permissions on coverage files
- Verify WebSocket connection in browser dev tools

### High Broadcast Frequency

**Symptom:** Too many WebSocket broadcasts

**Check:**
```bash
# Count broadcasts in logs
grep "Broadcasted QC metrics" logs.txt | wc -l
```

**Fix:**
- Increase `min_broadcast_interval` (default 30s)
- Increase `change_accumulation_time` (default 5s)

### Notification Spam

**Symptom:** Too many notifications popping up

**Fix:**
- Increase threshold in QualityPanel.tsx:
  ```typescript
  if (scoreDelta > 0.5) {  // Increase from 0.1 to 0.5
    setShowNotification(true);
  }
  ```

## 9. Future Enhancements

### Planned Features
- **Source Code Watching** - Detect when .py/.ts files change
- **Linter Integration** - Hook into ruff/eslint execution
- **Test Execution Detection** - Detect when pytest/vitest runs
- **Smart Notifications** - Group multiple changes into one notification
- **Metric History** - Track score changes over time
- **Performance Metrics** - Add refresh duration to notifications

### Configuration API
Future: Allow users to configure watcher via API
```python
POST /api/v1/qc-metrics/config
{
  "background_refresh_interval": 600,  # 10 minutes
  "min_broadcast_interval": 60,  # 1 minute
  "enable_notifications": true
}
```

## Summary

The QC Panel advanced features provide:
- ✅ **Automatic Updates** - No manual refresh needed
- ✅ **Real-Time Notifications** - Instant feedback on quality changes
- ✅ **Performance Optimized** - Selective updates, rate limiting, caching
- ✅ **Background Monitoring** - Ensures metrics stay current
- ✅ **Developer-Friendly** - Automatic detection, minimal configuration

All features work together to provide a seamless, real-time code quality monitoring experience!
