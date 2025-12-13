# Performance Score Improvements - Implementation Plan

## Problem Statement

The performance score shows **0.0 for ALL workflows** (100%) because `duration_seconds` is never populated. The current logic only calculates duration for completed workflows, but most workflows are still running, and even completed ones lack the required `start_time` data.

## Current Behavior

**Performance Score Logic** (workflow_analytics.py:249-321):
```python
duration = workflow.get("duration_seconds", 0) or 0
if duration <= 0:
    return 0.0  # ← ALL workflows hit this
```

**Duration Calculation Logic** (workflow_history.py:997-1006):
```python
# Calculate duration if we have start and end times
duration_seconds = None
if workflow_data.get("start_time") and workflow_data["status"] == "completed":
    duration_seconds = int((end_dt - start_dt).total_seconds())
```

**Data Availability (27 workflows):**
- ❌ `duration_seconds`: **0 workflows** have this populated (0%)
- ⚠️ `start_time`: Not consistently available in state files
- ❌ `end_time`: Never tracked
- ✅ `phase_durations`: Available for some workflows (from cost data)

**Result:** Score is 0.0 for all workflows due to missing duration data

## Root Causes

1. **Limited calculation scope**: Only calculates for `status == "completed"` workflows
2. **Missing start_time**: `adw_state.json` doesn't consistently store `start_time`
3. **No end_time tracking**: Workflows don't record completion timestamp
4. **Running workflows ignored**: Most workflows are in "running" state

---

## Proposed Solution

### Phase 1: Extract Duration from Existing Data (High Priority)
Calculate duration from timestamps in `raw_output.jsonl` for all workflows.

### Phase 2: Track Duration for Running Workflows (High Priority)
Calculate elapsed time for running workflows (now - start_time).

### Phase 3: Enhance Phase-Level Performance Tracking (Medium Priority)
Add more granular performance metrics per phase.

---

## Implementation Details

### Phase 1: Extract Duration from raw_output.jsonl

#### 1.1 Timestamp Extraction Logic

**File:** `core/workflow_history.py`

Add function to extract workflow start/end times from raw_output.jsonl:
```python
def extract_workflow_timestamps(adw_id: str) -> dict:
    """
    Extract start and end timestamps from raw_output.jsonl.

    Returns:
        {
            "start_time": str (ISO 8601),
            "end_time": str or None (ISO 8601),
            "duration_seconds": int or None
        }
    """
    project_root = Path(__file__).parent.parent.parent.parent
    agents_dir = project_root / "agents" / adw_id

    # Try to find raw_output.jsonl in agent directory or subdirectories
    raw_output_files = list(agents_dir.rglob("raw_output.jsonl"))

    if not raw_output_files:
        return {"start_time": None, "end_time": None, "duration_seconds": None}

    # Read first and last messages to get start/end times
    start_time = None
    end_time = None

    for raw_output_file in raw_output_files:
        try:
            with open(raw_output_file) as f:
                lines = f.readlines()

            if not lines:
                continue

            # Parse first message for start time
            first_msg = json.loads(lines[0])
            if "timestamp" in first_msg:
                start_time = first_msg["timestamp"]
            elif first_msg.get("type") == "system" and "subtype" in first_msg:
                # Use file creation time as fallback
                start_time = datetime.fromtimestamp(
                    raw_output_file.stat().st_ctime,
                    tz=timezone.utc
                ).isoformat()

            # Parse last message for end time
            last_msg = json.loads(lines[-1])
            if "timestamp" in last_msg:
                end_time = last_msg["timestamp"]
            # Check for result/completion message
            elif last_msg.get("type") in ["result", "system"] and last_msg.get("stop_reason"):
                end_time = datetime.fromtimestamp(
                    raw_output_file.stat().st_mtime,
                    tz=timezone.utc
                ).isoformat()

        except Exception as e:
            logger.debug(f"Could not parse timestamps from {raw_output_file}: {e}")
            continue

    # Calculate duration if we have both timestamps
    duration_seconds = None
    if start_time and end_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            duration_seconds = int((end_dt - start_dt).total_seconds())
        except Exception as e:
            logger.debug(f"Could not calculate duration: {e}")

    return {
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration_seconds
    }
```

#### 1.2 Integration into Sync

**File:** `core/workflow_history.py` - `sync_workflow_history()`

Replace the existing duration calculation (lines 997-1006) with:
```python
# Extract timestamps from raw_output.jsonl
try:
    timestamp_data = extract_workflow_timestamps(adw_id)

    # Update workflow data with extracted timestamps
    if timestamp_data["start_time"]:
        workflow_data["start_time"] = timestamp_data["start_time"]

    if timestamp_data["end_time"]:
        workflow_data["end_time"] = timestamp_data["end_time"]

    # Calculate duration based on status
    if workflow_data["status"] == "completed" and timestamp_data["duration_seconds"]:
        # Use actual duration from raw_output.jsonl
        duration_seconds = timestamp_data["duration_seconds"]
    elif workflow_data["status"] == "running" and timestamp_data["start_time"]:
        # Calculate elapsed time for running workflows
        start_dt = datetime.fromisoformat(timestamp_data["start_time"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        duration_seconds = int((now - start_dt).total_seconds())
        logger.debug(f"[SYNC] Running workflow {adw_id} elapsed: {duration_seconds}s")
    else:
        duration_seconds = None

    if duration_seconds:
        workflow_data["duration_seconds"] = duration_seconds

except Exception as e:
    logger.debug(f"[SYNC] Could not extract timestamps for {adw_id}: {e}")
    duration_seconds = None
```

#### 1.3 Database Schema Enhancement

**Add `end_time` column:**
```sql
ALTER TABLE workflow_history ADD COLUMN end_time TEXT DEFAULT NULL;
```

Update the field list in `insert_workflow_history()` and `update_workflow_history()` to include `end_time`.

---

### Phase 2: Continuous Duration Updates for Running Workflows

#### 2.1 Update Logic for Running Workflows

**File:** `core/workflow_history.py` - `sync_workflow_history()`

Ensure running workflows get their duration updated on every sync:
```python
# Update duration for existing running workflows
if existing and existing["status"] == "running":
    # Recalculate elapsed time
    if workflow_data.get("start_time") or existing.get("start_time"):
        start_time = workflow_data.get("start_time") or existing.get("start_time")
        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            new_duration = int((now - start_dt).total_seconds())

            # Update if duration increased
            old_duration = existing.get("duration_seconds", 0) or 0
            if new_duration > old_duration:
                updates["duration_seconds"] = new_duration
                logger.debug(f"[SYNC] Updated duration for running workflow {adw_id}: {new_duration}s")
        except Exception as e:
            logger.debug(f"[SYNC] Could not update duration for {adw_id}: {e}")
```

#### 2.2 Periodic Sync Scheduling

**File:** `app/server/server.py` - Add background task

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.workflow_history import sync_workflow_history

# Initialize scheduler
scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", minutes=5)
def sync_workflow_data():
    """Periodic sync of workflow history (every 5 minutes)."""
    try:
        count = sync_workflow_history()
        logger.info(f"[SCHEDULER] Synced {count} workflows")
    except Exception as e:
        logger.error(f"[SCHEDULER] Sync failed: {e}")

@app.on_event("startup")
async def start_scheduler():
    """Start background scheduler."""
    scheduler.start()
    logger.info("[SCHEDULER] Started workflow sync scheduler (5 min interval)")

@app.on_event("shutdown")
async def stop_scheduler():
    """Stop background scheduler."""
    scheduler.shutdown()
```

**Dependencies:**
```bash
# Add to requirements
uv add apscheduler
```

---

### Phase 3: Enhanced Phase-Level Performance Metrics

#### 3.1 Additional Metrics to Track

**Database Schema Additions:**
```sql
-- Add more granular performance metrics
ALTER TABLE workflow_history ADD COLUMN avg_phase_duration REAL DEFAULT NULL;
ALTER TABLE workflow_history ADD COLUMN slowest_phase TEXT DEFAULT NULL;
ALTER TABLE workflow_history ADD COLUMN phase_variance REAL DEFAULT NULL;
```

#### 3.2 Calculate Advanced Metrics

**File:** `core/workflow_history.py`

```python
def calculate_advanced_phase_metrics(phase_durations: dict) -> dict:
    """
    Calculate advanced performance metrics from phase durations.

    Returns:
        {
            "avg_phase_duration": float,  # Average duration per phase
            "slowest_phase": str,  # Phase with longest duration
            "phase_variance": float  # Variance in phase durations
        }
    """
    if not phase_durations:
        return {
            "avg_phase_duration": None,
            "slowest_phase": None,
            "phase_variance": None
        }

    durations = list(phase_durations.values())

    avg_duration = statistics.mean(durations)
    slowest_phase = max(phase_durations.items(), key=lambda x: x[1])[0]

    # Calculate variance if we have enough data points
    variance = statistics.variance(durations) if len(durations) > 1 else 0.0

    return {
        "avg_phase_duration": avg_duration,
        "slowest_phase": slowest_phase,
        "phase_variance": variance
    }
```

Add to sync logic:
```python
# Calculate advanced phase metrics
if workflow_data.get("phase_durations"):
    advanced_metrics = calculate_advanced_phase_metrics(workflow_data["phase_durations"])
    workflow_data.update(advanced_metrics)
```

#### 3.3 Performance Score Enhancement

**File:** `core/workflow_analytics.py` - `calculate_performance_score()`

Add variance penalty:
```python
# Phase variance penalty (uneven distribution = lower score)
phase_variance = workflow.get("phase_variance", 0) or 0
if phase_variance > 0:
    # High variance suggests inefficiency
    # Normalize variance by mean phase duration
    avg_phase = workflow.get("avg_phase_duration", 1) or 1
    variance_ratio = phase_variance / (avg_phase ** 2)

    if variance_ratio > 0.5:  # High variance
        base_score -= 10
        logger.info(f"High phase variance detected: {variance_ratio:.2f}")
```

---

## Testing Plan

### Unit Tests

**File:** `tests/test_workflow_duration.py`

```python
def test_extract_timestamps_from_raw_output():
    """Test timestamp extraction from raw_output.jsonl"""
    # Create mock raw_output.jsonl with known timestamps
    # Verify extraction returns correct start/end times

def test_duration_calculation_completed():
    """Test duration calculation for completed workflows"""
    workflow = {
        "start_time": "2025-11-18T10:00:00Z",
        "end_time": "2025-11-18T10:15:00Z",
        "status": "completed"
    }
    # Duration should be 900 seconds (15 minutes)

def test_duration_calculation_running():
    """Test duration calculation for running workflows"""
    workflow = {
        "start_time": "2025-11-18T10:00:00Z",
        "status": "running"
    }
    # Duration should be time since start_time

def test_performance_score_with_duration():
    """Test performance score calculation with valid duration"""
    workflow = {
        "duration_seconds": 180,  # 3 minutes
        "phase_durations": {"plan": 60, "build": 90, "test": 30}
    }
    score = calculate_performance_score(workflow)
    assert score > 0  # Should not be zero
    assert 0 <= score <= 100
```

### Integration Tests

1. **Timestamp Extraction**: Run on real `raw_output.jsonl` files, verify correct extraction
2. **Sync Updates**: Trigger sync, verify durations populated for all workflows
3. **Score Calculation**: Verify performance scores update to non-zero values

### Manual Testing

1. Run sync on existing workflows
2. Check `duration_seconds` populated for all workflows in database
3. Verify performance scores show differentiation (not all 0.0)
4. Check running workflows update duration on subsequent syncs

---

## Migration Strategy

### Step 1: Add Database Columns
```bash
cd app/server
uv run python -c "
from core.workflow_history import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()

    # Add end_time column
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN end_time TEXT DEFAULT NULL')

    # Add advanced metrics columns
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN avg_phase_duration REAL DEFAULT NULL')
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN slowest_phase TEXT DEFAULT NULL')
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN phase_variance REAL DEFAULT NULL')

    conn.commit()
    print('Database migration complete')
"
```

### Step 2: Backfill Duration Data
```bash
# Run sync to populate duration for all workflows
uv run python -c "
from core.workflow_history import sync_workflow_history
synced = sync_workflow_history()
print(f'Backfilled duration for {synced} workflows')
"
```

### Step 3: Verify Data Quality
```bash
# Check how many workflows now have duration
sqlite3 db/workflow_history.db "
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN duration_seconds IS NOT NULL AND duration_seconds > 0 THEN 1 ELSE 0 END) as with_duration,
        SUM(CASE WHEN performance_score > 0 THEN 1 ELSE 0 END) as with_perf_score
    FROM workflow_history
"
```

### Step 4: Start Background Sync
```bash
# Restart server to enable periodic sync
# Duration for running workflows will update every 5 minutes
pkill -f server.py
uv run python server.py
```

---

## Acceptance Criteria

### Phase 1 (Duration Extraction)
- [ ] Timestamp extraction function parses `raw_output.jsonl` correctly
- [ ] All workflows (27/27) have `duration_seconds` populated
- [ ] Performance scores show non-zero values
- [ ] Completed workflows show accurate total duration
- [ ] Running workflows show elapsed time

### Phase 2 (Continuous Updates)
- [ ] Background sync scheduler runs every 5 minutes
- [ ] Running workflows update duration on each sync
- [ ] Performance scores update as workflows progress
- [ ] No performance degradation from periodic syncs

### Phase 3 (Advanced Metrics)
- [ ] Phase variance calculated correctly
- [ ] Slowest phase identified
- [ ] Performance score penalizes high variance
- [ ] Advanced metrics display in UI

---

## Timeline Estimate

- **Phase 1**: 6-8 hours (timestamp extraction + integration)
- **Phase 2**: 4-6 hours (background scheduler + continuous updates)
- **Phase 3**: 4-6 hours (advanced metrics)

**Total**: 14-20 hours for complete implementation

---

## Dependencies

- Background scheduler library (`apscheduler`)
- Access to `raw_output.jsonl` files for all workflows
- Sufficient system resources for periodic sync

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `raw_output.jsonl` missing timestamps | Duration extraction fails | Use file creation/modification times as fallback |
| Large `raw_output.jsonl` files | Slow parsing | Only read first and last few lines |
| Periodic sync overhead | Server performance | Limit sync frequency, add circuit breaker |
| Clock skew issues | Incorrect durations | Validate timestamp sanity (not negative, not >1 year) |

---

## Performance Considerations

### Optimizations

1. **Lazy parsing**: Only read first/last 10 lines of `raw_output.jsonl`
2. **Caching**: Cache extracted timestamps to avoid re-parsing
3. **Incremental updates**: Only sync changed workflows
4. **Batch updates**: Group database updates to reduce commits

### Monitoring

Add metrics to track:
- Sync execution time
- Number of workflows updated per sync
- Database write latency
- Parse failures/errors

---

## Future Enhancements

1. **Real-time duration tracking**: WebSocket updates for live duration display
2. **Phase duration prediction**: Estimate remaining time for running workflows
3. **Performance anomaly detection**: Alert on unusually slow workflows
4. **Historical performance trends**: Track performance over time
5. **Comparative benchmarking**: Compare against similar workflows
6. **Phase-level bottleneck analysis**: Detailed breakdown of slow phases
7. **Resource utilization correlation**: Link duration to CPU/memory usage

---

## Comparison: Before vs After

### Before
```
Workflow d87f2a65:
  Duration: NULL
  Performance Score: 0.0
  Status: Can't evaluate performance
```

### After
```
Workflow d87f2a65:
  Duration: 847 seconds (14m 7s)
  Performance Score: 72.5
  Status: Slightly slower than similar workflows
  Bottleneck: build phase (35% of time)
  Phase Variance: Low (consistent pacing)
```

---

## Success Metrics

- **Coverage**: 100% of workflows have duration data (up from 0%)
- **Score Distribution**: Performance scores span 30-95 range (not all 0)
- **Update Frequency**: Running workflows update every 5 minutes
- **Accuracy**: Duration within ±5% of actual elapsed time
- **Performance**: Sync completes in <10 seconds for 50 workflows
