---
description: Run all preflight checks before ADW workflow launch
---

# Preflight Checks

Run comprehensive preflight checks for ADW workflow launch readiness.

## Checks Performed (9 total):

**Blocking Checks** (must pass):
1. Critical Tests - PhaseCoordinator, ADW Monitor, Database integrity
2. Git State - No uncommitted changes on main branch
3. Worktree Availability - Available slots (max 15)
4. Python Environment - uv package manager availability
5. Observability Database - PostgreSQL connection and tables

**Warning Checks** (won't block):
6. Port Availability - ADW ports (9100-9114, 9200-9214)
7. Disk Space - Minimum 1GB free
8. Hook Events Recording - Observability data collection
9. Pattern Analysis System - Analytics scripts functional

## Usage

Call the preflight checks API endpoint and display results:

**IMPORTANT:** The backend port is configured in `.ports.env` (default: BACKEND_PORT=8002)

```bash
# Read backend port from .ports.env
BACKEND_PORT=$(grep BACKEND_PORT .ports.env | cut -d '=' -f2)
curl -s http://localhost:${BACKEND_PORT}/api/v1/preflight-checks
```

## Instructions

1. Read BACKEND_PORT from .ports.env file
2. Check if backend is running on that port
3. Call the preflight checks endpoint using the configured port
4. Parse the JSON response
5. Display results in a clear, formatted way:
   - Overall status (PASSED/FAILED)
   - List all blocking failures with fixes
   - List all warnings with impact
   - Show individual check results with duration
   - Total duration

## Output Format

Display results like this:

```
🔍 Preflight Checks - <PASSED/FAILED>

<If any blocking failures:>
❌ BLOCKING FAILURES:
  • <Check Name>: <Error>
    Fix: <Fix suggestion>

<If any warnings:>
⚠️  WARNINGS:
  • <Check Name>: <Message>
    Impact: <Impact>

✅ CHECK RESULTS:
  ✓ <check_name>: <status> (<duration>ms) - <details>
  ✗ <check_name>: <status> (<duration>ms) - <details>

⏱️  Total Duration: <total_duration_ms>ms
```

If backend is not running, inform the user and suggest:
```bash
cd app/server && uv run python server.py
```

The backend will use the port specified in `.ports.env` (BACKEND_PORT, default: 8002).

## Query Parameters

- `skip_tests=true` - Skip test suite check for faster results (useful during development)

Example with skip_tests:
```bash
# Read backend port from .ports.env
BACKEND_PORT=$(grep BACKEND_PORT .ports.env | cut -d '=' -f2)
curl -s "http://localhost:${BACKEND_PORT}/api/v1/preflight-checks?skip_tests=true"
```
