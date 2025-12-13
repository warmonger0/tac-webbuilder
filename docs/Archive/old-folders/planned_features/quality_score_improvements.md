# Quality Score Improvements - Implementation Plan

## Problem Statement

The quality score currently shows **95.0 across all workflows** because it lacks sufficient data to differentiate workflow quality. All workflows appear "perfect" due to missing error tracking, PR/CI integration, and review cycle metrics.

## Current Behavior

**Quality Score Logic** (workflow_analytics.py:324-391):
```python
if error_count == 0 and retry_count == 0:
    base_score = 95.0  # ← ALL workflows hit this branch
```

**Data Availability:**
- ✅ `retry_count`: Available (all currently 0)
- ❌ `error_count`: Column doesn't exist in database
- ❌ `error_types`: Not tracked
- ❌ `pr_merged`: Not tracked
- ❌ `ci_passed`: Not tracked
- ❌ `review_cycles`: Not tracked

**Result:** Uniform 95.0 score with no differentiation between workflows

## Proposed Solution

### Phase 1: Error Tracking (High Priority)
Track errors encountered during workflow execution to differentiate quality.

### Phase 2: PR/CI Integration (Medium Priority)
Track GitHub PR merge status and CI/test results.

### Phase 3: Review Metrics (Low Priority)
Track review cycles and feedback iterations.

---

## Implementation Details

### Phase 1: Error Tracking

#### 1.1 Database Schema Changes

**Add columns to `workflow_history` table:**
```sql
ALTER TABLE workflow_history ADD COLUMN error_count INTEGER DEFAULT 0;
ALTER TABLE workflow_history ADD COLUMN error_types TEXT DEFAULT '[]';  -- JSON array
ALTER TABLE workflow_history ADD COLUMN error_details TEXT DEFAULT '[]';  -- JSON array of {phase, error_type, message}
```

#### 1.2 Error Extraction Logic

**File:** `core/workflow_history.py`

Add function to parse errors from `raw_output.jsonl`:
```python
def extract_errors_from_raw_output(adw_id: str) -> dict:
    """
    Parse raw_output.jsonl to count and categorize errors.

    Returns:
        {
            "error_count": int,
            "error_types": list[str],
            "error_details": list[dict]
        }
    """
    # Look for messages with type="error" or stop_reason="error"
    # Parse error messages to categorize them
    # Return aggregated error data
```

**Error Categories to Detect:**
- `syntax_error`: Python/JS syntax errors
- `type_error`: Type mismatches
- `timeout`: Operation timeouts
- `rate_limit`: API rate limiting
- `api_quota`: API quota exhaustion
- `network`: Network/connectivity errors
- `validation`: Input validation errors
- `test_failure`: Test execution failures

#### 1.3 Integration into Sync

**File:** `core/workflow_history.py` - `sync_workflow_history()`

Add after cost data extraction (around line 940):
```python
# Extract error data from raw_output.jsonl
try:
    error_data = extract_errors_from_raw_output(adw_id)
    workflow_data["error_count"] = error_data["error_count"]
    workflow_data["error_types"] = json.dumps(error_data["error_types"])
    workflow_data["error_details"] = json.dumps(error_data["error_details"])
except Exception as e:
    logger.debug(f"[SYNC] Could not extract errors for {adw_id}: {e}")
    workflow_data["error_count"] = 0
    workflow_data["error_types"] = "[]"
    workflow_data["error_details"] = "[]"
```

#### 1.4 Quality Score Update

**File:** `core/workflow_analytics.py` - `calculate_quality_score()`

The scoring logic already supports `error_count` and `error_types`, so once the data is available, it will automatically produce differentiated scores:
- 0 errors: 90-95
- 1-2 errors: 60-80
- 3+ errors: 40-60
- Severity penalties: -5 to -10 per error type

---

### Phase 2: PR/CI Integration

#### 2.1 Database Schema Changes

**Add columns to `workflow_history` table:**
```sql
ALTER TABLE workflow_history ADD COLUMN pr_number INTEGER DEFAULT NULL;
ALTER TABLE workflow_history ADD COLUMN pr_merged INTEGER DEFAULT 0;  -- Boolean
ALTER TABLE workflow_history ADD COLUMN ci_passed INTEGER DEFAULT 0;  -- Boolean
ALTER TABLE workflow_history ADD COLUMN tests_passed INTEGER DEFAULT NULL;
ALTER TABLE workflow_history ADD COLUMN tests_failed INTEGER DEFAULT NULL;
```

#### 2.2 GitHub API Integration

**File:** `core/github_integration.py` (new file)

```python
def get_pr_status(issue_number: int) -> dict:
    """
    Fetch PR status for an issue from GitHub API.

    Returns:
        {
            "pr_number": int or None,
            "pr_merged": bool,
            "ci_passed": bool,
            "tests_passed": int,
            "tests_failed": int
        }
    """
    # Use gh CLI or GitHub API to fetch PR data
    # Parse PR status and CI check results
    # Return aggregated data
```

#### 2.3 Integration into Sync

**File:** `core/workflow_history.py` - `sync_workflow_history()`

Add for completed workflows:
```python
# Fetch PR/CI data for completed workflows
if workflow_data["status"] == "completed" and workflow_data.get("issue_number"):
    try:
        from core.github_integration import get_pr_status
        pr_data = get_pr_status(workflow_data["issue_number"])
        workflow_data.update(pr_data)
    except Exception as e:
        logger.debug(f"[SYNC] Could not fetch PR data for {adw_id}: {e}")
```

#### 2.4 Quality Score Impact

**Existing logic in `calculate_quality_score()`:**
```python
# PR/CI success bonus
pr_success = workflow.get("pr_merged", False)
ci_success = workflow.get("ci_passed", False)

if pr_success:
    base_score += 5  # +5 for merged PR
if ci_success:
    base_score += 5  # +5 for passing CI
```

---

### Phase 3: Review Metrics

#### 3.1 Database Schema Changes

**Add columns to `workflow_history` table:**
```sql
ALTER TABLE workflow_history ADD COLUMN review_cycles INTEGER DEFAULT 0;
ALTER TABLE workflow_history ADD COLUMN code_review_comments INTEGER DEFAULT 0;
ALTER TABLE workflow_history ADD COLUMN pr_iterations INTEGER DEFAULT 0;
```

#### 3.2 Review Data Extraction

**File:** `core/github_integration.py`

```python
def get_pr_review_metrics(issue_number: int) -> dict:
    """
    Extract review cycle metrics from GitHub PR.

    Returns:
        {
            "review_cycles": int,  # Number of review rounds
            "code_review_comments": int,  # Total review comments
            "pr_iterations": int  # Number of PR updates after reviews
        }
    """
    # Use GitHub API to fetch PR review history
    # Count review rounds, comments, and iterations
```

#### 3.3 Quality Score Enhancement

**File:** `core/workflow_analytics.py` - `calculate_quality_score()`

Add review cycle penalty:
```python
# Review cycle penalty (many cycles = lower quality)
review_cycles = workflow.get("review_cycles", 0) or 0
if review_cycles > 3:
    base_score -= (review_cycles - 3) * 3  # -3 per extra cycle beyond 3
elif review_cycles == 1:
    base_score += 5  # Bonus for single review cycle (clean code)
```

---

## Testing Plan

### Unit Tests

**File:** `tests/test_workflow_analytics_quality.py`

```python
def test_quality_score_with_errors():
    """Test quality score decreases with error count"""
    workflow_no_errors = {"error_count": 0, "retry_count": 0}
    workflow_with_errors = {"error_count": 3, "retry_count": 0}

    score_no_errors = calculate_quality_score(workflow_no_errors)
    score_with_errors = calculate_quality_score(workflow_with_errors)

    assert score_no_errors > score_with_errors
    assert score_with_errors < 80  # Should be penalized

def test_quality_score_pr_bonus():
    """Test quality score increases with PR merge"""
    workflow_no_pr = {"error_count": 0, "retry_count": 0}
    workflow_with_pr = {"error_count": 0, "retry_count": 0, "pr_merged": True}

    score_no_pr = calculate_quality_score(workflow_no_pr)
    score_with_pr = calculate_quality_score(workflow_with_pr)

    assert score_with_pr == score_no_pr + 5
```

### Integration Tests

1. **Error Extraction**: Create test `raw_output.jsonl` with known errors, verify extraction
2. **GitHub API**: Mock GitHub API responses, verify PR/CI data parsing
3. **Score Calculation**: Test end-to-end workflow sync with quality score updates

### Manual Testing

1. Run sync on existing workflows with various error patterns
2. Verify quality scores show differentiation (not all 95.0)
3. Check workflows with PRs get appropriate bonuses
4. Verify database schema changes applied correctly

---

## Migration Strategy

### Step 1: Database Migration
```bash
cd app/server
uv run python -c "
from core.workflow_history import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()

    # Add new columns
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN error_count INTEGER DEFAULT 0')
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN error_types TEXT DEFAULT \"[]\"')
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN error_details TEXT DEFAULT \"[]\"')

    # Phase 2 columns
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN pr_number INTEGER DEFAULT NULL')
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN pr_merged INTEGER DEFAULT 0')
    cursor.execute('ALTER TABLE workflow_history ADD COLUMN ci_passed INTEGER DEFAULT 0')

    conn.commit()
    print('Database migration complete')
"
```

### Step 2: Backfill Historical Data
```bash
# Run sync to populate error data for existing workflows
uv run python -c "
from core.workflow_history import sync_workflow_history
synced = sync_workflow_history()
print(f'Backfilled {synced} workflows with error data')
"
```

### Step 3: Verify Data Quality
```bash
# Check score distribution
sqlite3 db/workflow_history.db "
    SELECT
        ROUND(quality_score/10)*10 as score_bucket,
        COUNT(*) as count
    FROM workflow_history
    GROUP BY score_bucket
    ORDER BY score_bucket
"
```

---

## Acceptance Criteria

### Phase 1 (Error Tracking)
- [ ] Database columns added: `error_count`, `error_types`, `error_details`
- [ ] Error extraction function parses `raw_output.jsonl` correctly
- [ ] Quality scores show differentiation (not all 95.0)
- [ ] Workflows with errors have lower scores than error-free workflows
- [ ] Error categorization works for common error types

### Phase 2 (PR/CI Integration)
- [ ] Database columns added: `pr_number`, `pr_merged`, `ci_passed`
- [ ] GitHub API integration fetches PR status correctly
- [ ] Quality scores increase by +5 for merged PRs
- [ ] Quality scores increase by +5 for passing CI

### Phase 3 (Review Metrics)
- [ ] Database columns added: `review_cycles`, `code_review_comments`
- [ ] Review data extracted from GitHub API
- [ ] Quality score adjusted based on review cycle count
- [ ] Clean first-pass workflows (1 review cycle) get bonus

---

## Timeline Estimate

- **Phase 1**: 4-6 hours (error tracking)
- **Phase 2**: 6-8 hours (PR/CI integration)
- **Phase 3**: 4-6 hours (review metrics)

**Total**: 14-20 hours for complete implementation

---

## Dependencies

- GitHub CLI (`gh`) or GitHub API token for Phase 2 & 3
- Access to repository PR/review data
- Existing `raw_output.jsonl` files for historical backfill

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `raw_output.jsonl` format varies | Error extraction fails | Implement robust parsing with fallbacks |
| GitHub API rate limits | Slow backfill | Batch requests, cache results |
| Historical workflows missing data | Incomplete backfill | Accept partial data, mark as "insufficient data" |
| Schema changes break existing queries | Application errors | Test migration on copy of database first |

---

## Future Enhancements

1. **Error severity weighting**: Different penalties for warnings vs critical errors
2. **Time-to-resolution tracking**: How long errors took to fix
3. **Error recurrence detection**: Penalize repeated similar errors
4. **Test coverage metrics**: Integrate with code coverage tools
5. **Linting score integration**: Factor in code quality metrics
