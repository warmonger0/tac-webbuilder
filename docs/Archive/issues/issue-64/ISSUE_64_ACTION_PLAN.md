# Issue #64 - Workflow History Bug Fix Action Plan

**Date**: 2025-11-20
**Related Documents**: `ISSUE_64_ADW_FAILURE_ANALYSIS.md`
**Original Issue**: #64 - "table workflow_history has no column named hour_of_day"
**Failed PR**: #65 (phantom merge - never landed on main)

---

## Quick Summary

**Problem**: Database schema has `submission_hour`/`submission_day_of_week`, but Python code expects `hour_of_day`/`day_of_week`

**Root Cause**: Schema-code mismatch causing Pydantic validation failure

**ADW Status**: Thought it fixed the issue, but changes never made it to main

**Action Required**: Apply the fix that should have been deployed

---

## Immediate Fix (Quick Band-Aid)

### Option A: Column Aliases in SELECT Query

**Timeline**: 15-30 minutes
**Risk**: Low
**Reversibility**: Easy

**Implementation**:

1. Edit `app/server/core/workflow_history_utils/database.py:456-462`

**Before**:
```python
# Get paginated results
query = f"""
    SELECT * FROM workflow_history
    {where_sql}
    ORDER BY {sort_by} {sort_order}
    LIMIT ? OFFSET ?
"""
```

**After**:
```python
# Get paginated results
# Note: Use aliases to bridge schema mismatch (submission_hour -> hour_of_day)
query = f"""
    SELECT
        *,
        submission_hour as hour_of_day,
        submission_day_of_week as day_of_week
    FROM workflow_history
    {where_sql}
    ORDER BY {{sort_by}} {{sort_order}}
    LIMIT ? OFFSET ?
"""
```

2. **Test locally**:
```bash
cd app/server
uv run python -c "
from core.workflow_history_utils.database import get_workflow_history
workflows, count = get_workflow_history(limit=5)
print(f'✅ Loaded {len(workflows)} workflows')
print(f'✅ Fields: {workflows[0].keys() if workflows else \"no data\"}')
"
```

3. **Verify error is gone**:
```bash
# Start server
uv run python server.py

# In another terminal, trigger the endpoint
curl http://localhost:8000/api/workflow-history?limit=5

# Check logs - should NOT see:
# [WORKFLOW_SERVICE] Failed to get workflow history data: table workflow_history has no column named hour_of_day
```

4. **Commit and test**:
```bash
git add app/server/core/workflow_history_utils/database.py
git commit -m "fix: Add column aliases to bridge schema mismatch in workflow history query

- Database schema has submission_hour/submission_day_of_week
- Python models expect hour_of_day/day_of_week
- SELECT query now aliases columns to match Pydantic expectations
- Fixes: table workflow_history has no column named hour_of_day error

Related: #64, failed PR #65
Band-aid fix until proper migration in place"
```

5. **Run tests**:
```bash
cd app/server
uv run pytest tests/core/workflow_history_utils/test_database.py -v
uv run pytest tests/integration/test_database_operations.py -v
```

6. **Deploy to main** (if tests pass)

**Pros**:
- ✅ Quick fix (< 30 min)
- ✅ No database migration needed
- ✅ Works with existing data
- ✅ Low risk
- ✅ Easy to revert

**Cons**:
- ⚠️ Band-aid solution (doesn't fix root cause)
- ⚠️ Redundant columns in result set (minor performance impact)
- ⚠️ Still have schema-code inconsistency

---

## Long-Term Fix (Proper Schema Migration)

### Option B: Apply ADW's Migration

**Timeline**: 1-2 days (with proper testing)
**Risk**: Medium
**Reversibility**: Requires rollback migration

**Prerequisites**:
1. ✅ Option A must be deployed first (to stop immediate errors)
2. ✅ Full database backup before migration
3. ✅ Test migration on copy of production DB
4. ✅ Comprehensive test suite passing

**Implementation Steps**:

#### Step 1: Extract Migration from Failed PR

```bash
# Checkout the PR branch
git fetch origin bug-issue-64-adw-af4246c1-fix-workflow-history-column

# Cherry-pick just the migration file
git checkout origin/bug-issue-64-adw-af4246c1-fix-workflow-history-column -- \
  app/server/db/migrations/005_rename_temporal_columns.sql

# Review the migration
cat app/server/db/migrations/005_rename_temporal_columns.sql
```

#### Step 2: Review and Refine Migration

**Verify the migration handles**:
- ✅ Creates new columns (`hour_of_day`, `day_of_week`)
- ✅ Copies data from old columns
- ✅ Drops old columns safely
- ✅ Recreates indexes
- ✅ Handles NULL values
- ✅ Is idempotent (can run multiple times safely)

**Review file**: Check if migration needs updates based on current schema

#### Step 3: Test Migration on Copy of Production DB

```bash
# Create backup of production DB
cp app/server/db/workflow_history.db app/server/db/workflow_history.db.backup

# Create test copy
cp app/server/db/workflow_history.db app/server/db/workflow_history_test.db

# Run migration on test DB
sqlite3 app/server/db/workflow_history_test.db < \
  app/server/db/migrations/005_rename_temporal_columns.sql

# Verify schema
sqlite3 app/server/db/workflow_history_test.db \
  "PRAGMA table_info(workflow_history);" | grep -E "hour|day"

# Expected output:
# Should show hour_of_day and day_of_week
# Should NOT show submission_hour or submission_day_of_week

# Verify data integrity
sqlite3 app/server/db/workflow_history_test.db \
  "SELECT COUNT(*) FROM workflow_history;"

# Compare with original
sqlite3 app/server/db/workflow_history.db \
  "SELECT COUNT(*) FROM workflow_history;"

# Row counts should match
```

#### Step 4: Update Code to Remove Aliases

Once migration is confirmed working, remove the band-aid fix:

**File**: `app/server/core/workflow_history_utils/database.py:456-462`

```python
# Get paginated results
query = f"""
    SELECT * FROM workflow_history
    {where_sql}
    ORDER BY {sort_by} {sort_order}
    LIMIT ? OFFSET ?
"""
```

#### Step 5: Update Tests

Verify all tests pass with new schema:

```bash
cd app/server
uv run pytest tests/core/workflow_history_utils/ -v
uv run pytest tests/integration/test_database_operations.py -v
uv run pytest tests/e2e/test_workflow_journey.py -v
```

#### Step 6: Create Migration Runner

**Option 1**: Manual execution
```bash
# Run migration during maintenance window
sqlite3 app/server/db/workflow_history.db < \
  app/server/db/migrations/005_rename_temporal_columns.sql
```

**Option 2**: Automated migration on startup (if applicable)
```python
# In server startup code
from pathlib import Path
import sqlite3

def run_migrations():
    migrations_dir = Path(__file__).parent / "db" / "migrations"
    db_path = Path(__file__).parent / "db" / "workflow_history.db"

    # Track applied migrations
    # Run pending migrations
    # Log results
```

#### Step 7: Deployment Checklist

- [ ] Migration tested on production DB copy
- [ ] Data integrity verified
- [ ] All tests passing
- [ ] Backup created
- [ ] Rollback plan documented
- [ ] Maintenance window scheduled (if needed)
- [ ] Migration applied
- [ ] Application restarted
- [ ] Health checks pass
- [ ] Original error no longer appears in logs
- [ ] Cleanup band-aid fix (remove column aliases)

**Rollback Plan**:
```bash
# If migration fails, restore backup
cp app/server/db/workflow_history.db.backup \
   app/server/db/workflow_history.db

# Revert code changes
git revert <migration-commit-hash>

# Redeploy Option A (column aliases)
```

---

## ADW Workflow Process Improvements

### Improvement 1: Post-Merge Verification

**File**: `adws/adw_ship_iso.py`

**Add after merge**:
```python
def verify_merge_landed(pr_number: int, expected_files: list[str], target_branch: str = "main"):
    """
    Verify that PR merge actually landed on target branch.

    Args:
        pr_number: PR number that was merged
        expected_files: Files that should exist on target after merge
        target_branch: Branch to verify (default: main)

    Returns:
        bool: True if merge verified, False otherwise

    Raises:
        MergeVerificationError: If merge didn't land as expected
    """
    # 1. Get PR merge commit SHA
    merge_commit = get_pr_merge_commit(pr_number)

    # 2. Verify commit exists on target branch
    result = subprocess.run(
        ["git", "branch", "-r", "--contains", merge_commit],
        capture_output=True,
        text=True
    )

    if f"origin/{target_branch}" not in result.stdout:
        raise MergeVerificationError(
            f"PR #{pr_number} merge commit {merge_commit} not found on {target_branch}"
        )

    # 3. Verify expected files exist on target branch
    for file_path in expected_files:
        result = subprocess.run(
            ["git", "show", f"origin/{target_branch}:{file_path}"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise MergeVerificationError(
                f"Expected file {file_path} not found on {target_branch} after merge"
            )

    logger.info(f"✅ Verified PR #{pr_number} landed on {target_branch}")
    logger.info(f"✅ Verified {len(expected_files)} expected files exist")
    return True
```

**Usage in ship workflow**:
```python
# After merge API call
merge_response = github.merge_pr(pr_number)

# Don't just trust the API
if merge_response.status == 200:
    try:
        verify_merge_landed(
            pr_number=pr_number,
            expected_files=[
                "app/server/db/migrations/005_rename_temporal_columns.sql",
                ".adw-context.json"
            ],
            target_branch="main"
        )
    except MergeVerificationError as e:
        logger.error(f"❌ Merge verification failed: {e}")
        # Reopen issue
        # Alert user
        # Don't cleanup worktree
        raise
```

### Improvement 2: End-to-End Validation Phase

**File**: `adws/adw_validate_fix.py` (new)

```python
def validate_fix_applied(issue_number: int, validation_script: str | None = None):
    """
    Validate that the fix actually resolved the original issue.

    This runs after merge to confirm:
    1. Original bug is no longer reproducible
    2. Application health checks pass
    3. No regressions introduced

    Args:
        issue_number: Issue number to validate
        validation_script: Optional script to run for validation

    Returns:
        ValidationResult with success/failure and details
    """
    logger.info(f"🔍 Validating fix for issue #{issue_number}")

    # 1. Extract original error from issue description
    issue = get_github_issue(issue_number)
    original_error = extract_error_from_issue(issue)

    # 2. Attempt to reproduce original error
    reproduction_result = attempt_reproduction(original_error)

    if reproduction_result.error_still_occurs:
        return ValidationResult(
            success=False,
            message=f"Original error still occurs: {original_error}",
            details=reproduction_result
        )

    # 3. Run health checks
    health_check = run_comprehensive_health_check()

    if not health_check.all_passed:
        return ValidationResult(
            success=False,
            message="Health checks failed after merge",
            details=health_check.failures
        )

    # 4. Run custom validation script if provided
    if validation_script:
        script_result = run_validation_script(validation_script)
        if not script_result.success:
            return ValidationResult(
                success=False,
                message="Custom validation failed",
                details=script_result
            )

    logger.info(f"✅ Validation passed for issue #{issue_number}")
    return ValidationResult(success=True)
```

**Integration into ship workflow**:
```python
# After merge verification
verify_merge_landed(pr_number, expected_files)

# Before cleanup
validation = validate_fix_applied(issue_number)
if not validation.success:
    logger.error(f"❌ Fix validation failed: {validation.message}")
    # Reopen issue with validation details
    # Alert user
    # Consider reverting merge
    raise FixValidationError(validation)

# Only cleanup if validation passed
cleanup_worktree()
```

### Improvement 3: Enhanced Health Check Interpretation

**File**: `scripts/health_check.sh` or equivalent

**Current behavior**:
```bash
[WORKFLOW_SERVICE] Failed to get workflow history data: ...
✅ Backend Workflow History API: 0 workflows
   ⚠️  No workflow history data (normal for fresh installs)
```

**Improved behavior**:
```bash
# Distinguish between:
# 1. No data (empty but successful query)
# 2. Error loading data (exception occurred)

if error_in_logs:
    ❌ Backend Workflow History API: ERROR
       Last error: table workflow_history has no column named hour_of_day
       This indicates a schema mismatch bug
else if workflow_count == 0:
    ⚠️  Backend Workflow History API: 0 workflows
       No workflow history data (normal for fresh installs)
else:
    ✅ Backend Workflow History API: {workflow_count} workflows
```

**Implementation**:
- Check application logs for errors during health check
- Don't just check return status - verify data quality
- Differentiate between empty state and error state

### Improvement 4: Enhanced Review Phase Validation

**File**: `adws/adw_review_iso.py` (enhancement)

**Current Problem**: Review phase took screenshot showing "No workflow history found" but interpreted it as success

**Required Improvements**:

```python
def validate_screenshot_with_data_integrity(screenshot_path: str, page_context: dict):
    """
    Validate screenshot shows expected data, not just successful rendering.

    Args:
        screenshot_path: Path to screenshot file
        page_context: Context about what data should be visible
            {
                'expected_data_count': int,  # Expected number of items
                'database_record_count': int,  # Actual count in database
                'api_endpoint': str,  # Endpoint to verify
                'error_patterns': list[str]  # Error messages to check in logs
            }

    Returns:
        ValidationResult with screenshot analysis and data integrity checks
    """
    # 1. Analyze screenshot for visual indicators
    screenshot_analysis = analyze_screenshot_content(screenshot_path)

    # 2. Check if "no data" message is shown
    if screenshot_analysis.shows_empty_state:
        # This could be legitimate OR a silent failure
        logger.warning("⚠️  Screenshot shows empty state - validating if legitimate")

        # 3. Cross-reference with database
        if page_context['database_record_count'] > 0:
            # Red flag: DB has data but UI shows none
            logger.error(
                f"❌ Data integrity issue: DB has {page_context['database_record_count']} "
                f"records but UI shows 0"
            )

            # 4. Check backend logs for errors during screenshot
            log_errors = check_logs_for_errors(
                patterns=page_context['error_patterns'],
                timeframe='last_5_minutes'
            )

            if log_errors:
                return ValidationResult(
                    success=False,
                    message=f"Screenshot shows empty state but errors in logs: {log_errors}",
                    recommendation="Investigate backend query failures"
                )

        # 5. Test API directly
        api_response = test_api_endpoint(page_context['api_endpoint'])

        if api_response.status_code != 200 or not api_response.data:
            return ValidationResult(
                success=False,
                message="API endpoint failing or returning no data",
                details=api_response
            )

    # 6. If all checks pass, empty state is legitimate
    return ValidationResult(success=True)
```

**Integration into review workflow**:
```python
# After taking screenshot
screenshot_path = take_screenshot("workflow-history-page")

# Don't just check if page loaded
validation = validate_screenshot_with_data_integrity(
    screenshot_path,
    page_context={
        'expected_data_count': get_expected_workflow_count(),
        'database_record_count': query_database_record_count(),
        'api_endpoint': '/api/workflow-history?limit=5',
        'error_patterns': [
            'has no column named',
            'Failed to get workflow history',
            'schema mismatch'
        ]
    }
)

if not validation.success:
    logger.error(f"❌ Screenshot validation failed: {validation.message}")
    raise ReviewValidationError(validation)
```

### Improvement 5: Explicit Success Criteria

**File**: `adws/success_criteria.yaml` (new)

Define what "success" means before starting workflow:

```yaml
issue_64:
  bug_description: "table workflow_history has no column named hour_of_day"

  success_criteria:
    - name: "Error no longer appears in logs"
      validation: |
        # Start application
        # Trigger workflow history endpoint
        # Check logs for error message
        ! grep "has no column named hour_of_day" logs/server.log

    - name: "Workflow history endpoint returns data"
      validation: |
        curl http://localhost:8000/api/workflow-history?limit=5
        # Should return 200 OK with valid JSON

    - name: "Data integrity check"
      validation: |
        # DB record count should match API response count
        db_count=$(sqlite3 db/workflow_history.db "SELECT COUNT(*) FROM workflow_history;")
        api_count=$(curl -s http://localhost:8000/api/workflow-history?limit=1000 | jq '.total_count')
        [ "$db_count" -eq "$api_count" ] || exit 1

    - name: "Screenshot shows data (not empty state)"
      validation: |
        # Take screenshot and verify it shows workflow data
        # Should NOT see "No workflow history found" if DB has records

    - name: "Migration file exists on main"
      validation: |
        git show main:app/server/db/migrations/005_rename_temporal_columns.sql

    - name: "All tests pass"
      validation: |
        cd app/server && pytest tests/ -v

  rollback_plan:
    - "Restore database backup"
    - "Revert migration commit"
    - "Redeploy previous version"
```

---

## Monitoring & Alerting

### Post-Fix Monitoring

**What to watch**:
1. Error rate for workflow history endpoint
2. Query performance (aliases might impact speed slightly)
3. Database schema consistency
4. Pydantic validation errors

**Alerts to set up**:
```python
# If this error appears again
if "has no column named" in logs:
    alert("Schema mismatch error detected - fix may have regressed")

# If query time increases significantly
if query_duration > baseline * 1.5:
    alert("Workflow history query performance degraded")
```

### Metrics to Track

```python
metrics = {
    "workflow_history_query_success_rate": "Target: 100%",
    "workflow_history_query_duration_p95": "Target: < 100ms",
    "schema_validation_errors": "Target: 0",
    "data_completeness": "Target: 100% (all fields populated)"
}
```

---

## Timeline

### Immediate (Today)
- ✅ Analysis complete (`ISSUE_64_ADW_FAILURE_ANALYSIS.md`)
- ✅ Action plan documented (this file)
- 🔲 Apply Option A (column alias fix)
- 🔲 Test locally
- 🔲 Commit and deploy to main
- 🔲 Verify error is gone

### Short-term (This Week)
- 🔲 Extract migration from failed PR
- 🔲 Test migration on DB copy
- 🔲 Review and refine migration
- 🔲 Create comprehensive test suite

### Medium-term (Next Week)
- 🔲 Deploy Option B (proper migration)
- 🔲 Remove Option A aliases (cleanup)
- 🔲 Verify all tests pass with new schema
- 🔲 Document migration process

### Long-term (Ongoing)
- 🔲 Implement ADW ship verification improvements
- 🔲 Add validation phase to ADW workflows
- 🔲 Enhance health check interpretation
- 🔲 Define explicit success criteria for future ADW workflows

---

## Decision Record

**Chosen Approach**: Start with Option A, then migrate to Option B

**Rationale**:
1. **Immediate relief**: Option A stops the errors right away (low risk)
2. **Proper fix**: Option B addresses root cause (higher quality)
3. **Safety**: Two-phase approach allows validation at each step
4. **Learning**: We can test migration thoroughly while Option A is in place

**Rejected Alternatives**:
- ❌ **Do nothing**: Error continues, user experience suffers
- ❌ **Only Option A**: Leaves technical debt
- ❌ **Only Option B**: Riskier, takes longer to deploy
- ❌ **Rename Python fields**: More code changes, less semantic

---

## Open Questions

1. **Migration timing**: Should we run migration during maintenance window or automated on startup?
2. **Rollback strategy**: How quickly can we revert if issues arise?
3. **Data validation**: What additional checks should we run post-migration?
4. **ADW improvements**: Which ship verification enhancements are highest priority?
5. **Documentation**: Where should we document schema change history?

---

## Success Definition

**Immediate Fix is Successful When**:
- ✅ No more "has no column named hour_of_day" errors in logs
- ✅ Workflow history API returns data correctly
- ✅ All existing tests pass
- ✅ No performance degradation

**Long-term Fix is Successful When**:
- ✅ All above, plus:
- ✅ Database schema matches Python model expectations
- ✅ No band-aid aliases needed
- ✅ Migration is reversible and documented
- ✅ ADW ship process has verification safeguards

---

**Plan created**: 2025-11-20
**Plan owner**: Claude (Sonnet 4.5)
**Next action**: Apply Option A (column alias fix)
