# Structured Logging Guide

## Overview

The tac-webbuilder project now includes a comprehensive structured logging system that writes logs in JSONL (JSON Lines) format. This enables powerful log analysis, debugging, and observability.

## Benefits

- **Structured Data**: All logs are JSON objects with consistent schemas
- **Per-Workflow Isolation**: Each ADW workflow gets its own log file
- **Pydantic Validation**: Type-safe log events with automatic validation
- **Zero-Overhead**: Non-blocking, failures don't raise exceptions
- **Easy Analysis**: JSONL format is machine-readable and can be processed with standard tools (jq, grep, Python)
- **Dual Output**: Logs go to both JSONL files and the database (via API)

## Architecture

### Log Event Types

The system supports multiple event types with specific schemas:

1. **WorkflowLogEvent** - ADW workflow execution events
2. **PhaseLogEvent** - ADW phase-level events
3. **SystemLogEvent** - System-level operations
4. **DatabaseLogEvent** - Database query events
5. **HTTPLogEvent** - HTTP request/response events
6. **MetricsLogEvent** - Metrics and measurements

### Log File Structure

```
logs/structured/
├── workflow_adw-abc123.jsonl       # Per-workflow logs
├── workflow_adw-def456.jsonl
├── general_2025-12-02.jsonl        # System logs (date-based)
└── general_2025-12-03.jsonl
```

## Usage

### Backend Service Logging

```python
from services.structured_logger import get_structured_logger

logger = get_structured_logger()

# Log a workflow event
logger.log_workflow_event(
    adw_id="adw-abc123",
    issue_number=42,
    message="Workflow started",
    workflow_status="started",
    workflow_template="adw_sdlc_complete_iso"
)

# Log a phase event
logger.log_phase_event(
    adw_id="adw-abc123",
    issue_number=42,
    phase_name="Plan",
    phase_number=1,
    phase_status="completed",
    message="Planning phase completed",
    duration_seconds=45.2,
    tokens_used=15000,
    cost_usd=0.05
)

# Log a system event
logger.log_system_event(
    component="database",
    operation="migrate",
    status="success",
    message="Database migration completed",
    duration_ms=1500.5
)

# Log an HTTP request
logger.log_http_event(
    method="POST",
    path="/api/v1/workflows",
    status_code=201,
    duration_ms=125.5,
    message="Workflow created successfully",
    client_ip="192.168.1.1"
)

# Log a metric
logger.log_metric(
    metric_name="workflow_duration",
    metric_value=120.5,
    metric_unit="seconds",
    message="Workflow duration recorded",
    dimensions={"workflow": "sdlc", "status": "completed"}
)
```

### ADW Workflow Logging

ADW workflows automatically log to JSONL files when using the observability module:

```python
from adw_modules.observability import log_phase_completion, log_task_completion

# Log phase completion (automatically logs to JSONL + API)
log_phase_completion(
    adw_id="adw-abc123",
    issue_number=42,
    phase_name="Build",
    phase_number=3,
    success=True,
    workflow_template="adw_sdlc_complete_iso",
    started_at=phase_start_time
)

# Direct structured logging
from adw_modules.structured_logger import get_adw_logger

logger = get_adw_logger()
logger.log_workflow(
    adw_id="adw-abc123",
    issue_number=42,
    workflow_status="completed",
    message="SDLC workflow completed successfully",
    duration_seconds=300.5,
    total_tokens=50000,
    total_cost_usd=1.25
)
```

## Log Event Schema

### Base Log Event

All log events include these common fields:

```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "timestamp": "2025-12-02T10:30:00.123Z",
  "level": "info",
  "source": "adw_workflow",
  "message": "Phase completed successfully",
  "context": {},
  "correlation_id": null,
  "session_id": null,
  "request_id": null
}
```

### Workflow Log Event

```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "timestamp": "2025-12-02T10:30:00Z",
  "level": "info",
  "source": "adw_workflow",
  "message": "Phase completed successfully",
  "adw_id": "adw-abc123",
  "issue_number": 42,
  "workflow_template": "adw_sdlc_complete_iso",
  "workflow_status": "in_progress",
  "phase_name": "Plan",
  "phase_number": 1,
  "phase_status": "completed",
  "duration_seconds": 45.2,
  "tokens_used": 15000,
  "cost_usd": 0.05
}
```

### Phase Log Event

```json
{
  "event_id": "evt_def456",
  "timestamp": "2025-12-02T10:35:00Z",
  "level": "info",
  "source": "adw_workflow",
  "message": "Build phase completed",
  "adw_id": "adw-abc123",
  "issue_number": 42,
  "phase_name": "Build",
  "phase_number": 3,
  "workflow_template": "adw_sdlc_complete_iso",
  "phase_status": "completed",
  "started_at": "2025-12-02T10:30:00Z",
  "completed_at": "2025-12-02T10:35:00Z",
  "duration_seconds": 300.0,
  "tokens_used": 25000,
  "cost_usd": 0.75,
  "cache_hits": 15,
  "cache_efficiency": 60.0
}
```

## Analyzing Logs

### Using jq

```bash
# Get all events for a specific workflow
cat logs/structured/workflow_adw-abc123.jsonl | jq '.'

# Get only completed phases
cat logs/structured/workflow_adw-abc123.jsonl | jq 'select(.phase_status == "completed")'

# Calculate total cost for a workflow
cat logs/structured/workflow_adw-abc123.jsonl | jq -s 'map(.cost_usd // 0) | add'

# Get all failed phases across all workflows
cat logs/structured/workflow_*.jsonl | jq 'select(.phase_status == "failed")'

# Extract phase duration statistics
cat logs/structured/workflow_adw-abc123.jsonl | jq -s 'map(.duration_seconds // 0) | {min: min, max: max, avg: (add / length)}'
```

### Using Python

```python
import json
from pathlib import Path

# Read all log entries for a workflow
def read_workflow_logs(adw_id: str):
    log_file = Path(f"logs/structured/workflow_{adw_id}.jsonl")
    events = []
    with open(log_file, "r") as f:
        for line in f:
            events.append(json.loads(line))
    return events

# Analyze workflow performance
def analyze_workflow(adw_id: str):
    events = read_workflow_logs(adw_id)

    total_cost = sum(e.get("cost_usd", 0) for e in events)
    total_tokens = sum(e.get("tokens_used", 0) for e in events)
    phase_durations = {
        e["phase_name"]: e["duration_seconds"]
        for e in events
        if "phase_name" in e and "duration_seconds" in e
    }

    return {
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "phase_durations": phase_durations,
        "total_events": len(events)
    }

# Find longest-running phases
def find_slow_phases(threshold_seconds=60):
    slow_phases = []
    for log_file in Path("logs/structured").glob("workflow_*.jsonl"):
        with open(log_file, "r") as f:
            for line in f:
                event = json.loads(line)
                duration = event.get("duration_seconds", 0)
                if duration > threshold_seconds:
                    slow_phases.append({
                        "adw_id": event["adw_id"],
                        "phase_name": event["phase_name"],
                        "duration": duration
                    })
    return sorted(slow_phases, key=lambda x: x["duration"], reverse=True)
```

### Using grep

```bash
# Find all error events
grep '"level":"error"' logs/structured/*.jsonl

# Find specific phase
grep '"phase_name":"Test"' logs/structured/workflow_adw-abc123.jsonl

# Count completed phases
grep '"phase_status":"completed"' logs/structured/*.jsonl | wc -l
```

## Best Practices

1. **Always Include Context**: Use the `**context` parameter to add custom fields
2. **Log at Appropriate Levels**: Use ERROR for failures, INFO for normal events, DEBUG for detailed info
3. **Per-Workflow Isolation**: Workflow logs automatically go to separate files
4. **Correlation IDs**: Use correlation_id to track related events across services
5. **Structured Errors**: Include error_message and error_type for failures

## Error Handling

The structured logger is designed to be **zero-overhead**:

```python
# Logging failures don't raise exceptions
success = logger.log_workflow_event(...)
# success is False if logging failed, but execution continues
```

## Integration with Existing Logging

Structured logging complements, not replaces, the existing logging:

- **Python logging** - Standard application logs (console, file)
- **Structured logging** - Machine-readable JSONL files
- **Database logging** - Task logs stored in the database via API

All three work together:

```python
import logging
from services.structured_logger import get_structured_logger

app_logger = logging.getLogger(__name__)
structured_logger = get_structured_logger()

# Traditional logging
app_logger.info("Processing workflow")

# Structured logging
structured_logger.log_workflow_event(
    adw_id="adw-abc123",
    issue_number=42,
    message="Processing workflow",
    workflow_status="in_progress"
)

# Database logging happens via API in observability module
```

## Log Rotation and Cleanup

### Manual Cleanup

```bash
# Remove logs older than 30 days
find logs/structured -name "*.jsonl" -mtime +30 -delete

# Compress old logs
find logs/structured -name "*.jsonl" -mtime +7 -exec gzip {} \;
```

### Automated Cleanup (Future Enhancement)

A log rotation service will be added to automatically:
- Compress logs older than 7 days
- Archive logs older than 30 days
- Delete logs older than 90 days

## Troubleshooting

### Logs not being created

1. Check log directory permissions: `ls -la logs/structured/`
2. Check that `enable_file=True` (default)
3. Verify no exceptions in application logs

### Log file corruption

JSONL files are line-based, so corruption affects only one line:

```bash
# Find invalid JSON lines
while IFS= read -r line; do
  echo "$line" | jq . > /dev/null 2>&1 || echo "Invalid JSON: $line"
done < logs/structured/workflow_adw-abc123.jsonl
```

### Performance concerns

Structured logging is designed to be zero-overhead:
- Thread-safe file writing
- Non-blocking operations
- Minimal memory usage
- Failed writes don't block execution

## Future Enhancements

- **Log streaming**: Real-time log streaming to external services
- **Log aggregation**: Central log aggregation service
- **Log analytics UI**: Web-based log viewer and analysis
- **Automatic rotation**: Built-in log rotation and archiving
- **Log compression**: Automatic compression of old logs
- **Alerting**: Automatic alerts based on log patterns

## See Also

- **observability.py**: ADW workflow logging module
- **structured_logger.py**: Core logging service
- **structured_logs.py**: Pydantic log event models
- **test_structured_logger.py**: Test examples
